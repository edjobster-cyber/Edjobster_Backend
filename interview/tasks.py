from datetime import datetime, date, timedelta
from django.utils import timezone
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from settings.models import Feature
from settings.decorators import check_feature_availability, check_feature_access

from .models import Interview, InterviewCandidateStatus, InterviewerStatus
import pytz
from candidates.models import Candidate

OFFSETS = {
    "10 minutes before": 10,
    "15 minutes before": 15,
    "30 minutes before": 30,
    "1 hour before": 60,
    "2 hours before": 120,
    "24 hours before": 1440
}

# @shared_task
# def send_interview_reminders():
#     """Send reminders for all interviews based on dynamic_interview_data and Candidate model linkage."""
#     # print(f"[INTERVIEW_REMINDER] Starting task execution at {timezone.now()}")
#     now = timezone.now()
#     # Get all interviews that have dynamic_interview_data with schedule information
#     interviews = Interview.objects.filter(dynamic_interview_data__isnull=False).exclude(dynamic_interview_data={})
#     # print(f"[INTERVIEW_REMINDER] Found {interviews.count()} interviews with dynamic data")
    
#     for interview in interviews:
#         dinfo = interview.dynamic_interview_data or {}
#         schedule = dinfo.get("schedule") or dinfo.get("Schedule") or {}
#         basic = dinfo.get("basic_info", {})
#         reminders = (dinfo.get("Reminder Settings", {}).get("select_reminders") or
#                      dinfo.get("reminder_settings", {}).get("select_reminders") or [])
#         # print(f"[INTERVIEW_REMINDER] Reminders configured: {reminders}")
#         # Skip if no reminders configured
#         if not reminders:
#             continue

#         # Get date and time from schedule
#         dt_str = schedule.get("date")
#         tm_str = schedule.get("time") or schedule.get("start_time")
#         tzinfo = schedule.get("time_zone", {}).get("id") or "UTC"
        
#         # Fallback: skip interview if missing time
#         if not dt_str or not tm_str:
#             continue
            
#         try:
#             # Parse time - handle both HH:MM and HH:MM:SS formats
#             if len(tm_str.split(':')) == 2:
#                 # HH:MM format
#                 naive_dt = datetime.datetime.strptime(f"{dt_str} {tm_str}", "%Y-%m-%d %H:%M")
#             else:
#                 # HH:MM:SS format
#                 naive_dt = datetime.datetime.strptime(f"{dt_str} {tm_str}", "%Y-%m-%d %H:%M:%S")
            
#             # Handle timezone
#             if tzinfo and tzinfo != "UTC":
#                 try:
#                     tzone = pytz.timezone(tzinfo)
#                     interview_start = tzone.localize(naive_dt)
#                 except pytz.exceptions.UnknownTimeZoneError:
#                     # Fallback to UTC if timezone is unknown
#                     tzone = pytz.UTC
#                     interview_start = tzone.localize(naive_dt)
#             else:
#                 tzone = pytz.UTC
#                 interview_start = tzone.localize(naive_dt)
                
#         except Exception as e:
#             print(f"Error parsing datetime for interview {interview.id}: {e}")
#             continue

#         # Email info
#         title = basic.get("interview_title") or interview.title or "Interview"
#         mode = basic.get("mode_of_interview") or "Online"
#         meeting_link = basic.get("interview_link") or interview.meeting_link or ""
        
#         # Build candidate-specific email entries: [(emails_for_candidate, candidate_display_name, candidate_id), ...]
#         candidate_email_entries = []
#         for c in interview.candidate.all():
#             c_emails = []
#             if c.email and '@' in c.email:
#                 c_emails.append(c.email)
#             webform = getattr(c, "webform_candidate_data", None)
#             if webform and isinstance(webform, dict):
#                 pd = webform.get("Personal Details", {})
#                 email2 = pd.get("email")
#                 if email2 and isinstance(email2, str) and '@' in email2 and email2 not in c_emails:
#                     c_emails.append(email2)
#             # Candidate display name
#             c_first = getattr(c, 'first_name', '') or ''
#             c_last = getattr(c, 'last_name', '') or ''
#             c_name = (c_first + ' ' + c_last).strip() or getattr(c, 'name', '') or 'Candidate'
#             if c_emails:
#                 candidate_email_entries.append((c_emails, c_name, c.id))

