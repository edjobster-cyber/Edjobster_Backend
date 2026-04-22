from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
import logging
from django.urls import reverse
from datetime import datetime
from .models import Interview, InterviewCandidateStatus, InterviewerStatus
from candidates.models import Candidate
from settings.models import Contacts

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _format_date_to_dd_mm_yyyy(date_str):
    """Convert date from YYYY-MM-DD format to dd/mm/yyyy format"""
    if not date_str:
        return ""
    
    try:
        # Parse the date string (YYYY-MM-DD format)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # Format to dd/mm/yyyy
        return date_obj.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        # If parsing fails, return the original string
        return date_str

def _extract_schedule_context(interview, instance, isurlflag):
    """Builds a dict with schedule and display info from dynamic data.
    
    Args:
        interview: The Interview instance
        instance: Either InterviewCandidateStatus or InterviewerStatus instance
        isurlflag: String indicating user type ('isinterviewer' or 'iscandidate')
    """
    from .models import InterviewCandidateStatus, InterviewerStatus
    
    dinfo = interview.dynamic_interview_data or {}
    schedule = dinfo.get("schedule") or dinfo.get("Schedule") or {}
    basic = dinfo.get("basic_info", {})

    title = basic.get("interview_title") or interview.title or "Interview"
    mode = basic.get("mode_of_interview") or ""
    meeting_link = (
        basic.get("interview_link")
        or basic.get("interview_linklocation")
        or interview.meeting_link
        or ""
    )
    date = schedule.get("date") or ""
    formatted_date = _format_date_to_dd_mm_yyyy(date)
    start_time = schedule.get("time") or schedule.get("start_time") or ""
    end_time = (
        schedule.get("end_time")
        or schedule.get("time_end")
        or ""
    )
    tzid = (schedule.get("time_zone") or {}).get("id") or ""

    interviewer_names = ", ".join([getattr(i, "name", str(i)) for i in interview.interviewers.all()])
    candidate_names = ", ".join([
        (f"{getattr(c, 'first_name', '')} {getattr(c, 'last_name', '')}").strip()
        for c in interview.candidate.all()
    ])

    # ICS link (best-effort)
    try:
        base = getattr(settings, "API_URL", "")
        ics_url = f"{base}{reverse('interview-ics', args=[interview.id])}"
    except Exception:
        ics_url = ""

    # Action links with tokens for candidate actions
    base_url = settings.APP_URL.rstrip('/')
    action_url = base_url
    
    # Initialize context with common fields
    context = {
        "jobTitle": title,
        "companyName": getattr(getattr(interview, "company", None), "name", "Edjobster"),
        "startAt": f"{formatted_date} {start_time}".strip(),
        "endAt": end_time,
        "timezone": tzid,
        "interviewerNames": interviewer_names,
        "candidateNames": candidate_names,
        "mode": mode,
        "meetingLink": meeting_link,
        "icsUrl": ics_url,
        # action buttons
        "headlessCandidateUrl": action_url,
    }
    
    # Handle InterviewCandidateStatus
    if isinstance(instance, InterviewCandidateStatus):
        candidate = getattr(instance, 'candidate', None)
        if candidate and hasattr(instance, 'headless_token'):
            token = instance.headless_token
            context.update({
                "headlessAcceptUrl": f"{base_url}/headless/{instance.id}/iscandidate/{token}",
                "headlessDeclineUrl": f"{base_url}/headless/{instance.id}/iscandidate/{token}",
                "headlessRescheduleUrl": f"{base_url}/headless/{instance.id}/iscandidate/{token}",
                "rescheduleUrl": f"{base_url}/headless/{instance.id}/iscandidate/{token}",
                "status": instance.status,
                "statusDisplay": instance.get_status_display(),
            })
    
    # Handle InterviewerStatus
    elif isinstance(instance, InterviewerStatus):
        interviewer = getattr(instance, 'interviewer', None)
        if interviewer and hasattr(instance, 'headless_token'):
            token = instance.headless_token
            context.update({
                "headlessAcceptUrl": f"{base_url}/headless/{instance.id}/isinterviewer/{token}",
                "headlessDeclineUrl": f"{base_url}/headless/{instance.id}/isinterviewer/{token}",
                "headlessRescheduleUrl": f"{base_url}/headless/{instance.id}/isinterviewer/{token}",
                "rescheduleUrl": f"{base_url}/headless/{instance.id}/isinterviewer/{token}",
                "status": instance.status,
                "statusDisplay": instance.get_status_display(),
            })
    
    # Fallback for when instance is not a status model
    else:
        context.update({
            "headlessAcceptUrl": action_url,
            "headlessDeclineUrl": action_url,
            "headlessRescheduleUrl": action_url,
            "rescheduleUrl": action_url,
        })
    
    return context

