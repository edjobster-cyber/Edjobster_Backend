from django.db import models
from django.contrib.postgres.fields import ArrayField
from account.models import Company, Account
from job.models import Job
from settings.models import Location, EmailTemplate, Contacts
from candidates.models import Candidate
import uuid
import jwt
from django.conf import settings
from django.utils import timezone

STATUS_CHOICES = [
    ("scheduled", "Scheduled"),
    ("accepted", "Accepted"),
    ("declined", "Declined"),
    ("reschedule_requested", "Reschedule Requested"),
    ("rescheduled", "Rescheduled"),
    ("cancelled", "Cancelled"),
    ("completed", "Completed"),
]

# Create your models here.
class Interview(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job, default=None, null=False, verbose_name='Job', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, default=None, null=False, verbose_name='Company', on_delete=models.CASCADE)
    candidate = models.ManyToManyField(Candidate, blank=True)
    title = models.CharField(max_length=250, null=True, blank=True)
    # type = models.CharField(max_length=2, choices=INTEVIEW_TYPES, default=IN_PERSON)
    date = models.DateField(default=None, null=True, blank=True)
    time_start = models.TimeField(default=None, null=True, blank=True)
    time_end = models.TimeField(default=None, null=True, blank=True)
    location = models.ForeignKey(Location, default=None, null=True, verbose_name='Location', on_delete=models.SET_NULL)
    interviewers = models.ManyToManyField(Contacts,blank=True)
    meeting_link = models.URLField(blank=True, null=True)
    calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="scheduled")
    dynamic_interview_data = models.JSONField(null=True, blank=True) 
    created_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, related_name='created_interviews')
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    # headless_tokens: store token ids (we will store the raw token string here for Phase1; in prod store hashed)
    # headless_tokens = models.JSONField(default=dict, blank=True)
    # audit_log: list of {'action':..., 'by':..., 'at':..., 'meta': {...}}
    audit_log = models.JSONField(default=list, blank=True)

    def __str__(self):
        return str(self.job.title)[:20]+' '+str(self.title)[:20]

    class Meta:
        ordering = ["-created"]
        verbose_name = 'Interview'
        verbose_name_plural = 'Interviews'

        # --------------------------
    # Utility functions
    # --------------------------

    # def generate_meeting_link(self):
    #     """Generate simple random meeting link if not provided"""
    #     if not self.meeting_link:
    #         import uuid as _uuid
    #         self.meeting_link = f"https://meet.edjobster/{_uuid.uuid4().hex[:10]}"
            
    #         # Initialize dynamic_interview_data if it's None
    #         if self.dynamic_interview_data is None:
    #             self.dynamic_interview_data = {}
            
    #         # Ensure basic_info exists
    #         if 'basic_info' not in self.dynamic_interview_data:
    #             self.dynamic_interview_data['basic_info'] = {}
            
    #         # Set the interview link at the root level of basic_info
    #         self.dynamic_interview_data['basic_info']['interview_link'] = self.meeting_link
            
    #         # Also set it at the root level for backward compatibility
    #         self.dynamic_interview_data['interview_link'] = self.meeting_link
            
    #         self.save(update_fields=["meeting_link", "dynamic_interview_data"])
    #     return self.meeting_link

    def add_audit(self, action, by=None, meta=None):
        """Record audit log entry"""
        entry = {
            "action": action,
            "by": str(by) if by else None,
            "at": timezone.now().isoformat(),
            "meta": meta or {},
        }
        logs = self.audit_log or []
        logs.append(entry)
        self.audit_log = logs
        self.save(update_fields=["audit_log"])

    # def generate_headless_tokens(self, candidate_ttl_hours=72, manager_ttl_hours=72):
    #     """Generate secure JWT headless tokens"""
    #     secret = settings.SECRET_KEY
    #     now = timezone.now()

    #     tokens = {"candidates": [], "manager": None}

    #     # Candidate tokens (multiple)
    #     for candidate in self.candidate.all():
    #         payload = {
    #             "interview_id": str(self.id),
    #             "role": "candidate",
    #             "candidate_id": candidate.id,
    #             "iat": int(now.timestamp()),
    #             "exp": int((now + timezone.timedelta(hours=candidate_ttl_hours)).timestamp()),
    #             "nonce": uuid.uuid4().hex,
    #         }
    #         token = jwt.encode(payload, secret, algorithm="HS256")
    #         tokens["candidates"].append({"candidate_id": candidate.id, "token": token})

    #     # Manager token
    #     if self.created_by:
    #         manager_payload = {
    #             "interview_id": str(self.id),
    #             "role": "manager",
    #             "account_id": self.created_by.id,
    #             "iat": int(now.timestamp()),
    #             "exp": int((now + timezone.timedelta(hours=manager_ttl_hours)).timestamp()),
    #             "nonce": uuid.uuid4().hex,
    #         }
    #         manager_token = jwt.encode(manager_payload, secret, algorithm="HS256")
    #         tokens["manager"] = manager_token

    #     self.headless_tokens = tokens
    #     self.save(update_fields=["headless_tokens"])
    #     return tokens


    @staticmethod
    def getById(id, job):
        if Interview.objects.filter(job=job, id=id).exists():
            return Interview.objects.get(id=id)
        return None
    
    @staticmethod
    def getByIdAndCompany(id, company):
        if Interview.objects.filter(company=company, id=id).exists():
            return Interview.objects.get(id=id)
        return None

    @staticmethod
    def getByJob(job):
        return Interview.objects.filter(job=job)

    @staticmethod
    def getByCandidate(candidate):
        return Interview.objects.filter(candidate=candidate)

    @staticmethod
    def getByCompany(company):
        return Interview.objects.filter(company=company)