#         # Build interviewer emails (once)
#         interviewer_emails = []
#         interviewer_nodes = (dinfo.get("interviewers", {}).get("interviewers") or [])
#         for i in interviewer_nodes:
#             if isinstance(i, dict) and i.get("email") and '@' in i["email"] and i["email"] not in interviewer_emails:
#                 interviewer_emails.append(i["email"])
#         for i in interview.interviewers.all():
#             if hasattr(i, 'email') and i.email and '@' in i.email and i.email not in interviewer_emails:
#                 interviewer_emails.append(i.email)
        
#         if not candidate_email_entries and not interviewer_emails:
#             print(f"No valid recipient emails found for interview {interview.id}")
#             continue
#         # Parse all reminders & check if due
#         # Build set of already-sent offsets to prevent duplicates
#         already_sent_offsets = set()
#         try:
#             for log in (interview.audit_log or []):
#                 if isinstance(log, dict) and log.get("action") == "reminder_sent":
#                     meta = log.get("meta") or {}
#                     off = meta.get("offset_minutes")
#                     if isinstance(off, int):
#                         already_sent_offsets.add(off)
#         except Exception:
#             pass
            
#         # print(f"[INTERVIEW_REMINDER] Processing interview: {interview.id}")
#         # print(f"[INTERVIEW_REMINDER] Interview start time: {interview_start}")
#         # print(f"[INTERVIEW_REMINDER] Current time: {now}")
#         # print(f"[INTERVIEW_REMINDER] Reminders configured: {reminders}")
#         # print(f"[INTERVIEW_REMINDER] Already sent offsets: {already_sent_offsets}")
        
#         for r_display in reminders:
#             offset = OFFSETS.get(r_display, None)
#             if offset is None and isinstance(r_display, str):
#                 try:
#                     if "minute" in r_display:
#                         offset = int(r_display.split()[0])
#                     elif "hour" in r_display:
#                         offset = int(float(r_display.split()[0]) * 60)
#                 except Exception:
#                     continue
#             if offset is None:
#                 continue
                
#             # Skip if this offset was already delivered
#             if offset in already_sent_offsets:
#                 print(f"[INTERVIEW_REMINDER] Skipping {r_display} - already sent")
#                 continue
                
#             remind_at = interview_start - timedelta(minutes=offset)
#             # time_diff = abs((remind_at - now).total_seconds())
#             # Note: now is already set at the top of the function as timezone.now()
#             # print(f"[INTERVIEW_REMINDER] Reminder '{r_display}' should be sent at: {remind_at}")
#             # print(f"[INTERVIEW_REMINDER] Time difference: {time_diff} seconds")
            
#             if remind_at.date() != now.date():
#                 # print(f"[INTERVIEW_REMINDER] Skipping {r_display} - already sent")
#                 continue

#             # Send reminder if within 60-second window
#             if now.hour == remind_at.hour and now.minute == remind_at.minute:
#                 # print(f"time_diff {time_diff}")
#                 print(f"[INTERVIEW_REMINDER] Sending reminder for {r_display}")
#                 subject = f"Interview Reminder: {title}"
                
#                 # Format interview start time for display
#                 interview_start_display = interview_start.strftime("%d/%m/%Y %H:%M")
                
#                 # Plain text body
#                 body = (
#                     f"Hello,\n\n"
#                     f"This is a reminder for your interview:\n\n"
#                     f"Title: {title}\n"
#                     f"Start Time: {interview_start_display}\n"
#                     f"Mode: {mode}\n"
#                     f"Meeting Link: {meeting_link}\n\n"
#                     f"Best regards,\n"
#                     f"Edjobster Team"
#                 )
                
#                 # HTML body using template
#                 from django.template.loader import render_to_string
                
#                 # Get candidate and company names for personalization
#                 candidate_names = []
#                 for candidate in interview.candidate.all():
#                     if candidate.name:
#                         candidate_names.append(candidate.name)
                
#                 company_name = interview.company.name if interview.company else "Company"
#                 job_title = title  # Using the interview title as job title
                
#                 html_body = render_to_string('interview_reminder.html', {
#                     'title': title,
#                     'start_time': interview_start_display,
#                     'mode': mode or '-',
#                     'meeting_link': meeting_link,
#                     'year': timezone.now().year,
#                     'candidateName': ', '.join(candidate_names) if candidate_names else 'Candidate',
#                     'jobTitle': job_title,
#                     'companyName': company_name
#                 })
                
