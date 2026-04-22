from django.db import models
from account.models import Account, Company
from common.models import Country, NoteType, State, City
from common.file_utils import (
    job_document_path, 
    CompanyFileStorage, 
    job_board_credentials_path,
    company_banner_path
)
from settings.models import Department, Pipeline, Webform, Location, QRModel, ShortLink
from django.contrib.postgres.fields import ArrayField
from django.db.models import JSONField
from urllib.parse import quote
from django.conf import settings
import qrcode
import io
from django.core.files.base import ContentFile
import uuid
# process_job_import moved inside save method to avoid circular import

class AssesmentCategory(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)[:20]

    class Meta:
        verbose_name = 'Assesment Category'
        verbose_name_plural = 'Assesment Categories'

    @staticmethod
    def getById(id, company):
        if AssesmentCategory.objects.filter(company=company, id=id).exists():
            return AssesmentCategory.objects.get(id=id)
        return None
    
    @staticmethod
    def getByName(name, company):
        return AssesmentCategory.objects.filter(company=company, name=name).exists()
           

    @staticmethod
    def getForCompany(company):
        return AssesmentCategory.objects.filter(company=company)

    @staticmethod
    def getAll():
        return AssesmentCategory.objects.all()

class Assesment(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, default=None, null=False, verbose_name='Company', on_delete=models.CASCADE)
    category = models.ForeignKey(AssesmentCategory, default=None, null=True, blank = True,verbose_name='Category', on_delete=models.SET_NULL)
    name = models.CharField(max_length=50, null=True, blank=True)
    form = JSONField(null=True, blank=True, default=None)
    dynamic_assessment_data = JSONField(null=True, blank=True)
    created_by =  models.ForeignKey(Account, default=None, null=True, verbose_name='Created By', on_delete=models.SET_NULL)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.company.name)+' '+str(self.name)[:20]

    class Meta:
        verbose_name = 'Assesment'
        verbose_name_plural = 'Assesments'

    @staticmethod
    def getById(id, company):
        if Assesment.objects.filter(company=company, id=id).exists():
            return Assesment.objects.get(id=id)
        return None
    
    @staticmethod
    def getByAssessmentId(id):
        if Assesment.objects.filter(id=id).exists():
            return Assesment.objects.get(id=id)
        return None
    
    @staticmethod
    def getByName(name, company):
        return Assesment.objects.filter(company=company, name=name).exists()

    @staticmethod
    def getByNameAndCategory(name, category):
        return Assesment.objects.filter(category=category, name=name).exists()           

    @staticmethod
    def getForCompany(company):
        return Assesment.objects.filter(company=company)

    @staticmethod
    def getAll():
        return Assesment.objects.all()

class CompanyCredentials(models.Model):
    LINKEDIN = 'L'
    TYPE = [
        (LINKEDIN, 'LINKEDIN'),
    ] 
    board = models.CharField(max_length=2, choices=TYPE, default=LINKEDIN)
    company = models.ForeignKey(Company, default=None, null=False, verbose_name='Company', on_delete=models.CASCADE)
    linkedIn_company_id = models.CharField(max_length=20, verbose_name='LinkedIn Company ID', primary_key=True)
    client_id = models.CharField(max_length=50, verbose_name='Client ID')
    client_secret = models.CharField(max_length=50, verbose_name='Client Secret')
    auth_token = models.CharField(max_length=100, verbose_name='Auth Token', null=True, blank=True)
    def __str__(self):
        return str(self.company.name)+' '+str(self.board)[:20]


    class Meta:
        verbose_name = 'Company Credential'
        verbose_name_plural = 'Company Credentials'

