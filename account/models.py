from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from common.models import Country, State, City
from datetime import datetime, timedelta
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.conf import settings
from hr_services.models import ContactDetails
from common.file_utils import (
    company_file_path,
    user_photo_path, 
    company_logo_path, 
    company_banner_path,
    CompanyFileStorage
)
from django.db.models import Q
class Account(AbstractUser):

    USER = 'U'
    ADMIN = 'A'
    TRIALUSER = 'T'
    CANDIDATE = 'C'

    ROLE_LIST = [USER, ADMIN, TRIALUSER, CANDIDATE]

    ROLE = [
        (USER, 'User'),
        (ADMIN, 'Admin'),
        (TRIALUSER, 'TrialUser'),
        (CANDIDATE, 'Candidate')
    ]

    account_id = models.UUIDField(
        primary_key=False, unique=True, editable=False)
    role = ArrayField(models.CharField(max_length=1, choices=ROLE), default=list, blank=True)
    mobile = models.CharField(
        max_length=20, unique=False, null=True, blank=True)
    photo = models.ImageField(
        upload_to=user_photo_path, 
        storage=CompanyFileStorage(),
        default=None, 
        null=True, 
        blank=True
    )
    verified = models.BooleanField(default=False)
    company_id = models.UUIDField(default=None, null=True, blank=True)
    designation = models.IntegerField(default=None, null=True, blank=True)
    department = models.IntegerField(default=None, null=True, blank=True)
    addedBy = models.UUIDField(default=None, null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    is_trial = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.account_id:
            self.account_id = uuid.uuid4()
        if self.is_superuser:
            self.username = self.email
        else:
            self.email != self.username
            self.email = self.username
        if self.is_superuser:
            self.role = [self.ADMIN]
            self.verified = True
        super(Account, self).save(*args, **kwargs)

    def start_trial(self, days: int = 14):
        self.trial_start = timezone.now()
        self.trial_end = self.trial_start + timedelta(days=days)
        self.is_trial = True

    def trial_active(self) -> bool:
        if not self.is_trial or not self.trial_end:
            return False
        return self.trial_end > timezone.now()

    def end_trial(self):
        self.is_trial = False

    def __str__(self):
        return str(self.first_name)

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    @staticmethod
    def getById(account_id):
        if Account.objects.filter(account_id=account_id).exists():
            return Account.objects.get(account_id=account_id)
        return None

    @staticmethod
    def getByIdAndCompany(account_id, company):
        if Account.objects.filter(company_id=company.id, account_id=account_id).exists():
            return Account.objects.get(account_id=account_id)
        return None        

    @staticmethod
    def getByAll():
        return Account.objects.all()

    @staticmethod
    def getByMobile(mobile):
        if Account.objects.filter(mobile=mobile).exists():
            return Account.objects.get(mobile=mobile)
        return None

    @staticmethod
    def getByEmail(email):
        if Account.objects.filter(email=email).exists():
            return Account.objects.get(email=email)
        return None

    @staticmethod
    def getMembers(company_id):
        return Account.objects.filter(company_id=company_id)

    @staticmethod
    def getByLogin(mobile, password):
        if Account.objects.filter(mobile=mobile, password=password).exists():
            return Account.objects.get(mobile=mobile)
        return None

JOB_CATEGORIES = [
    ("real_estate", "Real Estate"),
    ("banking_finance", "Banking & Finance"),
    ("construction", "Construction"),
    ("arts_entertainment", "Arts & Entertainment"),
    ("automotive", "Automotive"),
    ("childcare", "Childcare"),
    ("healthcare", "Healthcare"),
    ("media_pr", "Media & PR"),
    ("accounting", "Accounting"),
    ("energy", "Energy"),
    ("purchasing", "Purchasing"),
    ("manufacturing_production", "Manufacturing & Production"),
    ("legal", "Legal"),
    ("it_software", "IT & Software"),
    ("sales", "Sales"),
    ("insurance", "Insurance"),
    ("human_resources", "Human Resources"),
    ("marketing", "Marketing"),
    ("retail_wholesale", "Retail, Wholesale & Stocking"),
    ("medical", "Medical"),
    ("maintenance_installation", "Installation & Maintenance"),
    ("mining", "Mining"),
    ("civil_engineering", "Civil Engineering"),
    ("tourism_hospitality", "Hospitality & Tourism"),
    ("project_management", "Project Management"),
    ("architecture", "Architecture"),
    ("aviation", "Aviation"),
    ("catering", "Catering"),
    ("chemical_engineering", "Chemical Engineering"),
    ("electrical_engineering", "Electrical Engineering"),
    ("information_security", "Information Security"),
    ("mechanical_engineering", "Mechanical Engineering"),
    ("administrative_assistance", "Administrative Assistance"),
    ("agriculture_forestry", "Agriculture & Forestry"),
    ("apprenticeships_trainee", "Apprenticeships & Trainee"),
    ("beauty_wellness", "Beauty & Wellness"),
    ("charity_voluntary", "Charity & Voluntary"),
    ("cleaning_sanitation", "Cleaning & Sanitation"),
    ("customer_service_helpdesk", "Customer Service & Helpdesk"),
    ("dental", "Dental"),
    ("documentation", "Documentation"),
    ("driving_transport", "Driving & Transport"),
    ("education_teaching", "Education & Teaching"),
    ("fmcg", "FMCG"),
    ("government_public_sector", "Government & Public Sector"),
    ("graduate", "Graduate"),
    ("industrial_engineering", "Industrial Engineering"),
    ("logistics_warehousing", "Logistics & Warehousing"),
    ("management", "Management"),
    ("management_consultancy", "Management Consultancy"),
    ("nursing", "Nursing"),
    ("oil_gas", "Oil & Gas"),
    ("recruitment_consultancy", "Recruitment Consultancy"),
    ("scientific_research_development", "Scientific Research & Development"),
    ("security_public_safety", "Security & Public Safety"),
    ("social_science", "Social Science"),
    ("telecoms", "Telecoms"),
    ("translation_multilingual", "Translation & Multilingual"),
    ("veterinary", "Veterinary"),
    ("therapy", "Therapy"),
    ("military_public_safety", "Military & Public Safety"),
    ("leisure_sports", "Leisure & Sports"),
    ("community_social_care", "Community & Social Care"),
    ("creative_digital", "Creative & Digital"),
    ("ecommerce_social_media", "E-Commerce & Social Media"),
    ("pharmaceutical", "Pharmaceutical"),
    ("crypto_blockchain", "Crypto & Blockchain"),
    ("ai_emerging_technologies", "AI & Emerging Technologies"),
    ("sports", "Sports"),
    ("hybrid", "Hybrid"),
    ("other", "Other"),
]


class Company(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    # admin = models.OneToOneField(
    #     Account,
    #     on_delete=models.CASCADE,
    # )
    admin = models.OneToOneField(Account, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(
        max_length=100, unique=False, null=True, blank=True)
    logo = models.FileField(
        upload_to=company_logo_path,
        storage=CompanyFileStorage(),
        default=None,
        null=True,
        blank=True
    )
    banner = models.FileField(
        upload_to=company_banner_path,
        storage=CompanyFileStorage(),
        default=None,
        null=True,
        blank=True
    )
    domain = models.CharField(
        max_length=50, unique=False, null=False, blank=False)
    gst_no = models.CharField(max_length=15, null=True, blank=True)
    website = models.CharField(max_length=100, null=True, blank=True, default=None)
    description = models.TextField(max_length=5000, blank=True, null=True, default=None)
    tag = ArrayField(models.CharField(max_length=500, null=True, blank=True, default=None), null=True, blank=True, default=None)
    phone = models.CharField(max_length=15, null=False, blank=False)
    email = models.CharField(max_length=50, null=False, blank=False)
    address = models.TextField(max_length=500, blank=False, null=False)
    landmark = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.IntegerField(default=None, null=True, blank=True)
    country = models.ForeignKey(
        Country, default=None, null=True, verbose_name='Country', on_delete=models.SET_NULL)
    state = models.ForeignKey(
        State, default=None, null=True, verbose_name='State', on_delete=models.SET_NULL)
    city = models.ForeignKey(
        City, default=None, null=True, verbose_name='city', on_delete=models.SET_NULL)
    loc_lat = models.CharField(
        max_length=20, default=None, null=True, blank=True)
    loc_lon = models.CharField(
        max_length=20, default=None, null=True, blank=True)
    sector = models.CharField(max_length=100, null=True, blank=True, choices=JOB_CATEGORIES)
    linkedin = models.CharField(max_length=100 ,null=True, blank=True)
    twitter = models.CharField(max_length=100 ,null=True, blank=True)
    facebook = models.CharField(max_length=100 ,null=True, blank=True)
    instagram = models.CharField(max_length=100 ,null=True, blank=True)
    is_app_site = models.BooleanField(default=False)
    is_ai_letter_site = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.id) + ' ' + str(self.name)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    @staticmethod
    def getByUser(user):
        try:
            if Company.objects.filter(id=user.company_id).exists():
                return Company.objects.get(id=user.company_id)
        except Exception as e:
            return None
            
    @staticmethod
    def getByDomain(domain):
        if Company.objects.filter(domain=domain).exists():
            return Company.objects.get(domain=domain)
        return None        

    @staticmethod
    def getById(id):
        if Company.objects.filter(id=id).exists():
            return Company.objects.get(id=id)
        return None

    @staticmethod
    def getByOwner(account):
        if Company.objects.filter(owner=account).exists():
            return Company.objects.get(owner=account)
        return None

    def get_total_candidates(self):
        from candidates.models import Candidate
        return Candidate.objects.filter(job__company=self).count()

    def get_total_jobs(self):
        from job.models import Job
        return Job.objects.filter(company=self).count()

    def get_total_accounts(self):
        return Account.objects.filter(company_id=self.id).count()

    def get_candidate_timeline(self):
        from candidates.models import CandidateTimeline
        return CandidateTimeline.objects.filter(candidate__job__company=self).count()

    def get_company_totals(self):
        from job.models import Assesment, JobNotes, JobTimeline, WhatJobsJob,AssesmentCategory
        from candidates.models import Tasks, Events, Call, Note, CandidateExperience, CandidateQualification, ApplicantWebForm, Mail, Candidatewithoutlogin, EmailSettings
        from interview.models import Interview, Feedback, InterviewCandidateStatus, InterviewerStatus, RescheduleRequest,DeclineResponse

        from settings.models import Pipeline, Module, Webform, Location, Department, Designation, Contacts, Testimonials, QRModel, ShortLink, ZwayamAmplifyKey, JobBoard, Subscription, Degree, EmailTemplate, EmailCategory, CandidateEvaluationCriteria, CreditWallet
        
        return {
            'accounts': self.get_total_accounts(),
            'jobs': self.get_total_jobs(),
            'candidates': self.get_total_candidates(),
            'interviews': Interview.objects.filter(company=self).count(),
            'assessments': Assesment.objects.filter(company=self).count(),
            'job_notes': JobNotes.objects.filter(job__company=self).count(),
            'job_timelines': JobTimeline.objects.filter(job__company=self).count(),
            'whatjobs_jobs': WhatJobsJob.objects.filter(job__company=self).count(),
            'tasks': Tasks.objects.filter(Q(candidate__job__company=self) | Q(job__company=self)).count(),
            'events': Events.objects.filter(job__company=self).count(),
            'calls': Call.objects.filter(Q(candidate__job__company=self) | Q(posting_title__company=self)).count(),
            'notes': Note.objects.filter(candidate__job__company=self).count() + JobNotes.objects.filter(job__company=self).count(),
            'candidate_experiences': CandidateExperience.objects.filter(candidate__job__company=self).count(),
            'candidate_qualifications': CandidateQualification.objects.filter(candidate__job__company=self).count(),
            'applicant_webforms': ApplicantWebForm.objects.filter(job__company=self).count(),
            'mails': Mail.objects.filter(sender__company_id=self.id).count(),
            # 'candidate_without_login': Candidatewithoutlogin.objects.filter(job__company=self).count(),
            'pipelines': Pipeline.objects.filter(company=self).count(),
            'modules': Module.objects.filter(company=self).count(),
            'webforms': Webform.objects.filter(company=self).count(),
            'locations': Location.objects.filter(company=self).count(),
            'departments': Department.objects.filter(company=self).count(),
            'designations': Designation.objects.filter(company=self).count(),
            'contacts': Contacts.objects.filter(company=self).count(),

            "job_total": self.get_total_jobs() +JobNotes.objects.filter(job__company=self).count() +JobTimeline.objects.filter(job__company=self).count() +WhatJobsJob.objects.filter(job__company=self).count() + Tasks.objects.filter(Q(candidate__job__company=self) | Q(job__company=self)).count() + Events.objects.filter(job__company=self).count() + Call.objects.filter(Q(candidate__job__company=self) | Q(posting_title__company=self)).count() + JobNotes.objects.filter(job__company=self).count(), 

            "candidates_total":self.get_total_candidates() + self.get_candidate_timeline() + CandidateExperience.objects.filter(candidate__job__company=self).count() + CandidateQualification.objects.filter(candidate__job__company=self).count() + Tasks.objects.filter(candidate__job__company=self).count() + Note.objects.filter(candidate__job__company=self).count() + Call.objects.filter(candidate__job__company=self).count(),

            'interview_total': Interview.objects.filter(company= self).count() + InterviewCandidateStatus.objects.filter(interview__company= self).count() + InterviewerStatus.objects.filter(interview__company= self).count() + RescheduleRequest.objects.filter(interview__company=self).count() + Feedback.objects.filter(interview__company= self).count() +DeclineResponse.objects.filter(interview__company= self).count(),

            "assessment_total": Assesment.objects.filter(company=self).count(),

            "setting_total": self.get_total_accounts() + Degree.objects.filter(company=self).count() + Designation.objects.filter(company=self).count() + Department.objects.filter(company=self).count() + Location.objects.filter(company=self).count() + Module.objects.filter(company=self).count() + Pipeline.objects.filter(company=self).count() + Webform.objects.filter(company=self).count() +Contacts.objects.filter(company=self).count() + AssesmentCategory.objects.filter(company=self).count() + EmailTemplate.objects.filter(company=self).count() + EmailCategory.objects.filter(company=self).count() + EmailSettings.objects.filter(company=self).count() + CandidateEvaluationCriteria.objects.filter(company=self).count(),
            # 'testimonials': Testimonials.objects.filter(company=self).count(),
            # 'qr_codes': QRModel.objects.filter(job__company=self).count(),
            # 'short_links': ShortLink.objects.filter(job__company=self).count(),
            # 'zwayam_keys': ZwayamAmplifyKey.objects.filter(company=self).count(),
            # 'job_boards': JobBoard.objects.filter(company=self).count(),
            # 'subscriptions': Subscription.objects.filter(company=self).count(),
        }
    def get_total_records(self):
        total_director = self.get_company_totals()
        total = 0
        total += total_director['job_total']
        total += total_director['candidates_total']
        total += total_director['interview_total']
        total += total_director['assessment_total']
        total += total_director['setting_total']
        if Subscription.objects.filter(company= self, is_active=True).exists():
            CreditWallet.objects.filter(company= self, feature__code="total_records").update(used_credit= total)
        return total

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from settings.models import CreditWallet, EmailCategory, EmailTemplate, Pipeline, Module, Webform, CandidateEvaluationCriteria,Subscription
from rest_framework.exceptions import ValidationError

@receiver(post_save, sender=Company)
def company_created(sender, instance, created, **kwargs):
    if created:
        instance.get_total_records()
        create_defalut_pipeline_webform(sender, instance, created, **kwargs)

# Job related signals
from job.models import Job

@receiver(pre_save, sender=Job)
def job_pre_save(sender, instance, **kwargs):
    if not instance.pk and hasattr(instance, 'company') and instance.company:
        cw = CreditWallet.objects.filter(company=instance.company, feature__code="total_records").first()
        if cw and not cw.iswithoutcredit and (cw.total_credit - cw.used_credit) <= 0:
            raise ValidationError({'message': 'Total records limit reached. Please upgrade your plan.'})

@receiver([post_save, post_delete], sender=Job)
def job_changed(sender, instance, **kwargs):
    if hasattr(instance, 'company') and instance.company:
        instance.company.get_total_records()

# Account signals
@receiver(pre_save, sender=Account)
def account_pre_save(sender, instance, **kwargs):
    if not instance.pk and hasattr(instance, 'company_id') and instance.company_id:
        try:
            company = Company.objects.get(id=instance.company_id)
            cw = CreditWallet.objects.filter(company=company, feature__code="total_records").first()
            if cw and not cw.iswithoutcredit and (cw.total_credit - cw.used_credit) <= 0:
                raise ValidationError({'message': 'Total records limit reached. Please upgrade your plan.'})
        except Company.DoesNotExist:
            pass

@receiver([post_save, post_delete], sender=Account)
def account_changed(sender, instance, **kwargs):
    if hasattr(instance, 'company_id') and instance.company_id:
        try:
            company = Company.objects.get(id=instance.company_id)
            company.get_total_records()
        except Company.DoesNotExist:
            pass

# Import and register signals for other models
def register_model_signals():
    from job.models import Assesment, JobNotes, JobTimeline, WhatJobsJob, AssesmentCategory
    from candidates.models import Tasks, Events, Call, Note, CandidateExperience, CandidateQualification, ApplicantWebForm, Mail, Candidatewithoutlogin, EmailSettings
    from interview.models import Interview, Feedback, InterviewCandidateStatus, InterviewerStatus, RescheduleRequest, DeclineResponse
    from settings.models import Pipeline, Module, Webform, Location, Department, Designation, Contacts, Degree, EmailTemplate, EmailCategory, CandidateEvaluationCriteria
    
    models_to_monitor = [
        Assesment, JobNotes, JobTimeline, WhatJobsJob, AssesmentCategory,
        Tasks, Events, Call, Note, CandidateExperience, CandidateQualification, 
        ApplicantWebForm, Mail, Candidatewithoutlogin, EmailSettings,
        Interview, Feedback, InterviewCandidateStatus, InterviewerStatus, 
        RescheduleRequest, DeclineResponse,
        Pipeline, Module, Webform, Location, Department, Designation, 
        Contacts, Degree, EmailTemplate, EmailCategory, CandidateEvaluationCriteria
    ]
    
    for model in models_to_monitor:
        @receiver(pre_save, sender=model)
        def model_pre_save(sender, instance, **kwargs):
            if not instance.pk:
                company = None
                if hasattr(instance, 'company'):
                    company = instance.company
                elif hasattr(instance, 'job') and instance.job and hasattr(instance.job, 'company'):
                    company = instance.job.company
                elif hasattr(instance, 'candidate') and instance.candidate and hasattr(instance.candidate, 'job') and instance.candidate.job:
                    job_queryset = instance.candidate.job.all()
                    if job_queryset.exists():
                        company = job_queryset.first().company
                elif hasattr(instance, 'sender') and hasattr(instance.sender, 'company'):
                    company = instance.sender.company
                
                if company:
                    from settings.models import CreditWallet
                    cw = CreditWallet.objects.filter(company=company, feature__code="total_records").first()
                    if cw and not cw.iswithoutcredit and (cw.total_credit - cw.used_credit) <= 0:
                        raise ValidationError({'message': 'Total records limit reached. Please upgrade your plan.'})

        @receiver([post_save, post_delete], sender=model)
        def model_changed(sender, instance, **kwargs):
            company = None
            # Try different ways to get the company
            if hasattr(instance, 'company'):
                company = instance.company
            elif hasattr(instance, 'job') and instance.job and hasattr(instance.job, 'company'):
                company = instance.job.company
            elif hasattr(instance, 'candidate') and instance.candidate and hasattr(instance.candidate, 'job') and instance.candidate.job:
                # Handle ManyToManyField - get first job if available
                job_queryset = instance.candidate.job.all()
                if job_queryset.exists():
                    company = job_queryset.first().company
            elif hasattr(instance, 'sender') and hasattr(instance.sender, 'company'):
                company = instance.sender.company
            
            if company:
                company.get_total_records()

# Register the signals
def create_defalut_pipeline_webform(sender, instance, created, **kwargs):
    if created:
        pipeline = Pipeline()
        pipeline.company = instance
        pipeline.name = "Default Pipeline"
        pipeline.save()

        webform = Module()
        webform.company = instance
        webform.name = "Candidates"
        webform.module_type = 'candidate'
        webform.form = [{"id": 1743743713455, "name": "Personal Details", "label": "Personal Details", "fields": [{"id": 1743743715923, "name": "first_name", "type": "Single Line", "label": "First Name", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Name"}, {"id": 1743743718492, "name": "middle_name", "type": "Single Line", "label": "Middle Name", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Name"}, {"id": 1743744177852, "name": "last_name", "type": "Single Line", "label": "Last Name", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Name"}, {"id": 1743744213605, "name": "email", "type": "Email", "label": "Email ID", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Mail"}, {"id": 1743744215190, "name": "mobile", "type": "Phone", "label": "Mobile", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Phone number"}, {"id": 1744106414639, "name": "alternate_mobile", "type": "Phone", "label": "Alternate Mobile", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Alternate Phone number"}, {"id": 1743744221278, "name": "date_of_birth", "type": "Date", "label": "Date Of Birth", "options": [], "isdelete": False, "required": True, "placeholder": "Enter DOB"}, {"id": 1743744221279, "name": "age", "type": "Number", "label": "Age", "options": [], "isdelete": False, "required": False, "placeholder": "Enter Age"}, {"id": 1743744221280, "name": "gender", "type": "Pick List", "label": "Gender", "options": ["Male", "Female", "Other"], "isdelete": False, "required": True, "placeholder": "Select Gender"}, {"id": 1743744221281, "name": "marital_status", "type": "Pick List", "label": "Marital Status", "options": ["Single", "Married", "Divorced", "Widow"], "isdelete": True, "required": True, "placeholder": "Select Marital Status"}]}, {"id": 1743743713965, "name": "Professional Details", "label": "Professional Details", "fields": [{"id": 1743744415923, "name": "exp_years", "type": "Number", "label": "Experience in years", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Year Of Experience"}, {"id": 1743744500259, "name": "highest_qualification", "type": "Pick List", "label": "Highest Qualification held", "options": ["Secondary School", "High School", "Diploma", "Post Graduate Diploma"], "isdelete": True, "required": True, "placeholder": "Select Highest Qualification"}, {"id": 1743744500260, "name": "current_employer", "type": "Single Line", "label": "Current Employer", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Current Employer"}, {"id": 1743744500262, "name": "professional_start_date", "type": "Date", "label": "Professional Start Date", "options": [], "isdelete": True, "required": True, "placeholder": "Enter Professional Start Date"}, {"id": 1743744500263, "name": "professional_end_date", "type": "Date", "label": "Professional End Date", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Professional End Date"}, {"id": 1743744500261, "name": "currently_working", "type": "Checkbox", "label": "Currently Working", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Currently Working"}, {"id": 1744804225323, "name": "functional_area", "type": "Pick List", "label": "Functional Area", "options": ["Secondary School", "High School", "Diploma", "Post Graduate Diploma", "Graduate", "Post Graduate", "Doctorate"], "isdelete": True, "required": False, "placeholder": "Enter Functional Area"}, {"id": 1744804246567, "name": "current_salary", "type": "Number", "label": "Current Salary", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Current Salary"}, {"id": 1744804248519, "name": "expected_salary", "type": "Number", "label": "Expected Salary", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Expected Salary"}, {"id": 1744804227855, "name": "notice_period", "type": "Pick List", "label": "Notice Period", "options": ["15 Days", "1 month", "2 months", "3 months", "4 months", "5 months", "6 months", "7 months", "8 months"], "isdelete": True, "required": False, "placeholder": "Enter Notice Period"}, {"id": 1744804263548, "name": "salary_currency", "type": "Pick List", "label": "Currency for Salary", "options": ["Option 1", "Option 2"], "isdelete": True, "required": False, "placeholder": "Enter Salary Currency"}, {"id": 1744974163136, "name": "job", "type": "Multi Select", "label": "Job ", "options": [], "isdelete": False, "required": False, "placeholder": "Job select"}]}, {"id": 1743744705911, "name": "Address", "label": "Address", "fields": [{"id": 1743744819678, "name": "country", "type": "Pick List", "label": "Country", "options": ["India", "Option 2", "Option 3", "Option 4"], "isdelete": False, "required": True, "placeholder": "Select Country"}, {"id": 1743744821796, "name": "state", "type": "Pick List", "label": "State", "options": ["Delhi", "Gujrat", "Option 3", "Option 4"], "isdelete": False, "required": True, "placeholder": "Enter State"}, {"id": 1743744825049, "name": "city", "type": "Pick List", "label": "City", "options": ["Delhi", "Ahmedabad", "Option 3", "Option 4"], "isdelete": False, "required": True, "placeholder": "Enter City"}, {"id": 1743744726534, "name": "street", "type": "Single Line", "label": "Street", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Street"}, {"id": 1743744771412, "name": "pincode", "type": "Number", "label": "Pincode", "options": [], "isdelete": False, "required": True, "placeholder": "Enter Pincode"}]}, {"id": 1744804312792, "name": "Skills", "label": "Skills", "fields": [{"id": 1744973551758, "name": "skill", "type": "Tags", "label": "Skills", "options": [], "isdelete": False, "required": True, "placeholder": "Skills"}]}, {"id": 1744804373986, "name": "Experience", "label": "Experience", "fields": [{"id": 1744804390565, "name": "name_of_company", "type": "Single Line", "label": "Name of Company", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Name of Company"}, {"id": 1744804392511, "name": "designation", "type": "Single Line", "label": "Designation", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Designation"}, {"id": 1744804398682, "name": "job_responsibilities", "type": "Multi-Line", "label": "Job Responsibilities", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Job Responsibilities"}, {"id": 1744804403129, "name": "from_date", "type": "Date", "label": "Start Date", "options": [], "isdelete": True, "required": False, "placeholder": "Enter From Date"}, {"id": 1744804405178, "name": "to_date", "type": "Date", "label": "End Date", "options": [], "isdelete": True, "required": False, "placeholder": "Enter To Date"}, {"id": 1772538483851, "name": "currently_working_experience", "type": "Checkbox", "label": "Currently working", "options": [], "required": False, "isEditable": True, "placeholder": ""}]}, {"id": 1744804418450, "name": "Education", "label": "Education", "fields": [{"id": 1744804442053, "name": "school_name", "type": "Single Line", "label": "School Name", "options": [], "isdelete": True, "required": False, "placeholder": "Enter School Name"}, {"id": 1744804455170, "name": "education_degree", "type": "Single Line", "label": "Education Degree", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Education Degree"}, {"id": 1744804459553, "name": "education_specialization", "type": "Single Line", "label": "Education Specialization", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Education Specialization"}, {"id": 1744804462501, "name": "start_date", "type": "Date", "label": "Start Date", "options": [], "isdelete": True, "required": False, "placeholder": "Enter Start Date"}, {"id": 1744804464885, "name": "end_date", "type": "Date", "label": "End Date", "options": [], "isdelete": True, "required": False, "placeholder": "Enter End Date"}, {"id": 1772538606587, "name": "currently_pursuing", "type": "Checkbox", "label": "Currently Pursuing", "options": [], "required": False, "isEditable": True, "placeholder": ""}]}]

        webform.save()
        instance.save()
    
        webform = Module()
        webform.company = instance
        webform.name = "Job Openings"
        webform.module_type = 'job_opening'
        webform.form = [
            {
                "id": 1744786434889,
                "name": "Create Job",
                'label': "Create Job",
                "fields": [
                {
                    "id": 1744786440082,
                    "name": "title",
                    "type": "Single Line",
                    "label": "Job Title",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Enter Job TItle"
                },
                {
                    "id": 1744786618271,
                    "name": "vacancies",
                    "type": "Number",
                    "label": "Number of Vacancies",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Enter Number of Vacancies"
                },
                {
                    "id": 1744786726119,
                    "name": "department",
                    "type": "Pick List",
                    "label": "Department",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Enter Department"
                },
                {
                    "id": 1744803220732,
                    "name": "owner",
                    "type": "Pick List",
                    "label": "Owner",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Select Owner"
                },
                {
                    "id": 1744803317300,
                    "name": "members",
                    "type": "Multi Select",
                    "label": "Team Member",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Select Team Member"
                },
                {
                    "id": 1744786783795,
                    "name": "type",
                    "type": "Pick List",
                    "label": "Type",
                    "options": [
                        "Full Time",
                        "Part Time"
                    ],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Select Tyep"
                },
                {
                    "id": 1744786843652,
                    "name": "nature",
                    "type": "Pick List",
                    "label": "Job Nature",
                    "options": [
                        "Remote",
                        "Physical"
                    ],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Select Job Nature"
                },
                {
                    "id": 1744787101161,
                    "name": "educations",
                    "type": "Pick List",
                    "label": "Education",
                    "options": [
                        "HighSchool",
                        "JuniorCollege",
                        "Bachelors",
                        "Masters"
                    ],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Select Education"
                },
                {
                    "id": 1744787598403,
                    "name": "exp_min",
                    "type": "Number",
                    "label": "Work Ex. min. (years)",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Enter Work Ex"
                },
                {
                    "id": 1744787645294,
                    "name": "exp_max",
                    "type": "Number",
                    "label": "Work Ex. max. (years)",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Enter Max Work"
                },
                {
                    "id": 1744787720348,
                    "name": "salary_min",
                    "type": "Number",
                    "label": "Salary (Minimum)",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Enter Salary Minimum"
                },
                {
                    "id": 1744787769508,
                    "name": "salary_max",
                    "type": "Number",
                    "label": "Salary (Maximum)",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Enter Salary Maximum"
                },
                {
                    "id": 1744787803786,
                    "name": "currency",
                    "type": "Pick List",
                    "label": "Currency",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Currency"
                },
                {
                    "id": 1744787841146,
                    "name": "salary_type",
                    "type": "Pick List",
                    "label": "Salary Type",
                    "options": [
                        "Daily",
                        "Weekly",
                        "Monthly",
                        "Yearly"
                    ],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Salary Type"
                },
                {
                    "id": 1744787899154,
                    "name": "pipeline",
                    "type": "Pick List",
                    "label": "Pipeline",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Pipeline"
                },
                {
                    "id": 1744787404529,
                    "name": "speciality",
                    "type": "Tags",
                    "label": "Key Skills",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Select Speciality"
                },
            ]
            },
            {
            "id": 1752475274569,
            "name": "Address Information",
            "label": "Address Information",
            "fields": [
                {
                    "id": 1752239452649,
                    "name": "country",
                    "type": "Pick List",
                    "label": "Country",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "isEditable": True,
                    "placeholder": "Country"
                },
                {
                    "id": 1752239455534,
                    "name": "state",
                    "type": "Pick List",
                    "label": "State",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "isEditable": True,
                    "placeholder": "State"
                },
                {
                    "id": 1752239459823,
                    "name": "city",
                    "type": "Pick List",
                    "label": "City",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "isEditable": True,
                    "placeholder": "City"
                },
                {
                    "id": 1752475364328,
                    "name": "pincode",
                    "type": "Number",
                    "label": "Pincode",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "isEditable": True,
                    "placeholder": "Pincode"
                }
            ]
            },
            {
            "id": 1752475312081,
            "name": "Description Information",
            "label": "Description Information",
            "fields": [
                {
                    "id": 1746180241835,
                    "name": "description",
                    "type": "Description",
                    "label": "Job Description",
                    "options": [],
                    "isdelete": False,
                    "required": True,
                    "placeholder": "Job Description"
                }
            ]
            }
        ]

        webform.save()
        instance.save()
        
        webform = Module()
        webform.company = instance
        webform.name = "Interviews"
        webform.module_type = 'interview'
        webform.form = [
            {
                "id": 1760336752768,
                "name": "basic_info",
                "label": "Basic Info",
                "fields": [
                    {
                        "id": 1760336777385,
                        "name": "interview_title",
                        "type": "Single Line",
                        "label": "Interview Title",
                        "options": [],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Interview Title"
                    },
                    {
                        "id": 1760336909538,
                        "name": "interview_type",
                        "type": "Pick List",
                        "label": "Interview Type",
                        "options": [
                            "Online",
                            "Offline",
                            "Phone",
                            "Panel"
                        ],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Interview Type"
                    },
                    {
                        "id": 1760337120170,
                        "name": "mode_of_interview",
                        "type": "Pick List",
                        "label": "Mode of Interview",
                        "options": [
                            "Zoom",
                            "Microsoft Teams",
                            "Google Meet",
                            "In-person",
                            "Other"
                        ],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Mode of Interview"
                    },
                    {
                        "id": 1760508432505,
                        "name": "interview_link",
                        "type": "URL",
                        "label": "Interview Link",
                        "options": [],
                        "isdelete": False,
                        "required": False,
                        "isEditable": True,
                        "placeholder": "Interview Link"
                    },
                    {
                        "id": 1760508455534,
                        "name": "interview_location",
                        "type": "Pick List",
                        "label": "Interview Location",
                        "options": [],
                        "isdelete": False,
                        "required": False,
                        "isEditable": True,
                        "placeholder": "Interview Location"
                    },
                    {
                        "id": 1760348939874,
                        "name": "job",
                        "type": "Pick List",
                        "label": "Select Job",
                        "options": [],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Select Job"
                    },
                    {
                        "id": 1760336817918,
                        "name": "candidate",
                        "type": "Multi Select",
                        "label": "Select Candidate(s)",
                        "options": [],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Select Candidate(s)"
                    },
                    {
                        "id": 1760337241155,
                        "name": "interview_round",
                        "type": "Pick List",
                        "label": "Interview Round",
                        "options": [
                            "Screening",
                            "Technical",
                            "Managerial",
                            "HR",
                            "Final"
                        ],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Interview Round"
                    }
                ],
                "isDelete": False
            },
            {
                "id": 1760337321714,
                "name": "interviewers",
                "label": "Interviewer(s)",
                "fields": [
                    {
                        "id": 1760337378723,
                        "name": "interviewers",
                        "type": "Multi Select",
                        "label": "Select Interviewer(s) from Platform",
                        "options": [],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Select Interviewer(s) from Platform"
                    }
                ],
                "isDelete": False
            },
            {
                "id": 1760337400067,
                "name": "schedule",
                "label": "Schedule",
                "fields": [
                    {
                        "id": 1760337455757,
                        "name": "date",
                        "type": "Date",
                        "label": "Date",
                        "options": [],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Date"
                    },
                    {
                        "id": 1760338014026,
                        "name": "time",
                        "type": "Time",
                        "label": "Time",
                        "options": [],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Time"
                    },
                    {
                        "id": 1760337556807,
                        "name": "duration",
                        "type": "Pick List",
                        "label": "Duration",
                        "options": [
                            "15 minutes",
                            "30 minutes",
                            "45 minutes",
                            "60 minutes",
                            "90 minutes",
                            "120 minutes"
                        ],
                        "isdelete": False,
                        "required": False,
                        "isEditable": False,
                        "placeholder": "Duration"
                    },
                    {
                        "id": 1760337519361,
                        "name": "time_zone",
                        "type": "Pick List",
                        "label": "Time Zone",
                        "options": [],
                        "isdelete": False,
                        "required": True,
                        "isEditable": False,
                        "placeholder": "Time Zone"
                    }
                ],
                "isDelete": False
            },
            {
                "id": 1760337691381,
                "name": "additional_information",
                "label": "Additional Information",
                "fields": [
                    {
                        "id": 1760337725409,
                        "name": "notes_for_interviewer_private",
                        "type": "Multi-Line",
                        "label": "Notes for Interviewer (Private)",
                        "options": [],
                        "isdelete": False,
                        "required": False,
                        "isEditable": False,
                        "placeholder": "Notes for Interviewer (Private)"
                    },
                    {
                        "id": 1760337744391,
                        "name": "notes_for_candidate_public",
                        "type": "Multi-Line",
                        "label": "Notes for Candidate (Public)",
                        "options": [],
                        "isdelete": False,
                        "required": False,
                        "isEditable": False,
                        "placeholder": "Notes for Candidate (Public)"
                    }
                ],
                "isDelete": False
            },
            {
                "id": 1760337772999,
                "name": "Reminder Settings",
                "label": "Reminder Settings",
                "fields": [
                    {
                        "id": 1760338334493,
                        "name": "select_reminders",
                        "type": "Multiple Radio Select",
                        "label": "Select Reminders",
                        "options": [
                            "24 hours before",
                            "1 hour before",
                            "15 minutes before"
                        ],
                        "isdelete": False,
                        "required": False,
                        "isEditable": False,
                        "placeholder": "Select Reminders"
                    }
                ],
                "isDelete": False
            }
        ]

        
        webform.save()
        instance.save()
        
        webform = Module()
        webform.company = instance
        webform.name = "Assessment"
        webform.module_type = 'assessment'
        webform.form = [{"id": 1744804418450, "name": "Assessment", "label": "Assessment Information", "fields": []}]

        webform.save()
        instance.save()
        
        default_webform = Webform()
        default_webform.company = instance
        default_webform.name = "Default Webform "
        default_webform.form = [{"id": 1743743713455, "name": "Personal Details", "label": "Personal Details", "fields": [{"id": 1772538662026, "name": "first_name", "type": "Single Line", "label": "First Name", "options": [], "required": True, "placeholder": "Enter Name"}, {"id": 1772538665369, "name": "middle_name", "type": "Single Line", "label": "Middle Name", "options": [], "required": False, "placeholder": "Enter Name"}, {"id": 1772538665730, "name": "last_name", "type": "Single Line", "label": "Last Name", "options": [], "required": True, "placeholder": "Enter Name"}, {"id": 1772538666210, "name": "email", "type": "Email", "label": "Email ID", "options": [], "required": True, "placeholder": "Enter Mail"}, {"id": 1772538668959, "name": "mobile", "type": "Phone", "label": "Mobile", "options": [], "required": True, "placeholder": "Enter Phone number"}, {"id": 1772538669276, "name": "alternate_mobile", "type": "Phone", "label": "Alternate Mobile", "options": [], "required": False, "placeholder": "Enter Alternate Phone number"}, {"id": 1772538669620, "name": "date_of_birth", "type": "Date", "label": "Date Of Birth", "options": [], "required": True, "placeholder": "Enter DOB"}, {"id": 1772538670751, "name": "age", "type": "Number", "label": "Age", "options": [], "required": False, "placeholder": "Enter Age"}]}, {"id": 1743743713965, "name": "Professional Details", "label": "Professional Details", "fields": [{"id": 1772538677642, "name": "exp_years", "type": "Number", "label": "Experience in years", "options": [], "required": False, "placeholder": "Enter Year Of Experience"}, {"id": 1772538677958, "name": "highest_qualification", "type": "Pick List", "label": "Highest Qualification held", "options": ["Secondary School", "High School", "Diploma", "Post Graduate Diploma"], "required": True, "placeholder": "Select Highest Qualification"}, {"id": 1772538678273, "name": "current_employer", "type": "Single Line", "label": "Current Employer", "options": [], "required": False, "placeholder": "Enter Current Employer"}, {"id": 1772538678594, "name": "professional_start_date", "type": "Date", "label": "Professional Start Date", "options": [], "required": True, "placeholder": "Enter Professional Start Date"}, {"id": 1772538678931, "name": "professional_end_date", "type": "Date", "label": "Professional End Date", "options": [], "required": False, "placeholder": "Enter Professional End Date"}, {"id": 1772538679232, "name": "currently_working", "type": "Checkbox", "label": "Currently Working", "options": [], "required": False, "placeholder": "Enter Currently Working"}, {"id": 1772538679523, "name": "functional_area", "type": "Pick List", "label": "Functional Area", "options": ["Secondary School", "High School", "Diploma", "Post Graduate Diploma", "Graduate", "Post Graduate", "Doctorate"], "required": False, "placeholder": "Enter Functional Area"}]}, {"id": 1743744705911, "name": "Address", "label": "Address", "fields": [{"id": 1772538707112, "name": "country", "type": "Pick List", "label": "Country", "options": ["India", "Option 2", "Option 3", "Option 4"], "required": True, "placeholder": "Select Country"}, {"id": 1772538707706, "name": "state", "type": "Pick List", "label": "State", "options": ["Delhi", "Gujrat", "Option 3", "Option 4"], "required": True, "placeholder": "Enter State"}, {"id": 1772538708785, "name": "city", "type": "Pick List", "label": "City", "options": ["Delhi", "Ahmedabad", "Option 3", "Option 4"], "required": True, "placeholder": "Enter City"}, {"id": 1772538710644, "name": "pincode", "type": "Number", "label": "Pincode", "options": [], "required": True, "placeholder": "Enter Pincode"}]}, {"id": 1744804312792, "name": "Skills", "label": "Skills", "fields": [{"id": 1772538712474, "name": "skill", "type": "Tags", "label": "Skills", "options": [], "required": True, "placeholder": "Skills"}]}, {"id": 1744804373986, "name": "Experience", "label": "Experience", "fields": [{"id": 1772538717444, "name": "name_of_company", "type": "Single Line", "label": "Name of Company", "options": [], "required": False, "placeholder": "Enter Name of Company"}, {"id": 1772538718486, "name": "designation", "type": "Single Line", "label": "Designation", "options": [], "required": False, "placeholder": "Enter Designation"}, {"id": 1772538717685, "name": "job_responsibilities", "type": "Multi-Line", "label": "Job Responsibilities", "options": [], "required": False, "placeholder": "Enter Job Responsibilities"}, {"id": 1772538717901, "name": "from_date", "type": "Date", "label": "Start Date", "options": [], "required": False, "placeholder": "Enter From Date"}, {"id": 1772538718734, "name": "to_date", "type": "Date", "label": "End Date", "options": [], "required": False, "placeholder": "Enter To Date"}, {"id": 1772538718965, "name": "currently_working_experience", "type": "Checkbox", "label": "Currently working", "options": [], "required": False, "placeholder": ""}]}, {"id": 1744804418450, "name": "Education", "label": "Education", "fields": [{"id": 1772538719220, "name": "school_name", "type": "Single Line", "label": "School Name", "options": [], "required": False, "placeholder": "Enter School Name"}, {"id": 1772538719677, "name": "education_degree", "type": "Single Line", "label": "Education Degree", "options": [], "required": False, "placeholder": "Enter Education Degree"}, {"id": 1772538719925, "name": "education_specialization", "type": "Single Line", "label": "Education Specialization", "options": [], "required": False, "placeholder": "Enter Education Specialization"}, {"id": 1772538720172, "name": "start_date", "type": "Date", "label": "Start Date", "options": [], "required": False, "placeholder": "Enter Start Date"}, {"id": 1772538720420, "name": "end_date", "type": "Date", "label": "End Date", "options": [], "required": False, "placeholder": "Enter End Date"}, {"id": 1772538722760, "name": "currently_pursuing", "type": "Checkbox", "label": "Currently Pursuing", "options": [], "required": False, "placeholder": ""}]}]

        default_webform.save()
        instance.save()
        
        # Create default evaluation criteria for the company
        default_prompt = {
            "core_skills": 35,
            "relevant_experience": 30,
            "tools_and_technologies": 15,
            "responsibilities": 10,
            "education_certifications": 10
        }
        
        CandidateEvaluationCriteria.objects.create(
            company=instance,
            prompt=default_prompt
        )
        
class TokenResetPassword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        Account, default=1, verbose_name="User", on_delete=models.CASCADE
    )
    active = models.BooleanField(default=True)
    validity = models.DateTimeField()
    created = models.DateTimeField(
        auto_now=False, auto_now_add=True, null=True)

    def __str__(self):
        return str(self.id) + " : " + str(self.user.id)[:50]

    @staticmethod
    def getByTokenId(id):
        try:
            if TokenResetPassword.objects.filter(id=id).exists():
                return TokenResetPassword.objects.get(id=id)
            return None
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def getByUser(user):
        try:
            if TokenResetPassword.objects.filter(user=user).exists():
                return TokenResetPassword.objects.get(user=user)
            return None
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def createToken(user):
        token = TokenResetPassword.getByUser(user)

        if not token:
            token = TokenResetPassword()
            token.user = user

        validity = datetime.now() + timedelta(hours=24)
        token.validity = validity
        token.active = True
        token.save()
        return token

    class Meta:
        verbose_name = "Token Reset Password"
        verbose_name_plural = "Tokens Reset Password"


class TokenEmailVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        Account, default=1, verbose_name="User", on_delete=models.CASCADE
    )
    is_verified = models.BooleanField(default=False)
    created = models.DateTimeField(
        auto_now=False, auto_now_add=True, null=True)

    def __str__(self):
        return str(self.id) + " : " + str(self.user.id)[:50]

    @staticmethod
    def getByTokenId(id):
        try:
            if TokenEmailVerification.objects.filter(id=id).exists():
                return TokenEmailVerification.objects.get(id=id)
            return None
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def getByUser(user):
        try:
            if TokenEmailVerification.objects.filter(user=user).exists():
                return TokenEmailVerification.objects.get(user=user)
            return None
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def createToken(user):
        token = TokenEmailVerification.getByUser(user)
        if not token:
            token = TokenEmailVerification()
            token.user = user
        token.is_verified = False
        token.save()
        return token

    class Meta:
        verbose_name = "Token Email Verification"
        verbose_name_plural = "Tokens Email Verification"