#                 try:
#                     if interview.company:
#                         from candidates.models import EmailSettings
#                         email_settings = EmailSettings.objects.filter(company=interview.company).order_by('-created_at').first()
#                         if email_settings:
#                             from django.core.mail import get_connection
#                             connection = get_connection(
#                                 backend=email_settings.email_backend,
#                                 host=email_settings.email_host,
#                                 port=email_settings.email_port,
#                                 username=email_settings.sender_mail,
#                                 password=email_settings.auth_password,
#                                 use_ssl=email_settings.email_ssl,
#                                 use_tls=email_settings.email_tls
#                             )
#                         else:
#                             connection = None
#                     else:
#                         connection = None
#                 except Exception as e:
#                     print(f"[Interview Reminder] Error getting email settings for company {interview.company}: {e}")
#                     connection = None

#                 # Helper to send one email
#                 def _send(to_list, html_body):
#                     try:
#                         if email_settings:
#                             send_mail(
#                                 subject,
#                                 f"Hello,\n\nThis is a reminder for your interview.\nTitle: {title}\nStart Time: {interview_start_display}\nMode: {mode}\nMeeting Link: {meeting_link}\n\nBest regards,\nEdjobster Team",
#                                 email_settings.sender_mail,
#                                 to_list,
#                                 fail_silently=False,
#                                 html_message=html_body,
#                                 connection=connection,
#                             )
#                         else:
#                             send_mail(
#                                 subject,
#                                 f"Hello,\n\nThis is a reminder for your interview.\nTitle: {title}\nStart Time: {interview_start_display}\nMode: {mode}\nMeeting Link: {meeting_link}\n\nBest regards,\nEdjobster Team",
#                                 getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
#                                 to_list,
#                                 fail_silently=False,
#                                 html_message=html_body,
#                             )
#                         return True
#                     except Exception as e:
#                         print(f"[INTERVIEW_REMINDER] Failed to send reminder email to {to_list}: {e}")
#                         return False

#                 company_name = interview.company.name if interview.company else "Company"
#                 job_title = title

#                 # 1) Send per-candidate emails
#                 for c_emails, c_name, c_id in candidate_email_entries:
#                     html_body = None
#                     try:
#                         html_body = render_to_string('interview_reminder.html', {
#                             'title': title,
#                             'start_time': interview_start_display,
#                             'mode': mode or '-',
#                             'meeting_link': meeting_link,
#                             'year': timezone.now().year,
#                             'candidateName': c_name,
#                             'candidateId': c_id,
#                             'jobTitle': job_title,
#                             'companyName': company_name
#                         })
#                     except Exception:
#                         html_body = None
#                     _send(c_emails, html_body)

#                 # 2) Send interviewer emails (single batch)
#                 if interviewer_emails:
#                     html_body = None
#                     try:
#                         html_body = render_to_string('interview_reminder.html', {
#                             'title': title,
#                             'start_time': interview_start_display,
#                             'mode': mode or '-',
#                             'meeting_link': meeting_link,
#                             'year': timezone.now().year,
#                             'candidateName': 'Candidate',
#                             'jobTitle': job_title,
#                             'companyName': company_name
#                         })
#                     except Exception:
#                         html_body = None
#                     _send(interviewer_emails, html_body)

#                 # Record in audit log once per offset
#                 interview.add_audit(
#                     "reminder_sent",
#                     meta={
#                         "offset_minutes": offset,
#                         "recipients": {
#                             "candidates": [e for e_list, _, _ in candidate_email_entries for e in e_list],
#                             "interviewers": interviewer_emails,
#                         },
#                         "reminder_type": r_display,
#                     },
#                 )
#             else:
#                 print(f"[INTERVIEW_REMINDER] Reminder '{r_display}' not due yet (time diff: )")
    
#     # print(f"[INTERVIEW_REMINDER] Task execution completed at {timezone.now()}")



