import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from account.models import Company, Account
from django.contrib.postgres.fields import ArrayField, JSONField
# from common.file_utils import CompanyFileStorage, company_file_path
from common.file_utils import CompanyFileStorage, email_template_document_path, qr_code_path, testimonial_profile_photo_path
from common.models import Country, State, City
from common.utils import generateFileName, generateTemplateFileName
from django.db.models import JSONField


class Location(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, default=None, null=False, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    country = models.ForeignKey(
        Country, default=None, null=True, verbose_name='Country', on_delete=models.SET_NULL)
    state = models.ForeignKey(
        State, default=None, null=True, verbose_name='State', on_delete=models.SET_NULL)
    city = models.ForeignKey(
        City, default=None, null=True, verbose_name='City', on_delete=models.SET_NULL)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    loc_lat = models.CharField(max_length=20, null=True, blank=True)
    loc_lon = models.CharField(max_length=20, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.company)+' '+str(self.name)[:20]

    class Meta:
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

    @staticmethod
    def getById(id, company):
        if Location.objects.filter(company=company, id=id).exists():
            return Location.objects.get(id=id)
        return None

    @staticmethod
    def getForCompany(company):
        return Location.objects.filter(company=company)

    @staticmethod
    def getAll():
        return Location.objects.all()


class Department(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.company)+' '+str(self.name)[:20]

    class Meta:
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    @staticmethod
    def getByDid(id):
        if Department.objects.filter(id=id).exists():
            return Department.objects.get(id=id)
        return None
    

    @staticmethod
    def getById(id, company):
        if Department.objects.filter(company=company, id=id).exists():
            return Department.objects.get(id=id)
        return None
    
    @staticmethod
    def getByName(name, company):
        return Department.objects.filter(company=company, name=name).exists()
           

    @staticmethod
    def getForCompany(company):
        return Department.objects.filter(company=company)

    @staticmethod
    def getAll():
        return Department.objects.all()


class Designation(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.company)+' '+str(self.name)[:20]

    class Meta:
        verbose_name = 'Designation'
        verbose_name_plural = 'Designations'

    @staticmethod
    def getByDid(id):
        if Designation.objects.filter(id=id).exists():
            return Designation.objects.get(id=id)
        return None

    @staticmethod
    def getById(id, company):
        if Designation.objects.filter(company=company, id=id).exists():
            return Designation.objects.get(id=id)
        return None

    @staticmethod
    def getByName(name, company):
        return Designation.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getAll():
        return Designation.objects.all()

    @staticmethod
    def getForCompany(company):
        return Designation.objects.filter(company=company)


class Degree(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.company)+' '+str(self.name)[:20]

    class Meta:
        verbose_name = 'Degree'
        verbose_name_plural = 'Degrees'

    @staticmethod
    def getById(id, company):
        if Degree.objects.filter(id=id, company=company).exists():
            return Degree.objects.get(id=id)
        return None

    @staticmethod
    def getByIds(ids, company):
        # Old code for multiple degrees
        # return Degree.objects.filter(company=company, id__in=ids)
        # New code for single degree as of now
        return Degree.objects.filter(company=company, id=ids)

    @staticmethod
    def getByName(name, company):
        return Degree.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getAll():
        return Degree.objects.all()

    @staticmethod
    def getForCompany(company):
        return Degree.objects.filter(company=company)


# Pipeline
class PipelineStage(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    status = ArrayField(models.CharField(max_length=50), blank=True, default=list) 
    active_status = models.IntegerField(verbose_name="active status integer", default=0)
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)[:20]

    class Meta:
        verbose_name = 'PipelineStage'
        verbose_name_plural = 'PipelineStages'

    @staticmethod
    def getById(id):
        if PipelineStage.objects.filter(id=id).exists():
            return PipelineStage.objects.get(id=id)
        return None

    @staticmethod
    def getByName(name, company):
        return Department.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getAll():
        return PipelineStage.objects.all()

    @staticmethod
    def getForCompany(company):
        return PipelineStage.objects.filter(company=company)

    @staticmethod
    def getByPipeline(id):
        return PipelineStage.objects.get(id=id)


class Pipeline(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, default=None, null=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True,)
    created = models.DateTimeField(auto_now_add=True)
    # on Delete it should keep rest stages
    stage1 = models.ForeignKey(PipelineStage, blank=True, null=True, verbose_name='Pipeline Stage 1', related_name='pipeline_stages_1', on_delete=models.DO_NOTHING)
    stage2 = models.ForeignKey(PipelineStage, blank=True, null=True, verbose_name='Pipeline Stage 2', related_name='pipeline_stages_2', on_delete=models.DO_NOTHING)
    stage3 = models.ForeignKey(PipelineStage, blank=True, null=True, verbose_name='Pipeline Stage 3', related_name='pipeline_stages_3', on_delete=models.DO_NOTHING)
    stage4 = models.ForeignKey(PipelineStage, blank=True, null=True, verbose_name='Pipeline Stage 4', related_name='pipeline_stages_4', on_delete=models.DO_NOTHING)
    stage5 = models.ForeignKey(PipelineStage, blank=True, null=True, verbose_name='Pipeline Stage 5', related_name='pipeline_stages_5', on_delete=models.DO_NOTHING)
    stage6 = models.ForeignKey(PipelineStage, blank=True, null=True, verbose_name='Pipeline Stage 6', related_name='pipeline_stages_6', on_delete=models.DO_NOTHING)
    stage7 = models.ForeignKey(PipelineStage, blank=True, null=True, verbose_name='Pipeline Stage 7', related_name='pipeline_stages_7', on_delete=models.DO_NOTHING)

    def __str__(self):
        return str(self.company)+' '+str(self.name)[:20]

    class Meta:
        verbose_name = 'Pipeline'
        verbose_name_plural = 'Pipelines'

    @staticmethod
    def getByName(name, company):
        return Department.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getById(id, company):
        if Pipeline.objects.filter(company=company, id=id).exists():
            return Pipeline.objects.get(id=id)
        return None

    @staticmethod
    def getAll():
        return Pipeline.objects.all()

    @staticmethod
    def getForCompany(company):
        return Pipeline.objects.filter(company=company)

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Pipeline)
def create_pipeline_stages(sender, instance, created, **kwargs):
    if created:
        stage_list = ["Screening", "Applied", "Shortlisted", "Interview", "Offered", "Hired", "Onboarded"]
        stage_status = [["Associated", "Contacted", "Unqualified", "Contact in future", "Not-Contacted", "Junk Candidate", "Attempted to contact", "Candidate not interested"],
                        [],
                        ["Qualified", "Under review", "Waiting for evaluation", "Suitable for other openings"],
                        ["Interview to be scheduled", "Interview Scheduled", "Interview in progress", "On-Hold", "Rejected for interview"],
                        ["To be offered", "Offer Made", "Offer Accepted", "Offer Withdrawn", "Offer declined"],
                        ["Hired", "Joined", "No Show", "Forward to onboarding", "Converted-Employee"],
                        []]
        i = 1
        for stage in stage_list:
            stage_instance = PipelineStage.objects.create(name=stage)
            print(stage_instance)

            stage_instance.status = stage_status[i-1]
            cmd =  f"instance.stage{i} = stage_instance"
            
            exec(cmd)
            
            i+=1
            
            stage_instance.save()
            instance.save()    

