from google.cloud.talent_v4beta1.types import company
from account.models import Account
from candidates.models import Candidate
from rest_framework import serializers
from .models import Interview, RescheduleRequest, Feedback, AuditLog, InterviewCandidateStatus, InterviewerStatus, DeclineResponse
from job.serializer import JobListSerializer
from candidates.serializer import CandidateListSerializer
from account.serializer import AccountSerializer
from settings.models import Contacts
from settings.serializer import ContactsDataSerializer, LocationSerializer

class InterviewListSerializer(serializers.ModelSerializer):

    job = serializers.SerializerMethodField()
    candidate = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = ['id', 'dynamic_interview_data', 'title', 'date', 'time_start', 'time_end', 
                  'job', 'candidate','company','interviewers','location','updated']

    def get_job(self, obj):
        if obj.job:
            return {
                'id': obj.job.id,
                # 'title': obj.job.title,
                'title': obj.job.dynamic_job_data['Create Job']['title'],
            }
        return None      

    def get_candidate(self, obj):
        # candidate is a ManyToManyField; return a list of candidates
        candidates = []
        try:
            for c in obj.candidate.all():
                candidates.append({
                    'id': c.id,
                    'first_name': getattr(c, 'first_name', None),
                    'middle_name': getattr(c, 'middle_name', None),
                    'last_name': getattr(c, 'last_name', None),
                    'email': getattr(c, 'email', None),
                    'mobile': getattr(c, 'mobile', None),
                    'exp_years': getattr(c, 'exp_years', None),
                    'exp_months': getattr(c, 'exp_months', None),
                })
        except Exception:
            candidates = []
        return candidates  
    
    def get_company(self, obj):
        if obj.company:
            return {
                'id': obj.company.id,
                'name': obj.company.name
            }   
        return None 
    
    def get_location(self, obj):
        if obj.location:
            return {
                'id':obj.location.id,
                'name':obj.location.name,
                'address':obj.location.address
            }   
        return None 

class InterviewDetailsSerializer(serializers.ModelSerializer):

    job = serializers.SerializerMethodField()
    candidate = serializers.SerializerMethodField()
    interviewers = serializers.SerializerMethodField()

    def get_job(self, obj):
        if obj.job:
            return JobListSerializer(obj.job).data
        return None      

    def get_candidate(self, obj):
        if obj.candidate:
            return CandidateListSerializer(obj.candidate).data
        return None               

    def get_interviewers(self, obj):
        interviewers = []
        if obj.interviewers:
            for account in obj.interviewers.all():
                try:
                    interviewers.append(ContactsDataSerializer(account).data)
                except Exception:
                    continue
        return interviewers

    class Meta:
        model = Interview
        fields = ['id', 'title',  'date', 'time_start', 'time_end', 'job', 'candidate','company','interviewers','location','email_temp','email_sub','updated',"dynamic_interview_data"]

class InterviewJsonDataSerializer(serializers.ModelSerializer):
    class Meta:
        model =Interview
        fields= "__all__"