# Utility: Send reminder email
# ------------------------------
def _send_reminder_email(interview, reminder_type):
    # Manual check for feature availability
    has_access, _, _, _ = check_feature_access(interview.company_id, "auto_response_rules")
    if not has_access:
        return

    dynamic_data = interview.dynamic_interview_data or {}
    schedule = dynamic_data.get("schedule", {})
    basic_info = dynamic_data.get("basic_info", {})

    # Basic fields
    interview_title = basic_info.get("interview_title") or interview.title or "Interview"
    job_name = basic_info.get("job", {}).get("name", "")
    interview_link = basic_info.get("interview_link") or getattr(interview, "meeting_link", "") or ""
    mode = basic_info.get("mode_of_interview", "")

    # Build interview start datetime for display using timezone id
    dt_str = schedule.get("date")
    tm_str = schedule.get("time") or schedule.get("start_time")
    tzid = schedule.get("time_zone", {}).get("id") or "Asia/Kolkata"
    interview_start_display = "-"
    try:
        # Support HH:MM and HH:MM:SS
        if tm_str and len(tm_str.split(":")) == 2:
            naive_start = datetime.strptime(f"{dt_str} {tm_str}", "%Y-%m-%d %H:%M")
        else:
            naive_start = datetime.strptime(f"{dt_str} {tm_str}", "%Y-%m-%d %H:%M:%S")
        try:
            tzone = pytz.timezone(tzid)
        except Exception:
            tzone = pytz.timezone("Asia/Kolkata")
        interview_start = tzone.localize(naive_start)
        interview_start_display = interview_start.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass

    # Subject
    subject = f"Interview Reminder: {interview_title}"

    # Company-specific email settings
    email_settings = None
    connection = None
    try:
        if interview.company:
            try:
                from candidates.models import EmailSettings
                email_settings = EmailSettings.objects.filter(company=interview.company).order_by('-created_at').first()
            except Exception:
                email_settings = None
        if email_settings:
            from django.core.mail import get_connection
            connection = get_connection(
                backend=email_settings.email_backend,
                host=email_settings.email_host,
                port=email_settings.email_port,
                username=email_settings.sender_mail,
                password=email_settings.auth_password,
                use_ssl=email_settings.email_ssl,
                use_tls=email_settings.email_tls,
            )
    except Exception as e:
        print(f"[Interview Reminder] Error preparing email connection for interview {interview.id}: {e}")
        connection = None

    # Template rendering helper
    from django.template.loader import render_to_string

    sent_candidates = []
    sent_interviewers = []

    # Send to candidates (personalized)
    for candidate_status in InterviewCandidateStatus.objects.filter(interview=interview):
        candidate = getattr(candidate_status, 'candidate', None)
        to_list = []
        # Only use email from webform_candidate_data
        webform = getattr(candidate, 'webform_candidate_data', None)
        candidate_email = None
        if webform and isinstance(webform, dict):
            personal = webform.get('Personal Details', {})
            email2 = personal.get('email')
            if email2 and '@' in email2:
                candidate_email = email2
        if candidate_email and '@' in candidate_email:
            to_list.append(candidate_email)
        else:
            print(f"[Interview Reminder] Candidate skipped for interview {interview.id}: No valid webform email for candidate {getattr(candidate, 'id', 'unknown')} ({getattr(candidate, 'first_name', '')} {getattr(candidate, 'last_name', '')})")
        if not to_list:
            continue
        candidate_name = (
            f"{getattr(candidate, 'first_name', '')} {getattr(candidate, 'last_name', '')}".strip()
            or getattr(candidate, 'name', '')
            or 'Candidate'
        )
        try:
            html_body = render_to_string('interview_reminder.html', {
                'title': interview_title,
                'start_time': interview_start_display,
                'mode': mode or '-',
                'meeting_link': interview_link,
                'year': timezone.now().year,
                'candidateName': candidate_name,
                'jobTitle': job_name or interview_title,
                'companyName': interview.company.name if interview.company else 'Company',
            })
        except Exception:
            html_body = None

        try:
            send_mail(
                subject,
                f"Hello,\n\nThis is a reminder for your interview.\nTitle: {interview_title}\nStart Time: {interview_start_display}\nMode: {mode}\nMeeting Link: {interview_link}\n\nBest regards,\nEdjobster Team",
                email_settings.sender_mail if email_settings else getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
                to_list,
                fail_silently=False,
                html_message=html_body,
                connection=connection,
            )
            sent_candidates.extend(to_list)
        except Exception as e:
            print(f"[Interview Reminder] Failed to send candidate reminder for interview {interview.id} to {to_list}: {e}")

    # Send to interviewers (send each separately)
    interviewer_emails = []
    for interviewer_status in InterviewerStatus.objects.filter(interview=interview):
        interviewer_obj = getattr(interviewer_status, 'interviewer', None)
        em = getattr(interviewer_obj, 'email', None)
        if em and '@' in em and em not in interviewer_emails:
            interviewer_emails.append((em, interviewer_obj))
    for interviewer_email, interviewer_obj in interviewer_emails:
        interviewer_name = (
            f"{getattr(interviewer_obj, 'first_name', '')} {getattr(interviewer_obj, 'last_name', '')}".strip()
            or getattr(interviewer_obj, 'name', '')
            or 'Interviewer'
        )
        try:
            html_body = render_to_string('interview_reminder.html', {
                'title': interview_title,
                'start_time': interview_start_display,
                'mode': mode or '-',
                'meeting_link': interview_link,
                'year': timezone.now().year,
                'candidateName': interviewer_name,
                'jobTitle': job_name or interview_title,
                'companyName': interview.company.name if interview.company else 'Company',
            })
        except Exception:
            html_body = None
        try:
            send_mail(
                subject,
                f"Hello,\n\nThis is a reminder for the upcoming interview.\nTitle: {interview_title}\nStart Time: {interview_start_display}\nMode: {mode}\nMeeting Link: {interview_link}\n\nBest regards,\nEdjobster Team",
                email_settings.sender_mail if email_settings else getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
                [interviewer_email],  # send only to one interviewer
                fail_silently=False,
                html_message=html_body,
                connection=connection,
            )
            sent_interviewers.append(interviewer_email)
        except Exception as e:
            print(f"[Interview Reminder] Failed to send interviewer reminder for interview {interview.id} to {interviewer_email}: {e}")

    # Record audit
    interview.add_audit(
        f"reminder_sent_{reminder_type}",
        meta={
            'recipients': {
                'candidates': sent_candidates,
                'interviewers': sent_interviewers,
            },
            'at': timezone.now().isoformat(),
        },
    )