# Email
class EmailCategory(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)[:20]

    class Meta:
        verbose_name = 'EmailCategory'
        verbose_name_plural = 'EmailCategories'

    @staticmethod
    def getById(id, company):
        if EmailCategory.objects.filter(company=company, id=id).exists():
            return EmailCategory.objects.get(id=id)
        return None

    @staticmethod
    def getByName(name, company):
        return EmailCategory.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getForCompany(company):
        return EmailCategory.objects.filter(company=company)

    @staticmethod
    def getAll():
        return EmailCategory.objects.all()

class TemplateVariables(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, default=None, null=False, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True, verbose_name='name')
    variables = models.JSONField(null=True, blank=True, default=dict, verbose_name='variable')
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.company)+' '+str(self.name)[:20]

    class Meta:
        verbose_name = 'TemplateVariables'
        verbose_name_plural = 'TemplateVariables'

    @staticmethod
    def getById(id, company):
        if TemplateVariables.objects.filter(company=company, id=id).exists():
            return TemplateVariables.objects.get(id=id)
        return None

    @staticmethod
    def getByName(name, company):
        return TemplateVariables.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getForCompany(company):
        return TemplateVariables.objects.filter(company=company)

    @staticmethod
    def getAll():
        return TemplateVariables.objects.all()

class EmailTemplate(models.Model):

    CANDIDATE = 'C'
    INTERNAL = 'I'
    EMAIL_TYPES = [CANDIDATE, INTERNAL]
    TYPE = [
        (CANDIDATE, 'Candidate'),
        (INTERNAL, 'Internal')
    ]

    # Attachment Category Choices
    JOB_OPENINGS = 'job_openings'
    CANDIDATES = 'candidates'
    # CLIENTS = 'clients'
    # CONTACTS = 'contacts'
    
    ATTACHMENT_CATEGORY_CHOICES = [
        (JOB_OPENINGS, 'Job Openings'),
        (CANDIDATES, 'Candidates'),
        # (CLIENTS, 'Clients'),
        # (CONTACTS, 'Contacts'),
    ]

    # Attachment Subcategory Choices
    # Job Openings subcategories
    # JOB_SUMMARY = 'job_summary'
    JOB_DOCUMENT = 'job_document'
    
    # Candidates subcategories
    RESUME = 'resume'
    CERTIFICATE = 'certificate'
    COVER_LETTER = 'cover_letter'
    PROFILE_PICTURE = 'profile_picture'
    OFFER = 'offer'
    
    # Clients subcategories
    CLIENT_CONTRACT = 'client_contract'
    INVOICE = 'invoice'
    
    # Common subcategory
    OTHERS = 'others'
    
    ATTACHMENT_SUBCATEGORY_CHOICES = [
        # Job Openings
        (JOB_DOCUMENT, 'Job Document'),
        # (OTHERS, 'Others'),
        
        # Candidates
        (RESUME, 'Resume'),
        (CERTIFICATE , 'Certificate'),
        (COVER_LETTER, 'Cover Letter'),
        # (PROFILE_PICTURE, 'Profile Picture'),
        # (OFFER, 'Offer'),
        
        # Clients
        # (CLIENT_CONTRACT, 'Client Contract'),
        # (INVOICE, 'Invoice'),
        
        # Common
        # (OTHERS, 'Others'),
    ]

    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    category = models.ForeignKey(
        EmailCategory, null=False, verbose_name='Category', on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=TYPE, default=CANDIDATE)
    name = models.TextField(max_length=500, null=True, blank=True)
    from_email = models.EmailField(max_length=254, null=True, blank=True, verbose_name='From Email')
    reply_to = models.EmailField(max_length=254, null=True, blank=True, verbose_name='Reply To Email')
    subject = models.TextField(max_length=500, null=False, blank=False)
    message = models.TextField(max_length=5000, null=False, blank=False)
    add_signature = models.BooleanField(default=False, verbose_name='Add Signature')
    footer = models.TextField(max_length=1000, null=True, blank=True, verbose_name='Footer')
    attachment = models.FileField(
        upload_to=email_template_document_path, storage=CompanyFileStorage(), default=None, null=True, blank=True)
    attachment_category = models.CharField(
        max_length=50, 
        choices=ATTACHMENT_CATEGORY_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name='Attachment Category'
    )
    attachment_subcategory = models.CharField(
        max_length=50, 
        choices=ATTACHMENT_SUBCATEGORY_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name='Attachment Subcategory'
    )
    unsubscribe_link =models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.subject)

    class Meta:
        verbose_name = 'EmailTemplate'
        verbose_name_plural = 'EmailTemplates'

    @staticmethod
    def getById(id, company):
        if EmailTemplate.objects.filter(company=company, id=id).exists():
            return EmailTemplate.objects.get(id=id)
        return None

    @staticmethod
    def getByName(subject, company):
        return EmailTemplate.objects.filter(company=company, subject=subject).exists()

    @staticmethod
    def getForCompany(company):
        return EmailTemplate.objects.filter(company=company)

    @staticmethod
    def getAll():
        return EmailTemplate.objects.all()


