from account.serializer import AccountSerializer
from rest_framework import serializers
from settings.models import Webform
from settings.serializer import WebformListSerializer, DegreeSerializer
from .models import *
from common.encoder import encode
from common.serializer import NoteTypeSerializer
from django.conf import settings
from common.serializer import StateSerializer, CountrySerializer, CitySerializer
from job.serializer import Job, JobListSerializer, JobsSerializer
from job import models as jobmodels
from settings.models import Department

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']

class SubjectSpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectSpecialization
        fields = ['id', 'name']
        
class CandidateJsonDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = "__all__"

class CandidateListSerializer(serializers.ModelSerializer):

    state = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    webform_id = serializers.SerializerMethodField()
    job = JobsSerializer(many=True)
    skills = SkillSerializer(many=True)
    subjects = SubjectSpecializationSerializer(many=True)
    current_job_title = serializers.SerializerMethodField()
    professional_degree = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    RJMSAnalysis = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = "__all__"

    # def get_job_id(self, obj):
    #     if obj.job:
    #         return obj.job.id
    #     return None
    # def get_job_id(self, obj):
    #     return [job.id for job in obj.job.all()]
    
    def get_id(self, obj):
        return obj.id
    
    def get_state(self, obj):
        if obj.state:
            return StateSerializer(obj.state).data
        return None
    
    def get_country(self, obj):
        if obj.country:
            return CountrySerializer(obj.country).data
        return None
    
    def get_city(self, obj):
        if obj.city:
            return CitySerializer(obj.city).data
        return None

    def get_webform_id(self, obj):
        webform_ids = []
        for job in obj.job.all():
            if job.webform:
                webform_ids.append(job.webform.id)
        return webform_ids if webform_ids else None

    def get_current_job_title(self, obj):
        for job in obj.job.all():
            if job.title:
                return job.title
        return None
    
    def get_job_title(self, obj):
        return [job.title for job in obj.job.all()]
    
    def get_professional_degree(self, obj):
        if obj.professional_degree:
            return DegreeSerializer(obj.professional_degree).data
        return None
        
    def get_RJMSAnalysis(self, obj):
        analysis = RJMSAnalysis.objects.filter(candidate=obj)
        if analysis.exists():
            return RJMSAnalysisSerializer(analysis, many=True).data
        return None
    
class CandidateDetailsSerializer(serializers.ModelSerializer):

    # resume = serializers.SerializerMethodField()
    job_department = serializers.SerializerMethodField()
    RJMSAnalysis = serializers.SerializerMethodField()
    # state = serializers.SerializerMethodField()
    # country = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = '__all__'
        depth = 2
        # exclude = ('resume_parse_data',)

    # def get_resume(self, obj):
    #     if obj.resume:
    #         tmp = str(obj.resume)
    #         return settings.RESUME_FILE_URL+tmp[13:]
    #     return None              
    

    # def get_job_department(self, obj):
    #     try:
    #         assessment = Department.objects.get(pk=obj.job.department.id)
    #         return assessment.name
    #     except Department.DoesNotExist:
    #         return None   
        
    def get_job_department(self, obj):
        departments = []
        for job in obj.job.all():
            if job.department:
                departments.append(job.department.name)
        return departments if departments else None       


    def get_job(self, obj):
        if obj.job:
            return JobListSerializer(obj.job).data
        return None  


    def get_state(self, obj):
        if obj.state:
            return StateSerializer(obj.state).data
        return None  

    def get_country(self, obj):
        if obj.country:
            return CountrySerializer(obj.country).data
        return None          

    def get_RJMSAnalysis(self, obj):
        analysis = RJMSAnalysis.objects.filter(candidate=obj)
        if analysis.exists():
            return RJMSAnalysisSerializer(analysis, many=True).data
        return None

class RJMSAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for RJMS (Resume-Job Matching Score) Analysis."""
    job_title = serializers.SerializerMethodField()
    
    class Meta:
        model = RJMSAnalysis
        fields = "__all__"
    
    def get_job_title(self, obj):
        if not obj.job:
            return None
        return self._get_job_title(obj.job)
    
    def _get_job_title(self, job):
        """Extract job title from job data with fallbacks"""
        try:
            if job.dynamic_job_data:
                data = job.dynamic_job_data
                if isinstance(data, str):
                    data = json.loads(data)
                if isinstance(data, dict) and 'Create Job' in data:
                    return data['Create Job'].get('title')
            return job.title
        except (TypeError, json.JSONDecodeError, AttributeError, KeyError):
            return job.title or "No Title Available"

class NoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Note
        fields = ['id','candidate', 'note', 'created', 'updated']

    def get_type(self, obj):
        if obj.type:
            return NoteTypeSerializer(obj.type).data
        return None           

    def get_added_by(self, obj):
        if obj.added_by:
            return AccountSerializer(obj.added_by).data
        return None    
    

class CandidateExperienceSerializer(serializers.ModelSerializer):

    class Meta:
        model = CandidateExperience
        fields = '__all__'

class CandidateQualificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CandidateQualification
        fields = '__all__'
    
        
class MailSerializer(serializers.ModelSerializer):

    class Meta:
        model = CandidateQualification
        fields = '__all__'
    

class ApplicantWebFormSerializer(serializers.ModelSerializer):
    # assingment = serializers.ListField(child=HourlySerializer(), min_length=24, max_length=24)
    class Meta:
        model = ApplicantWebForm
        fields = [
            'id',
            'job',
            'webform',
            'assingment',
            'form',      
        ]
        depth=1


class CandidateSerializer(serializers.ModelSerializer):
    # web_form_id = serializers.SerializerMethodField()
    job = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.all(),
        many=True
    )
    # subjects = serializers.PrimaryKeyRelatedField(queryset=SubjectSpecialization.objects.all(), many=True)

    def get_web_form_id(self, obj):
        web_form_ids = []
        for job in obj.job.all():
            if job.webform:
                web_form_ids.append(job.webform.id)
        return web_form_ids if web_form_ids else None

    class Meta:
        model = Candidate
        fields = ['account', 'webform_candidate_data', 'job', 'resume', 'first_name', 'last_name', 'cover_letter', 'certificate', 'assessment_data', 'resume_user', 'resume_data', 'company', 'pipeline_stage', 'pipeline_stage_status', 'source']

    def __init__(self, *args, **kwargs):
        super(CandidateSerializer, self).__init__(*args, **kwargs)

        # Set required=False for all fields
        for field_name, field in self.fields.items():
            field.required = False



# class TasksSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Tasks
#         fields = '__all__'
        
class TaskSerializer(serializers.ModelSerializer):
    # To handle account as a string (account_id)
    owner = serializers.CharField(source='owner.account_id', required=False, allow_null=True)

    class Meta:
        model = Tasks
        fields = '__all__'

    def create(self, validated_data):
        # Extract the account ID string from the validated data
        owner_data = validated_data.pop('owner', None)
        if owner_data:
            # Fetch the account instance using account_id
            account_instance = Account.objects.get(account_id=owner_data['account_id'])
            validated_data['owner'] = account_instance
        else:
            validated_data['owner'] = None  # Explicitly set to None if not provided

        # Create the task instance
        return Tasks.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Handle updates if needed for account field
        owner_data = validated_data.pop('owner', None)
        if owner_data:
            account_instance = Account.objects.get(account_id=owner_data['account_id'])
            instance.owner = account_instance
        else:
            instance.owner = None  # Explicitly set to None if not provided

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class EventSerializer(serializers.ModelSerializer):
    host = serializers.CharField(source='host.account_id', required=False, allow_null=True)
    participants = serializers.PrimaryKeyRelatedField(
        queryset=Contacts.objects.all(), many=True, required=False
    )

    class Meta:
        model = Events
        fields = '__all__'

    def create(self, validated_data):
        host_data = validated_data.pop('host', None)
        participants_data = validated_data.pop('participants', [])

        if host_data:
            account_instance = Account.objects.get(account_id=host_data['account_id'])
            validated_data['host'] = account_instance
        else:
            validated_data['host'] = None

        event = Events.objects.create(**validated_data)

        if participants_data:
            event.participants.set(participants_data)

        return event

    def update(self, instance, validated_data):
        host_data = validated_data.pop('host', None)
        participants_data = validated_data.pop('participants', None)

        if host_data:
            account_instance = Account.objects.get(account_id=host_data['account_id'])
            instance.host = account_instance
        else:
            instance.host = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if participants_data is not None:
            instance.participants.set(participants_data)

        instance.save()
        return instance
    
class CallSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all(), required=False, allow_null=True)
    # owner = serializers.CharField(source='owner.account_id', required=False, allow_null=True)
    contact_name_contact = serializers.PrimaryKeyRelatedField(queryset=Contacts.objects.all(), required=False, allow_null=True)
    contact_name_candidate = serializers.PrimaryKeyRelatedField(queryset=Candidate.objects.all(), required=False, allow_null=True)
    candidate = serializers.PrimaryKeyRelatedField(queryset=Candidate.objects.all(), required=False, allow_null=True)
    posting_title = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Call
        fields = '__all__'
        
    def to_representation(self, instance):
            representation = super().to_representation(instance)
            if instance.owner:
                representation['owner'] = instance.owner.account_id  # Get account_id from owner
            return representation

    # def create(self, validated_data):
    #     # Handle owner field (account)
    #     owner_data = validated_data.pop('owner', None)
    #     if owner_data and 'account_id' in owner_data:
    #         account_instance = Account.objects.get(account_id=owner_data['account_id'])
    #         validated_data['owner'] = account_instance
    #     else:
    #         validated_data['owner'] = None

    #     # Handle related fields
    #     contact_name_contact_data = validated_data.pop('contact_name_contact', None)
    #     contact_name_candidate_data = validated_data.pop('contact_name_candidate', None)
    #     candidate_data = validated_data.pop('candidate', None)
    #     posting_title_data = validated_data.pop('posting_title', None)

    #     call = Call.objects.create(**validated_data)

    #     if contact_name_contact_data:
    #         call.contact_name_contact = contact_name_contact_data
    #     if contact_name_candidate_data:
    #         call.contact_name_candidate = contact_name_candidate_data
    #     if candidate_data:
    #         call.candidate = candidate_data
    #     if posting_title_data:
    #         call.posting_title = posting_title_data

    #     call.save()
    #     return call

    # def update(self, instance, validated_data):
    #     # Handle owner field (account)
    #     owner_data = validated_data.pop('owner', None)
    #     if owner_data:
    #         account_instance = Account.objects.get(account_id=owner_data['account_id'])
    #         instance.owner = account_instance
    #     else:
    #         instance.owner = None

    #     # Handle related fields
    #     contact_name_contact_data = validated_data.pop('contact_name_contact', None)
    #     contact_name_candidate_data = validated_data.pop('contact_name_candidate', None)
    #     candidate_data = validated_data.pop('candidate', None)
    #     posting_title_data = validated_data.pop('posting_title', None)

    #     if contact_name_contact_data:
    #         instance.contact_name_contact = contact_name_contact_data
    #     if contact_name_candidate_data:
    #         instance.contact_name_candidate = contact_name_candidate_data
    #     if candidate_data:
    #         instance.candidate = candidate_data
    #     if posting_title_data:
    #         instance.posting_title = posting_title_data

    #     for attr, value in validated_data.items():
    #         setattr(instance, attr, value)

    #     instance.save()
    #     return instance

class MultipleCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = '__all__'
        # Assuming 'resume', 'cover_letter', and 'certificate' are FileFields
        extra_kwargs = {
            'resume': {'write_only': True},
            'cover_letter': {'write_only': True},
            'certificate': {'write_only': True},
            'professional_certificate': {'write_only': True},
        }


# class CandidateSerializer(serializers.ModelSerializer):
#     web_form_id = serializers.SerializerMethodField()

#     # def get_web_form_id(self, obj):
#     #     job_id = obj.job

#     #     # Check if job_id is an instance of Job
#     #     if isinstance(job_id, jobmodels.Job):
#     #         # If it's an instance, use its id directly
#     #         return job_id.webform.id
#     #     else:
#     #         # If it's not an instance, assume it's a valid primary key
#     #         try:
#     #             job = jobmodels.Job.objects.get(pk=job_id)
#     #             return job.webform.id
#     #         except jobmodels.Job.DoesNotExist:
#     #             # Handle the case where the Job with the given primary key doesn't exist
#     #             return None
    
#     def get_web_form_id(self, obj):
#         web_form_ids = []
#         for job in obj.job.all():
#             if job.webform:
#                 web_form_ids.append(job.webform.id)
#         return web_form_ids if web_form_ids else None

#     class Meta:
#         model = Candidate
#         fields = '__all__'
        
class EmailSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSettings
        fields = ['id','sender_mail','auth_password','email_backend','email_host','email_port','email_tls','email_ssl']
        
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user_id'] = user
        validated_data['company_id'] = user.company_id
        return super().create(validated_data)
    

class CandidateWithoutLoginSerializer(serializers.ModelSerializer):
    web_form_id = serializers.SerializerMethodField()
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all(), many=True)
    
    def get_web_form_id(self, obj):
        web_form_ids = []
        for job in obj.job.all():
            if job.webform:
                web_form_ids.append(job.webform.id)
        return web_form_ids if web_form_ids else None
    class Meta:
        model = Candidatewithoutlogin
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CandidateWithoutLoginSerializer, self).__init__(*args, **kwargs)

        # Set required=False for all fields
        for field_name, field in self.fields.items():
            field.required = False

class CandidateTimelineSerializer(serializers.ModelSerializer):
    job = serializers.SerializerMethodField()
    candidate = serializers.SerializerMethodField()
    interview = serializers.SerializerMethodField()
    performed_by = serializers.SerializerMethodField()
    related_task = serializers.SerializerMethodField()
    related_note = serializers.SerializerMethodField()

    class Meta:
        model = CandidateTimeline
        fields = '__all__'
    
    def get_job(self, obj):
        if obj.job.exists():
            return JobListSerializer(obj.job.all(), many=True).data
        return []
    
    def get_candidate(self, obj):
        if obj.candidate:
            return CandidateListSerializer(obj.candidate).data
        return None

    def get_interview(self, obj):
        if obj.interview:
            from interview.serializer import InterviewListSerializer
            return InterviewListSerializer(obj.interview).data
        return None
    
    def get_performed_by(self, obj):
        if obj.performed_by:
            return AccountSerializer(obj.performed_by).data
        return None
    
    def get_related_task(self, obj):
        if obj.related_task:
            return TaskSerializer(obj.related_task).data
    
    def get_related_note(self,obj):
        if obj.related_note:
            return NoteSerializer(obj.related_note).data
        
    def get_related_call(self,obj):
        if obj.related_call:
            return CallSerializer(obj.related_call).data

class SavedJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedJob
        fields = ['id', 'candidate', 'job']
        read_only_fields = ['id', 'candidate']


class CandidateResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateResume
        fields = '__all__'

class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = '__all__'

class CoresignalPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoresignalPreview
        fields = '__all__'

class CoresignalCandidateStatusSerializer(serializers.ModelSerializer):
    coresignal_candidate = CoresignalPreviewSerializer(read_only=True)
    coresignal_candidate_id = serializers.UUIDField(write_only=True, required=False)
   
    class Meta:
        model = CoresignalCandidateStatus
        fields = [
            'id',
            'coresignal_candidate',
            'coresignal_candidate_id',
            'company',
            'status',
            'created_at',
            'updated_at'
        ]
        
    def create(self, validated_data):
        coresignal_candidate_id = validated_data.pop('coresignal_candidate_id', None)
        if coresignal_candidate_id:
            validated_data['coresignal_candidate_id'] = coresignal_candidate_id
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        coresignal_candidate_id = validated_data.pop('coresignal_candidate_id', None)
        if coresignal_candidate_id:
            validated_data['coresignal_candidate_id'] = coresignal_candidate_id
        return super().update(instance, validated_data)
        
    # def create(self, validated_data):
    #     coresignal_candidate_id = validated_data.pop('coresignal_candidate', None)
    #     instance = super().create(validated_data)
    #     if coresignal_candidate_id:
    #         instance.coresignal_candidate_id = coresignal_candidate_id
    #         instance.save()
    #     return instance

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'