# ------------------------------
# Interview Serializer
# ------------------------------
class InterviewSerializer(serializers.ModelSerializer):
    # candidates = CandidateListSerializer(many=True, read_only=True)
    # candidate_ids = serializers.ListField(
    #     child=serializers.IntegerField(), write_only=True, required=False
    # )

    # interviewers = ContactsDataSerializer(many=True, read_only=True)
    # interviewer_ids = serializers.ListField(
    #     child=serializers.IntegerField(), write_only=True, required=False
    # )

    # location = LocationSerializer(read_only=True)
    # location_id = serializers.IntegerField(write_only=True, required=False)

    # company = CompanySerializer(read_only=True, value=request.user.company_id)
    # company_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Interview
        fields = [
            "id",
            "job",
            "candidate",
            "interviewers",
            "location",
            "created_by",
            "title",
            "meeting_link",
            "dynamic_interview_data",
            "company",
            "audit_log",
            "created",
            "updated",
            "status",
            "date",
            "time_start",
            "time_end",
        ]
        read_only_fields = ["id", "meeting_link", "audit_log", "created", "updated"]

    def create(self, validated_data):
        """Create interview with audit logging"""
        interview = super().create(validated_data)

        # Capture initial field values for audit
        request = self.context.get("request")
        user = request.user if request else None

        # Build field data for audit
        field_data = {}
        for field in self.Meta.fields:
            if field not in ["id", "audit_log", "created", "updated"]:
                value = getattr(interview, field, None)
                if value is not None:
                    if field in ["candidate", "interviewers"]:
                        # Handle ManyToMany fields
                        field_data[field] = [str(v) for v in value.all()]
                    elif hasattr(value, 'id'):
                        # Handle ForeignKey fields - convert id to string for JSON serialization
                        field_data[field] = {"id": str(value.id), "str": str(value)}
                    else:
                        field_data[field] = str(value)

        interview.add_audit(
            "created",
            by=user,
            meta={"fields": field_data}
        )
        return interview

    def update(self, instance, validated_data):
        """Update interview with change tracking audit logging"""
        request = self.context.get("request")
        user = request.user if request else None

        # Track changes before update
        changed_fields = {}
        for field, new_value in validated_data.items():
            if field in ["id", "audit_log", "created", "updated"]:
                continue

            old_value = getattr(instance, field, None)

            # Handle ManyToMany fields
            if field in ["candidate", "interviewers"]:
                old_list = list(old_value.all()) if old_value else []
                # Need to get IDs since new_value might be a queryset
                if hasattr(new_value, 'all'):
                    new_list = list(new_value.all())
                else:
                    new_list = new_value if isinstance(new_value, list) else [new_value]

                old_ids = [str(o.id) for o in old_list]
                new_ids = [str(n.id) if hasattr(n, 'id') else str(n) for n in new_list]

                if set(old_ids) != set(new_ids):
                    changed_fields[field] = {
                        "old": old_ids,
                        "new": new_ids
                    }
            # Handle ForeignKey fields
            elif hasattr(old_value, 'id') or hasattr(new_value, 'id'):
                old_id = str(old_value.id) if old_value and hasattr(old_value, 'id') else None
                new_id = str(new_value.id) if new_value and hasattr(new_value, 'id') else None
                if old_id != new_id:
                    changed_fields[field] = {
                        "old": {"id": old_id, "str": str(old_value)} if old_id else None,
                        "new": {"id": new_id, "str": str(new_value)} if new_id else None
                    }
            # Handle simple fields
            elif str(old_value) != str(new_value):
                changed_fields[field] = {
                    "old": str(old_value) if old_value is not None else None,
                    "new": str(new_value) if new_value is not None else None
                }

        # Perform the update
        interview = super().update(instance, validated_data)

        # Add audit entry with changes
        if changed_fields:
            interview.add_audit(
                "updated",
                by=user,
                meta={"changes": changed_fields}
            )
        else:
            interview.add_audit("updated", by=user, meta={"changes": "no_fields_changed"})

        return interview


# ------------------------------
# Reschedule Serializer
# ------------------------------
class RescheduleRequestSerializer(serializers.ModelSerializer):
    interview = serializers.SerializerMethodField()
    # write-only field to set FK
    interview_id = serializers.PrimaryKeyRelatedField(
        queryset=Interview.objects.all(), source="interview", write_only=True
    )
    
    class Meta:
        model = RescheduleRequest
        fields = [
            "id",
            "interview_id",
            "interview",
            "candidate_status",
            "interviewer_status",
            "actor_type",
            "reschedule_reason_type",
            "proposed_date",
            "proposed_time",
            "proposed_timezone",
            "message",
            "status",
            "created_at",
        ]

    def get_interview(self, obj):
        if not obj.interview:
            return None
        return InterviewSerializer(obj.interview).data

    def create(self, validated_data):
        # If interview wasn't set via interview_id, fallback to raw 'interview' from payload
        if not validated_data.get("interview"):
            raw_interview = self.initial_data.get("interview")
            if raw_interview:
                try:
                    validated_data["interview"] = Interview.objects.get(pk=raw_interview)
                except Interview.DoesNotExist:
                    raise serializers.ValidationError({"interview": "Interview not found"})
        return super().create(validated_data)

# ------------------------------
# Feedback Serializer
# ------------------------------
class FeedbackSerializer(serializers.ModelSerializer):
    interviewer = serializers.PrimaryKeyRelatedField(queryset=Contacts.objects.all(), write_only=True)
    interviewer_data = serializers.SerializerMethodField(read_only=True)
    candidate = serializers.PrimaryKeyRelatedField(queryset=Candidate.objects.all(), required=False, allow_null=True)
    evaluation = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Feedback
        fields = [
            "id",
            "interview",
            "interviewer",
            "interviewer_data",
            "candidate",
            "rating",
            "reason",
            "recommend",
            "comments",
            "submitted_at",
            "evaluation",
        ]
        read_only_fields = ["submitted_at", "interviewer_data"]

    def get_interviewer_data(self, obj):
        if not obj.interviewer:
            return None
        return ContactsDataSerializer(obj.interviewer).data

    def create(self, validated_data):
        # Ignore any incoming 'evaluation' field (not stored in model)
        validated_data.pop("evaluation", None)
        return super().create(validated_data)

# ------------------------------
# Audit Log Serializer
# ------------------------------
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "interview", "action", "by", "meta", "created_at"]

