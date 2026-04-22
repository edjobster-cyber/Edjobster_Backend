from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from .import helper
from common.utils import makeResponse
from .models import Interview, RescheduleRequest, Feedback, InterviewCandidateStatus, InterviewerStatus, DeclineResponse
from .serializer import InterviewJsonDataSerializer, InterviewSerializer, RescheduleRequestSerializer, FeedbackSerializer, InterviewCandidateStatusSerializer, InterviewerStatusSerializer, DeclineResponseSerializer
from django.shortcuts import get_object_or_404
import jwt
from django.conf import settings
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.core.mail import send_mail
from django.urls import reverse
from django.http import HttpResponse
from datetime import datetime
from datetime import timezone as dt_tz
from django.utils import timezone as djtz
from zoneinfo import ZoneInfo
from django.template.loader import render_to_string
from datetime import timedelta
from settings.models import Contacts
from candidates.models import Candidate, EmailSettings

import interview
 
# class InterviewApi(APIView):

#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         data = helper.getInterviews(request)
#         return makeResponse(data)

#     def post(self, request):
#         data = helper.scheduleInterview(request)
#         return makeResponse(data)

#     def delete(self, request):
#         data = helper.delteInterview(request)
#         return makeResponse(data)                

# class InterviewDetailsApi(APIView):

#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         data = helper.interviewDetails(request)
#         return makeResponse(data)
    
#     def put(self, request):
#         data = helper.updateInterviewDetails(request)
#         return makeResponse(data)
        