# ------------------------------
# Interview candidate Status
# ------------------------------
class InterviewCandidateStatus(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="candidate_statuses")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    headless_token = models.CharField(max_length=512, blank=True, null=True)  # 👈 store per-candidate token
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_headless_token(self):
        """Generate a JWT token for headless access with candidate and interview info"""
        payload = {
            'type': 'candidate',
            'interview_id': str(self.interview.id),
            'candidate_id': str(self.candidate.id),
            'exp': timezone.now() + timezone.timedelta(days=30)  # Token expires in 30 days
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    def save(self, *args, **kwargs):
        if not self.headless_token:
            self.headless_token = self.generate_headless_token()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.candidate} - {self.status} ({self.interview.id})"

    
# ------------------------------
# Interviewer Status
# ------------------------------
class InterviewerStatus(models.Model):
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name="interviewer_statuses")
    interviewer = models.ForeignKey(Contacts, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    headless_token = models.CharField(max_length=512, blank=True, null=True)  # optional for future use
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_headless_token(self):
        """Generate a JWT token for headless access with interviewer and interview info"""
        payload = {
            'type': 'interviewer',
            'interview_id': str(self.interview.id),
            'interviewer_id': str(self.interviewer.id),
            'exp': timezone.now() + timezone.timedelta(days=30)  # Token expires in 30 days
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    def save(self, *args, **kwargs):
        if not self.headless_token:
            self.headless_token = self.generate_headless_token()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.interviewer} - {self.status} ({self.interview.id})"


# ------------------------------
# RESCHEDULE REQUEST
# ------------------------------
class RescheduleRequest(models.Model):
    ACTOR_CHOICES = [
        ("candidate", "Candidate"),
        ("interviewer", "Interviewer"),
    ]
    actor_type = models.CharField(null=True, blank=True, max_length=20, choices=ACTOR_CHOICES)
    interview = models.ForeignKey(
        Interview, on_delete=models.CASCADE, related_name="reschedule_requests"
    )
    candidate_status = models.ForeignKey(
        InterviewCandidateStatus, on_delete=models.CASCADE, null=True, blank=True, related_name="reshedule_candidatestatus"
    )
    interviewer_status = models.ForeignKey(
        InterviewerStatus, on_delete=models.CASCADE, null=True, blank=True, related_name="reshedule_interviewerstatus"
    )
    message = models.TextField(blank=True, null=True)
    reschedule_reason_type = models.CharField(null=True, blank=True, max_length=255)
    proposed_date = models.DateField(null=True, blank=True)
    proposed_time = models.TimeField(null=True, blank=True)
    proposed_timezone = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("interviewer_email_send", "Interviewer Email Send")
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"Reschedule Request ({self.interview_id}) - {self.status}"


# ------------------------------
# FEEDBACK MODEL
# ------------------------------
class Feedback(models.Model):
    interview = models.ForeignKey(
        Interview, on_delete=models.CASCADE, related_name="feedbacks"
    )
    interviewer = models.ForeignKey(
        Contacts, on_delete=models.CASCADE, related_name="feedbacks"
    )
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="feedbacks",null=True,blank=True
    )
    reason = models.CharField(max_length=255,null=True,blank=True)
    rating = models.IntegerField(default=0)
    recommend = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback ({self.interview_id}) by {self.interviewer}"


# ------------------------------
# DECLINE RESPONSE (store reason/details)
# ------------------------------
class DeclineResponse(models.Model):
    ACTOR_CHOICES = [
        ("candidate", "Candidate"),
        ("interviewer", "Interviewer"),
    ]

    interview = models.ForeignKey(
        Interview, on_delete=models.CASCADE, related_name="decline_responses"
    )
    actor_type = models.CharField(max_length=20, choices=ACTOR_CHOICES)
    candidate_status = models.ForeignKey(
        InterviewCandidateStatus, on_delete=models.CASCADE, null=True, blank=True, related_name="interview_candidatestatus"
    )
    interviewer_status = models.ForeignKey(
        InterviewerStatus, on_delete=models.CASCADE, null=True, blank=True, related_name="interview_interviewerstatus"
    )

    reason = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     who = self.candidate or self.interviewer or self.actor_type
    #     return f"Decline {self.interview_id} by {who}"

# ------------------------------
# AUDIT LOG (Optional if not JSON)
# ------------------------------
class AuditLog(models.Model):
    interview = models.ForeignKey(
        Interview, on_delete=models.CASCADE, related_name="audit_logs"
    )
    action = models.CharField(max_length=100)
    by = models.CharField(max_length=255, blank=True, null=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.interview_id} - {self.action}"