class EmailFields(models.Model):

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    email_template = models.ForeignKey(EmailTemplate, null=True, blank=True, on_delete=models.CASCADE)
    value = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.name)+' '+str(self.value)[:20]

    class Meta:
        verbose_name = 'EmailField'
        verbose_name_plural = 'EmailFields'

    @staticmethod
    def getByName(name, company):
        return EmailFields.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getById(id):
        if EmailFields.objects.filter(id=id).exists():
            return EmailFields.objects.get(id=id)
        return None

    @staticmethod
    def getForCompany(company):
        return EmailFields.objects.filter(company=company)

    @staticmethod
    def getAll():
        return EmailFields.objects.all()    
    
class CandidateEvaluationCriteria(models.Model):
    """
    Model to store weights for different evaluation criteria for candidates.
    The total of all weights should be 100.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    prompt = models.JSONField(help_text="JSON configuration for evaluation prompt")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UnsubscribeLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.body

class OrganizationalEmail(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    signature = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    
class UnsubscribeEmailToken(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, auto_created=True)
    candidate = models.ForeignKey('candidates.Candidate', on_delete=models.CASCADE, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.token)[:20]
    
    @staticmethod
    def getByToken(token):
        try:
            return UnsubscribeEmailToken.objects.get(token=token)
        except UnsubscribeEmailToken.DoesNotExist:
            return None    

class EmailCredential(models.Model):
    Name = models.CharField(max_length=100, null=True, blank=True)
    Email_host = models.CharField(max_length=100, null=True, blank=True)
    Email_port = models.CharField(max_length=100, null=True, blank=True)
    Email_use_tls = models.BooleanField(default=True)
    Email_use_ssl = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
Module_type_choices = [
    ('job_opening', 'Job Opening'),
    ('candidate', 'Candidate'),
    ('interview', 'Interview'),
    ('assessment', 'Assessment'),
]

class Module(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, default=None, null=True, verbose_name='Company', on_delete=models.CASCADE)
    module_type=models.CharField(choices=Module_type_choices)
    name = models.CharField(max_length=50, null=True, blank=True)
    form = JSONField(null=True, default=None)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)
    
    def getById(id, company):
        if Module.objects.filter(id=id, company=company).exists():
            return Module.objects.get(id=id)
        return None

class Webform(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, default=None, null=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    form = JSONField(null=True, default=None)
    module = models.ForeignKey(Module, null=True, blank=True, on_delete=models.SET_NULL)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        verbose_name = 'Webform'
        verbose_name_plural = 'Webforms'

    @staticmethod
    def getByName(name, company):
        return Webform.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getById(id, company):
        if Webform.objects.filter(id=id, company=company).exists():
            return Webform.objects.get(id=id)
        return None
    
    @staticmethod
    def getByWebformId(id):
        if Webform.objects.filter(id=id).exists():
            return Webform.objects.get(id=id)
        return None

    @staticmethod
    def getForCompany(company):
        return Webform.objects.filter(company=company)

    @staticmethod
    def getAll():
        return Webform.objects.all()    


class Contacts(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, default=None, null=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)

    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'

    @staticmethod
    def getByName(name, company):
        return Contacts.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getById(id, company):
        if Contacts.objects.filter(id=id, company=company).exists():
            return Contacts.objects.get(id=id)
        return None
    
    @staticmethod
    def getByContactId(id):
        if Contacts.objects.filter(id=id).exists():
            return Contacts.objects.get(id=id)
        return None

    @staticmethod
    def getByEmailId(email, company):
        return Contacts.objects.filter(company=company, email=email).exists()

    @staticmethod
    def getByMobile(mobile, company):
        return Contacts.objects.filter(company=company, mobile=mobile).exists()     

    @staticmethod
    def getForCompany(company):
        return Contacts.objects.filter(company=company)

    @staticmethod
    def getAll():
        return Contacts.objects.all()         
    
class Testimonials(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True,blank=True)
    designation = models.CharField(max_length=100,null=True,blank=True)
    testimonials = models.TextField(max_length=2000, null=True, blank=True)
    # Profile_picture = models.ImageField(upload_to='media/users/photos', default=None, null=True, blank=True)
    Profile_picture = models.ImageField(
        upload_to=testimonial_profile_photo_path,
        storage=CompanyFileStorage(),
        default=None,
        null=True,
        blank=True
    )

    def __str__(self):
        return  f"{str(self.company)} {str(self.name)}"

    class Meta:
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        
class RazorpaySettings(models.Model):
    MODE_CHOICES = [
        ('test', 'Test Mode'),
        ('live', 'Live Mode'),
    ]
    mode = models.CharField(max_length=4, choices=MODE_CHOICES, default='test')

    def __str__(self):
        return self.mode

# class ApplyCoupan(models.Model):
#     code = models.CharField(max_length=50, unique=True)
#     discount = models.DecimalField(max_digits=5, decimal_places=2)
#     valid_from = models.DateTimeField()
#     valid_to = models.DateTimeField()
#     active = models.BooleanField(default=True)

#     def __str__(self):
#         return self.code 

# class Plan(models.Model):
#     name = models.CharField(max_length=100, null=True, blank=True)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     features = models.TextField(null=True, blank=True)
#     offer = models.CharField(max_length=100, null=True, blank=True)
#     # duration_in_months = models.PositiveIntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return self.name 

# class Subscription(models.Model):
#     user = models.ForeignKey(Account, on_delete=models.CASCADE)
#     plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
#     start_date = models.DateTimeField(auto_now_add=True)
#     end_date = models.DateTimeField(null=True, blank=True)
#     active = models.BooleanField(default=True)

# class Feature(models.Model):
#     code = models.CharField(max_length=100, unique=True)
#     name = models.CharField(max_length=100)
#     description = models.TextField(blank=True)

#     def __str__(self):
#         return self.name
    
# class Payment(models.Model):
#     razorpay_order_id = models.CharField(max_length=100)
#     razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
#     razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return self.razorpay_order_id

class ShortLink(models.Model):
    code = models.CharField(max_length=10, unique=True)
    long_url = models.URLField()
    job = models.ForeignKey('job.Job', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class QRModel(models.Model):
    url = models.URLField()
    job = models.ForeignKey('job.Job', on_delete=models.CASCADE)
    # qr_image = models.ImageField(upload_to="media/qr_codes/", blank=True, null=True)
    qr_image = models.ImageField(
    upload_to=qr_code_path,
    storage=CompanyFileStorage(),
    default=None,
    null=True,
    blank=True
)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.url

class LinkdingCompanyid(models.Model):
    """
    Model to store company IDs from Linkding service.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='linkding_ids')
    linkding_id = models.CharField(max_length=100, unique=True, help_text='Company ID from Linkding service')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(blank=True, null=True, help_text='Additional metadata from Linkding')