class LatestInterviewDetailsApi(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = helper.latestInterviewDetails(request)
        return makeResponse(data)
    

class JobInterviewDetailsApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getJobInterviewsDetails(request)
        return makeResponse(data)

class CandidateInterviewDetailsApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getCandidateInterviewsDetails(request)
        return makeResponse(data)
    
# class InterviewJsonDataView(APIView):
#     def get(self,request):
#         data =Interview.objects.all()
#         serializer = InterviewJsonDataSerializer(data,many=True)
#         return Response(serializer.data)
    
    
# from django.db.models import Q
# import re
# from interview import models
# from rest_framework.response import Response
    
# class InterviewSQLQueryView(APIView):
#     def post(self, request, *args, **kwargs):
#         try:
#             user = request.user
#             data = request.data
#             query = data.get('query')
#             if query:
#                 query = query.replace('%', '')
#             # Use Django ORM to filter interviews
#             interviews = models.Interview.objects.select_related('job', 'company', 'candidate', 'location', 'email_temp')

#             if not user.is_superuser:
#                 interviews = interviews.filter(company__id=user.company_id)

#             if query:
#                 # Replace logical operators with Python's operators
#                 query = query.replace(" AND ", " and ").replace(" OR ", " or ")
                
#                 # Parse and construct the Q object
#                 q_object = self.construct_q_object(query)
                
#                 # Apply the Q object to filter interviews
#                 interviews = interviews.filter(q_object)

#             results = interviews.values(
#                 'id', 'job__title', 'company__name', 'candidate__first_name', 'candidate__last_name','job__id','candidate__id',
#                 'title', 'type', 'date', 'time_start', 'time_end', 'location__name',
#                 'interviewers', 'email_temp__name', 'email_sub', 'email_msg', 'document',
#                 'updated', 'created'
#             )

#             results_list = list(results)
#             return Response({'result': results_list}, status=status.HTTP_200_OK)
#         except Exception as e:
#             # Return all interviews in case of an error
#             interviews = models.Interview.objects.select_related('job', 'company', 'candidate', 'location', 'email_temp').values(
#                 'id', 'job__title', 'company__name', 'candidate__first_name', 'candidate__last_name','job__id','candidate__id',
#                 'title', 'type', 'date', 'time_start', 'time_end', 'location__name',
#                 'interviewers', 'email_temp__name', 'email_sub', 'email_msg', 'document',
#                 'updated', 'created'
#             )
#             results_list = list(interviews)
#             return Response({'result': results_list, 'error': str(e)}, status=status.HTTP_200_OK)

#     def construct_q_object(self, query):
#         # Tokenize the query using regex to handle nested conditions and operators
#         tokens = re.split(r'(\(|\)|\s+and\s+|\s+or\s+)', query)
#         tokens = [token for token in tokens if token.strip()]

#         # Stack to manage nested conditions and Q objects
#         stack = []
#         current_q = None
#         current_operator = None

#         for token in tokens:
#             token = token.strip().lower()

#             if token == '(':
#                 stack.append((current_q, current_operator))
#                 current_q = None
#                 current_operator = None
#             elif token == ')':
#                 temp_q = current_q
#                 if stack:
#                     current_q, current_operator = stack.pop()
#                     if current_operator == 'and':
#                         current_q &= temp_q
#                     elif current_operator == 'or':
#                         current_q |= temp_q
#                     else:
#                         current_q = temp_q
#             elif token == 'and':
#                 current_operator = 'and'
#             elif token == 'or':
#                 current_operator = 'or'
#             else:
#                 # Parse the condition token (e.g., "field operator value")
#                 # match = re.match(r'(\w+) (like|not like|=|<>|>|>=|<|<=|startwith|endwith) (.+)', token)
#                 match = re.match(r"(\w+)\s+(like|not like|=|<>|>|>=|<|<=|startwith|endwith|IS NULL|IS NOT NULL)\s+('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|[^\s]+)", token, re.IGNORECASE)
#                 if match:
#                     field, operator, value = match.groups()
#                     value = value.strip().strip("'")
                    
#                     # Map field names to Django ORM fields
#                     if field in ['company', 'location', 'email_temp']:
#                         field = f"{field}__name"
#                     elif field == 'job':
#                         field = 'job__title'
#                     elif field == 'candidate':
#                         field = 'candidate__first_name'
                    
#                     # Construct the condition Q object
#                     if operator == 'like':
#                         condition = Q(**{f"{field}__icontains": value})
#                     elif operator == 'not like':
#                         condition = ~Q(**{f"{field}__icontains": value})
#                     elif operator == '=':
#                         condition = Q(**{f"{field}__iexact": value})
#                     elif operator == '<>':
#                         condition = ~Q(**{f"{field}__iexact": value})
#                     elif operator == '>':
#                         condition = Q(**{f"{field}__gt": value})
#                     elif operator == '>=':
#                         condition = Q(**{f"{field}__gte": value})
#                     elif operator == '<':
#                         condition = Q(**{f"{field}__lt": value})
#                     elif operator == '<=':
#                         condition = Q(**{f"{field}__lte": value})
#                     elif operator == 'startwith':
#                         condition = Q(**{f"{field}__istartswith": value})
#                     elif operator == 'endwith':
#                         condition = Q(**{f"{field}__iendswith": value})
#                     elif operator == 'is null':
#                         condition = Q(**{f"{field}__isnull": True})
#                     elif operator == 'is not null':
#                         condition = ~Q(**{f"{field}__isnull": True})

#                     # Apply the current operator
#                     if current_q is None:
#                         current_q = condition
#                     elif current_operator == 'and':
#                         current_q &= condition
#                     elif current_operator == 'or':
#                         current_q |= condition

#                     current_operator = None

#         return current_q if current_q else Q()


class InterviewListCreateAPIView(APIView):
    """
    GET  → list all interviews
    POST → create new interview
    """
    permission_classes = [IsAuthenticated]
    

    def get(self, request):
        """List all interviews"""
        if request.user.is_superuser:
            interviews = Interview.objects.all()
        else:
            interviews = (
                Interview.objects
                .select_related("location", "created_by")
                .prefetch_related("candidate", "interviewers")
                .filter(company_id=request.user.company_id)
            )
        serializer = InterviewSerializer(interviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create new interview"""
        data = request.data
        data['company'] = request.user.company_id
        data['created_by'] = request.user.id

        serializer = InterviewSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            interview = serializer.save()

            # Generate meeting link and tokens
            # interview.generate_meeting_link()
            # interview.generate_headless_tokens()
            interview.add_audit("created", by=request.user)

            # -------------------------------
            # Create related status records
            # -------------------------------
            # Create InterviewCandidateStatus for each candidate
            candidates = interview.candidate.all()
            # Update all candidates in a single query for better performance
            candidates.update(
                pipeline_stage="Interview",
                pipeline_stage_status="Interview Scheduled"
            )
            
            # Create InterviewCandidateStatus for each candidate
            for candidate in candidates:
                InterviewCandidateStatus.objects.get_or_create(
                    interview=interview,
                    candidate=candidate,
                    defaults={'status': 'scheduled'}
                )

            # Create InterviewerStatus for each interviewer
            interviewers = interview.interviewers.all()
            for interviewer in interviewers:
                InterviewerStatus.objects.get_or_create(
                    interview=interview,
                    interviewer=interviewer,
                    defaults={'status': 'scheduled'}
                )

            return Response(InterviewSerializer(interview).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def post(self, request):
    #     """Create new interview"""
    #     data = request.data
    #     data['company'] = request.user.company_id
    #     data['created_by'] = request.user.id
    #     # data['candidate'] = request.data.get('Schedule', {}).get('basic_info', {}).get('candidate_id')
    #     serializer = InterviewSerializer(data=data, context={"request": request})
    #     if serializer.is_valid():
    #         interview = serializer.save()
    #         interview.generate_meeting_link()
    #         interview.generate_headless_tokens()
    #         interview.add_audit("created", by=request.user)

    #         # Create a provider calendar event (Phase 1: synthetic/no-op provider)
    #         try:
    #             cal_result = CalendarService.create_event_from_interview(request, interview)
    #         except Exception:
    #             cal_result = {"joinUrl": interview.meeting_link}

    #         # 1) Collect schedule/info from dynamic_interview_data
    #         dinfo = interview.dynamic_interview_data or {}
    #         schedule = dinfo.get("schedule") or dinfo.get("Schedule") or {}
    #         basic = dinfo.get("basic_info", {})
    #         title = basic.get("interview_title") or interview.title
    #         mode = basic.get("mode_of_interview")
    #         meeting_link = (
    #             basic.get("interview_link")
    #             or basic.get("interview_linklocation")
    #             or cal_result.get("joinUrl")
    #             or interview.meeting_link
    #         )
    #         date = schedule.get("date")
    #         time_val = schedule.get("time") or schedule.get("start_time")
    #         tzid = (schedule.get("time_zone") or {}).get("id")

    #         # 2) Build action URLs
    #         reschedule_url = request.build_absolute_uri(reverse('reschedule-list-create', args=[interview.id]))
    #         feedback_url = request.build_absolute_uri(reverse('feedback', args=[interview.id]))
    #         ics_url = request.build_absolute_uri(reverse('interview-ics', args=[interview.id]))

    #         # Headless tokens (manager + candidates)
    #         headless = interview.headless_tokens or {}
    #         manager_token = headless.get("manager")
    #         candidate_tokens = headless.get("candidates", [])
    #         headless_links = []
    #         if manager_token:
    #             headless_links.append(request.build_absolute_uri(reverse('headless-validate', args=[manager_token])))
    #         for c in candidate_tokens:
    #             token = c.get("token")
    #             if token:
    #                 headless_links.append(request.build_absolute_uri(reverse('headless-validate', args=[token])))

    #         # Candidate primary headless token (first if exists) and action URLs
    #         headless_candidate_token = candidate_tokens[0]["token"] if candidate_tokens and candidate_tokens[0].get("token") else None
    #         headless_base_url = request.build_absolute_uri(reverse('headless-validate', args=[headless_candidate_token])) if headless_candidate_token else ""
    #         headless_action_base = request.build_absolute_uri(reverse('headless-action', args=[headless_candidate_token])) if headless_candidate_token else ""
    #         headless_accept_url = f"{headless_action_base}?action=accept" if headless_action_base else ""
    #         headless_decline_url = f"{headless_action_base}?action=decline" if headless_action_base else ""
    #         headless_reschedule_url = f"{headless_action_base}?action=reschedule" if headless_action_base else ""

    #         # 3) Resolve recipients from Candidate model + webform
    #         recipients = []
    #         for c in interview.candidate.all():
    #             if getattr(c, 'email', None) and c.email not in recipients:
    #                 recipients.append(c.email)
    #             w = getattr(c, 'webform_candidate_data', None)
    #             if isinstance(w, dict):
    #                 pd = w.get('Personal Details', {})
    #                 em = pd.get('email')
    #                 if em and em not in recipients:
    #                     recipients.append(em)

    #         # 4) Render HTML email using template
    #         from django.template.loader import render_to_string
    #         context = {
    #             "jobTitle": title,
    #             "candidateName": "",
    #             "companyName": getattr(request.user.company, 'name', 'Edjobster'),
    #             "startAt": f"{date} {time_val}",
    #             "endAt": "",
    #             "timezone": tzid,
    #             "interviewerNames": ", ".join([getattr(i, 'name', str(i)) for i in interview.interviewers.all()]),
    #             "mode": mode,
    #             "meetingLink": meeting_link,
    #             "icsUrl": ics_url,
    #             "headlessCandidateUrl": headless_base_url,
    #             "headlessAcceptUrl": headless_accept_url,
    #             "headlessDeclineUrl": headless_decline_url,
    #             "headlessRescheduleUrl": headless_reschedule_url,
    #             "rescheduleUrl": reschedule_url,
    #             "year": datetime.now().year,
    #         }
    #         subject = f"Interview Scheduled: {title}"
    #         html_body = render_to_string("interview_scheduled.html", context)
    #         # Fallback plain text
    #         plain = f"Interview Scheduled: {title}\nWhen: {date} {time_val} ({tzid})\nAdd to calendar: {ics_url}\n"

    #         if recipients:
    #             try:
    #                 send_mail(subject, plain, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True, html_message=html_body)
    #                 interview.add_audit("schedule_mail_sent", by=request.user, meta={"recipients": recipients})
    #             except Exception:
    #                 pass

    #         return Response(InterviewSerializer(interview).data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InterviewDetailAPIView(APIView):
    """
    GET    → get interview detail
    PUT    → update interview
    DELETE → delete interview
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Interview, pk=pk)

    def get(self, request, pk):
        """Retrieve single interview"""
        interview = self.get_object(pk)

        candidate_status = InterviewCandidateStatus.objects.filter(interview=interview)
        interviewer_status = InterviewerStatus.objects.filter(interview=interview)
        reschedule_request = RescheduleRequest.objects.filter(interview=interview)
        decline_response = DeclineResponse.objects.filter(interview=interview)

        # Serialize data    
        interview_serializer = InterviewSerializer(interview)
        candidate_status_serializer = InterviewCandidateStatusSerializer(candidate_status, many=True)
        interviewer_status_serializer = InterviewerStatusSerializer(interviewer_status, many=True)
        reschedule_request_serializer = RescheduleRequestSerializer(reschedule_request, many=True)
        decline_response_serializer = DeclineResponseSerializer(decline_response, many=True)

        # Combine all serialized data
        data = {
            "interview": interview_serializer.data,
            "candidateStatus": candidate_status_serializer.data,
            "interviewerStatus": interviewer_status_serializer.data,
            "rescheduleRequest": reschedule_request_serializer.data,
            "declineResponse": decline_response_serializer.data,
        }

        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Update interview - handle interviewer/candidate changes with status and email notifications"""
        interview = self.get_object(pk)
        
        # Store original interviewers and candidates before update
        original_interviewers = set(interview.interviewers.all().values_list('id', flat=True))
        original_candidates = set(interview.candidate.all().values_list('id', flat=True))
        
        # Store original date/time from dynamic_interview_data to check if interview is rescheduled
        original_dynamic_data = interview.dynamic_interview_data or {}
        original_schedule = self._get_section_fields(original_dynamic_data, 'schedule')
        original_date = original_schedule.get('date')
        original_time = original_schedule.get('time')
        original_duration = original_schedule.get('duration')
        
        serializer = InterviewSerializer(interview, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            interview = serializer.save()
            
            # Get updated schedule from dynamic_interview_data
            new_dynamic_data = interview.dynamic_interview_data or {}
            new_schedule = self._get_section_fields(new_dynamic_data, 'schedule')
            new_date = new_schedule.get('date')
            new_time = new_schedule.get('time')
            new_duration = new_schedule.get('duration')
            
            # Check if interview time/date changed (rescheduled)
            time_changed = (
                new_date != original_date or
                new_time != original_time or
                new_duration != original_duration
            )
            # If interview time changed, update status to rescheduled
            if time_changed:
                interview.status = "rescheduled"
                interview.save(update_fields=["status"])
                # Update all candidate statuses to pending (need re-acceptance)
                InterviewCandidateStatus.objects.filter(interview=interview).update(status="scheduled")
                # Update all interviewer statuses to pending (need re-acceptance)
                InterviewerStatus.objects.filter(interview=interview).update(status="scheduled")
                
                # Send reschedule emails to all candidates and interviewers
                self._send_reschedule_emails(interview, request, original_date, original_time)
            
            # Get updated interviewers and candidates after save
            new_interviewers = set(interview.interviewers.all().values_list('id', flat=True))
            new_candidates = set(interview.candidate.all().values_list('id', flat=True))
            
            # Calculate additions and removals
            removed_interviewers = original_interviewers - new_interviewers
            added_interviewers = new_interviewers - original_interviewers
            removed_candidates = original_candidates - new_candidates
            added_candidates = new_candidates - original_candidates
            
            print(f"[INTERVIEW UPDATE] Interview {interview.id}: Original interviewers: {original_interviewers}, New interviewers: {new_interviewers}")
            print(f"[INTERVIEW UPDATE] Removed: {removed_interviewers}, Added: {added_interviewers}")
            
            # Calculate interviewers who remain after removals (for notifications)
            remaining_interviewer_ids = list(original_interviewers - removed_interviewers)
            print(f"[INTERVIEW UPDATE] Remaining interviewers for removal notifications: {remaining_interviewer_ids}")
            
            # Handle removed interviewers
            removed_interviewer_names = []
            for interviewer_id in removed_interviewers:
                try:
                    status_record = InterviewerStatus.objects.get(
                        interview=interview, 
                        interviewer_id=interviewer_id
                    )
                    removed_interviewer_name = getattr(status_record.interviewer, 'name', '') or 'An interviewer'
                    removed_interviewer_names.append(removed_interviewer_name)
                    print(f"[INTERVIEW UPDATE] Removing interviewer: {removed_interviewer_name} (ID: {interviewer_id})")
                    # Send cancellation email to removed interviewer
                    self._send_interviewer_cancellation_email(interview, status_record.interviewer, request)
                    # Delete status record
                    status_record.delete()
                except InterviewerStatus.DoesNotExist:
                    print(f"[INTERVIEW UPDATE] No status record found for removed interviewer {interviewer_id}")
                    pass
            
            # Notify remaining interviewers about removals
            print(f"[INTERVIEW UPDATE] Notifying {len(remaining_interviewer_ids)} interviewers about removals: {removed_interviewer_names}")
            for removed_name in removed_interviewer_names:
                self._send_interviewer_removed_notification_to_others(interview, removed_name, request, remaining_interviewer_ids)
            
            # Handle added interviewers
            added_interviewer_objects = []
            for interviewer_id in added_interviewers:
                from settings.models import Contacts
                try:
                    interviewer = Contacts.objects.get(id=interviewer_id)
                    added_interviewer_objects.append(interviewer)
                    print(f"[INTERVIEW UPDATE] Adding interviewer: {getattr(interviewer, 'name', '')} (ID: {interviewer_id})")
                    # Use get_or_create to prevent duplicates
                    InterviewerStatus.objects.get_or_create(
                        interview=interview,
                        interviewer=interviewer,
                        defaults={'status': 'scheduled'}
                    )
                    # Send schedule email
                    self._send_interviewer_schedule_email(interview, interviewer, request)
                except Contacts.DoesNotExist:
                    print(f"[INTERVIEW UPDATE] Contact not found for added interviewer {interviewer_id}")
                    pass
            
            # Notify existing interviewers about additions (exclude the newly added ones)
            existing_interviewer_ids = list(original_interviewers - removed_interviewers)
            print(f"[INTERVIEW UPDATE] Notifying {len(existing_interviewer_ids)} existing interviewers about additions: {[getattr(i, 'name', i.id) for i in added_interviewer_objects]}")
            for added_interviewer in added_interviewer_objects:
                self._send_interviewer_added_notification_to_others(interview, added_interviewer, request, existing_interviewer_ids)
            
            # Handle removed candidates
            for candidate_id in removed_candidates:
                try:
                    status_record = InterviewCandidateStatus.objects.get(
                        interview=interview,
                        candidate_id=candidate_id
                    )
                    candidate = status_record.candidate
                    # Send cancellation email
                    self._send_candidate_cancellation_email(interview, candidate, request)
                    # Delete status record
                    status_record.delete()
                    # Reset candidate pipeline stage
                    candidate.pipeline_stage = ""
                    candidate.pipeline_stage_status = ""
                    candidate.save(update_fields=["pipeline_stage", "pipeline_stage_status"])
                except InterviewCandidateStatus.DoesNotExist:
                    pass
            
            # Handle added candidates
            for candidate_id in added_candidates:
                from candidates.models import Candidate
                try:
                    candidate = Candidate.objects.get(id=candidate_id)
                    # Update candidate pipeline
                    candidate.pipeline_stage = "Interview"
                    candidate.pipeline_stage_status = "Interview Scheduled"
                    candidate.save(update_fields=["pipeline_stage", "pipeline_stage_status"])
                    # Use get_or_create to prevent duplicates
                    InterviewCandidateStatus.objects.get_or_create(
                        interview=interview,
                        candidate=candidate,
                        defaults={'status': 'scheduled'}
                    )
                    # Send schedule email
                    self._send_candidate_schedule_email(interview, candidate, request)
                except Candidate.DoesNotExist:
                    pass
            
            # Prepare audit meta data
            audit_meta = {
                "removed_interviewers": list(removed_interviewers),
                "added_interviewers": list(added_interviewers),
                "removed_candidates": list(removed_candidates),
                "added_candidates": list(added_candidates)
            }
            
            # Add time change info to audit if rescheduled
            if time_changed:
                audit_meta["schedule_changed"] = {
                    "date": {"old": original_date, "new": new_date},
                    "time": {"old": original_time, "new": new_time},
                    "duration": {"old": original_duration, "new": new_duration}
                }
                audit_meta["status_updated"] = "rescheduled"
            
            interview.add_audit("updated", by=request.user, meta=audit_meta)
            return Response(InterviewSerializer(interview).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_section_fields(self, dynamic_data, section_name):
        """Extract fields from dynamic_interview_data nested object structure"""
        if not dynamic_data or not isinstance(dynamic_data, dict):
            return {}
        
        section = dynamic_data.get(section_name, {})
        if isinstance(section, dict):
            return section
        return {}
    
    def _send_interviewer_cancellation_email(self, interview, interviewer, request):
        """Send cancellation email to removed interviewer using template"""
        try:
            email = getattr(interviewer, 'email', None)
            if not email:
                return
            
            # Get interview details from dynamic data
            dynamic_data = interview.dynamic_interview_data or {}
            basic_info = dynamic_data.get('basic_info', {})
            schedule = dynamic_data.get('schedule', {})
            
            job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
            date_str = schedule.get('date', str(interview.date) if interview.date else 'TBD')
            time_str = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
            
            # Build context for template
            context = {
                'candidate_name': getattr(interviewer, 'name', '') or 'Interviewer',
                'job_title': job_title,
                'company_name': interview.company.name if interview.company else 'Company',
                'interview_title': basic_info.get('interview_title') or interview.title or 'Interview',
                'scheduled_date': date_str,
                'scheduled_time': time_str,
                'cancellation_reason': 'You have been removed from this interview',
                'contact_email': getattr(interview.company, 'email', '') if interview.company else ''
            }
            
            from django.template.loader import render_to_string
            html_message = render_to_string('interview_cancelled.html', context)
            
            subject = f"Interview Cancelled: {job_title} at {context['company_name']}"
            plain_message = f"Your interview for {job_title} at {context['company_name']} has been cancelled."
            
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=True)
        except Exception:
            pass
    
    def _send_interviewer_schedule_email(self, interview, interviewer, request):
        """Send schedule email to newly added interviewer using template"""
        try:
            email = getattr(interviewer, 'email', None)
            if not email:
                return
            
            # Get interview details from dynamic data
            dynamic_data = interview.dynamic_interview_data or {}
            basic_info = dynamic_data.get('basic_info', {})
            schedule = dynamic_data.get('schedule', {})
            
            job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
            date_str = schedule.get('date', str(interview.date) if interview.date else 'TBD')
            time_str = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
            timezone_str = schedule.get('time_zone', {}).get('name', 'UTC')
            meeting_link = basic_info.get('interview_link') or interview.meeting_link or ''
            interview_type = basic_info.get('interview_type', 'TBD')
            
            # Build candidate names list
            candidate_names = []
            for c in interview.candidate.all():
                c_name = f"{getattr(c, 'first_name', '')} {getattr(c, 'last_name', '')}".strip() or getattr(c, 'name', '')
                if c_name:
                    candidate_names.append(c_name)
            
            # Get or create interviewer status to get headless token
            interviewer_status, _ = InterviewerStatus.objects.get_or_create(
                interview=interview,
                interviewer=interviewer,
                defaults={'status': 'scheduled'}
            )
            
            # Generate headless token if not exists
            token = interviewer_status.headless_token
            if not token:
                import jwt
                token = jwt.encode(
                    {"interview_id": interview.id, "interviewer_id": interviewer.id, "type": "interviewer"},
                    settings.SECRET_KEY,
                    algorithm="HS256"
                )
                interviewer_status.headless_token = token
                interviewer_status.save(update_fields=['headless_token'])
            
            # Build headless URLs
            base_url = settings.APP_URL.rstrip('/')
            headless_url = f"{base_url}/headless/{interviewer_status.id}/isinterviewer/{token}"
            
            # Build context for template
            context = {
                'candidateName': getattr(interviewer, 'name', '') or 'Interviewer',
                'jobTitle': job_title,
                'companyName': interview.company.name if interview.company else 'Company',
                'startAt': f"{date_str} {time_str}",
                'timezone': timezone_str,
                'mode': interview_type,
                'meetingLink': meeting_link,
                'isInterviewer': True,
                'candidateNames': ', '.join(candidate_names) if candidate_names else 'Candidate',
                'interviewerNames': getattr(interviewer, 'name', '') or 'Interviewer',
                'year': djtz.now().year,
                'icsUrl': request.build_absolute_uri(reverse('interview-ics', args=[interview.id])) if request else '',
                'headlessAcceptUrl': headless_url,
                'headlessDeclineUrl': headless_url,
                'headlessRescheduleUrl': headless_url,
                'rescheduleUrl': headless_url,
            }
            
            from django.template.loader import render_to_string
            html_message = render_to_string('interview_scheduled.html', context)
            
            subject = f"Interview Scheduled: {job_title}"
            plain_message = f"You have been scheduled for an interview: {job_title} on {date_str} at {time_str}"
            
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=True)
        except Exception:
            pass
    
    def _send_candidate_cancellation_email(self, interview, candidate, request):
        """Send cancellation email to removed candidate using template"""
        try:
            # Get candidate email from webform or direct attribute
            email = candidate.email
            if not email and hasattr(candidate, 'webform_candidate_data') and candidate.webform_candidate_data:
                personal_details = candidate.webform_candidate_data.get('Personal Details', {})
                email = personal_details.get('email')
            
            if not email:
                return
            
            # Get interview details from dynamic data
            dynamic_data = interview.dynamic_interview_data or {}
            basic_info = dynamic_data.get('basic_info', {})
            schedule = dynamic_data.get('schedule', {})
            
            job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
            date_str = schedule.get('date', str(interview.date) if interview.date else 'TBD')
            time_str = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
            
            # Get candidate name
            first_name = candidate.first_name or ''
            last_name = candidate.last_name or ''
            if not first_name and candidate.webform_candidate_data:
                personal_details = candidate.webform_candidate_data.get('Personal Details', {})
                first_name = personal_details.get('first_name', '')
                last_name = personal_details.get('last_name', '')
            candidate_name = f"{first_name} {last_name}".strip() or 'Candidate'
            
            # Build context for template
            context = {
                'candidate_name': candidate_name,
                'job_title': job_title,
                'company_name': interview.company.name if interview.company else 'Company',
                'interview_title': basic_info.get('interview_title') or interview.title or 'Interview',
                'scheduled_date': date_str,
                'scheduled_time': time_str,
                'cancellation_reason': 'You have been removed from this interview',
                'contact_email': getattr(interview.company, 'email', '') if interview.company else ''
            }
            
            from django.template.loader import render_to_string
            html_message = render_to_string('interview_cancelled.html', context)
            
            subject = f"Interview Cancelled: {job_title} at {context['company_name']}"
            plain_message = f"Your interview for {job_title} at {context['company_name']} has been cancelled."
            
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=True)
        except Exception:
            pass
    
    def _send_candidate_schedule_email(self, interview, candidate, request):
        """Send schedule email to newly added candidate using template"""
        try:
            # Get candidate email from webform or direct attribute
            email = candidate.email
            if not email and hasattr(candidate, 'webform_candidate_data') and candidate.webform_candidate_data:
                personal_details = candidate.webform_candidate_data.get('Personal Details', {})
                email = personal_details.get('email')
            
            if not email:
                return
            
            # Get interview details from dynamic data
            dynamic_data = interview.dynamic_interview_data or {}
            basic_info = dynamic_data.get('basic_info', {})
            schedule = dynamic_data.get('schedule', {})
            
            job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
            date_str = schedule.get('date', str(interview.date) if interview.date else 'TBD')
            time_str = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
            timezone_str = schedule.get('time_zone', {}).get('name', 'UTC')
            meeting_link = basic_info.get('interview_link') or interview.meeting_link or ''
            interview_type = basic_info.get('interview_type', 'TBD')
            
            # Get candidate name
            first_name = candidate.first_name or ''
            last_name = candidate.last_name or ''
            if not first_name and candidate.webform_candidate_data:
                personal_details = candidate.webform_candidate_data.get('Personal Details', {})
                first_name = personal_details.get('first_name', '')
                last_name = personal_details.get('last_name', '')
            candidate_name = f"{first_name} {last_name}".strip() or 'Candidate'
            
            # Build interviewer names list
            interviewer_names = []
            for i in interview.interviewers.all():
                i_name = getattr(i, 'name', '') or f"{getattr(i, 'first_name', '')} {getattr(i, 'last_name', '')}".strip()
                if i_name:
                    interviewer_names.append(i_name)
            
            # Get or create candidate status to get headless token
            candidate_status, _ = InterviewCandidateStatus.objects.get_or_create(
                interview=interview,
                candidate=candidate,
                defaults={'status': 'scheduled'}
            )
            
            # Generate headless token if not exists
            token = candidate_status.headless_token
            if not token:
                import jwt
                token = jwt.encode(
                    {"interview_id": interview.id, "candidate_id": candidate.id, "type": "candidate"},
                    settings.SECRET_KEY,
                    algorithm="HS256"
                )
                candidate_status.headless_token = token
                candidate_status.save(update_fields=['headless_token'])
            
            # Build headless URLs
            # base_url = f"{request.scheme}://{request.get_host()}"
            # headless_url = f"{base_url}/headless/{candidate_status.id}/iscandidate/{token}"
            base_url = settings.APP_URL.rstrip('/')
            headless_url = f"{base_url}/headless/{candidate_status.id}/iscandidate/{token}"

            
            # Build context for template
            context = {
                'candidateName': candidate_name,
                'jobTitle': job_title,
                'companyName': interview.company.name if interview.company else 'Company',
                'startAt': f"{date_str} {time_str}",
                'timezone': timezone_str,
                'mode': interview_type,
                'meetingLink': meeting_link,
                'isInterviewer': False,
                'interviewerNames': ', '.join(interviewer_names) if interviewer_names else 'Interviewer',
                'year': djtz.now().year,
                'icsUrl': request.build_absolute_uri(reverse('interview-ics', args=[interview.id])) if request else '',
                'headlessAcceptUrl': headless_url,
                'headlessDeclineUrl': headless_url,
                'headlessRescheduleUrl': headless_url,
                'rescheduleUrl': headless_url,
            }
            
            from django.template.loader import render_to_string
            html_message = render_to_string('interview_scheduled.html', context)
            
            subject = f"Interview Scheduled: {job_title}"
            plain_message = f"Your interview has been scheduled: {job_title} on {date_str} at {time_str}"
            
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=True)
        except Exception:
            pass
    
    def _send_reschedule_emails(self, interview, request, old_date, old_time):
        """Send reschedule emails to all candidates and interviewers"""
        print(f"[RESCHEDULE] Sending reschedule emails for interview {interview.id}")
        # Send to all candidates
        for candidate in interview.candidate.all():
            print(f"[RESCHEDULE] Sending to candidate {candidate.id}")
            self._send_candidate_reschedule_email(interview, candidate, request, old_date, old_time)
        
        # Send to all interviewers
        for interviewer in interview.interviewers.all():
            print(f"[RESCHEDULE] Sending to interviewer {interviewer.id}")
            self._send_interviewer_reschedule_email(interview, interviewer, request, old_date, old_time)
    
    def _send_candidate_reschedule_email(self, interview, candidate, request, old_date, old_time):
        """Send reschedule email to candidate when interview time changes using template"""
        try:
            # Get candidate email from webform or direct attribute
            email = candidate.email
            if not email and hasattr(candidate, 'webform_candidate_data') and candidate.webform_candidate_data:
                personal_details = candidate.webform_candidate_data.get('Personal Details', {})
                email = personal_details.get('email')
            
            if not email:
                return
            
            # Get interview details from dynamic data
            dynamic_data = interview.dynamic_interview_data or {}
            basic_info = dynamic_data.get('basic_info', {})
            schedule = dynamic_data.get('schedule', {})
            
            job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
            new_date = schedule.get('date', str(interview.date) if interview.date else 'TBD')
            new_time = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
            timezone_str = schedule.get('time_zone', {}).get('name', 'UTC')
            meeting_link = basic_info.get('interview_link') or interview.meeting_link or ''
            interview_type = basic_info.get('interview_type', 'TBD')
            
            # Get candidate name
            first_name = candidate.first_name or ''
            last_name = candidate.last_name or ''
            if not first_name and candidate.webform_candidate_data:
                personal_details = candidate.webform_candidate_data.get('Personal Details', {})
                first_name = personal_details.get('first_name', '')
                last_name = personal_details.get('last_name', '')
            candidate_name = f"{first_name} {last_name}".strip() or 'Candidate'
            
            # Build interviewer names list
            interviewer_names = []
            for i in interview.interviewers.all():
                i_name = getattr(i, 'name', '') or f"{getattr(i, 'first_name', '')} {getattr(i, 'last_name', '')}".strip()
                if i_name:
                    interviewer_names.append(i_name)
            
            # Get candidate status for headless token
            try:
                candidate_status = InterviewCandidateStatus.objects.get(interview=interview, candidate=candidate)
                
                # Generate headless token if not exists
                token = candidate_status.headless_token
                if not token:
                    import jwt
                    token = jwt.encode(
                        {"interview_id": interview.id, "candidate_id": candidate.id, "type": "candidate"},
                        settings.SECRET_KEY,
                        algorithm="HS256"
                    )
                    candidate_status.headless_token = token
                    candidate_status.save(update_fields=['headless_token'])
                
                # Build headless URLs
                base_url = settings.APP_URL.rstrip('/')
                headless_url = f"{base_url}/headless/{candidate_status.id}/iscandidate/{token}"
            except InterviewCandidateStatus.DoesNotExist:
                headless_url = None
            
            # Build context for template
            context = {
                'candidateName': candidate_name,
                'jobTitle': job_title,
                'companyName': interview.company.name if interview.company else 'Company',
                'startAt': f"{new_date} {new_time}",
                'timezone': timezone_str,
                'mode': interview_type,
                'meetingLink': meeting_link,
                'isInterviewer': False,
                'interviewerNames': ', '.join(interviewer_names) if interviewer_names else 'Interviewer',
                'year': djtz.now().year,
                'icsUrl': request.build_absolute_uri(reverse('interview-ics', args=[interview.id])) if request else '',
                'headlessAcceptUrl': headless_url,
                'headlessDeclineUrl': headless_url,
                'headlessRescheduleUrl': headless_url,
                'rescheduleUrl': headless_url,
            }
            
            from django.template.loader import render_to_string
            html_message = render_to_string('interview_rescheduled.html', context)
            
            subject = f"Interview Rescheduled: {job_title}"
            plain_message = f"Your interview has been rescheduled to {new_date} at {new_time}"
            
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=False)
            print(f"[RESCHEDULE] Email sent to candidate {candidate.id} at {email}")
        except Exception as e:
            import traceback
            print(f"[RESCHEDULE EMAIL ERROR] Candidate {candidate.id}: {e}")
            print(traceback.format_exc())
            pass
    
    def _send_interviewer_reschedule_email(self, interview, interviewer, request, old_date, old_time):
        """Send reschedule email to interviewer when interview time changes using template"""
        try:
            email = getattr(interviewer, 'email', None)
            if not email:
                return
            
            # Get interview details from dynamic data
            dynamic_data = interview.dynamic_interview_data or {}
            basic_info = dynamic_data.get('basic_info', {})
            schedule = dynamic_data.get('schedule', {})
            
            job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
            new_date = schedule.get('date', str(interview.date) if interview.date else 'TBD')
            new_time = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
            timezone_str = schedule.get('time_zone', {}).get('name', 'UTC')
            meeting_link = basic_info.get('interview_link') or interview.meeting_link or ''
            interview_type = basic_info.get('interview_type', 'TBD')
            
            # Build candidate names list
            candidate_names = []
            for c in interview.candidate.all():
                c_name = f"{getattr(c, 'first_name', '')} {getattr(c, 'last_name', '')}".strip() or getattr(c, 'name', '')
                if c_name:
                    candidate_names.append(c_name)
            
            # Get interviewer status for headless token
            try:
                interviewer_status = InterviewerStatus.objects.get(interview=interview, interviewer=interviewer)
                
                # Generate headless token if not exists
                token = interviewer_status.headless_token
                if not token:
                    import jwt
                    token = jwt.encode(
                        {"interview_id": interview.id, "interviewer_id": interviewer.id, "type": "interviewer"},
                        settings.SECRET_KEY,
                        algorithm="HS256"
                    )
                    interviewer_status.headless_token = token
                    interviewer_status.save(update_fields=['headless_token'])
                
                # Build headless URLs
                base_url = settings.APP_URL.rstrip('/')
                headless_url = f"{base_url}/headless/{interviewer_status.id}/isinterviewer/{token}"
            except InterviewerStatus.DoesNotExist:
                headless_url = None
            
            # Build context for template
            context = {
                'candidateName': getattr(interviewer, 'name', '') or 'Interviewer',
                'jobTitle': job_title,
                'companyName': interview.company.name if interview.company else 'Company',
                'startAt': f"{new_date} {new_time}",
                'timezone': timezone_str,
                'mode': interview_type,
                'meetingLink': meeting_link,
                'isInterviewer': True,
                'candidateNames': ', '.join(candidate_names) if candidate_names else 'Candidate',
                'interviewerNames': getattr(interviewer, 'name', '') or 'Interviewer',
                'year': djtz.now().year,
                'icsUrl': request.build_absolute_uri(reverse('interview-ics', args=[interview.id])) if request else '',
                'headlessAcceptUrl': headless_url,
                'headlessDeclineUrl': headless_url,
                'headlessRescheduleUrl': headless_url,
                'rescheduleUrl': headless_url,
            }
            
            from django.template.loader import render_to_string
            html_message = render_to_string('interview_rescheduled.html', context)
            
            subject = f"Interview Rescheduled: {job_title}"
            plain_message = f"The interview has been rescheduled to {new_date} at {new_time}"
            
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=False)
            print(f"[RESCHEDULE] Email sent to interviewer {interviewer.id} at {email}")
        except Exception as e:
            import traceback
            print(f"[RESCHEDULE EMAIL ERROR] Interviewer {interviewer.id}: {e}")
            print(traceback.format_exc())
            pass

    def _send_interviewer_added_notification_to_others(self, interview, added_interviewer, request, other_interviewer_ids):
        """Notify existing interviewers that a new interviewer was added"""
        print(f"[PANEL NOTIFICATION] Starting added notification. Interview: {interview.id}, Added: {getattr(added_interviewer, 'name', added_interviewer.id)}, Others: {other_interviewer_ids}")
        
        if not other_interviewer_ids:
            print("[PANEL NOTIFICATION] No other interviewers to notify")
            return
        
        from settings.models import Contacts
        
        for interviewer_id in other_interviewer_ids:
            try:
                print(f"[PANEL NOTIFICATION] Processing interviewer_id: {interviewer_id}")
                interviewer = Contacts.objects.get(id=interviewer_id)
                email = getattr(interviewer, 'email', None)
                print(f"[PANEL NOTIFICATION] Interviewer: {getattr(interviewer, 'name', '')}, Email: {email}")
                if not email:
                    print(f"[PANEL NOTIFICATION] No email for interviewer {interviewer_id}, skipping")
                    continue
                
                dynamic_data = interview.dynamic_interview_data or {}
                basic_info = dynamic_data.get('basic_info', {})
                schedule = dynamic_data.get('schedule', {})
                
                job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
                date_str = schedule.get('date', str(interview.date) if interview.date else 'TBD')
                time_str = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
                
                context = {
                    'candidateName': getattr(interviewer, 'name', '') or 'Interviewer',
                    'jobTitle': job_title,
                    'companyName': interview.company.name if interview.company else 'Company',
                    'interviewTitle': basic_info.get('interview_title') or interview.title or 'Interview',
                    'scheduledDate': date_str,
                    'scheduledTime': time_str,
                    'changeType': 'added',
                    'changedInterviewerName': getattr(added_interviewer, 'name', '') or 'A new interviewer',
                    'message': f"{getattr(added_interviewer, 'name', 'A new interviewer')} has been added to the interview panel.",
                    'contactEmail': getattr(interview.company, 'email', '') if interview.company else ''
                }
                
                html_message = render_to_string('interview_panel_changed.html', context)
                
                subject = f"Interview Panel Updated: {job_title}"
                plain_message = f"A new interviewer has been added to your interview panel for {job_title}."
                
                print(f"[PANEL NOTIFICATION] Sending email to {email}")
                send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=False)
                print(f"[PANEL NOTIFICATION] Email sent successfully to {email}")
            except Exception as e:
                import traceback
                print(f"[PANEL NOTIFICATION ERROR] Failed to notify interviewer {interviewer_id}: {e}")
                print(traceback.format_exc())
                pass
    
    def _send_interviewer_removed_notification_to_others(self, interview, removed_interviewer_name, request, other_interviewer_ids):
        """Notify remaining interviewers that an interviewer was removed"""
        print(f"[PANEL NOTIFICATION] Starting removed notification. Interview: {interview.id}, Removed: {removed_interviewer_name}, Others: {other_interviewer_ids}")
        
        if not other_interviewer_ids:
            print("[PANEL NOTIFICATION] No other interviewers to notify")
            return
        
        from settings.models import Contacts
        
        for interviewer_id in other_interviewer_ids:
            try:
                print(f"[PANEL NOTIFICATION] Processing interviewer_id: {interviewer_id}")
                interviewer = Contacts.objects.get(id=interviewer_id)
                email = getattr(interviewer, 'email', None)
                print(f"[PANEL NOTIFICATION] Interviewer: {getattr(interviewer, 'name', '')}, Email: {email}")
                if not email:
                    print(f"[PANEL NOTIFICATION] No email for interviewer {interviewer_id}, skipping")
                    continue
                
                dynamic_data = interview.dynamic_interview_data or {}
                basic_info = dynamic_data.get('basic_info', {})
                schedule = dynamic_data.get('schedule', {})
                
                job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
                date_str = schedule.get('date', str(interview.date) if interview.date else 'TBD')
                time_str = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
                
                context = {
                    'candidateName': getattr(interviewer, 'name', '') or 'Interviewer',
                    'jobTitle': job_title,
                    'companyName': interview.company.name if interview.company else 'Company',
                    'interviewTitle': basic_info.get('interview_title') or interview.title or 'Interview',
                    'scheduledDate': date_str,
                    'scheduledTime': time_str,
                    'changeType': 'removed',
                    'changedInterviewerName': removed_interviewer_name or 'An interviewer',
                    'message': f"{removed_interviewer_name or 'An interviewer'} has been removed from the interview panel.",
                    'contactEmail': getattr(interview.company, 'email', '') if interview.company else ''
                }
                
                html_message = render_to_string('interview_panel_changed.html', context)
                
                subject = f"Interview Panel Updated: {job_title}"
                plain_message = f"An interviewer has been removed from your interview panel for {job_title}."
                
                send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [email], html_message=html_message, fail_silently=True)
            except Exception:
                pass

    def _send_acceptance_notification_to_company(self, interview, role, request, job_title, date_str, time_str, company_name):
        """Notify company/recruiter when candidate or interviewer accepts"""
        try:
            company_email = getattr(interview.company, 'email', None)
            if not company_email:
                return

            # Get the name of who accepted
            if role == "candidate":
                acceptor_name = "A candidate"
            else:
                acceptor_name = "An interviewer"

            context = {
                'candidateName': 'Recruitment Team',
                'jobTitle': job_title,
                'companyName': company_name,
                'scheduledDate': date_str,
                'scheduledTime': time_str,
                'acceptorRole': role,
                'acceptorName': acceptor_name,
                'year': djtz.now().year,
            }

            try:
                html_message = render_to_string('interview_acceptance_notification.html', context)
            except Exception:
                html_message = f"""
                <p>Hi Recruitment Team,</p>
                <p>{acceptor_name} has <strong>accepted</strong> the interview for <strong>{job_title}</strong>.</p>
                <p><strong>Date:</strong> {date_str}<br><strong>Time:</strong> {time_str}</p>
                <p>Best regards,<br>{company_name} Team</p>
                """

            subject = f"Interview Accepted: {job_title}"
            plain_message = f"{acceptor_name} has accepted the interview for {job_title} on {date_str} at {time_str}."

            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [company_email],
                     html_message=html_message, fail_silently=True)
        except Exception as e:
            print(f"[COMPANY ACCEPT NOTIFICATION ERROR] {e}")
    def delete(self, request, pk):
        """Delete interview"""
        interview = self.get_object(pk)
        interview.add_audit("deleted", by=request.user)
        interview.delete()
        return Response({"detail": "Interview deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 1️⃣  RESCHEDULE REQUEST (Candidate Request)
# ==========================================================
class RescheduleRequestAPIView(APIView):
    """
    POST  → Candidate requests new time slot (token version supported)
    GET   → List all reschedule requests for an interview (id version)
    PUT   → Update (approve/reject) a reschedule request by pk
    """
    # permission_classes = [IsAuthenticated]

    def post(self, request, token=None):
        """Handles reschedule requests, both via headless token and normal interview_id."""
        data = request.data.copy()
        candidate_status = None
        interview = None
        interviewer_status = None

        # HEADLESS (token in URL):
        if token:
            secret = settings.SECRET_KEY
            try:
                payload = jwt.decode(token, secret, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)
            except jwt.InvalidTokenError:
                return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

            interview_id = payload.get("interview_id")
            candidate_id = payload.get("candidate_id")
            interviewer_id = payload.get("interviewer_id")
            interview = get_object_or_404(Interview, id=interview_id)
            if candidate_id:
                candidate_status = get_object_or_404(InterviewCandidateStatus, interview_id=interview_id, candidate_id=candidate_id)

                data["interview_id"] = interview_id
                data["candidate_status"] = candidate_status.id
                data["actor_type"] = "candidate"
            elif interviewer_id:
                interviewer_status = get_object_or_404(InterviewerStatus, interview_id=interview_id, interviewer_id=interviewer_id)

                data["interview_id"] = interview_id
                data["interviewer_status"] = interviewer_status.id
                data["actor_type"] = "interviewer"
        # AUTHENTICATED (classic):
        else:
            interview_id_val = data.get("interview_id") or data.get("interview")
            if not interview_id_val:
                return Response({"detail": "interview_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            interview = get_object_or_404(Interview, id=interview_id_val)
            data["interview_id"] = interview.id
            # (potentially locate candidate_status by request.user)
        serializer = RescheduleRequestSerializer(data=data)
        if serializer.is_valid():
            reschedule = serializer.save()
            # Update only the candidate status, do not update Interview.status
            if candidate_status:
                candidate_status.status = "reschedule_requested"
                candidate_status.save(update_fields=["status"])
            interview.add_audit(
                "reschedule_requested",
                by="headless" if token else request.user.account.id,
                meta={
                    "proposed_date": data.get("proposed_date"),
                    "proposed_time": data.get("proposed_time"),
                    "proposed_timezone": data.get("proposed_timezone"),
                    "reschedule_reason_type": data.get("reschedule_reason_type"),
                    "message": data.get("message"),
                },
            )
            if interviewer_status:
                interviewer_status.status = "reschedule_requested"
                interviewer_status.save(update_fields=["status"])
            interview.add_audit(
                "reschedule_requested",
                by="headless" if token else request.user.account.id,
                meta={
                    "proposed_date": data.get("proposed_date"),
                    "proposed_time": data.get("proposed_time"),
                    "proposed_timezone": data.get("proposed_timezone"),
                    "reschedule_reason_type": data.get("reschedule_reason_type"),
                    "message": data.get("message"),
                },
            )
            # Notify recruiter (created_by) on reschedule request
            try:
                recruiter_email = getattr(interview.created_by, 'email', None)
                if recruiter_email:
                    dynamic_data = interview.dynamic_interview_data or {}
                    basic_info = dynamic_data.get('basic_info', {})
                    schedule = dynamic_data.get('schedule', {})
                    
                    job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
                    company_name = interview.company.name if interview.company else 'Company'
                    scheduled_date = schedule.get('date', str(interview.date) if interview.date else 'TBD')
                    scheduled_time = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
                    
                    # Get actor name based on actor_type
                    actor_type = data.get("actor_type", "candidate")
                    if actor_type == "candidate" and candidate_status:
                        webform_data = candidate_status.candidate.webform_candidate_data or {}
                        personal_details = webform_data.get("Personal Details", {})
                        first_name = personal_details.get("first_name", "")
                        last_name = personal_details.get("last_name", "")
                        actor_name = f"{first_name} {last_name}".strip() or "Candidate"
                    elif actor_type == "interviewer" and interviewer_status:
                        actor_name = interviewer_status.interviewer.name if interviewer_status.interviewer else "Interviewer"
                    else:
                        actor_name = request.user.account.name if hasattr(request.user, 'account') and hasattr(request.user, 'account') else 'User'
                    
                    context = {
                        'candidate_name': actor_name,
                        'job_title': job_title,
                        'company_name': company_name,
                        'interview_title': basic_info.get('interview_title') if dynamic_data else interview.title or 'Interview',
                        'scheduled_date': scheduled_date,
                        'scheduled_time': scheduled_time,
                        'cancellation_reason': f"Reschedule requested. Proposed: {data.get('proposed_date')} {data.get('proposed_time')} ({data.get('proposed_timezone')}). Reason: {data.get('reschedule_reason_type')}. Message: {data.get('message')}",
                        'contact_email': settings.DEFAULT_FROM_EMAIL,
                    }
                    
                    html_message = render_to_string("interview_reschedule_requested.html", context)
                    subject = f"Reschedule Request: {job_title}"
                    plain_message = f"A reschedule has been requested for {job_title}. Proposed: {data.get('proposed_date')} {data.get('proposed_time')}."
                    
                    send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [recruiter_email], html_message=html_message, fail_silently=True)
            except Exception:
                pass
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, token=None, interview_id=None):
        """List all reschedule requests for a specific interview"""
        reschedules = RescheduleRequest.objects.filter(interview_id=interview_id)
        serializer = RescheduleRequestSerializer(reschedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Approve or Reject reschedule"""
        reschedule = get_object_or_404(RescheduleRequest, pk=pk)
        status_value = request.data.get("status")

        if status_value not in ["approved", "rejected"]:
            return Response(
                {"detail": "Status must be 'approved' or 'rejected'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reschedule.status = status_value
        reschedule.save(update_fields=["status"])
        reschedule.interview.add_audit(
            f"reschedule_{status_value}",
            by=request.user.account.id,
            meta={"reschedule_id": reschedule.id},
        )

        if status_value == "approved":
            reschedule.interview.start_at = reschedule.proposed_start
            reschedule.interview.end_at = reschedule.proposed_end
            reschedule.interview.status = "rescheduled"
            reschedule.interview.save(update_fields=["start_at", "end_at", "status"])
            try:
                CalendarService.update_event_on_reschedule(reschedule.interview)
            except Exception:
                pass
            # Notify participants on approval
            try:
                recipients = []
                for c in reschedule.interview.candidate.all():
                    if getattr(c, 'email', None) and c.email not in recipients:
                        recipients.append(c.email)
                subject = f"Interview Rescheduled: #{reschedule.interview.id}"
                ics_url = self.request.build_absolute_uri(reverse('interview-ics', args=[reschedule.interview.id]))
                body = (
                    f"Your interview has been rescheduled.\n\n"
                    f"Add to calendar: {ics_url}\n"
                )
                if recipients:
                    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
            except Exception:
                pass

        return Response({"detail": f"Reschedule {status_value} successfully"})


# ==========================================================
# 2️⃣  FEEDBACK (Interviewer Feedback)
# ==========================================================
class FeedbackAPIView(APIView):
    """
    POST → Submit feedback for an interview
    GET  → Get feedback list for an interview
    """
    # permission_classes = [IsAuthenticated]

    def get(self, request, interview_id):
        """Get all feedback for one interview"""
        feedbacks = Feedback.objects.filter(interview_id=interview_id)
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, interview_id):
        """Submit feedback"""
        data = request.data.copy()
        data["interview"] = interview_id
        serializer = FeedbackSerializer(data=data)
        if serializer.is_valid():
            feedback = serializer.save()
            feedback.interview.add_audit(
                "feedback_submitted",
                by=request.user,
                meta={"feedback_id": feedback.id},
            )

            # Update candidate status
            candidate_status =InterviewCandidateStatus.objects.get(interview_id=interview_id, candidate_id=feedback.candidate_id)
            candidate_status.status = "completed"
            candidate_status.save(update_fields=["status"])

            # Update interviewer status
            interviewer_status =InterviewerStatus.objects.get(interview_id=interview_id, interviewer_id=feedback.interviewer_id)
            interviewer_status.status = "completed"
            interviewer_status.save(update_fields=["status"])

            # Update interview status
            interview =Interview.objects.get(id=interview_id)
            interview.status = "completed"
            interview.save(update_fields=["status"])

            # Send email to created_by
            try:
                if interview.created_by and interview.created_by.email:
                    subject = f"Interview Feedback Submitted: #{interview.id}"
                    body = (
                        f"Feedback has been submitted for interview #{interview.id}.\n\n"
                        f"Job: {interview.dynamic_interview_data.get('basic_info', {}).get('job', {}).get('name') if interview.dynamic_interview_data else interview.job.title if interview.job else 'Position'}\n"
                        f"Interview Title: {interview.dynamic_interview_data.get('basic_info', {}).get('interview_title') if interview.dynamic_interview_data else interview.title or 'Interview'}\n"
                        f"Status: {interview.status}\n\n"
                        f"You can view the feedback details in your interview."
                    )
                    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [interview.created_by.email], fail_silently=True)
            except Exception as e:
                # Log error but don't fail the response
                pass

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================================
# 3️⃣  HEADLESS TOKEN APIs (No Login Required)
# ==========================================================
class HeadlessValidateAPIView(APIView):
    """
    GET → Validate a headless token (candidate/manager)
    """
    # permission_classes = [AllowAny]

    def get(self, request, token,user_type,interview_id):
        secret = settings.SECRET_KEY
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        # interview_id = payload.get("interview_id")
        # interview = get_object_or_404(Interview, id=interview_id)
        if user_type == "iscandidate":
            candidatestatus = get_object_or_404(InterviewCandidateStatus, id=interview_id, headless_token=token)
            # Check if interview is cancelled
            if candidatestatus.interview.status == "cancelled":
                return Response({"detail": "Interview has been cancelled"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = InterviewCandidateStatusSerializer(candidatestatus)
        elif user_type == "isinterviewer":
            interviewerstatus = get_object_or_404(InterviewerStatus, id=interview_id, headless_token=token)
            # Check if interview is cancelled
            if interviewerstatus.interview.status == "cancelled":
                return Response({"detail": "Interview has been cancelled"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = InterviewerStatusSerializer(interviewerstatus)
        return Response({
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class HeadlessActionAPIView(APIView):
    """
    POST → Perform action using headless token (accept / decline / reschedule)
    """
    # permission_classes = [AllowAny]
    def _perform_action(self, request, token, action):
        secret = settings.SECRET_KEY
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        interview_id = payload.get("interview_id")
        # Support both 'type' (current) and 'role' (legacy) keys
        role = payload.get("type") or payload.get("role")
        print("payload",payload)
        interview = get_object_or_404(Interview, id=interview_id)

        # Resolve the correct status object based on token type
        status_obj = None
        candidate_id = None
        interviewer_id = None
        if role == "candidate":
            candidate_id = payload.get("candidate_id")
            status_obj = InterviewCandidateStatus.objects.filter(
                interview_id=interview_id,
                candidate_id=candidate_id,
                headless_token=token,
            ).first()
        elif role == "interviewer":
            interviewer_id = payload.get("interviewer_id")
            status_obj = InterviewerStatus.objects.filter(
                interview_id=interview_id,
                interviewer_id=interviewer_id,
                headless_token=token,
            ).first()

        if status_obj is None:
            return Response({"detail": "Status not found for token"}, status=status.HTTP_404_NOT_FOUND)

        if action == "accept":
            # Update per-user status only (no Interview.status field)
            status_obj.status = "accepted"
            status_obj.save(update_fields=["status"])
            interview.add_audit("accepted", by=role)
            try:
                CalendarService.set_rsvp(interview, "accepted", by=role)
            except Exception:
                pass
            # confirmation emails with company info
            try:
                # Get interview details
                dynamic_data = interview.dynamic_interview_data or {}
                basic_info = dynamic_data.get('basic_info', {})
                schedule = dynamic_data.get('schedule', {})
                
                job_title = basic_info.get('job', {}).get('name', interview.job.title if interview.job else 'Position')
                date_str = schedule.get('date', str(interview.date) if interview.date else 'TBD')
                time_str = schedule.get('time') or schedule.get('start_time', str(interview.time_start) if interview.time_start else 'TBD')
                company_name = interview.company.name if interview.company else 'Company'
                company_email = getattr(interview.company, 'email', '') if interview.company else ''
                
                ics_url = request.build_absolute_uri(reverse('interview-ics', args=[interview.id]))
                
                self._send_acceptance_notification_to_company(interview, role, request, job_title, date_str, time_str, company_name, candidate_id=candidate_id, interviewer_id=interviewer_id)
            except Exception as e:
                print(f"[ACCEPT EMAIL ERROR] {e}")
                pass
            return Response({"detail": "Accepted"}, status=status.HTTP_200_OK)

        elif action == "decline":
            # capture decline reason/details if provided
            reason = request.data.get("reason_type")
            details = request.data.get("reason")

            # persist decline response, linking the correct FK
            decline_kwargs = {
                "interview": interview,
                "actor_type": role,
                "reason": reason,
                "details": details,
            }
            if role == "candidate":
                decline_kwargs["candidate_status"] = status_obj
            elif role == "interviewer":
                decline_kwargs["interviewer_status"] = status_obj
            DeclineResponse.objects.create(**decline_kwargs)

            # update per-user status
            status_obj.status = "declined"
            status_obj.save(update_fields=["status"])
            interview.add_audit("declined", by=role, meta={"reason": reason})
            try:
                CalendarService.set_rsvp(interview, "declined", by=role)
            except Exception:
                pass
            
            # Send email notification to interview creator about decline
            try:
                email_settings = EmailSettings.objects.filter(company_id=interview.company_id).order_by('-created_at').first()
                if email_settings and interview.created_by and interview.created_by.email:
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
                    
                    # Get actor name based on role
                    if role == "candidate":
                        # actor_name = status_obj.candidate.first_name if status_obj.candidate else "Candidate"
                        webform_data = status_obj.candidate.webform_candidate_data or {}
                        personal_details = webform_data.get("Personal Details", {})
                        first_name = personal_details.get("first_name", "")
                        last_name = personal_details.get("last_name", "")
                        actor_name =f'{first_name} {last_name}'
                    else:
                        actor_name = status_obj.interviewer.name if status_obj.interviewer else "Interviewer"
                    
                    context = {
                        'candidate_name': actor_name,
                        'job_title': interview.dynamic_interview_data.get('basic_info', {}).get('job', {}).get('name') if interview.dynamic_interview_data else interview.job.title if interview.job else 'Position',
                        'company_name': interview.company.name if interview.company else 'Company',
                        'interview_title': interview.dynamic_interview_data.get('basic_info', {}).get('interview_title') if interview.dynamic_interview_data else interview.title or 'Interview',
                        'scheduled_date': interview.date.strftime('%B %d, %Y') if interview.date else '',
                        'scheduled_time': interview.time_start.strftime('%I:%M %p') if interview.time_start else '',
                        'cancellation_reason': f'Interview declined by {role}: {actor_name}. Reason: {reason}' if reason else f'Interview declined by {role}: {actor_name}',
                        'contact_email': email_settings.sender_mail
                    }
                    
                    html_message = render_to_string("interview_declined.html", context)
                    subject = f"Interview Declined: {context['job_title']} by {actor_name}"
                    plain_message = f"The interview for {context['job_title']} has been declined by {role}: {actor_name}."
                    
                    send_mail(
                        subject,
                        plain_message,
                        email_settings.sender_mail,
                        [interview.created_by.email],
                        html_message=html_message,
                        fail_silently=False,
                        connection=connection,
                    )
                    print(f"[Interview Decline] Notification email sent to creator: {interview.created_by.email}")
            except Exception as e:
                print(f"[Interview Decline] Error sending notification email to company: {e}")
            
            return Response({"detail": "Declined"}, status=status.HTTP_200_OK)

        elif action == "reschedule":
            proposed_start = request.data.get("proposed_start")
            proposed_end = request.data.get("proposed_end")
            msg = request.data.get("message")

            interview.add_audit(
                "reschedule_requested",
                by=role,
                meta={
                    "proposed_start": proposed_start,
                    "proposed_end": proposed_end,
                    "message": msg,
                },
            )
            status_obj.status = "reschedule_requested"
            status_obj.save(update_fields=["status"])
            
            # Send email notification to interview creator about reschedule request
            try:
                email_settings = EmailSettings.objects.filter(company_id=interview.company_id).order_by('-created_at').first()
                if email_settings and interview.created_by and interview.created_by.email:
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
                    
                    # Get actor name based on role
                    if role == "candidate":
                        webform_data = status_obj.candidate.webform_candidate_data or {}
                        personal_details = webform_data.get("Personal Details", {})
                        first_name = personal_details.get("first_name", "")
                        last_name = personal_details.get("last_name", "")
                        actor_name = f"{first_name} {last_name}".strip() or "Candidate"
                    else:
                        actor_name = status_obj.interviewer.name if status_obj.interviewer else "Interviewer"
                    
                    context = {
                        'candidate_name': actor_name,
                        'job_title': interview.dynamic_interview_data.get('basic_info', {}).get('job', {}).get('name') if interview.dynamic_interview_data else interview.job.title if interview.job else 'Position',
                        'company_name': interview.company.name if interview.company else 'Company',
                        'interview_title': interview.dynamic_interview_data.get('basic_info', {}).get('interview_title') if interview.dynamic_interview_data else interview.title or 'Interview',
                        'scheduled_date': interview.date.strftime('%B %d, %Y') if interview.date else '',
                        'scheduled_time': interview.time_start.strftime('%I:%M %p') if interview.time_start else '',
                        'cancellation_reason': f'Reschedule requested by {role}: {actor_name}. Proposed start: {proposed_start}, Proposed end: {proposed_end}. Message: {msg}',
                        'contact_email': email_settings.sender_mail
                    }
                    
                    html_message = render_to_string("interview_reschedule_requested.html", context)
                    subject = f"Interview Reschedule Request: {context['job_title']} by {actor_name}"
                    plain_message = f"A reschedule has been requested for the interview of {context['job_title']} by {role}: {actor_name}. Proposed time: {proposed_start} to {proposed_end}. Message: {msg}"
                    
                    send_mail(
                        subject,
                        plain_message,
                        email_settings.sender_mail,
                        [interview.created_by.email],
                        html_message=html_message,
                        fail_silently=False,
                        connection=connection,
                    )
                    print(f"[Interview Reschedule] Notification email sent to creator: {interview.created_by.email}")
            except Exception as e:
                print(f"[Interview Reschedule] Error sending notification email to company: {e}")
            
            return Response({"detail": "Reschedule requested"}, status=status.HTTP_200_OK)

        return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, token):
        action = request.data.get("action")
        return self._perform_action(request, token, action)

    # def get(self, request, token):
    #     action = request.GET.get("action")
    #     return self._perform_action(request, token, action)

    def _send_acceptance_notification_to_company(self, interview, role, request, job_title, date_str, time_str, company_name,candidate_id=None,interviewer_id=None):
        """Notify created_by user when candidate or interviewer accepts"""
        try:
            creator = interview.created_by
            creator_email = getattr(creator, 'email', None)
            if not creator_email:
                return

            # Get the name of who accepted and build details URL
            if role == "candidate":
                acceptor_name = "A candidate"
                # Link to candidate details - use first candidate if multiple
                candidate = Candidate.objects.get(id=candidate_id)
                if candidate:
                    # Get name from webform_candidate_data JSON
                    webform_data = candidate.webform_candidate_data or {}
                    personal_details = webform_data.get("Personal Details", {})
                    first_name = personal_details.get("first_name", "")
                    last_name = personal_details.get("last_name", "")
                    details_url = f"{first_name} {last_name}".strip()
                    # acceptor_name = f"{first_name} {last_name}".strip() or "A candidate"
                else:
                    details_url = ""
                    acceptor_name = "A candidate"
            else:
                acceptor_name = "An interviewer"
                # Link to interview details
                if interviewer_id:
                    try:
                        interviewer = Contacts.objects.get(id=interviewer_id)
                        # acceptor_name = interviewer.name or "An interviewer"
                        details_url = interviewer.name
                    except Contacts.DoesNotExist:
                        pass

            creator_name = getattr(creator, 'first_name', '') or 'Interview Creator'
            context = {
                'candidateName': details_url,
                'jobTitle': job_title,
                'companyName': company_name,
                'scheduledDate': date_str,
                'scheduledTime': time_str,
                'acceptorRole': role,
                'acceptorName': acceptor_name,
                'year': djtz.now().year,
                'detailsUrl': details_url,
            }

            try:
                html_message = render_to_string('interview_acceptance_notification.html', context)
            except Exception:
                html_message = f"""
                <p>Hi Recruitment Team,</p>
                <p>{acceptor_name} has <strong>accepted</strong> the interview for <strong>{job_title}</strong>.</p>
                <p><strong>Date:</strong> {date_str}<br><strong>Time:</strong> {time_str}</p>
                <p><a href="{details_url}">View Details</a></p>
                <p>Best regards,<br>{company_name} Team</p>
                """

            subject = f"Interview Accepted: {job_title} by {acceptor_name}"
            plain_message = f"{acceptor_name} has accepted the interview for {job_title} on {date_str} at {time_str}. View details: {details_url}"

            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [creator_email],
                     html_message=html_message, fail_silently=True)
            print(f"[Interview Accept] Notification email sent to creator: {creator_email}")
        except Exception as e:
            print(f"[CREATOR ACCEPT NOTIFICATION ERROR] {e}")


class InterviewICSAPIView(APIView):
    """Return an .ics calendar invite for the interview."""
    permission_classes = [AllowAny]

    def get(self, request, interview_id):
        try:
            interview = get_object_or_404(Interview, pk=interview_id)
            dinfo = interview.dynamic_interview_data or {}
            schedule = dinfo.get("schedule") or dinfo.get("Schedule") or {}
            basic = dinfo.get("basic_info", {})

            # Validate required fields
            if not schedule.get("date"):
                return Response({"detail": "Interview date is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not schedule.get("time"):
                return Response({"detail": "Interview time is required"}, status=status.HTTP_400_BAD_REQUEST)

            title = basic.get("interview_title") or interview.title or "Interview"
            tzid = (schedule.get("time_zone") or {}).get("id") or "UTC"
            date = schedule.get("date")
            time_val = schedule.get("time") or schedule.get("start_time") or "00:00"
            duration = schedule.get("duration", "30 minutes")
            meeting_link = basic.get("interview_link") or basic.get("interview_linklocation") or interview.meeting_link or ""

            # Parse time format - handle both HH:MM and HH:MM:SS formats
            try:
                if len(time_val.split(':')) == 2:
                    time_val += ":00"  # Add seconds if missing
                start_dt = datetime.strptime(f"{date} {time_val}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return Response({"detail": "Invalid time format"}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate end time from duration
            try:
                # Parse duration (e.g., "30 minutes", "1 hour", "45 mins")
                duration_str = duration.lower().strip()
                if "hour" in duration_str:
                    hours = int(''.join(filter(str.isdigit, duration_str)))
                    minutes = 0
                elif "min" in duration_str:
                    minutes = int(''.join(filter(str.isdigit, duration_str)))
                    hours = 0
                else:
                    # Default to 30 minutes if duration format is not recognized
                    minutes = 30
                    hours = 0
                
                # Calculate end time
                end_dt = start_dt + timedelta(hours=hours, minutes=minutes)
                
            except (ValueError, TypeError):
                # Fallback to 30 minutes if duration parsing fails
                end_dt = start_dt + timedelta(minutes=30)

            # Convert to UTC for ICS (use provided tzid when possible)
            try:
                tz = ZoneInfo(tzid)
            except Exception:
                try:
                    tz = ZoneInfo("UTC")
                except Exception:
                    # Fallback to Django's current timezone if ZoneInfo fails
                    tz = djtz.get_current_timezone()

            start_aware = djtz.make_aware(start_dt, tz).astimezone(dt_tz.utc)
            end_aware = djtz.make_aware(end_dt, tz).astimezone(dt_tz.utc)

            def fmt(dt):
                return dt.strftime("%Y%m%dT%H%M%SZ")

            # Generate ICS content
            ics = []
            ics.append("BEGIN:VCALENDAR")
            ics.append("PRODID:-//Edjobster//Interview//EN")
            ics.append("VERSION:2.0")
            ics.append("CALSCALE:GREGORIAN")
            ics.append("METHOD:REQUEST")
            ics.append("BEGIN:VEVENT")
            ics.append(f"UID:{interview.id}@edjobster.com")
            ics.append(f"DTSTAMP:{fmt(djtz.now().astimezone(dt_tz.utc))}")
            ics.append(f"DTSTART:{fmt(start_aware)}")
            ics.append(f"DTEND:{fmt(end_aware)}")
            ics.append(f"SUMMARY:{title}")
            
            # Enhanced description with more details
            description_parts = [f"Interview: {title}"]
            if basic.get("interview_round"):
                description_parts.append(f"Round: {basic.get('interview_round')}")
            if basic.get("interview_type"):
                description_parts.append(f"Type: {basic.get('interview_type')}")
            if meeting_link:
                description_parts.append(f"Meeting Link: {meeting_link}")
            if basic.get("notes_for_candidate_public"):
                description_parts.append(f"Notes: {basic.get('notes_for_candidate_public')}")
            
            description = "\\n".join(description_parts)
            ics.append(f"DESCRIPTION:{description}")
            
            # Location - use meeting link or interview location
            location = meeting_link or basic.get("interview_location", {}).get("name", "Video Meeting")
            ics.append(f"LOCATION:{location}")
            
            # Add organizer information if available
            if interview.created_by:
                ics.append(f"ORGANIZER:CN=Edjobster:mailto:noreply@edjobster.com")
            
            # Add attendees (candidates and interviewers)
            candidates = basic.get("candidate", [])
            interviewers_data = dinfo.get("interviewers", {}).get("interviewers", [])
            
            for candidate in candidates:
                if candidate.get("name"):
                    ics.append(f"ATTENDEE:CN={candidate['name']}:mailto:candidate@edjobster.com")
            
            for interviewer in interviewers_data:
                if interviewer.get("name"):
                    ics.append(f"ATTENDEE:CN={interviewer['name']}:mailto:interviewer@edjobster.com")
            
            ics.append("END:VEVENT")
            ics.append("END:VCALENDAR")

            content = "\r\n".join(ics)
            response = HttpResponse(content, content_type="text/calendar")
            response["Content-Disposition"] = f"attachment; filename=interview-{interview.id}.ics"
            return response
            
        except Exception as e:
            return Response({"detail": f"Error generating ICS file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RescheduleAPIView(APIView):
    """
    POST   → Reschedule interview
    """
    # permission_classes = [IsAuthenticated]

    def get(sefl,request,pk):
        reschedule_request = get_object_or_404(RescheduleRequest, pk=pk,status="interviewer_email_send")
        serializer = RescheduleRequestSerializer(reschedule_request)
        return Response(serializer.data) 

    def parse_duration(self, duration_str):
        """Parse duration string like '15 minutes' into timedelta"""
        if not duration_str:
            return timedelta(hours=1)  # default
        parts = duration_str.split()
        if len(parts) == 2:
            try:
                num = int(parts[0])
                unit = parts[1].lower()
                if unit in ['minute', 'minutes']:
                    return timedelta(minutes=num)
                elif unit in ['hour', 'hours']:
                    return timedelta(hours=num)
            except ValueError:
                pass
        return timedelta(hours=1)  # default

    def create_new_interview(self, interview, reschedule_request, request):
        """Create a new interview based on reschedule request"""
        # Prepare data for new interview
        new_data = {
            'job': interview.job.id,
            'company': interview.company.id,
            'candidate': [c.id for c in interview.candidate.all()],
            'title': interview.title,
            'date': reschedule_request.proposed_date,
            'location': interview.location.id if interview.location else None,
            'interviewers': [i.id for i in interview.interviewers.all()],
            'dynamic_interview_data': interview.dynamic_interview_data,
            'created_by': request.user.id,
        }
        # Get the candidate(s) from original interview - keep all candidates for reschedule
        # For interviewer reschedule, we keep all original candidates
        # For candidate reschedule, we keep only the specific candidate who requested
        if reschedule_request.actor_type == "candidate":
            candidate_id = reschedule_request.candidate_status.candidate.id
            new_data['candidate'] = [candidate_id]
        else:
            # For interviewer reschedule, keep all original candidates
            new_data['candidate'] = [c.id for c in interview.candidate.all()]
        
        # Update dynamic_interview_data with new schedule
        dynamic_data = interview.dynamic_interview_data.copy()
        schedule = dynamic_data.get('schedule', {})
        schedule['date'] = str(reschedule_request.proposed_date)
        schedule['time'] = str(reschedule_request.proposed_time)
        dynamic_data['schedule'] = schedule
        
        # Filter basic_info.candidate based on actor_type
        basic_info = dynamic_data.get('basic_info', {})
        if 'candidate' in basic_info:
            if reschedule_request.actor_type == "candidate":
                # For candidate reschedule, only include the specific candidate
                basic_info['candidate'] = [c for c in basic_info['candidate'] if c.get('id') == candidate_id]
            # For interviewer reschedule, keep all candidates as-is
        dynamic_data['basic_info'] = basic_info
        
        new_data['dynamic_interview_data'] = dynamic_data
        
        # Calculate time_end based on duration from dynamic_interview_data
        duration_str = schedule.get('duration', '')
        duration = self.parse_duration(duration_str)
        start_time = reschedule_request.proposed_time
        end_time = (datetime.combine(datetime.today(), start_time) + duration).time()
        new_data['time_end'] = end_time
        
        new_data['date'] = reschedule_request.proposed_date
        new_data['time_start'] = reschedule_request.proposed_time

        # Create new interview
        serializer = InterviewSerializer(data=new_data, context={"request": request})
        if serializer.is_valid():
            new_interview = serializer.save()
            new_interview.status = "rescheduled"
            new_interview.save()
            # new_interview.generate_meeting_link()
            new_interview.add_audit("created from reschedule", by=request.user)
            
            # Create InterviewCandidateStatus for each candidate
            for candidate in new_interview.candidate.all():
                InterviewCandidateStatus.objects.create(
                    interview=new_interview,
                    candidate=candidate,
                    status="scheduled"
                )
            
            # Create InterviewerStatus for each interviewer
            for interviewer in new_interview.interviewers.all():
                InterviewerStatus.objects.create(
                    interview=new_interview,
                    interviewer=interviewer,
                    status="scheduled"
                )
            
            # Update old interview status to cancelled
            interview.status = "cancelled"
            interview.save(update_fields=["status"])
            
            # If interviewer reschedule, send cancellation email to candidates
            if reschedule_request.actor_type == "interviewer":
                try:
                    email_settings = EmailSettings.objects.filter(company_id=interview.company_id).order_by('-created_at').first()
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
                        
                        for candidate in interview.candidate.all():
                            candidate_email = getattr(candidate, 'email', None)
                            if not candidate_email:
                                try:
                                    webform = getattr(candidate, "webform_candidate_data", None)
                                    if isinstance(webform, dict):
                                        personal = webform.get("Personal Details", {})
                                        candidate_email = personal.get("email") or personal.get("Email")
                                except Exception:
                                    pass
                            
                            if candidate_email and '@' in candidate_email:
                                context = {
                                    'candidate_name': getattr(candidate, 'first_name', '') or 'Candidate',
                                    'job_title': interview.dynamic_interview_data.get('basic_info', {}).get('job', {}).get('name') if interview.dynamic_interview_data else interview.job.title if interview.job else 'Position',
                                    'company_name': interview.company.name if interview.company else 'Company',
                                    'interview_title': interview.dynamic_interview_data.get('basic_info', {}).get('interview_title') if interview.dynamic_interview_data else interview.title or 'Interview',
                                    'scheduled_date': interview.date.strftime('%B %d, %Y') if interview.date else '',
                                    'scheduled_time': interview.time_start.strftime('%I:%M %p') if interview.time_start else '',
                                    'cancellation_reason': 'Interview rescheduled by interviewer',
                                    'contact_email': email_settings.sender_mail
                                }
                                
                                html_message = render_to_string("interview_cancelled.html", context)
                                subject = f"Interview Cancelled: {context['job_title']} at {context['company_name']}"
                                plain_message = f"Your interview for {context['job_title']} at {context['company_name']} has been cancelled."
                                
                                send_mail(
                                    subject,
                                    plain_message,
                                    email_settings.sender_mail,
                                    [candidate_email],
                                    html_message=html_message,
                                    fail_silently=False,
                                    connection=connection,
                                )
                                print(f"[Interview Reschedule] Cancellation email sent to candidate: {candidate_email}")
                except Exception as e:
                    print(f"[Interview Reschedule] Error sending cancellation email: {e}")
            
            interview.add_audit("rescheduled", by=request.user, meta={"new_interview_id": new_interview.id})
            return new_interview
        else:
            raise ValueError(serializer.errors)

    def post(self, request, pk):
        """Reschedule interview"""
        reschedule_request = get_object_or_404(RescheduleRequest, pk=pk)
        if reschedule_request.actor_type == "candidate":
            candidate_status = get_object_or_404(InterviewCandidateStatus, id=reschedule_request.candidate_status_id)
            interviewer_status = None
        else:
            interviewer_status = get_object_or_404(InterviewerStatus, id=reschedule_request.interviewer_status_id)
            candidate_status = None    
        interview = get_object_or_404(Interview, id=reschedule_request.interview_id)
        # interviewers = Contacts.objects.filter(interviewerstatus__interview=interview).values_list('email', flat=True)
        data=request.data
        # Normalize action from either nested or flat payloads (supports form-POST and JSON)
        try:
            action = (data.get("data") or {}).get("action")
        except AttributeError:
            action = None
        if not action:
            action = data.get("action")
        if action:
            action = str(action).lower()
        message=''

        if action == "accept":
            try:
                self.create_new_interview(interview, reschedule_request, request)
                reschedule_request.status = "approved"
                if reschedule_request.actor_type == "candidate":
                    candidate_status.status = "rescheduled"
                else:
                    interviewer_status.status = "rescheduled"
            except ValueError as e:
                return Response({"errors": e}, status=status.HTTP_400_BAD_REQUEST)
                
        elif action == "interviewer_email_send":
            # Update status
            reschedule_request.status="interviewer_email_send"
            if reschedule_request.actor_type == "candidate":
                candidate_status.status="rescheduled"
            else:
                interviewer_status.status="rescheduled"
            message='Interview Reschedule Approved'

            # Send email notifications to interviewers
            email_settings = EmailSettings.objects.filter(company_id=interview.company_id).order_by('-created_at').first()
            print("Email settings found for user", email_settings)
            if email_settings:
                # Get list of interviewer emails (filter out None values)
                interviewer_emails = list(interview.interviewers.filter(email__isnull=False).values_list('email', flat=True))
                if interviewer_emails:  # Only send if there are emails
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
                    subject = "Interview Reschedule Approved"
                    plain = "Interview Reschedule Approved"
                    # Get the appropriate status ID for email context
                    status_id = candidate_status.id if candidate_status else interviewer_status.id
                    context = {
                        "company": getattr(getattr(request.user, "company", None), "name", "Edjobster"),
                        "new_date": reschedule_request.proposed_date,
                        "new_time": reschedule_request.proposed_time,
                        "timezone": getattr(reschedule_request, "proposed_timezone", None),
                        "reschedule_reason": getattr(reschedule_request, "reschedule_reason_type", None),
                        "meetingLink": getattr(interview, "meeting_link", None),
                        "icsUrl": request.build_absolute_uri(reverse('interview-ics', args=[interview.id])) if hasattr(interview, 'id') else None,
                        "year": datetime.now().year,
                        # IDs explicitly passed per request
                        "interview_id": interview.id,
                        "reschedule_id": reschedule_request.id,
                        "candidate_status_id": status_id,
                        # Base URL and action links for email buttons
                        "baseurl": request.build_absolute_uri("/").rstrip("/"),
                        "acceptUrl": request.build_absolute_uri(f"/interview/reschedule-action/{reschedule_request.id}?action=accept"),
                        "rejectUrl": request.build_absolute_uri(f"/interview/reschedule-action/{reschedule_request.id}?action=reject"),
                        "postActionUrl": request.build_absolute_uri(f"/interview/reschedule-action/{reschedule_request.id}"),
                        # Frontend headless reschedule URL using APP_URL from settings
                        "headlessRescheduleUrl": f"{settings.APP_URL}/headless/reschedule/{reschedule_request.id}",
                    }
                    html = render_to_string("interviewers_reschedul_approved.html", context)
                    send_mail(
                        subject,
                        plain,
                        email_settings.sender_mail,
                            interviewer_emails,
                        html_message=html,
                        fail_silently=False,
                        connection=connection,
                    )
                    print(f"[Interview Email] SENT with company SMTP → {interviewer_emails}")
        elif action == "reject":
            reschedule_request.status="declined"
            if reschedule_request.actor_type == "candidate":
                candidate_status.status="cancelled"
                # If only one candidate, cancel the full interview
                if interview.candidate.count() == 1:
                    interview.status = "cancelled"
                    interview.save(update_fields=["status"])
            else:
                interviewer_status.status="cancelled"
                # If only one interviewer, cancel the full interview
                if interview.interviewers.count() == 1:
                    interview.status = "cancelled"
                    interview.save(update_fields=["status"])
            message='Interview Reschedule Rejected'
        else:
            return Response(
                {"detail": "Action must be 'accept', 'interviewer_email_send', or 'reject'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        reschedule_request.save()
        if candidate_status:
            candidate_status.save()
        if interviewer_status:
            interviewer_status.save()
        
        serializer = RescheduleRequestSerializer(reschedule_request)

        return Response(serializer.data, status=status.HTTP_200_OK)

class InterviewStatusChangeAPIView(APIView):
    def post(self,request,pk):
        interview =get_object_or_404(Interview,id=pk)
        interview.status = request.data.get("status")
        interview.save()
        if interview.status == "cancelled":
            # Send cancellation emails to candidates
            try:
                email_settings = EmailSettings.objects.filter(company_id=interview.company_id).order_by('-created_at').first()
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
                    
                    # Send to all candidates
                    for candidate in interview.candidate.all():
                        candidate_email = getattr(candidate, 'email', None)
                        if not candidate_email:
                            # Try to get email from webform data
                            try:
                                webform = getattr(candidate, "webform_candidate_data", None)
                                if isinstance(webform, dict):
                                    personal = webform.get("Personal Details", {})
                                    candidate_email = personal.get("email") or personal.get("Email")
                            except Exception:
                                pass
                        
                        if candidate_email and '@' in candidate_email:
                            context = {
                                'candidate_name': getattr(candidate, 'first_name', '') or 'Candidate',
                                'job_title': interview.dynamic_interview_data.get('basic_info', {}).get('job', {}).get('name') if interview.dynamic_interview_data else interview.job.title if interview.job else 'Position',
                                'company_name': interview.company.name if interview.company else 'Company',
                                'interview_title': interview.dynamic_interview_data.get('basic_info', {}).get('interview_title') if interview.dynamic_interview_data else interview.title or 'Interview',
                                'scheduled_date': interview.date.strftime('%B %d, %Y') if interview.date else '',
                                'scheduled_time': interview.time_start.strftime('%I:%M %p') if interview.time_start else '',
                                'cancellation_reason': request.data.get('cancellation_reason', 'No reason provided'),
                                'contact_email': email_settings.sender_mail
                            }
                            
                            html_message = render_to_string("interview_cancelled.html", context)
                            subject = f"Interview Cancelled: {context['job_title']} at {context['company_name']}"
                            plain_message = f"Your interview for {context['job_title']} at {context['company_name']} has been cancelled."
                            
                            send_mail(
                                subject,
                                plain_message,
                                email_settings.sender_mail,
                                [candidate_email],
                                html_message=html_message,
                                fail_silently=False,
                                connection=connection,
                            )
                            print(f"[Interview Cancellation] Email sent to candidate: {candidate_email}")
                    
                    # Send to interviewers
                    # interviewer_emails = interview.interviewers.filter(email__isnull=False)
                    for interviewer in interview.interviewers.all():
                        interviewer_email = getattr(interviewer, 'email', None)
                        context = {
                            'candidate_name': getattr(interviewer, 'name', '') or 'Interviewer',
                            'job_title': interview.dynamic_interview_data.get('basic_info', {}).get('job', {}).get('name') if interview.dynamic_interview_data else interview.job.title if interview.job else 'Position',
                            'company_name': interview.company.name if interview.company else 'Company',
                            'interview_title': interview.dynamic_interview_data.get('basic_info', {}).get('interview_title') if interview.dynamic_interview_data else interview.title or 'Interview',
                            'scheduled_date': interview.date.strftime('%B %d, %Y') if interview.date else '',
                            'scheduled_time': interview.time_start.strftime('%I:%M %p') if interview.time_start else '',
                            'cancellation_reason': request.data.get('cancellation_reason', 'No reason provided'),
                            'contact_email': email_settings.sender_mail
                        }
                        
                        html_message = render_to_string("interview_cancelled.html", context)
                        subject = f"Interview Cancelled: {context['job_title']} at {context['company_name']}"
                        plain_message = f"The interview for {context['job_title']} at {context['company_name']} has been cancelled."
                        
                        send_mail(
                            subject,
                            plain_message,
                            email_settings.sender_mail,
                            [interviewer_email],
                            html_message=html_message,
                            fail_silently=False,
                            connection=connection,
                        )
                        print(f"[Interview Cancellation] Email sent to interviewer: {interviewer_email}")
                        
            except Exception as e:
                print(f"[Interview Cancellation] Error sending emails: {e}")

        return Response({"message": "status change successful"})

class CandidateStatusChangeAPIView(APIView):
    def post(self, request, pk):
        candidate_status = get_object_or_404(InterviewCandidateStatus, id=pk)
        new_status = request.data.get("status")
        old_status = candidate_status.status
        candidate_status.status = new_status
        candidate_status.save()

        # Send email notification on status change
        try:
            interview = candidate_status.interview
            candidate = candidate_status.candidate
            email_settings = EmailSettings.objects.filter(company_id=interview.company_id).order_by('-created_at').first()
            
            # Extract email and name from webform_candidate_data
            candidate_email = None
            candidate_name = None
            if candidate and candidate.webform_candidate_data:
                personal_details = candidate.webform_candidate_data.get('Personal Details', {})
                candidate_email = personal_details.get('email')
                first_name = personal_details.get('first_name', '')
                last_name = personal_details.get('last_name', '')
                candidate_name = f"{first_name} {last_name}".strip()
            
            if email_settings and candidate_email:
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
                
                job_title = interview.job.title if interview.job else "Position"
                company_name = interview.company.name if interview.company else "Edjobster"
                
                # Send email to candidate
                context = {
                    "candidate_name": candidate_name or candidate_email,
                    "job_title": job_title,
                    "company_name": company_name,
                    "old_status": old_status,
                    "new_status": new_status,
                    "interview_title": interview.title or "Interview",
                    "interview_date": interview.date,
                    "interview_time": interview.time_start,
                }
                
                html_message = render_to_string("status_change_notification.html", context)
                plain_message = f"Your interview status for {job_title} has changed from {old_status} to {new_status}."
                
                subject = f"Interview Status Updated: {job_title}"
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=email_settings.sender_mail,
                    recipient_list=[candidate_email],
                    html_message=html_message,
                    fail_silently=True,
                    connection=connection,
                )
                
                # Send email to all interviewers
                # Update the interview status to match candidate status if only one candidate
                interview = candidate_status.interview
                # print(interview.candidate.count() == 1)
                if interview.candidate.count() == 1:
                    interview.status = new_status
                    interview.save(update_fields=["status"])

                interviewers = interview.interviewers.all()
                for interviewer in interviewers:
                    if interviewer and interviewer.email:
                        interviewer_name = interviewer.name if hasattr(interviewer, 'name') and interviewer.name else interviewer.email
                        
                        interviewer_context = {
                            "interviewer_name": interviewer_name,
                            "job_title": job_title,
                            "company_name": company_name,
                            "old_status": old_status,
                            "new_status": new_status,
                            "interview_title": interview.title or "Interview",
                            "interview_date": interview.date,
                            "interview_time": interview.time_start,
                        }
                        
                        interviewer_html = render_to_string("status_change_notification.html", interviewer_context)
                        interviewer_plain = f"The interview status for {job_title} has changed from {old_status} to {new_status}."
                        
                        send_mail(
                            subject=subject,
                            message=interviewer_plain,
                            from_email=email_settings.sender_mail,
                            recipient_list=[interviewer.email],
                            html_message=interviewer_html,
                            fail_silently=True,
                            connection=connection,
                        )
        except Exception as e:
            print(f"[Candidate Status Change] Error sending email: {e}")

        return Response({"message": "status change successful"})

class InterviewerStatusChangeAPIView(APIView):
    def post(self, request, pk):
        interviewer_status = get_object_or_404(InterviewerStatus, id=pk)
        new_status = request.data.get("status")
        old_status = interviewer_status.status
        interviewer_status.status = new_status
        interviewer_status.save()

        # Send email notification on status change
        try:
            interview = interviewer_status.interview
            interviewer = interviewer_status.interviewer
            email_settings = EmailSettings.objects.filter(company_id=interview.company_id).order_by('-created_at').first()
            
            if email_settings and interviewer and interviewer.email:
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
                
                job_title = interview.job.title if interview.job else "Position"
                company_name = interview.company.name if interview.company else "Edjobster"
                
                # Send email to interviewer
                context = {
                    "interviewer_name": interviewer.name if hasattr(interviewer, 'name') and interviewer.name else interviewer.email,
                    "job_title": job_title,
                    "company_name": company_name,
                    "old_status": old_status,
                    "new_status": new_status,
                    "interview_title": interview.title or "Interview",
                    "interview_date": interview.date,
                    "interview_time": interview.time_start,
                }
                
                html_message = render_to_string("status_change_notification.html", context)
                plain_message = f"The interview status for {job_title} has changed from {old_status} to {new_status}."
                
                subject = f"Interview Status Updated: {job_title}"
                
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=email_settings.sender_mail,
                    recipient_list=[interviewer.email],
                    html_message=html_message,
                    fail_silently=True,
                    connection=connection,
                )
                
                # Send email to all candidates
                # Update the interview status to match interviewer status if only one interviewer
                interview = interviewer_status.interview
                # print(interview.interviewers.count() == 1,"111")
                if interview.interviewers.count() == 1:
                    interview.status = new_status
                    interview.save(update_fields=["status"])

                candidates = interview.candidate.all()
                for candidate in candidates:
                    # Extract email and name from webform_candidate_data
                    candidate_email = None
                    candidate_name = None
                    if candidate and candidate.webform_candidate_data:
                        personal_details = candidate.webform_candidate_data.get('Personal Details', {})
                        candidate_email = personal_details.get('email')
                        first_name = personal_details.get('first_name', '')
                        last_name = personal_details.get('last_name', '')
                        candidate_name = f"{first_name} {last_name}".strip()
                    
                    if candidate_email:
                        candidate_context = {
                            "candidate_name": candidate_name or candidate_email,
                            "job_title": job_title,
                            "company_name": company_name,
                            "old_status": old_status,
                            "new_status": new_status,
                            "interview_title": interview.title or "Interview",
                            "interview_date": interview.date,
                            "interview_time": interview.time_start,
                        }
                        
                        candidate_html = render_to_string("status_change_notification.html", candidate_context)
                        candidate_plain = f"Your interview status for {job_title} has changed from {old_status} to {new_status}."
                        
                        send_mail(
                            subject=subject,
                            message=candidate_plain,
                            from_email=email_settings.sender_mail,
                            recipient_list=[candidate_email],
                            html_message=candidate_html,
                            fail_silently=True,
                            connection=connection,
                        )
        except Exception as e:
            print(f"[Interviewer Status Change] Error sending email: {e}")

        return Response({"message": "status change successful"})

class FeedbackFeelChackAPIView(APIView):
    def get(sefl,request,interview_id,interviewer_id,candidate_id):
        interview = get_object_or_404(Interview,id=interview_id)
        if interview:
            feedback=get_object_or_404(Feedback,interview=interview_id,interviewer=interviewer_id,candidate=candidate_id)
            return Response({"message": "Feedback Feeld"})