class InterviewCandidateStatusSerializer(serializers.ModelSerializer):
    interview = serializers.SerializerMethodField()
    candidate = serializers.SerializerMethodField()
    
    class Meta: 
        model = InterviewCandidateStatus
        fields = ["id", "interview", "candidate", "status", "headless_token", "created_at"]
    
    def get_interview(self, obj):
        if not obj.interview:
            return None
            
        data = {
            # 'id': obj.interview.id,
            'title': obj.interview.title,
            'interview_type': None,
            'interview_location': None,
            'interview_link': None,
            'schedule': None
        }
        
        # Get data from dynamic_interview_data if it exists
        if obj.interview.dynamic_interview_data:
            dynamic_data = obj.interview.dynamic_interview_data
            basic_info = dynamic_data.get('basic_info', {})
            
            # Get interview type or interview link/location
            data['interview_type'] = basic_info.get('interview_type')
            data['interview_location'] = basic_info.get('interview_location')
            data['interview_link'] = basic_info.get('interview_link')
            data['title'] = basic_info.get('interview_title')
            data['company_name'] = obj.interview.company.name if hasattr(obj.interview, 'company') and obj.interview.company else None
            # Get schedule information
            data['schedule'] = dynamic_data.get('schedule')
            data['interviewer'] = dynamic_data.get('interviewers').get('interviewers')
            
        return data
        
    def get_candidate(self, obj):
        if not obj.candidate:
            return None
            
        # Initialize default values
        first_name = ""
        last_name = ""
        
        # Try to get names from webform_candidate_data if it exists
        if hasattr(obj.candidate, 'webform_candidate_data') and obj.candidate.webform_candidate_data:
            personal_details = obj.candidate.webform_candidate_data.get('Personal Details', {})
            first_name = personal_details.get('first_name', '')
            last_name = personal_details.get('last_name', '')
        
        # Fallback to direct attributes if not found in webform data
        if not first_name and hasattr(obj.candidate, 'first_name'):
            first_name = obj.candidate.first_name or ""
        if not last_name and hasattr(obj.candidate, 'last_name'):
            last_name = obj.candidate.last_name or ""
        return {
            'first_name': first_name,
            'last_name': last_name,
            'email': obj.candidate.email,
            "id": obj.candidate.id,
        }
        
class InterviewerStatusSerializer(serializers.ModelSerializer):
    interview = serializers.SerializerMethodField()
    interviewer = serializers.SerializerMethodField()
    
    class Meta:
        model = InterviewerStatus
        fields = ["id", "interview", "interviewer", "status", "headless_token", "created_at"]
    
    def get_interview(self, obj):
        if not obj.interview:
            return None
            
        data = {
            # 'id': obj.interview.id,
            'title': obj.interview.title,
            'interview_type': None,
            'interview_location': None,
            'interview_link': None,
            'schedule': None
        }
        
        # Get data from dynamic_interview_data if it exists
        if obj.interview.dynamic_interview_data:
            dynamic_data = obj.interview.dynamic_interview_data
            basic_info = dynamic_data.get('basic_info', {})
            
            # Get interview type or interview link/location
            data['interview_type'] = basic_info.get('interview_type')
            data['interview_location'] = basic_info.get('interview_location')
            data['interview_link'] = basic_info.get('interview_link')
            data['title'] = basic_info.get('interview_title')
            data['company_name'] = obj.interview.company.name if hasattr(obj.interview, 'company') and obj.interview.company else None
            # Get schedule information
            data['schedule'] = dynamic_data.get('schedule')
            data['candidate'] = basic_info.get('candidate')
            
        return data
    
    def get_interviewer(self, obj):
        from settings.serializer import ContactsDataSerializer  # Using the correct serializer
        if not obj.interviewer:
            return None
        data = ContactsDataSerializer(obj.interviewer).data
        return {
            # 'id': data.get('id'),
            'name': data.get('name'),
            'email': data.get('email'),
            # 'mobile': data.get('mobile'),
            # 'company_name': data.get('company_name')
        }

class DeclineResponseSerializer(serializers.ModelSerializer):
    # candidate_status = InterviewCandidateStatusSerializer(read_only=True)
    # interviewer_status = InterviewerStatusSerializer(read_only=True)

    class Meta:
        model = DeclineResponse
        fields = [
            "id",
            "interview",
            "actor_type",
            # "candidate_status",
            # "interviewer_status",
            "reason",
            "details",
            "created_at",
        ]

class InterviewCandidateStatusCareerSerializer(serializers.ModelSerializer):
    interview = InterviewListSerializer()  # Nested serializer for interview data
    
    class Meta: 
        model = InterviewCandidateStatus
        fields = ["id", "interview", "candidate", "status", "headless_token", "created_at"]
        depth = 1  # This ensures related fields are serialized
    
    def to_representation(self, instance):
        # Get the default representation
        representation = super().to_representation(instance)
        # Add any additional fields or modifications here if needed
        return representation