class CareerSiteCompanyDetail(models.Model):
    company = models.ForeignKey(Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    background_image = models.ImageField(
    upload_to= company_file_path,
    storage=CompanyFileStorage(),
    default=None,
    null=True,
    blank=True
)
    title1 = models.TextField(max_length=500, blank=True, null=True, default=None)
    title2 = models.TextField(max_length=500, blank=True, null=True, default=None)
    title3 = models.TextField(max_length=500, blank=True, null=True, default=None)
    
    
class CaptureLead(models.Model):
    company = models.CharField(max_length=100, blank=True, null=True, default=None)
    fullname = models.CharField(max_length=100, blank=True, null=True, default=None)
    email = models.EmailField(max_length=100, blank=True, null=True, default=None)
    phone = models.CharField(max_length=100, blank=True, null=True, default=None)
    designation = models.CharField(max_length=100, blank=True, null=True, default=None)
    is_trial = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    
    
class ZohoToken(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_in = models.IntegerField()
    api_domain = models.URLField()
    token_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"Zoho Token (expires: {self.expires_at})"

    @classmethod
    def create_from_response(cls, data):
        expires_at = timezone.now() + timedelta(seconds=data.get('expires_in', 3600))
        return cls.objects.create(
            access_token=data['access_token'],
            refresh_token=data.get('refresh_token', ''),
            expires_in=data.get('expires_in', 3600),
            api_domain=data.get('api_domain', ''),
            token_type=data.get('token_type', 'Bearer'),
            expires_at=expires_at
        )

    @classmethod
    def get_latest_token(cls):
        return cls.objects.order_by('-created_at').first()


class LeadToken(models.Model):
    lead = models.ForeignKey(CaptureLead, default=None, null=True, blank=True, verbose_name='Lead', on_delete=models.CASCADE)
    token = models.CharField(max_length=100, blank=True, null=True, default=None)
    created = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)

    def is_expired(self):
        if not self.created:
            return True
        return self.created + timedelta(days=14) < timezone.now()

    @staticmethod
    def create_for_lead(lead: CaptureLead):
        token_str = uuid.uuid4().hex
        obj = LeadToken.objects.create(lead=lead, token=token_str)
        return obj
    

class ZohoCRMHistory(models.Model):
    contactus = models.ForeignKey(ContactDetails, default=None, null=True, blank=True, on_delete=models.CASCADE)
    lead = models.ForeignKey(CaptureLead, default=None, null=True, blank=True, on_delete=models.CASCADE)
    zohocrmid = models.CharField(max_length=100, blank=True, null=True, default=None)
    leadtype = models.CharField(max_length=100, blank=True, null=True, default=None)
    created = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    
    def __str__(self):
        return self.zohocrmid