# ------------------------------
# Main periodic Celery task
# ------------------------------
@shared_task
def send_interview_reminders():
    """
    Runs periodically (every few minutes).
    Checks all scheduled interviews and sends reminders automatically
    at 24h, 1h, or 15m before interview time.
    """
    now = timezone.now()
    upcoming_interviews = Interview.objects.filter(status="scheduled")

    reminder_map = {
        "24 hours before": timedelta(hours=24),
        "1 hour before": timedelta(hours=1),
        "15 minutes before": timedelta(minutes=15)
    }

    for interview in upcoming_interviews:
        dynamic_data = interview.dynamic_interview_data or {}
        schedule_data = dynamic_data.get("schedule", {})
        reminder_settings = dynamic_data.get("Reminder Settings", {}).get("select_reminders", [])

        if not schedule_data or not reminder_settings:
            continue

        interview_date = schedule_data.get("date")
        interview_time = schedule_data.get("time")
        time_zone_id = schedule_data.get("time_zone", {}).get("id")

        if not interview_date or not interview_time:
            continue

        try:
            tz = pytz.timezone(time_zone_id)
        except Exception:
            tz = pytz.timezone("Asia/Kolkata")
        try:
            interview_datetime = tz.localize(datetime.strptime(f"{interview_date} {interview_time}", "%Y-%m-%d %H:%M"))
        except Exception:
            continue

        # Loop through reminder types
        for reminder_label, delta in reminder_map.items():
            if reminder_label not in reminder_settings:
                continue

            reminder_time = interview_datetime - delta

            # If within ±1 minute of reminder time and not already sent
            already_sent = any(
                log["action"] == f"reminder_sent_{reminder_label}"
                for log in (interview.audit_log or [])
            )

            if not already_sent and abs((reminder_time - now).total_seconds()) <= 60:
                _send_reminder_email(interview, reminder_label)

    return f"✅ Checked interviews at {now.strftime('%Y-%m-%d %H:%M:%S')}"