class ZwayamAmplifyKey(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='zwayam_amplify_keys')
    api_key = models.CharField(max_length=100, unique=True, help_text='Company ID from Linkding service')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class JobBoardList(models.Model):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=400)
    logo = models.FileField(upload_to="media/job_board_list/logo/", blank=True, null=True)
    value = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class JobBoard(models.Model):
    job_board_list = models.ManyToManyField(JobBoardList, related_name='values')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_boards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Plan(models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)  # Starter, Growth, Pro
    description = models.TextField(null=True,blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class BillingCycle(models.Model):
    name = models.CharField(max_length=30)  # Monthly, Half-Yearly, Annually
    duration_in_months = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class PlanPricing(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="prices")
    billing_cycle = models.ForeignKey(BillingCycle, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offer = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("plan", "billing_cycle")

    def __str__(self):
        return f"{self.plan.name} - {self.billing_cycle.name}"

class Feature(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    isdayli = models.BooleanField(default=False)
    iscredit = models.BooleanField(default=False)
    iswithoutcredit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PlanFeatureCredit(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="feature_limits")
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    credit_limit = models.PositiveIntegerField(null=True, blank=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class FeatureUsage(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    used_credit = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AddonPlan(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="addon_plans")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    credits = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ("feature", "credits")
    
    def __str__(self):
        return f"{self.feature.name} - {self.credits} credits"

class Subscription(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    plan_pricing = models.ForeignKey(PlanPricing, on_delete=models.SET_NULL, null=True)
    # billingcycle = models.ForeignKey(BillingCycle, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.plan_pricing}"

class CreditWallet(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    total_credit = models.IntegerField(default=0)
    used_credit = models.IntegerField(default=0)
    isdayli = models.BooleanField(default=False)
    iscredit = models.BooleanField(default=False)
    iswithoutcredit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CreditHistory(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True,blank=True)
    credit_wallet = models.ForeignKey(CreditWallet, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.SET_NULL, null=True)
    feature_usage = models.ForeignKey(FeatureUsage, on_delete=models.SET_NULL, null=True)
    credit = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BilingHistory(models.Model):
    
    TRANSACTION_TYPE = (
        ("plan_allocation", "Plan Allocation"),
        ("addon", "Addon"),
        ('custom_addon','Custom Addon')
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    plan_pricing = models.ForeignKey(PlanPricing, on_delete=models.SET_NULL, null=True)
    feature = models.ForeignKey(Feature, on_delete=models.SET_NULL, null=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    credit = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Payment(models.Model):
    TYPE_CHOICES = [
        ('plan', 'Plan'),
        ('addon', 'Addon'),
        ('custom_addon','Custom Addon')
    ]
    
    payment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='plan')
    plan_pricing = models.ForeignKey('PlanPricing', on_delete=models.SET_NULL, null=True, blank=True)
    addon_plan = models.ForeignKey('AddonPlan', on_delete=models.SET_NULL, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.razorpay_order_id