def _render_and_send(subject, to_email, context, company=None):
    if not to_email:
        print(f"[Interview Email] SKIP send: empty email for subject='{subject}'")
        logger.warning(f"Interview email skipped (no recipient): {subject}")
        return
    
    # Get company-specific email settings
    email_settings = None
    if company:
        try:
            from candidates.models import EmailSettings
            email_settings = EmailSettings.objects.filter(company=company).order_by('-created_at').first()
            print(f"[Interview Email] Found email settings for company {company}: {email_settings}")
        except Exception as e:
            print(f"[Interview Email] Error getting email settings for company {company}: {e}")
    
    try:
        print(f"[Interview Email] SENDING to={to_email} subject='{subject}'")
        
        # Choose template based on status
        status = context.get('status', '').lower()
        if status == 'rescheduled':
            template_name = "interview_rescheduled.html"
            email_type = "Rescheduled"
        else:
            template_name = "interview_scheduled.html"
            email_type = "Scheduled"
            
        html = render_to_string(template_name, context)
        plain = (
            f"Interview {email_type}: {context.get('jobTitle','Interview')}\n"
            f"When: {context.get('startAt','')} {('to ' + context['endAt']) if context.get('endAt') else ''}"
            f" {('(' + context['timezone'] + ')') if context.get('timezone') else ''}\n"
        )
        
        # Use company-specific email settings if available
        if email_settings:
            from django.core.mail import get_connection
            connection = get_connection(
                backend=email_settings.email_backend,
                host=email_settings.email_host,
                port=email_settings.email_port,
                username=email_settings.sender_mail,
                password=email_settings.auth_password,
                use_ssl=email_settings.email_ssl,
                use_tls=email_settings.email_tls
            )
            send_mail(
                subject,
                plain,
                email_settings.sender_mail,
                [to_email],
                html_message=html,
                fail_silently=False,
                connection=connection,
            )
            print(f"[Interview Email] SENT with company SMTP → {to_email}")
        else:
            # Fallback to default email settings
            send_mail(
                subject,
                plain,
                settings.DEFAULT_FROM_EMAIL,
                [to_email],
                html_message=html,
                fail_silently=False,
            )
            print(f"[Interview Email] SENT with default SMTP → {to_email}")
            
    except Exception as e:
        logger.error(f"Failed to send interview email to {to_email}: {e}", exc_info=True)
        print(f"[Interview Email] ERROR sending to {to_email}: {e}")

def _get_candidate_email(candidate):
    """Prefer candidate.email; fallback to webform_candidate_data['Personal Details']['email']"""
    email = getattr(candidate, "email", None)
    if email:
        print(f"[Email Resolve] Candidate {candidate.id}: using candidate.email={email}")
        return email
    try:
        wf = getattr(candidate, "webform_candidate_data", None)
        if isinstance(wf, dict):
            personal = wf.get("Personal Details") or wf.get("personal_details") or {}
            email = personal.get("email") or personal.get("Email")
            if email:
                print(f"[Email Resolve] Candidate {candidate.id}: using webform email={email}")
                return email
    except Exception:
        pass
    print(f"[Email Resolve] Candidate {candidate.id}: no email found")
    return None

def send_interviewer_notification(instance, created):
    """Send notification to interviewer when their interview status changes"""
    interview = instance.interview
    interviewer = instance.interviewer
    base_ctx = _extract_schedule_context(interview,instance,"isinterviewer")
    ctx = {
        **base_ctx,
        "candidateName": getattr(interviewer, "name", "Interviewer"),  # greeting for interviewer
        "isInterviewer": True,
        "year": interview.created.year if interview.created else "",
        "status": instance.status,  # Add status to context
    }
    # token = getattr(instance, "headless_token", None)
    # if token:
    #     try:
    #         base = getattr(settings, "APP_URL", "")
    #         # reschedule_url = f"{base}/reschedule/{token}"
    #         ctx["headlessRescheduleUrl"] = reschedule_url
    #         ctx["rescheduleUrl"] = reschedule_url
    #     except Exception:
    #         pass
    # Customize subject line for interviewers when status is scheduled
    if instance.status == 'scheduled':
        subject = f"Interview Assigned: {base_ctx['candidateNames']} — {base_ctx['startAt']} ({base_ctx['timezone']})"
    else:
        subject = f"Interview {instance.get_status_display()}: {base_ctx['jobTitle']} — {base_ctx['startAt']} ({base_ctx['timezone']})"
    _render_and_send(subject, getattr(interviewer, "email", None), ctx, company=interview.company)

def send_candidate_notification(instance, created):
    """Send notification to candidate when their interview status changes"""
    interview = instance.interview
    candidate = instance.candidate
    base_ctx = _extract_schedule_context(interview,instance,"iscandidate")
    ctx = {
        **base_ctx,
        "candidateName": f"{getattr(candidate, 'first_name', '')} {getattr(candidate, 'last_name', '')}".strip(),
        "isInterviewer": False,
        "year": interview.created.year if interview.created else "",
        "status": instance.status,  # Add status to context
    }
    # Override action URLs with headless tokenized URLs for rescheduling
    # token = getattr(instance, "headless_token", None)
    # if token:
    #     try:
    #         base = getattr(settings, "APP_URL", "")
    #         reschedule_url = f"{base}/reschedule/{token}"
    #         ctx["headlessRescheduleUrl"] = reschedule_url
    #         ctx["rescheduleUrl"] = reschedule_url
    #     except Exception:
    #         pass
    subject = f"Interview {instance.get_status_display()}: {base_ctx['jobTitle']} — {base_ctx['startAt']} ({base_ctx['timezone']})"
    _render_and_send(subject, _get_candidate_email(candidate), ctx, company=interview.company)

@receiver(post_save, sender=InterviewCandidateStatus)
def handle_candidate_status_change(sender, instance, created, **kwargs):
    """Send emails when InterviewCandidateStatus is created; ignore updates."""
    # Skip if email is not configured
    if not getattr(settings, 'EMAIL_HOST', None):
        return

    if created:
        send_candidate_notification(instance, created)

@receiver(post_save, sender=InterviewerStatus)
def handle_interviewer_status_change(sender, instance, created, **kwargs):
    """Send emails when InterviewerStatus is created; ignore updates."""
    # Skip if email is not configured
    if not getattr(settings, 'EMAIL_HOST', None):
        return

    if created:
        send_interviewer_notification(instance, created)


# (Removed) Emails on Interview creation are now handled by status creation signals above.