class AssesmentQuestion(models.Model):
    
    RADIO = 'RADIO'
    CHECK = 'CHECK'
    SELECT = 'SELECT'
    TEXT = 'TEXT'

    TYPES = [RADIO, CHECK, SELECT, TEXT]

    TYPE = [
        (RADIO, 'Radio'),
        (CHECK, 'Check'),
        (SELECT, 'Select'),
        (TEXT, 'Text'),
    ] 

    id = models.AutoField(primary_key=True)
    assesment =  models.ForeignKey(Assesment, default=False, null=False, verbose_name='Assesment', on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE, default=RADIO)
    question = models.TextField(max_length=500, null=False, blank=False)
    options = ArrayField(models.CharField(max_length=100), blank=True)
    answer = models.CharField(max_length=100)
    marks = models.IntegerField(default=1)
    text = models.TextField(max_length=1000, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.assesment.company.name)+' '+str(self.question)[:40]

    class Meta:
        verbose_name = 'AssesmentQuestion'
        verbose_name_plural = 'AssesmentQuestions'

    @staticmethod
    def getById(id, assesment):
        if AssesmentQuestion.objects.filter(assesment=assesment, id=id).exists():
            return AssesmentQuestion.objects.get(id=id)
        return None

    @staticmethod
    def getByCompany(id, company):
        if AssesmentQuestion.objects.filter(id=id).exists():
            question = AssesmentQuestion.objects.get(id=id)
            if question.assesment.company.id == company.id:
                return question
        return None        

    @staticmethod
    def getAll():
        return AssesmentQuestion.objects.all()

    @staticmethod
    def getForAssesment(assesment):
        return AssesmentQuestion.objects.filter(assesment=assesment)