@shared_task
def auto_accept_interviews_one_hour_before():
    """Automatically set status to 'accepted' for InterviewCandidateStatus and InterviewerStatus 
    when interview is 1 hour away."""
    print(f"[AUTO_ACCEPT] Starting task execution at {timezone.now()}")
    now = timezone.now()
    
    # Get all interviews that have dynamic_interview_data with schedule information
    interviews = Interview.objects.filter(dynamic_interview_data__isnull=False).exclude(dynamic_interview_data={})
    print(f"[AUTO_ACCEPT] Found {interviews.count()} interviews with dynamic data")
    
    for interview in interviews:
        # Manual check for feature availability
        has_access, _, _, _ = check_feature_access(interview.company_id, "auto_response_rules")
        if not has_access:
            continue

        dinfo = interview.dynamic_interview_data or {}
        schedule = dinfo.get("schedule") or dinfo.get("Schedule") or {}
        
        # Get date and time from schedule
        dt_str = schedule.get("date")
        tm_str = schedule.get("time") or schedule.get("start_time")
        tzinfo = schedule.get("time_zone", {}).get("id") or "UTC"
        
        # Skip if missing time data
        if not dt_str or not tm_str:
            continue
            
        try:
            # Parse time - handle both HH:MM and HH:MM:SS formats
            if len(tm_str.split(':')) == 2:
                # HH:MM format
                naive_dt = datetime.strptime(f"{dt_str} {tm_str}", "%Y-%m-%d %H:%M")
            else:
                # HH:MM:SS format
                naive_dt = datetime.strptime(f"{dt_str} {tm_str}", "%Y-%m-%d %H:%M:%S")
            
            # Handle timezone
            if tzinfo and tzinfo != "UTC":
                try:
                    tzone = pytz.timezone(tzinfo)
                    interview_start = tzone.localize(naive_dt)
                except pytz.exceptions.UnknownTimeZoneError:
                    # Fallback to UTC if timezone is unknown
                    tzone = pytz.UTC
                    interview_start = tzone.localize(naive_dt)
            else:
                tzone = pytz.UTC
                interview_start = tzone.localize(naive_dt)
                
        except Exception as e:
            print(f"Error parsing datetime for interview {interview.id}: {e}")
            continue

        # Check if interview is exactly 1 hour away (within 5 minutes tolerance)
        one_hour_before = interview_start - timedelta(hours=1)
        time_diff = abs((one_hour_before - now).total_seconds())
        
        # Check if we're within 5 minutes of the 1-hour mark
        if time_diff <= 300:  # 5 minutes = 300 seconds
            print(f"[AUTO_ACCEPT] Interview {interview.id} is 1 hour away, auto-accepting...")
            
            # Check if already auto-accepted to avoid duplicates
            already_auto_accepted = False
            try:
                for log in (interview.audit_log or []):
                    if isinstance(log, dict) and log.get("action") == "auto_accepted_one_hour_before":
                        already_auto_accepted = True
                        break
            except Exception:
                pass
                
            if already_auto_accepted:
                print(f"[AUTO_ACCEPT] Interview {interview.id} already auto-accepted, skipping...")
                continue
            
            # Auto-accept all candidate statuses (only if status is "scheduled")
            candidate_statuses = InterviewCandidateStatus.objects.filter(interview=interview)
            for candidate_status in candidate_statuses:
                if candidate_status.status == "scheduled":
                    candidate_status.status = "accepted"
                    candidate_status.save()
                    print(f"[AUTO_ACCEPT] Set candidate {candidate_status.candidate} status to accepted")
            
            # Auto-accept all interviewer statuses (only if status is "scheduled")
            interviewer_statuses = InterviewerStatus.objects.filter(interview=interview)
            for interviewer_status in interviewer_statuses:
                if interviewer_status.status == "scheduled":
                    interviewer_status.status = "accepted"
                    interviewer_status.save()
                    print(f"[AUTO_ACCEPT] Set interviewer {interviewer_status.interviewer} status to accepted")
            
            # Record in audit log
            interview.add_audit(
                "auto_accepted_one_hour_before",
                meta={
                    "interview_start": interview_start.isoformat(),
                    "auto_accepted_at": now.isoformat(),
                    "candidate_count": candidate_statuses.count(),
                    "interviewer_count": interviewer_statuses.count()
                },
            )
            
            print(f"[AUTO_ACCEPT] Successfully auto-accepted interview {interview.id}")
        else:
            print(f"[AUTO_ACCEPT] Interview {interview.id} not yet 1 hour away (diff: {time_diff/60:.1f} minutes)")
    
    print(f"[AUTO_ACCEPT] Task execution completed at {timezone.now()}")


