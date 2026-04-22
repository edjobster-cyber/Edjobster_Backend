
from account.models import Account, Company
from common.models import Country, State
from rest_framework import serializers
from .models import Assesment, AssesmentCategory, AssesmentQuestion, Job, JobNotes, TemplateJob, JobBoard, JobTimeline, DraftSaveJob
from common.encoder import encode
from settings.serializer import DepartmentSerializer, DegreeSerializer, LocationSerializer, PipelineSerializer, WebformDataSerializer
from settings.models import Degree, Department, Location, Pipeline, Webform
from account.serializer import AccountSerializer
from common.serializer import CitySerializer, StateSerializer, CountrySerializer
from django.conf import settings
from job.models import Assesment
from settings.models import Department
from candidates.models import *

class AssesmentSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_owner_name(self, obj):
        if obj.company and hasattr(obj.company, 'admin') and obj.company.admin:
            return obj.company.admin.username
        return None
    
    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.first_name
        return None 

    class Meta:
        model = Assesment
        fields ='__all__'
        
class AssessmentJsonDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assesment
        fields="__all__"

class AssesmentCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = AssesmentCategory
        fields = ['id', 'name', 'company']

class AssesmentQuestionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssesmentQuestion
        fields = ['id', 'type', 'question', 'options', 'marks', 'created', 'updated' ]

class AssesmentQuestionDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssesmentQuestion
        fields = ['id', 'type', 'question', 'options', 'marks', 'answer', 'created', 'updated' ]        


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"

class JobsSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    assessment_name = serializers.SerializerMethodField()
    address_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    
    # owner_id = serializers.SerializerMethodField()
    # def get_owner_name(self, obj):
    #     # Use the owner object directly instead of querying again
    #     if obj.owner:
    #         return obj.owner.first_name  # Directly access the first_name
    #     return None

    # def get_owner_id(self, obj):
    #     # Use the owner object directly instead of querying again
    #     if obj.owner:
    #         return obj.owner.account_id  # Directly access the account_id
    #     return None
    
    def get_company_name(self, obj):
        return obj.company.name if obj.company else None

    def get_department_name(self, obj):
        # Change this to return the department ID instead of the object
        if obj.department:
            return obj.department.name  # Return the ID directly
        return None
    
    def get_assessment_name(self, obj):
        # Change this to return the assessment ID instead of the object
        if obj.assesment:
            return obj.assesment.name  # Return the ID directly
        return None
    
    # def get_address_name(self, obj):
    #     try:
    #         location = Location.objects.get(pk=obj.location.id)
    #         return location.name
    #     except Location.DoesNotExist:
    #         return None

    def get_address_name(self, obj):
        if obj.location is not None:
            try:
                location = Location.objects.get(pk=obj.location.id)
                return location.address
            except Location.DoesNotExist:
                return None
        return None

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'department_name', 'owner', 'address_name', 'assessment_name', 'company_name', 'dynamic_job_data', 'created', 'updated', 'job_status', 'assesment' ]
        
    def update(self, instance, validated_data):
        # Debugging output
        owner_data = validated_data.pop('owner', None)
        address_data = validated_data.pop('address', None)  
        education_data = validated_data.pop('education', None)
                
        if owner_data is not None:
            # Retrieve the Account instance using the account_id
            owner_instance = Account.objects.get(account_id=owner_data['account_id'])
            instance.owner = owner_instance  # Assign the Account instance to the job's owner
            
        if address_data is not None:
            location = Location.objects.get(pk=address_data)
            instance.location = location
            
        if education_data is not None:
            instance.education = education_data
            
        members_data = validated_data.pop('member_ids', None)
        if members_data is not None:
            instance.members = members_data
            
        instance = super().update(instance, validated_data)

        return instance
    
    def get_department(self, obj):
        if obj.department:
            department = Department.getById(obj.department.id, obj.company)
            if department:
                return DepartmentSerializer(department).data
        return None   

    def get_educations(self, obj):
        if obj.educations:
            educations = Degree.getByIds(obj.educations, obj.company)
            if educations:
                return DegreeSerializer(educations, many=True).data
        return []                     

    def get_owner(self, obj):
        if obj.owner:
            return AccountSerializer(obj.owner).data
        return None    

    def get_members(self, obj):
        if obj.members:
            members = []
            for memberId in obj.members:
                account = Account.getById(memberId)
                if account:
                    members.append(AccountSerializer(account).data)
            return members
        return None  

    def get_assesment(self, obj):
        if obj.assesment:
            assess = Assesment.getByAssessmentId(obj.assesment)
            return AssesmentSerializer(assess).data
        return None            

    def get_document(self, obj):
        if obj.document:
            return settings.JOB_DOC_FILE_URL+obj.document.name[11:]
        return None             

    def get_pipeline(self, obj):
        if obj.pipeline:
            print(f"One of the member is {obj.pipeline}")
            pipeline = Pipeline.getById(obj.pipeline, obj.company)
            if pipeline:
                return PipelineSerializer(pipeline).data
        return None  

    def get_webform(self, obj):
        if obj.webform:
            print(f"Webform is {obj.webform}")
            return WebformDataSerializer(obj.webform).data
        return None        

    def get_location(self, obj):
        if obj.location:
            print(f"Location is {obj.location}")
            return LocationSerializer(obj.location).data
        return None
    