class Job(models.Model):
    
    REMOTE = 'Remote'
    PHYSICAL = 'Physical'
    NATURES = [REMOTE, PHYSICAL]
    NATURE = [
        (PHYSICAL, 'Physical'),
        (REMOTE, 'Remote')
    ]
    HIGH_SCHOOL="High School"
    JUNIOR_COLLEGE = 'Junior College'
    BACHELORS = 'Bachelors'
    MASTERS = 'Masters'

    EDUCATION = [
        (HIGH_SCHOOL,"High School"),
        (JUNIOR_COLLEGE,"Junior College"),
        (BACHELORS,"Bachelors"),
        (MASTERS,"Masters")
    ]


    HIGH_SCHOOL= "HIGH_SCHOOL"
    JUNIOR_COLLEGE = "JUNIOR_COLLEGE"
    BACHELORS = "BACHELORS"
    MASTERS = "MASTERS"

    EDUCATIONS = [HIGH_SCHOOL,JUNIOR_COLLEGE,BACHELORS,MASTERS]

    EDUCATION=[
        (HIGH_SCHOOL,'HighSchool'),
        (JUNIOR_COLLEGE,'JuniorCollege'),
        (BACHELORS,'Bachelors'),
        (MASTERS,'Masters')
    ]

    FULL_TIME = 'FULL_TIME'
    PART_TIME = 'PART_TIME'
    TYPES = [FULL_TIME, PART_TIME]
    TYPE = [
        (FULL_TIME, 'Full Time'),
        (PART_TIME, 'Part Time')
    ]

    DAILY = 'DAILY'
    WEEKLY = 'WEKLY'
    MONTHY = 'MONTHLY'
    YEARLY = 'YEARLY'

    PAY_TYPES = [DAILY, WEEKLY, MONTHY, YEARLY]
    PAY_TYPE = [
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHY, 'Monthly'),
        (YEARLY, 'Yearly'),
    ]

    # Change here for changes status
    IN_PROGRESS = 'In Progress'
    FILLED = 'Filled'
    HOLD = 'On Hold'
    CLOSED = 'Closed'

    STATUS = [
        (IN_PROGRESS,'In Progress'),
        (FILLED,'Filled'),
        (HOLD, 'On Hold'),
        (CLOSED, 'Closed')
    ]

    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, default=None, null=True, verbose_name='Company', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=True, blank=True)
    vacancies = models.IntegerField(default=1, null=True, blank=True)
    # department = models.CharField(max_length=50, null=True, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, verbose_name='Department', on_delete = models.SET_NULL)
    # owner = models.CharField(max_length=50, null=True, blank=True)
    owner = models.ForeignKey(Account, default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_jobs')
    # assesment =  models.CharField(max_length=50, null=True, blank=True)
    assesment = models.ForeignKey(Assesment, null=True, blank=True, verbose_name='Assesment', on_delete = models.SET_NULL)
    # members = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    type = models.CharField(max_length=20, choices=TYPE, default=FULL_TIME)
    nature = models.CharField(max_length=10, choices=NATURE, default=PHYSICAL)
    # educations = models.CharField(null=True, max_length=20,choices=EDUCATION,default=HIGH_SCHOOL)
    description = models.TextField(null=True, blank=True)
    # speciality = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    exp_min = models.IntegerField(default=0, null=True, blank=True)
    exp_max = models.IntegerField(default=0, null=True, blank=True)
    salary_min = models.CharField(max_length=50, null=True, blank=True, default='')
    salary_max = models.CharField(max_length=50, null=True, blank=True, default='')
    # salary_type = models.CharField(max_length=20, choices=PAY_TYPE, default=MONTHY)
    currency = models.CharField(max_length=10, null=True, blank=True)

    job_status =  models.CharField(max_length=50, null=True, blank=True, choices=STATUS, default =IN_PROGRESS)

    location = models.ForeignKey(Location,null=True, blank=True, on_delete = models.SET_NULL)
    # created_by =  models.CharField(max_length=50, null=True, blank=True)
    created_by =  models.ForeignKey(Account, default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_jobs')
    document = models.FileField(upload_to=job_document_path, storage=CompanyFileStorage(), default=None, null=True, blank=True)  
    job_boards = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    job_link = models.CharField(max_length=200, null=True, blank=True)
    pipeline = models.ForeignKey(Pipeline,related_name='pipline_id',null=True,on_delete=models.SET_NULL)
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    startdate = models.DateField(null=True, blank=True)
    targetdate = models.DateField(null=True, blank=True)
    webform = models.ForeignKey(Webform,related_name='webform_id',null=True,on_delete=models.SET_NULL)
    dynamic_job_data = models.JSONField(null=True, blank=True)
    published = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        is_new = self.id is None
        if is_new:
            super().save(*args, **kwargs)
        # Build job_link safely
        title_val = None
        if isinstance(self.dynamic_job_data, dict):
            try:
                title_val = self.dynamic_job_data.get("Create Job", {}).get("title")
            except Exception:
                title_val = None
        if not title_val:
            title_val = self.title or f"Job-{self.id}"
        self.job_link = f"{settings.JOB_URL}/jobs/{self.id}"
        super().save(*args, **kwargs)

        if is_new:    
            try:
                url = self.job_link or f'{settings.JOB_URL}/jobs/{self.id}'
                if url:
                    qr = qrcode.QRCode(box_size=10, border=4)
                    qr.add_data(url)
                    qr.make(fit=True)

                    img = qr.make_image(fill_color="black", back_color="white")

                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    buffer.seek(0)

                    qr_obj = QRModel.objects.create(url=url, job=self)
                    qr_obj.qr_image.save(f"qr_{qr_obj.id}.png", ContentFile(buffer.getvalue()), save=True)

                    code = None
                    while True:
                        code = uuid.uuid4().hex[:6]
                        if not ShortLink.objects.filter(code=code).exists():
                            break
                    ShortLink.objects.create(code=code, long_url=url, job=self)
                    
                    # Trigger Celery task for job processing if published
                    if self.published:
                        try:
                            from .tasks import process_job_creation, submit_job_to_whatjobs_task
                            from settings.models import ZwayamAmplifyKey
                            import logging
                            
                            # Submit to Zwayam if API key exists
                            api_key = ZwayamAmplifyKey.objects.filter(company=self.company, is_active=True).first()
                            if api_key:
                                process_job_creation.delay(self.id, api_key.api_key)
                            else:
                                logger = logging.getLogger(__name__)
                                logger.warning(f"No active Zwayam API key found for company: {self.company}")
                            
                            # Submit to WhatJobs
                            submit_job_to_whatjobs_task.delay(self.id)
                                
                        except Exception as e:
                            logger = logging.getLogger(__name__)
                            logger.error(f"Error in job processing: {str(e)}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in job save: {str(e)}")
    
    def __str__(self):
        return str(self.company)+' '+str(self.title)[:20]

    class Meta:
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    @staticmethod
    def getById(id):
        if Job.objects.filter(id=id).exists():
            return Job.objects.filter(id=id, published=True).first()
        return None

    @staticmethod
    def getByIdAndCompany(id, company):
        if Job.objects.filter(company=company, id=id, published=True).exists():
            return Job.objects.filter(id=id, published=True).first()
        return None

    @staticmethod
    def getAll():
        return Job.objects.filter(published=True)

    @staticmethod
    def getForCompany(company):
        return Job.objects.filter(company=company)
    
class TemplateJob(models.Model):
    company = models.ForeignKey(Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=True, blank=True)
    # vacancies = models.IntegerField(default=1, null=True, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, verbose_name='Department', on_delete=models.CASCADE)
    owner = models.ForeignKey(Account, default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name='owned_template_jobs')
    assesment = models.ForeignKey(Assesment, null=True, blank=True, verbose_name='Assesment', on_delete=models.CASCADE)
    members = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    type = models.CharField(max_length=20, choices=Job.TYPE, default=Job.FULL_TIME)
    nature = models.CharField(max_length=10, choices=Job.NATURE, default=Job.PHYSICAL)
    educations = models.CharField(null=True, max_length=20, choices=Job.EDUCATION, default=Job.HIGH_SCHOOL)
    speciality = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    description = models.TextField(null=True, blank=True)
    exp_min = models.IntegerField(default=0, null=True, blank=True)
    exp_max = models.IntegerField(default=0, null=True, blank=True)
    salary_min = models.CharField(max_length=50, null=True, blank=True, default='')
    salary_max = models.CharField(max_length=50, null=True, blank=True, default='')
    salary_type = models.CharField(max_length=20, choices=Job.PAY_TYPE, default=Job.MONTHY)
    currency = models.CharField(max_length=10, null=True, blank=True)
    location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(Account, default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_template_jobs')
    document = models.FileField(upload_to='media/template_jobs/', storage=CompanyFileStorage(), default=None, null=True, blank=True)
    # document = models.FileField(
    #     upload_to='template_jobs/documents',
    #     storage=CompanyFileStorage(),
    #     default=None,
    #     null=True,
    #     blank=True
    # )
    job_boards = ArrayField(models.CharField(max_length=50), blank=True)
    pipeline = models.ForeignKey(Pipeline, related_name='template_pipline_id', null=True, blank=True, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    startdate = models.DateField(null=True, blank=True)
    targetdate = models.DateField(null=True, blank=True)
    webform = models.ForeignKey(Webform, related_name='template_webform_id', null=True, blank=True, on_delete=models.CASCADE)
    published = models.BooleanField(default=False)
    dynamic_job_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return str(self.company) + ' ' + str(self.title)[:20]

    class Meta:
        verbose_name = 'Template Job'
        verbose_name_plural = 'Template Jobs'

    @staticmethod
    def getById(id):
        if TemplateJob.objects.filter(id=id).exists():
            return TemplateJob.objects.filter(id=id).first()
        return None

    @staticmethod
    def getByIdAndCompany(id, company):
        if TemplateJob.objects.filter(company=company, id=id).exists():
            return TemplateJob.objects.filter(id=id).first()
        return None

    @staticmethod
    def getAll():
        return TemplateJob.objects.all()

    @staticmethod
    def getForCompany(company):
        return TemplateJob.objects.filter(company=company)
    
class DraftSaveJob(models.Model):
    id = models.AutoField(primary_key=True)
    assesment = models.ForeignKey(Assesment, null=True, blank=True, verbose_name='Assesment', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    created_by =  models.ForeignKey(Account, default=None, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_draftsavejobs')
    dynamic_job_data = models.JSONField(null=True, blank=True)
    webform = models.ForeignKey(Webform,related_name='draft_webform_id', null=True, blank=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return str(self.company)

    class Meta:
        verbose_name = 'draft Job'
        verbose_name_plural = 'draft Jobs'

    @staticmethod
    def getById(id):
        if DraftSaveJob.objects.filter(id=id).exists():
            return DraftSaveJob.objects.filter(id=id).first()
        return None

    @staticmethod
    def getByIdAndCompany(id, company):
        if DraftSaveJob.objects.filter(company=company, id=id).exists():
            return DraftSaveJob.objects.filter(id=id).first()
        return None

    @staticmethod
    def getAll():
        return DraftSaveJob.objects.all()

    @staticmethod
    def getForCompany(company):
        return DraftSaveJob.objects.filter(company=company)

class JobNotes(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(
        Job, default=None, null=False, verbose_name='Job', on_delete=models.CASCADE)
    added_by = models.ForeignKey(
        Account, default=None, null=True, verbose_name='Added by', on_delete=models.SET_NULL)
    note = models.TextField(max_length=1000, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.job)+' '+str(self.added_by)[:20]

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'

    @staticmethod
    def getById(id, job):
        if JobNotes.objects.filter(id=id, job=job).exists():
            return JobNotes.objects.get(id=id)
        return None

    @staticmethod
    def getForJob(Job):
        return JobNotes.objects.filter(job=Job)

    @staticmethod
    def getByIdAndCompany(id, company):
        if JobNotes.objects.filter(id=id).exists():
            note = JobNotes.objects.get(id=id)
            if note.job.company.id == company.id:
                return note
        return None

    @staticmethod
    def getAll():
        return JobNotes.objects.all()
    
class JobBoard(models.Model):
    company = models.ForeignKey(Company, default=None, null=True, blank=True, on_delete=models.CASCADE, related_name='job_board')
    platform = models.CharField(max_length=1000, null=True, blank=True)
    access_token = models.CharField(max_length=1000, null=True, blank=True)
    sub = models.CharField(max_length=1000, null=True, blank=True)
    credentials = models.FileField(upload_to=job_board_credentials_path, storage=CompanyFileStorage(), default=None, null=True, blank=True)
    project_id = models.CharField(max_length=1000, null=True, blank=True)
    google_company_id = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.company) + ' ' + str(self.platform)
    
ACTIVITY_TYPES = [
    ('CANDIDATE_CREATED', 'Candidate Created'),
    ('CANDIDATE_UPDATED', 'Candidate Updated'),
    ('JOB_UPDATED', 'Job Updated'),
    ('JOB_CREATED', 'Job Created'),
    ('STATUS_CHANGED', 'Status Changed'),
    ('INTERVIEW_SCHEDULED', 'Interview Scheduled'),
    ('INTERVIEW_COMPLETED', 'Interview Completed'),
    ('NOTE_ADDED', 'Note Added'),
    ('JOB_ASSOCIATED', 'Job Associated'),
    ('JOB_SUBMITTED', 'Job Submitted'),
    ('CALL_LOGGED', 'Call Logged'),
    ('TASK_CREATED', 'Task Created'),
    ('EVENT_CREATED', 'Event Created'),
    ('EMAIL_SENT', 'Email Sent'),
    ('DOCUMENT_UPLOADED', 'Document Uploaded'),
    ('ASSESSMENT_COMPLETED', 'Assessment Completed'),
    ('OFFER_MADE', 'Offer Made'),
    ('OFFER_ACCEPTED', 'Offer Accepted'),
    ('OFFER_REJECTED', 'Offer Rejected'),
    ('HIRED', 'Hired'),
    ('ONBOARDED', 'Onboarded'),
    ('CANDIDATE_JOB_ASSIGNED', 'Candidate Job Assigned'),
    ('CANDIDATE_JOB_APPLIED', 'Candidate Job Applied'),
    ('APPLIED', 'Applied')
]

class JobTimeline(models.Model):

    from candidates.models import Candidate, Note, Tasks, Events, Call

    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job,  null=True, blank=True, on_delete=models.CASCADE, related_name='job_timeline')
    candidate = models.ForeignKey(Candidate,null=True, blank=True, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    
    # Who performed the action
    performed_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    performed_by_name = models.CharField(max_length=100, null=True, blank=True)  # Fallback for name
    
    # Related objects
    related_note = models.ForeignKey(Note, on_delete=models.CASCADE, null=True, blank=True)
    related_task = models.ForeignKey(Tasks, on_delete=models.CASCADE, null=True, blank=True)
    related_event = models.ForeignKey(Events, on_delete=models.CASCADE, null=True, blank=True)
    related_call = models.ForeignKey(Call, on_delete=models.CASCADE, null=True, blank=True)
    
    interview = models.ForeignKey("interview.Interview", on_delete=models.CASCADE, null=True, blank=True)
    pipeline_stage_status = models.CharField(max_length=255, null=True, blank=True)
    document = models.CharField(max_length=255, null=True, blank=True)
    
    # Additional data for complex activities
    activity_data = models.JSONField(null=True, blank=True)  # Store additional context
    
    # Status tracking
    old_status = models.CharField(max_length=100, null=True, blank=True)
    new_status = models.CharField(max_length=100, null=True, blank=True)
    
    # Timestamps
    activity_date = models.DateTimeField(null=True, blank=True)  # When the actual activity happened
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    # class Meta:
    #     ordering = ['-activity_date', '-created']
    #     verbose_name = 'Candidate Timeline'
    #     verbose_name_plural = 'Candidate Timelines'
    
    # def __str__(self):
    #     return f"{self.candidate} - {self.activity_type} - {self.created.strftime('%Y-%m-%d %H:%M')}"
    
    @staticmethod
    def log_activity( activity_type, title, job, candidate=None, description=None, performed_by=None, 
                    activity_data=None, old_status=None, new_status=None, 
                    related_note=None, related_task=None, related_event=None, related_call=None,
                    activity_date=None, interview=None, pipeline_stage_status=None,document=None):
        """
        Helper method to log timeline activities
        """
        from django.utils import timezone
        
        # Ensure activity_data is JSON serializable
        if activity_data is not None:
            # Convert any non-serializable objects to strings or lists
            serializable_data = {}
            for key, value in activity_data.items():
                if hasattr(value, 'all'):  # Handle ManyRelatedManager
                    serializable_data[key] = [str(item) for item in value.all()]
                elif hasattr(value, '__dict__'):  # Handle model instances
                    serializable_data[key] = str(value)
                else:
                    serializable_data[key] = value
            activity_data = serializable_data

        # Create the timeline entry without the job field
        timeline = JobTimeline.objects.create(
            candidate=candidate,
            job=job,
            activity_type=activity_type,
            title=title,
            description=description,
            performed_by=performed_by,
            # performed_by_name=performed_by.get_full_name() if performed_by else None,
            activity_data=activity_data,
            old_status=old_status,
            new_status=new_status,
            related_note=related_note,
            related_task=related_task,
            related_event=related_event,
            related_call=related_call,
            interview=interview,
            activity_date=activity_date or timezone.now(),
            pipeline_stage_status=pipeline_stage_status,
            document=document
        )

        # Add the job after creation if provided
        # if job is not None:
        #     if isinstance(job, (list, tuple)):
        #         jobs = Job.objects.filter(id__in=job)
        #         if jobs.exists():
        #             timeline.job.set(jobs)
        #     else:
        #         try:
        #             job_obj = Job.objects.get(id=job)
        #             timeline.job.set([job_obj])
        #         except Job.DoesNotExist:
        #             pass

        # return timeline

    
    @staticmethod
    def get_candidate_timeline(candidate, job=None):
        """
        Get timeline for a specific candidate, optionally filtered by job
        """
        queryset = JobTimeline.objects.filter(candidate=candidate)
        if job:
            queryset = queryset.filter(job=job)
        return queryset.select_related('performed_by', 'job', 'related_note', 'related_task', 'related_event', 'related_call')


class WhatJobsJob(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    whatjobs_id = models.CharField(max_length=255)
    jobUrl = models.URLField()
    message = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)