@shared_task
def send_feedback_reminders_post_interview():
    """Send a feedback reminder to all interviewers right after interview end time.

    End time resolution priority:
    1) schedule.end_time (dynamic_interview_data)
    2) Interview.time_end (model field)
    3) schedule.duration (minutes) or duration object with value/unit
    """
    now = timezone.now()
    interviews = Interview.objects.filter(dynamic_interview_data__isnull=False).exclude(dynamic_interview_data={})

    for interview in interviews:
        # Manual check for auto_response_rules availability
        has_access, _, _, _ = check_feature_access(interview.company_id, "auto_response_rules")
        if not has_access:
            continue


        company = interview.company
        subscription = Subscription.objects.filter(company=company, is_active=True).first()
        feature = Feature.objects.get(code="Interview_feedback_form")
        # plan_feature = PlanFeatureCredit.objects.get(plan=subscription.plan, feature=feature).first()
        credit_wallet = CreditWallet.objects.filter(company=company, feature=feature).first()

        if credit_wallet:
            dinfo = interview.dynamic_interview_data or {}
            schedule = dinfo.get("schedule") or dinfo.get("Schedule") or {}
            basic = dinfo.get("basic_info", {})

            # Parse interview start
            dt_str = schedule.get("date")
            tm_start = schedule.get("time") or schedule.get("start_time")
            tzid = schedule.get("time_zone", {}).get("id") or "UTC"

            if not dt_str or not tm_start:
                continue

            try:
                if len(tm_start.split(":")) == 2:
                    naive_start = datetime.strptime(f"{dt_str} {tm_start}", "%Y-%m-%d %H:%M")
                else:
                    naive_start = datetime.strptime(f"{dt_str} {tm_start}", "%Y-%m-%d %H:%M:%S")

                if tzid and tzid != "UTC":
                    try:
                        tzone = pytz.timezone(tzid)
                        interview_start = tzone.localize(naive_start)
                    except pytz.exceptions.UnknownTimeZoneError:
                        tzone = pytz.UTC
                        interview_start = tzone.localize(naive_start)
                else:
                    tzone = pytz.UTC
                    interview_start = tzone.localize(naive_start)
            except Exception as e:
                print(f"[FEEDBACK_REMINDER] Error parsing start time for interview {interview.id}: {e}")
                continue

            # Determine interview end
            interview_end = None
            tm_end = schedule.get("end_time")
            if tm_end:
                try:
                    if len(tm_end.split(":")) == 2:
                        naive_end = datetime.strptime(f"{dt_str} {tm_end}", "%Y-%m-%d %H:%M")
                    else:
                        naive_end = datetime.strptime(f"{dt_str} {tm_end}", "%Y-%m-%d %H:%M:%S")
                    interview_end = tzone.localize(naive_end)
                except Exception:
                    interview_end = None

            # Fallback 2: model time_end
            if interview_end is None and interview.time_end:
                try:
                    naive_end = datetime.combine(
                        date.fromisoformat(dt_str), interview.time_end
                    )
                    interview_end = tzone.localize(naive_end)
                except Exception:
                    interview_end = None

            # Fallback 3: duration
            if interview_end is None:
                duration_minutes = None
                dur = schedule.get("duration") or schedule.get("duration_minutes") or schedule.get("duration_in_minutes")
                if isinstance(dur, int):
                    duration_minutes = dur
                elif isinstance(dur, str):
                    # Support formats like '15', '15.0', '15 minutes', '1 hour'
                    s = dur.strip().lower()
                    # Extract leading number
                    import re
                    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*(minute|minutes|hour|hours)?\s*", s)
                    if m:
                        num = float(m.group(1))
                        unit = m.group(2) or "minutes"
                        if "hour" in unit:
                            duration_minutes = int(num * 60)
                        else:
                            duration_minutes = int(num)
                    else:
                        try:
                            duration_minutes = int(float(s))
                        except Exception:
                            duration_minutes = None
                elif isinstance(dur, dict):
                    try:
                        val = dur.get("value")
                        unit = (dur.get("unit") or "minutes").lower()
                        if val is not None:
                            if "hour" in unit:
                                duration_minutes = int(float(val) * 60)
                            else:
                                duration_minutes = int(val)
                    except Exception:
                        duration_minutes = None

                if duration_minutes:
                    interview_end = interview_start + timedelta(minutes=duration_minutes)

            if interview_end is None:
                # Cannot compute end, skip
                continue

            # Prevent duplicate sends
            already_sent = False
            try:
                for log in (interview.audit_log or []):
                    if isinstance(log, dict) and log.get("action") == "feedback_reminder_sent":
                        # Only one feedback reminder per interview
                        already_sent = True
                        break
            except Exception:
                pass
            if already_sent:
                continue

            # Compare current time to end time at minute resolution (same-day and same hour/minute)
            now_naive = datetime.now()
            if interview_end.date() != now_naive.date():
                continue
            if not (now_naive.hour == interview_end.hour and now_naive.minute == interview_end.minute):
                continue

            # Build interviewer recipients list with IDs for personalized links
            interviewer_recipients = []  # list of tuples: (email, interviewer_id)
            found_emails = set()
            # Prefer model relation to ensure we have IDs
            for i in interview.interviewers.all():
                if hasattr(i, "email") and i.email and "@" in i.email:
                    if i.email not in found_emails:
                        interviewer_recipients.append((i.email, i.id))
                        found_emails.add(i.email)
            # Also check dynamic data (if any emails not covered above)
            try:
                interviewer_entries = (dinfo.get("interviewers", {}).get("interviewers") or [])
                for i in interviewer_entries:
                    if isinstance(i, dict):
                        em = i.get("email")
                        iid = i.get("id")
                        if em and "@" in em and em not in found_emails:
                            interviewer_recipients.append((em, iid))
                            found_emails.add(em)
            except Exception:
                pass

            if not interviewer_recipients:
                continue

            title = basic.get("interview_title") or interview.title or "Interview"
            company_name = interview.company.name if interview.company else "Company"
            end_display = interview_end.strftime("%Y-%m-%d %H:%M")

            subject = f"Feedback requested: {title} just ended"
            body = (
                "Hello,\n\n"
                f"The interview '{title}' has just concluded at {end_display}.\n"
                "Please submit your feedback in the system.\n\n"
                "Thank you,\nEdjobster Team"
            )

            # Determine one candidate_id to include in feedback URL (first candidate)
            candidate_id = None
            first_candidate = interview.candidate.first() if hasattr(interview.candidate, 'first') else None
            # if first_candidate:
            #     candidate_id = first_candidate.id

            # Company-specific email settings
            for candidate in interview.candidate.all():
                candidate_id = candidate.id
                try:
                    email_settings = None
                    if interview.company:
                        try:
                            from candidates.models import EmailSettings
                            email_settings = EmailSettings.objects.filter(company=interview.company).order_by('-created_at').first()
                        except Exception:
                            email_settings = None

                    from django.core.mail import get_connection
                    connection = None
                    if email_settings:
                        connection = get_connection(
                            backend=email_settings.email_backend,
                            host=email_settings.email_host,
                            port=email_settings.email_port,
                            username=email_settings.sender_mail,
                            password=email_settings.auth_password,
                            use_ssl=email_settings.email_ssl,
                            use_tls=email_settings.email_tls,
                        )

                    # Send per interviewer with personalized feedback URL
                    from django.template.loader import render_to_string
                    sent_to = []
                    for em, interviewer_id in interviewer_recipients:
                        feedback_url = f"{getattr(settings, 'APP_URL', '')}/headless/feedback/{interview.id}/{interviewer_id}/{candidate_id or ''}"
                        interview_not_done_feedback_url = f"{getattr(settings, 'APP_URL', '')}/headless/feedback/{interview.id}/{interviewer_id}/{candidate_id or ''}?action=interviewnotdone"
                        try:
                            html_body = render_to_string(
                                "interview_feedback_reminder.html",
                                {
                                    "title": title,
                                    "end_time": end_display,
                                    "companyName": company_name,
                                    "feedback_url": feedback_url,
                                    "interview_not_done_url": interview_not_done_feedback_url,
                                },
                            )
                        except Exception:
                            html_body = None

                        try:
                            send_mail(
                                subject,
                                body + f"\n\nFeedback: {feedback_url}",
                                email_settings.sender_mail if email_settings else getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
                                [em],
                                fail_silently=False,
                                html_message=html_body,
                                connection=connection,
                            )
                            sent_to.append(em)
                        except Exception as e:
                            print(f"[FEEDBACK_REMINDER] Failed to send to {em}: {e}")

                    if sent_to:
                        interview.add_audit("feedback_reminder_sent", meta={"recipients": sent_to, "at": now.isoformat()})
                        print(f"[FEEDBACK_REMINDER] Sent feedback reminder for interview {interview.id} to {sent_to}")
                except Exception as e:
                    print(f"[FEEDBACK_REMINDER] Failed to send feedback reminder for interview {interview.id}: {e}")