class JobsCarrerSerializer(serializers.ModelSerializer):
    # department_name = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    # assessment_name = serializers.SerializerMethodField()
    # address_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    # def get_department_name(self, obj):
    #     if obj.department:
    #         return obj.department.name  
    #     return None
    
    # def get_assessment_name(self, obj):
    #     if obj.assesment:
    #         return obj.assesment.name 
    #     return None
    
    # def get_address_name(self, obj):
    #     if obj.location is not None:
    #         try:
    #             location = Location.objects.get(pk=obj.location.id)
    #             return location.address
    #         except Location.DoesNotExist:
    #             return None
    #     return None
    
    # def get_department(self, obj):
    #     if obj.department:
    #         department = Department.getById(obj.department.id, obj.company)
    #         if department:
    #             return DepartmentSerializer(department).data
    #     return None   

    # def get_educations(self, obj):
    #     if obj.educations:
    #         educations = Degree.getByIds(obj.educations, obj.company)
    #         if educations:
    #             return DegreeSerializer(educations, many=True).data
    #     return []                     

    def get_owner(self, obj):
        if obj.owner:
            return AccountSerializer(obj.owner).data
        return None    

    def get_members(self, obj):
        if obj.members:
            members = []
            for memberId in obj.members:
                account = Account.getById(memberId)
                if account:
                    members.append(AccountSerializer(account).data)
            return members
        return None  

    # def get_assesment(self, obj):
    #     if obj.assesment:
    #         assess = Assesment.getByAssessmentId(obj.assesment)
    #         return AssesmentSerializer(assess).data
    #     return None            

    def get_document(self, obj):
        if obj.document:
            return settings.JOB_DOC_FILE_URL+obj.document.name[11:]
        return None             

    def get_pipeline(self, obj):
        if obj.pipeline:
            print(f"One of the member is {obj.pipeline}")
            pipeline = Pipeline.getById(obj.pipeline, obj.company)
            if pipeline:
                return PipelineSerializer(pipeline).data
        return None  

    def get_webform(self, obj):
        if obj.webform:
            print(f"Webform is {obj.webform}")
            return WebformDataSerializer(obj.webform).data
        return None        

    def get_location(self, obj):
        if obj.location:
            print(f"Location is {obj.location}")
            return LocationSerializer(obj.location).data
        return None

    def get_company_name(self, obj):
        if obj.company:
            return obj.company.name
        return None

    def get_company_logo(self, obj):
        if obj.company and obj.company.logo:
            try:
                # Try to get full URL from request context first
                request = self.context.get('request')
                if request and obj.company.logo:
                    return request.build_absolute_uri(obj.company.logo.url)
                # Fallback to settings API_URL + relative path
                elif hasattr(settings, 'API_URL') and obj.company.logo:
                    return f"{settings.API_URL}{obj.company.logo.url}"
                # Last fallback - just return relative URL
                elif obj.company.logo:
                    return obj.company.logo.url
            except:
                return None
        return None

    def get_is_saved(self, obj):
        try:
            request = self.context.get('request') if hasattr(self, 'context') else None
            if request and hasattr(request, 'user') and request.user and request.user.is_authenticated:
                return SavedJob.objects.filter(candidate=request.user, job=obj).exists()
            return False
        except Exception:
            return False

    class Meta:
        model = Job
        fields = "__all__"

class JobListSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()
    # state_name = serializers.CharField(source='state')
    # country_name = serializers.CharField(source='country')
    location = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['id', 'title', 'owner_id', 'vacancies', 'department', 'type',
         'nature', 'exp_min', 'exp_max', 'salary_min', 'salary_max', 'currency', 'location', 
         'created', 'updated', 'active', 'webform_id','pipeline', 'dynamic_job_data']

    def get_id(self, obj):
        return encode(obj.id)

    def get_owner_id(self, obj):
        if obj.owner_id:
            return AccountSerializer(obj.owner_id).data
        return None

    def get_department(self, obj):
        if obj.department:
            department = Department.getById(obj.department.id, obj.company)
            if department:
                return department.name
        return None

    def get_location(self, obj):
        if obj.location:
            return LocationSerializer(obj.location).data
        return None

class JobDetailsSerializer(serializers.ModelSerializer):

    department = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    assesment = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    # # state = serializers.SerializerMethodField()
    # # country = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    pipeline = serializers.SerializerMethodField()
    educations = serializers.SerializerMethodField()
    webform = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.id
        
    class Meta:
        model = Job
        fields = [
             'id', 'title', 'vacancies', 'department', 'owner', 'assesment', 'members', 'type', 'nature', 'educations', 'speciality', 'description',
             'exp_min', 'exp_max', 'salary_min', 'salary_max', 'salary_type', 'currency', 'location', 'created_by', 'document', 
             'job_boards', 'pipeline', 'active', 'updated', 'created', 'webform']
        depth=1
    
    def get_department(self, obj):
        if obj.department:
            print(f"The department is {obj.department}, of company {obj.company}")
            department = Department.getById(obj.department, obj.company)
            if department:
                return DepartmentSerializer(department).data
        return None   

    def get_educations(self, obj):
        if obj.educations:
            print(f"The Education is {obj.educations}, of company {obj.company}")
            educations = Degree.getByIds(obj.educations, obj.company)
            if educations:
                return DegreeSerializer(educations, many=True).data
        return []                     

    def get_owner(self, obj):
        if obj.owner:
            return AccountSerializer(obj.owner).data
        return None    

    def get_members(self, obj):
        if obj.members:
            members = []
            for memberId in obj.members:
                account = Account.getById(memberId)
                if account:
                    members.append(AccountSerializer(account).data)
            return members
        return None  

    def get_assesment(self, obj):
        if obj.assesment:
            assess = Assesment.getByAssessmentId(obj.assesment)
            return AssesmentSerializer(assess).data
        return None            

    def get_document(self, obj):
        if obj.document:
            return settings.JOB_DOC_FILE_URL+obj.document.name[11:]
        return None           

    # def get_state(self, obj):
    #     if obj.state:
    #         return StateSerializer(obj.state).data
    #     return None  

    # def get_country(self, obj):
    #     if obj.country:
    #         return CountrySerializer(obj.country).data
    #     return None          

    def get_pipeline(self, obj):
        if obj.pipeline:
            print(f"One of the member is {obj.pipeline}")
            pipeline = Pipeline.getById(obj.pipeline, obj.company)
            if pipeline:
                return PipelineSerializer(pipeline).data
        return None  

    def get_webform(self, obj):
        if obj.webform:
            print(f"Webform is {obj.webform}")
            return WebformDataSerializer(obj.webform).data
        return None        

    def get_location(self, obj):
        if obj.location:
            print(f"Location is {obj.location}")
            return LocationSerializer(obj.location).data
        return None
    
class TemplateJobSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    assessment_name = serializers.SerializerMethodField()
    address_name = serializers.SerializerMethodField()

    def get_department_name(self, obj):
        # Change this to return the department ID instead of the object
        if obj.department:
            return obj.department.name  # Return the ID directly
        return None
    
    def get_assessment_name(self, obj):
        # Change this to return the assessment ID instead of the object
        if obj.assesment:
            return obj.assesment.name  # Return the ID directly
        return None
    
    def get_address_name(self, obj):
        if obj.location is not None:
            try:
                location = Location.objects.get(pk=obj.location.id)
                return location.address
            except Location.DoesNotExist:
                return None
        return None
    
    def get_department(self, obj):
        if obj.department:
            department = Department.getById(obj.department.id, obj.company)
            if department:
                return DepartmentSerializer(department).data
        return None   

    def get_educations(self, obj):
        if obj.educations:
            educations = Degree.getByIds(obj.educations, obj.company)
            if educations:
                return DegreeSerializer(educations, many=True).data
        return []                     

    def get_owner(self, obj):
        if obj.owner:
            return AccountSerializer(obj.owner).data
        return None    

    def get_members(self, obj):
        if obj.members:
            members = []
            for memberId in obj.members:
                account = Account.getById(memberId)
                if account:
                    members.append(AccountSerializer(account).data)
            return members
        return None  

    def get_assesment(self, obj):
        if obj.assesment:
            assess = Assesment.getByAssessmentId(obj.assesment)
            return AssesmentSerializer(assess).data
        return None            

    def get_document(self, obj):
        if obj.document:
            return settings.JOB_DOC_FILE_URL+obj.document.name[11:]
        return None             

    def get_pipeline(self, obj):
        if obj.pipeline:
            print(f"One of the member is {obj.pipeline}")
            pipeline = Pipeline.getById(obj.pipeline, obj.company)
            if pipeline:
                return PipelineSerializer(pipeline).data
        return None  

    def get_webform(self, obj):
        if obj.webform:
            print(f"Webform is {obj.webform}")
            return WebformDataSerializer(obj.webform).data
        return None        

    def get_location(self, obj):
        if obj.location:
            print(f"Location is {obj.location}")
            return LocationSerializer(obj.location).data
        return None
    
    class Meta:
        model = TemplateJob
        fields = '__all__'
        
class DraftSaveJobSerializer(serializers.ModelSerializer):

    class Meta:
        model = DraftSaveJob
        fields = '__all__'

class JobNotesSerializer(serializers.ModelSerializer):
    job_id = serializers.CharField(source='job.id')
    added_by = serializers.SerializerMethodField()

    class Meta:
        model = JobNotes
        fields = ['id', 'job_id', 'added_by', 'note', 'created', 'updated']       

    def get_added_by(self, obj):
        if obj.added_by:
            return AccountSerializer(obj.added_by).data
        return None    

class JobTaskSerializer(serializers.ModelSerializer):
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
            try:
                account_instance = Account.objects.get(account_id=owner_data['account_id'])
                instance.owner = account_instance
            except Account.DoesNotExist:
                instance.owner = None 
        else:
            instance.owner = None  # Explicitly set to None if not provided

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class JobEventSerializer(serializers.ModelSerializer):
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
            try:
                account_instance = Account.objects.get(account_id=host_data['account_id'])
                instance.host = account_instance
            except Account.DoesNotExist:
                instance.host = None
        else:
            instance.host = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if participants_data is not None:
            instance.participants.set(participants_data)

        instance.save()
        return instance
    
class JobCallSerializer(serializers.ModelSerializer):
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
    #     if owner_data:
    #         account_instance = Account.objects.get(account_id=owner_data['account_id'])
    #         validated_data['owner'] = account_instance

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
    
class getCandidateApplyJobCareerSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'type', 'exp_min', 'exp_max', 'salary_min', 
                 'salary_max', 'location', 'created', 'company',
                 'city', 'state', 'country', 'pincode', 'description', 'dynamic_job_data' ]

    def get_company(self, obj):
        if obj.company:
            return obj.company.name
        return None

    def get_city(self, obj):
        if obj.location and obj.location.city:
            return obj.location.city.name 
        return None

    def get_state(self, obj):
        if obj.location and obj.location.state:
            return obj.location.state.name 
        return None

    def get_country(self, obj):
        if obj.location and obj.location.country:
            return obj.location.country.name 
        return None

    def get_pincode(self, obj):
        if obj.location and obj.location.pincode:
            return obj.location.pincode
        return None
    
class JobBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobBoard
        fields = ['company','credentials','platform','project_id','google_company_id']
        
class JobTimelineSerializer(serializers.ModelSerializer):
    # Use lazy imports to avoid circular dependency
    job = serializers.SerializerMethodField()
    candidate = serializers.SerializerMethodField()
    interview = serializers.SerializerMethodField()
    performed_by = serializers.SerializerMethodField()

    class Meta:
        model = JobTimeline
        fields = '__all__'
    
    def get_job(self, obj):
        if obj.job:
            from job.serializer import JobsSerializer
            return JobsSerializer(obj.job).data
        return None
    
    def get_candidate(self, obj):
        if obj.candidate:
            from candidates.serializer import CandidateListSerializer
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

class JobSearchSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    class Meta:
        model = Job
        fields = ['id', 'dynamic_job_data', 'company_name','job_status', 'created']

    def get_company_name(self, obj):
        return obj.company.name if obj.company else None