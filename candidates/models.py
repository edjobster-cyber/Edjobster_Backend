from email.policy import default
from pyexpat import model
from django.db import models
from openai._utils import is_list
from common.file_utils import CompanyFileStorage, certificate_upload_path, cover_letter_path, resume_upload_path
from common.models import Country, State, City, NoteType
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q
from job.models import Job
from django.db.models import JSONField
from settings.models import Webform, Contacts, Degree, Designation
from account.models import Company, Account
import uuid
from django.utils import module_loading, timezone

class SubjectSpecialization(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.name)
    
class Skill(models.Model):
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company, default=None, null=True, blank=True, verbose_name='Company', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.name)

class Candidate(models.Model):
    MARITAL_STATUS_CHOICES = [
        ('Married', 'Married'),
        ('Single', 'Single'),
        ('Divorced', 'Divorced'),
        ('Widow', 'Widow'),
    ]
    
    HIGHEST_QUALIFICATION_CHOICES = [
        ('Secondary School', 'Secondary School'),
        ('High School', 'High School'),
        ('Diploma', 'Diploma'),
        ('Post Graduate Diploma', 'Post Graduate Diploma'),
        ('Graduate', 'Graduate'),
        ('Post Graduate', 'Post Graduate'),
        ('Doctorate', 'Doctorate'),
    ]
    
    JOB_TITLE_CHOICES = [
        ('Fresher', 'Fresher'),
        ('Kindergarten/Nursery Teacher', 'Kindergarten/Nursery Teacher'),
        ('Primary Teacher', 'Primary Teacher'),
        ('Secondary teacher', 'Secondary teacher'),
        ('Upper primary teacher', 'Upper primary teacher'),
        ('Secondary teacher', 'Secondary teacher'),
        ('Higher Secondary Teacher', 'Higher Secondary Teacher'),
        ('Physical Education Teacher', 'Physical Education Teacher'),
        ('Assistant Teacher', 'Assistant Teacher'),
        ('Assistant Professor', 'Assistant Professor'),
        ('Assistant Director', 'Assistant Director'),
        ('Director', 'Director'),
        ('Deputy Director', 'Deputy Director'),
        ('Freelancer', 'Freelancer'),
        ('Consultant', 'Consultant'),
        ('Principal', 'Principal'),
        ('Assistant Principal', 'Assistant Principal'),
        ('Founder principal', 'Founder principal'),
        ('In-charge Principal', 'In-charge Principal'),
        ('Subject Matter expert', 'Subject Matter expert'),
        ('Vice Principal', 'Vice Principal'),
        ('Head Master/ Head Mistress', 'Head Master/ Head Mistress'),
        ('Coordinator', 'Coordinator'),
        ('Academic Coordinator', 'Academic Coordinator'),
        ('Primary Coordinator', 'Primary Coordinator'),
        ('Pre-Primary Coordinator', 'Pre-Primary Coordinator'),
        ('Supervisor', 'Supervisor'),
        ('Lecturer', 'Lecturer'),
        ('Guest Lecturer', 'Guest Lecturer'),
        ('Assistant Professor', 'Assistant Professor'),
        ('Associate Professor', 'Associate Professor'),
        ('Receptionist', 'Receptionist'),
        ('Clerk', 'Clerk'),
        ('HR', 'HR'),
        ('Accountant', 'Accountant'),
        ('Dean', 'Dean'),
        ('Content Writer', 'Content Writer'),
        ('Business Development Executive', 'Business Development Executive'),
        ('Finance manager', 'Finance manager'),
        ('Librarian', 'Librarian'),
        ('Physical Education Teacher', 'Physical Education Teacher'),
        ('Coach/Mentor', 'Coach/Mentor'),
        ('Trainer', 'Trainer'),
        ('Teacher Trainer', 'Teacher Trainer'),
        ('Research Scholar', 'Research Scholar'),
        ('Counsellor', 'Counsellor'),
        ('Admission counsellor', 'Admission counsellor'),
        ('Music teacher', 'Music teacher'),
        ('Intern', 'Intern'),
        ('Other', 'Other'),
    ]
    
    CURRICULUM_BOARD_CHOICES = [
        ('ICSE', 'ICSE'),
        ('CBSE', 'CBSE'),
        ('STATE BOARD', 'STATE BOARD'),
        ('IGCSE', 'IGCSE'),
        ('IB', 'IB'),
        ('OTHER', 'OTHER'),
        ('NONE', 'NONE'),
    ]
    
    FUNCTIONAL_AREA_CHOICES = [
        ('Teaching', 'Teaching'),
        ('Administer', 'Administer'),
        ('Manager', 'Manager'),
        ('Head of Department', 'Head of Department'),
        ('Coordinator', 'Coordinator'),
    ]

    BACHELORS_DEGREE_CHOICES = [
        ('B.Ed.', 'B.Ed.'),
        ('D.Ed.', 'D.Ed.'),
        ('B.E.', 'B.E.'),
        ('B.Arch.', 'B.Arch.'),
        ('MBBS', 'MBBS'),
        ('other', 'Other'),
    ]

    id = models.AutoField(primary_key=True)
    # job = models.ForeignKey(Job, default=None, null=True, verbose_name='Job', on_delete=models.SET_NULL)
    account = models.ForeignKey(Account, default=None, null=True, verbose_name='Account', on_delete=models.SET_NULL)
    job = models.ManyToManyField(Job, blank=True, related_name='candidates', verbose_name='Job')
    company = models.ForeignKey(Company, default=None, blank=True, null=True, verbose_name='Company', on_delete=models.SET_NULL)

    # Personal Details
    first_name = models.CharField(max_length=50, null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    alternate_mobile = models.CharField(max_length=15, blank=True)
    email = models.EmailField(null=True, blank=True)
    alternate_email = models.EmailField(blank=True)

    marital_status = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(default=None, null=True)
    gender = models.CharField(max_length=15, blank=True)
    age = models.IntegerField(null=True, blank=True)
    last_applied = models.DateTimeField(null=True, blank=True)

    # Address Info
    street = models.CharField(max_length=100, default=None, null=True)
    country = models.ForeignKey(
        Country, default=None, null=True, verbose_name='Country', on_delete=models.SET_NULL)
    state = models.ForeignKey(
        State, default=None, null=True, verbose_name='State', on_delete=models.SET_NULL)
    city = models.ForeignKey(
        City, default=None, null=True, verbose_name='City', on_delete=models.SET_NULL)
    pincode = models.CharField(max_length=10, default=None, null=True)
    headline = models.CharField(max_length=100, default=None, null=True)
    summary = models.TextField(blank=True,null=True)

    # Professional Details
    highest_qualification = models.CharField(max_length=200, null=True, blank=True)
    job_title = models.CharField(max_length=50, choices=JOB_TITLE_CHOICES, default='Fresher')
    bachelors_degree = models.CharField(max_length=100, choices=BACHELORS_DEGREE_CHOICES, default='B.Ed.')
    # professional_degree = models.CharField(max_length=100, null=True, blank=True)
    professional_degree = models.ForeignKey(Degree,verbose_name="Degree",blank=True,null=True,on_delete=models.SET_NULL)
    job_role = models.CharField(max_length=100, null=True, blank=True)
    curriculum_board = models.CharField(max_length=100, null=True, blank=True)
    functional_area = models.CharField(max_length=20, null=True, blank=True)
    professional_start_date = models.DateField(max_length=30, null=True, blank=True)
    professional_end_date = models.DateField(max_length=30, null=True, blank=True)
    currently_working = models.BooleanField(default=False)
    # professional_certificate = models.FileField(upload_to='media/resume/', default=None, null=True, blank=True)
    professional_certificate = models.CharField(max_length=250,blank=True,null=True)
    
    STAGES = [
        ('Associated-Screeening','Associated-Screeening' ),
        ('Applied','Applied' ),
        ('Shortlisted','Shortlisted'),
        ('Interview','Interview') ,
        ('Offered','Offered') ,
        ('Hired','Hired' ),
        ('Onboarded','Onboarded'),
    ]

    QUALIFICAION = [
        ('Secondary School', 'Secondary School'), 
        ('High School', 'High School'), 
        ('Diploma', 'Diploma'), 
        ('Post Graduate Diploma', 'Post Graduate Diploma'), 
        ('Graduate', 'Graduate'), 
        ('Post Graduate', 'Post Graduate'), 
        ('Doctorate', 'Doctorate')
    ]

    # The above code is not a valid Python code. It seems to be incomplete or incorrect.
    CURRENT_JOB_TITLE = [
        ('Fresher', 'Fresher'), 
        ('Kindergarten/Nursery Teacher', 'Kindergarten/Nursery Teacher'), 
        ('Primary-Teacher', 'Primary Teacher'),
        ('Secondary-teacher', 'Secondary teacher'), 
        ('Upper-primary-teacher', 'Upper primary teacher'), 
        ('Higher-Secondary-Teacher', 'Higher Secondary Teacher'),
        ('Physical-Education-Teacher', 'Physical Education Teacher'), 
        ('Assistant-Teacher', 'Assistant Teacher'), 
        ('Assistant-Professor', 'Assistant Professor'), 
        ('Assistant-Director', 'Assistant Director'), 
        ('Director', 'Director'), 
        ('Deputy-Director', 'Deputy Director'), 
        ('Freelancer', 'Freelancer'), 
        ('Consultant', 'Consultant'), 
        ('Principal', 'Principal'), 
        ('Assistant-Principal', 'Assistant Principal'), 
        ('Founder-principal', 'Founder principal'), 
        ('In-charge-Principal', 'In-charge Principal'), 
        ('Subject-Matter-expert', 'Subject Matter expert'), 
        ('Vice-Principal', 'Vice Principal'), 
        ('Head-Master/Head-Mistress', 'Head Master/ Head Mistress'), 
        ('Coordinator', 'Coordinator'), 
        ('Academic-Coordinator', 'Academic Coordinator'), 
        ('Primary-Coordinator', 'Primary Coordinator'), 
        ('Pre-Primary/Coordinator', 'Pre-Primary Coordinator'), 
        ('Supervisor', 'Supervisor'), 
        ('Lecturer', 'Lecturer'), 
        ('Guest-Lecturer', 'Guest Lecturer'), 
        ('Assistant-Professor', 'Assistant Professor'), 
        ('Associate-Professor', 'Associate Professor'), 
        ('Receptionist', 'Receptionist'), 
        ('Clerk', 'Clerk'), 
        ('HR', 'HR'), 
        ('Accountant', 'Accountant'), 
        ('Dean', 'Dean'), 
        ('Content Writer', 'Content Writer'), 
        ('Business Development Executive', 'Business Development Executive'), 
        ('Finance manager', 'Finance manager'), 
        ('Librarian', 'Librarian'), 
        ('Physical Education Teacher', 'Physical Education Teacher'), 
        ('Coach/Mentor', 'Coach/Mentor'), 
        ('Trainer', 'Trainer'), 
        ('Teacher Trainer', 'Teacher Trainer'), 
        ('Research Scholar', 'Research Scholar'), 
        ('Counsellor', 'Counsell'),
        ('Admission counsellor', 'Admission counsellor'),
        ('Music teacher', 'Music teacher'),
        ('Intern', 'Intern'),
        ('Other', 'Other'),
    ]
    # SUBJECT_CHOICES = [
    #     ('English', 'English'),
    #     ('Hindi', 'Hindi'),
    #     ('Math', 'Math'),
    #     ('Science', 'Science'),
    #     ('Social Science', 'Social Science'),
    #     ('Geography', 'Geography'),
    #     ('History', 'History'),
    #     ('Political Science', 'Political Science'),
    #     ('Humanities', 'Humanities'),
    #     ('Physics', 'Physics'),
    #     ('Chemistry', 'Chemistry'),
    #     ('Biology', 'Biology'),
    #     ('Botany', 'Botany'),
    #     ('Zoology', 'Zoology'),
    #     ('Sanskrit', 'Sanskrit'),
    #     ('Spanish', 'Spanish'),
    #     ('French', 'French'),
    #     ('Russian', 'Russian'),
    #     ('Fine Arts', 'Fine Arts'),
    #     ('Art and Craft', 'Art and Craft'),
    #     ('Music', 'Music'),
    #     ('Visual Arts', 'Visual Arts'),
    #     ('Sports Coach', 'Sports Coach'),
    #     ('Physical Education', 'Physical Education'),
    #     ('Other', 'Other'),
    # ]

    NOTICE_PERIOD_CHOICES = [
        ('Immediate joining', 'Immediate joining'),
        ('15 days', '15 days'),
        ('1 Month', '1 Month'),
        ('2 Month', '2 Month'),
        ('3 Month', '3 Month'),
        ('4 Month', '4 Month'),
        ('5 Month', '5 Month'),
        ('6 Month', '6 Month'),
    ]

    # subjects = ArrayField(models.CharField(max_length=1000, choices=SUBJECT_CHOICES), blank=True, null=True)
    subjects = models.ManyToManyField(SubjectSpecialization, blank=True)
    notice_period = models.CharField(max_length=20, null=True, blank=True)

    exp_years = models.IntegerField(null=True,blank=True)
    exp_months = models.IntegerField(null=True,blank=True)

    # current_job_title = models.CharField(max_length=100, default='Fresher')
    current_job_title = models.ForeignKey(Designation,verbose_name="Designation", on_delete=models.SET_NULL,null=True,blank=True)

    # Addition of admission_date and graduation_date
    admission_date = models.DateField(default=None,null=True, blank=True)
    graduation_date = models.DateField(default=None,null=True, blank=True)

    cur_job = models.CharField(max_length=100, null=True, blank=True)
    cur_employer = models.CharField(max_length=100, null=True, blank=True)
    current_salary = models.CharField(max_length=50, null=True, blank=True, default='')
    expected_salary = models.CharField(max_length=50, null=True, blank=True, default='')
    salary_currency = models.CharField(max_length=150, null=True, blank=True)

    pipeline_stage_status = models.CharField(max_length=100, null=True, blank=True)
    pipeline_stage = models.CharField(max_length=100, null=True, blank=True, default='Applied')
    certifications = models.TextField(null=True, blank=True)
    fun_area = models.TextField(null=True, blank=True)
    skills = ArrayField(models.CharField(max_length=100), blank=True, default=list)
    summary = models.TextField(null=True, blank=True)
    #experience
    user_experiences = models.JSONField(default=list)
    
    #education
    user_educations = models.JSONField(default=list)

    #attachements
    # resume = models.FileField(upload_to='media/resume/', default=None, null=True, blank=True)
    # cover_letter = models.FileField(upload_to='media/cover_letter/', default=None, null=True, blank=True) 
    # certificate = models.FileField(upload_to='media/resume/', default=None, null=True, blank=True)   
    resume = models.FileField(
    upload_to=resume_upload_path,
    storage=CompanyFileStorage(),
    default=None,
    null=True,
    blank=True
    )
    cover_letter = models.FileField(
        upload_to=cover_letter_path,
        storage=CompanyFileStorage(),
        default=None,
        null=True,
        blank=True
    )
    certificate = models.FileField(
        upload_to=certificate_upload_path,
        storage=CompanyFileStorage(),
        default=None,
        null=True,
        blank=True
    )
    resume_parse_data = JSONField(null=True, default=None)
    addional_fields = models.JSONField(null=True, blank=True, default=list)
    assessment_data = models.JSONField(null=True, blank=True, default=list)
    webform = models.ForeignKey(Webform, on_delete=models.SET_NULL, null=True, blank=True)
    webform_candidate_data = models.JSONField(null=True, blank=True)
    
    resume_user = models.CharField(max_length=150, null=True, blank=True)
    resume_data = models.JSONField(null=True, blank=True, default=list)

    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return str(self.job)+' '+str(self.email)[:30]

    class Meta:
        verbose_name = 'Candidate'
        verbose_name_plural = 'Candidates'

    @staticmethod
    def getById(id):
        if Candidate.objects.filter(id=id).exists():
            return Candidate.objects.get(id=id)
        return None

    @staticmethod
    def getByIdAndCompany(id, company):
        if Candidate.objects.filter(id=id).exists():
            candidate = Candidate.objects.get(id=id)
            # if candidate.job.company.id == company.id:
            #     return candidate
            if candidate.job.filter(company=company).exists():
                return candidate
        return None

    @staticmethod
    def getByCompany(company):
        return Candidate.objects.filter(job__company=company)

    @staticmethod
    def getByJob(job):
        return Candidate.objects.filter(job=job)

    @staticmethod
    def getByEmail(job, email):
        return Candidate.objects.filter(job=job).filter(email=email)

    @staticmethod
    def getByPhone(job, mobile):
        return Candidate.objects.filter(job=job).filter(mobile=mobile)

class CandidateExperience(models.Model):

    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, null=True, verbose_name='candidate', on_delete=models.CASCADE)
    employer = models.CharField(max_length=100, null=True, blank=True)
    jobProfile = models.CharField(max_length=100, null=True, blank=True)
    skills = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateField(max_length=30, null=True, blank=True)
    end_date = models.DateField(max_length=30, null=True, blank=True)
    jobDescription = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.employer)+' exp'

class CandidateQualification(models.Model):

    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, null=True, verbose_name='candidate', on_delete=models.CASCADE)
    institute_name = models.TextField(max_length=300, null=True, blank=True)
    degree = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    start_date = models.DateField(max_length=30, null=True, blank=True)
    end_date = models.DateField(max_length=30, null=True, blank=True)
    grade = models.CharField(max_length=30, null=True, blank=True)
    gradeType = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return str(self.id)+' '+str(self.candidate)
    
PRIORITY_FIELDS = [
    ('HIGH', 'high'),
    ('HIGHEST', 'highest'),
    ('LOW', 'low'),
    ('LOWEST', 'lowest'),
    ('NORMAL', 'normal'),
]
TASK_REPEAT = [
    ('DAILY', 'daily'),
    ('WEEKLY', 'weekly'),
    ('MONTHLY', 'monthly'),
    ('YEARLY', 'yearly'),
]
TASK_ALERT = [
    ('EMAIL', 'email'),
    ('POP-UP', 'pop-up'),
]
STATUS_FIELDS = [
    ('NOT STARTED', 'not started'),
    ('DEFERRED', 'deferred'),
    ('IN PROGRESS', 'in progress'),
    ('COMPLETED', 'completed'),
    ('WAITING ON SOMEONE ELSE', 'waiting on someone else'),
]
CURRENCY = [
    ('INR','inr'),
    ('SAR','sar'),
    ('AED','aed'),
    ('ELR','elr'),
    ('MXN','mxn'),
    ('GBP','gbp'),
]

TODO_TYPE = [
    ('TASKS', 'Tasks'),
    ('EVENTS', 'Events'),
    ('CALLS', 'Calls'),
]

class Tasks(models.Model):
    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, null=True, blank=True, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, null=True, blank=True, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255, null=True, blank=True)
    duedate = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_FIELDS, null=True, blank=True)
    owner = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    when_date = models.DateField(null=True, blank=True)
    when_time = models.TimeField(null=True, blank=True)
    task_repeat = models.CharField(max_length=20, choices=TASK_REPEAT, null=True, blank=True)
    task_alert = models.CharField(max_length=20, choices=TASK_ALERT, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    repeat_type = models.CharField(max_length=20, choices=TASK_REPEAT, null=True, blank=True) 
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    related_to = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_FIELDS, null=True, blank=True)
    currency = models.CharField(max_length=255, choices=CURRENCY, null=True, blank=True)
    email_notification = models.BooleanField(default=False)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    description = models.TextField(null=True, blank=True)
    todo_type = models.CharField(max_length=50, choices=TODO_TYPE, default="TASKS")
    completed = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Task: {self.subject}"
    
MEETING_VENUE = [
    ('CLIENT LOCATION', 'client location'),
    ('BUSINESS LOCATION', 'business location'),
]
RELATED_TO = [
    ('NONE', 'none'),
    ('CANDIDATE', 'candidate'),
    ('CONTACT', 'contact'),
    ('OTHERS', 'others'),
]
REPEAT_FIELDS = [
    ('NONE', 'None'),
    ('DAILY', 'Daily'),
    ('WEEKLY', 'Weekly'),
    ('MONTHLY', 'Monthly'),
    ('YEARLY', 'Yearly'),
]

REMINDER_FIELDS = [
    ('NONE', 'None'),
    ('ONCE', 'Once'),
    ('DAILY', 'Daily'),
    ('WEEKLY', 'Weekly'),
    ('BEFORE_EVENT', 'Before Event'),
]

class Events(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    event_name = models.CharField(max_length=255, null=True, blank=True)
    meeting_venue = models.CharField(max_length=50, choices=MEETING_VENUE, null=True, blank=True)  
    location = models.TextField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    from_date = models.DateTimeField(null=True, blank=True)
    to_date = models.DateTimeField(null=True, blank=True)
    host = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    related_to = models.CharField(max_length=50, choices=RELATED_TO, null=True, blank=True) 
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True, blank=True) 
    participants = models.ManyToManyField(Contacts, blank=True)  
    currency = models.CharField(max_length=50, choices=CURRENCY, null=True, blank=True)  
    description = models.TextField(null=True, blank=True)
    repeat = models.CharField(max_length=50, choices=REPEAT_FIELDS, null=True, blank=True)
    reminders = models.CharField(max_length=50, choices=REMINDER_FIELDS, null=True, blank=True)
    todo_type = models.CharField(max_length=50, choices=TODO_TYPE, default="EVENTS")
    completed = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Event: {self.event_name} ({self.from_date} - {self.to_date})"

CALL_TYPE_CHOICES = [
    ('INBOUND', 'Inbound'),
    ('OUTBOUND', 'Outbound'),
]

CALL_PURPOSE_CHOICES = [
    ('NONE', 'None'),
    ('ADMINISTRATIVE', 'Administrative'),
    ('DEMO', 'Demo'),
    ('NEGOTIATION', 'Negotiation'),
    ('PROJECT', 'Project'),
    ('PROSPECTING', 'Prospecting'),
    ('SUPPORT', 'Support'),
]

CALL_STATUS = [
    ('CURRENTCALL', 'Current Call'),
    ('COMPLETEDCALL', 'Completed Call'),
    ('SCHEDULECALL', 'Schedule Call'),
]

RELATED_TO_CHOICES = [
    ('JOB OPENING', 'Job Opening'),
    # Add other related options as needed
]

CALL_REMINDER_FIELDS = [
    ('NONE', 'None'),
    ('5_MIN', '5 minutes before'),
    ('10_MIN', '10 minutes before'),
    ('15_MIN', '15 minutes before'),
    ('30_MIN', '30 minutes before'),
    ('1_HOUR', '1 hour before'),
    ('2_HOURS', '2 hours before'),
    ('1_Day', '1 day before'),
    ('2_Days', '2 days before'),
]

class Call(models.Model):  # Singular form
    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True, blank=True, related_name='calls_as_candidate')
    subject = models.CharField(max_length=255, null=False, blank=False)
    call_type = models.CharField(max_length=50, choices=CALL_TYPE_CHOICES, null=True, blank=True)
    call_purpose = models.CharField(max_length=50, choices=CALL_PURPOSE_CHOICES, null=True, blank=True)
    contact_name_contact = models.ForeignKey(Contacts, on_delete=models.CASCADE, null=True, blank=True)
    contact_name_candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True, blank=True, related_name='calls_as_contact')
    related_to = models.CharField(max_length=255, null=True, blank=True)    
    posting_title = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)
    call_details = models.CharField(max_length=50, choices=CALL_STATUS, null=True, blank=True)
    call_timer = models.DurationField(null=True, blank=True)
    call_result = models.CharField(max_length=255, null=True, blank=True)
    call_start_time = models.DateTimeField(null=True, blank=True)
    call_duration = models.TimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    billable = models.BooleanField(default=False)
    owner = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    reminders = models.CharField(max_length=50, choices=CALL_REMINDER_FIELDS, null=True, blank=True)
    todo_type = models.CharField(max_length=50, choices=TODO_TYPE, default="CALLS")
    completed = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Call: {self.subject} - {self.call_type}"

class Note(models.Model):
    candidate  = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    note = models.TextField(max_length=1000, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.candidate)+' '+str(self.candidate)[:20]

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'

    @staticmethod
    def getById(id, candidate):
        if Note.objects.filter(id=id, candidate=candidate).exists():
            return Note.objects.get(id=id)
        return None

    @staticmethod
    def getForCandidate(candidate):
        return Note.objects.filter(candidate=candidate)

    @staticmethod
    def getByIdAndCompany(id, company):
        if Note.objects.filter(id=id).exists():
            note = Note.objects.get(id=id)
            # Check if any of the candidate's jobs belong to the given company
            if note.candidate.job.filter(company=company).exists():
                return note
        return None

    @staticmethod
    def getAll():
        return Note.objects.all()
    

class ResumeFiles(models.Model):
    id = models.AutoField(primary_key=True)
    resume = models.FileField(upload_to='media/resume/', default=None, null=True, blank=True)  
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.candidate)+' '+str(self.added_by)[:20]

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'


class ApplicantWebForm(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job, verbose_name='Job', on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, verbose_name='Candidate', on_delete=models.CASCADE)
    webform = ArrayField(models.CharField(max_length=1000), blank=True, null=True)
    # assingment = JSONField(blank=True, null=True, default=dict)
    assingment = ArrayField(models.JSONField(null=True, blank=True, default=dict), null=True, blank=True)
    form = JSONField(null=True, default=None)

    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ApplicantWebForm'
        verbose_name_plural = 'ApplicantWebForms'

    def __str__(self):
        return str(self.job)+str(self.id)[:20]
    
class Mail(models.Model):
    sender = models.ForeignKey(Account, verbose_name='account', on_delete=(models.CASCADE))
    receiver = ArrayField(models.CharField(max_length=1000), null=True, blank=True)
    subject = models.CharField(max_length=200, null=True, blank=True)
    date_time =  models.DateTimeField(auto_now=True)
    body = models.TextField(null=True, blank=True)

    class Meta : 
        verbose_name = 'Mail'

    def __str__(self):
        return str(self.sender)
    
class EmailSettings(models.Model):
    user_id = models.ForeignKey(Account, verbose_name='account', on_delete=(models.CASCADE))
    company = models.ForeignKey(Company, null=True, blank=True, verbose_name='company', on_delete=(models.CASCADE))
    sender_mail = models.EmailField()
    auth_password = models.CharField(max_length=255)
    email_backend = models.CharField(max_length=255, default='django_smtp_ssl.SSLEmailBackend')
    email_host = models.CharField(max_length=255)
    email_port = models.IntegerField(default=465)
    email_tls = models.BooleanField(default=True)
    email_ssl = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class Candidatewithoutlogin(models.Model):
    id = models.AutoField(primary_key=True)
    # job = models.ForeignKey(Job, default=None, null=True, verbose_name='Job', on_delete=models.SET_NULL)
    job = models.ManyToManyField('job.Job', default=None, verbose_name='Job')
    login_email = models.EmailField(null=True, blank=True)

    # Personal Details
    first_name = models.CharField(max_length=50, null=True, blank=True)
    source = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    alternate_mobile = models.CharField(max_length=15, blank=True)
    email = models.EmailField(null=True, blank=True)
    alternate_email = models.EmailField(blank=True)

    marital_status = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(default=None, null=True)
    gender = models.CharField(max_length=15, blank=True)
    age = models.IntegerField(null=True, blank=True)
    last_applied = models.DateTimeField(null=True, blank=True)

    # Address Info
    street = models.CharField(max_length=500, default=None, null=True)
    country = models.CharField(max_length=100,blank=True,null=True)
    state = models.CharField(max_length=100,blank=True,null=True)
    city = models.CharField(max_length=100,blank=True,null=True)
    pincode = models.CharField(max_length=10, default=None, null=True)
    headline = models.CharField(max_length=100, default=None, null=True)
    summary = models.TextField(blank=True,null=True)

    # Professional Details
    highest_qualification = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    bachelors_degree = models.CharField(max_length=100, null=True, blank=True)
    professional_degree = models.CharField(max_length=100,blank=True,null=True)
    job_role = models.CharField(max_length=100, null=True, blank=True)
    curriculum_board = models.CharField(max_length=100, null=True, blank=True)
    functional_area = models.CharField(max_length=20, null=True, blank=True)
    professional_start_date = models.DateField(max_length=30, null=True, blank=True)
    professional_end_date = models.DateField(max_length=30, null=True, blank=True)
    currently_working = models.BooleanField(default=False)
    # professional_certificate = models.FileField(upload_to='media/resume/', default=None, null=True, blank=True)
    professional_certificate = models.FileField(
        upload_to='candidates/professional_certificates',
        storage=CompanyFileStorage(),
        null=True,
        blank=True
    )

    subjects = models.CharField(max_length=100, null=True, blank=True)
    notice_period = models.CharField(max_length=20, null=True, blank=True)

    exp_years = models.IntegerField(null=True, blank=True)
    exp_months = models.IntegerField(null=True, blank=True)

    current_job_title = models.CharField( max_length=100, blank=True, null=True)

    # Addition of admission_date and graduation_date
    admission_date = models.DateField(default=None, null=True, blank=True)
    graduation_date = models.DateField(default=None, null=True, blank=True)

    cur_job = models.CharField(max_length=100, null=True, blank=True)
    cur_employer = models.CharField(max_length=100, null=True, blank=True)

    pipeline_stage_status = models.CharField(max_length=100, null=True, blank=True)
    pipeline_stage = models.CharField(max_length=100, null=True, blank=True, default='Applied')
    certifications = models.TextField(null=True, blank=True)
    fun_area = models.TextField(null=True, blank=True)
    skills = models.CharField(max_length=1000,blank=True,null=True)
    summary = models.TextField(null=True, blank=True)
    #experience
    user_experiences = models.JSONField(default=list)
    
    #education
    user_educations = models.JSONField(default=list)

    #attachements
    resume = models.URLField(max_length=500)
    cover_letter = models.FileField(upload_to='media/cover_letter/', default=None, null=True, blank=True) 
    certificate = models.FileField(upload_to='media/resume/', default=None, null=True, blank=True)   
    # cover_letter = models.FileField(
    #     upload_to='candidates/cover_letters',
    #     storage=CompanyFileStorage(),
    #     null=True,
    #     blank=True
    # )
    # certificate = models.FileField(
    #     upload_to='candidates/certificates',
    #     storage=CompanyFileStorage(),
    #     null=True,
    #     blank=True
    # )
    resume_parse_data = JSONField(null=True, default=None)
    addional_fields = models.JSONField(null=True, blank=True, default=list)
    assessment_data = models.JSONField(null=True, blank=True, default=list)
    webform = models.ForeignKey(Webform, on_delete=models.CASCADE, null=True, blank=True)

    updated = models.DateTimeField(auto_now=True, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.job)+' '+str(self.email)[:30]

    @staticmethod
    def getById(id):
        if Candidate.objects.filter(id=id).exists():
            return Candidate.objects.get(id=id)
        return None

    @staticmethod
    def getByIdAndCompany(id, company):
        if Candidate.objects.filter(id=id).exists():
            candidate = Candidate.objects.get(id=id)
            if candidate.job.filter(company=company).exists():
                return candidate
        return None

    @staticmethod
    def getByCompany(company):
        return Candidate.objects.filter(job__company=company)

    @staticmethod
    def getByJob(job):
        return Candidate.objects.filter(job=job)

    @staticmethod
    def getByEmail(job, email):
        return Candidate.objects.filter(job=job).filter(email=email)

    @staticmethod
    def getByPhone(job, mobile):
        return Candidate.objects.filter(job=job).filter(mobile=mobile)
    
ACTIVITY_TYPES = [
    ('CANDIDATE_CREATED', 'Candidate Created'),
    ('CANDIDATE_UPDATED', 'Candidate Updated'),
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
]

class CandidateTimeline(models.Model):
    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='timeline_activities')
    job = models.ManyToManyField(Job,  null=True, blank=True)
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
    pipeline_stage = models.CharField(max_length=255, null=True, blank=True)
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
    def log_activity(candidate, activity_type, title, description=None, performed_by=None, 
                    job=None, activity_data=None, old_status=None, new_status=None, 
                    related_note=None, related_task=None, related_event=None, related_call=None,
                    activity_date=None, interview=None, pipeline_stage_status=None,document=None,pipeline_stage=None):
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
        timeline = CandidateTimeline.objects.create(
            candidate=candidate,
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
            document=document,
            pipeline_stage=pipeline_stage
        )

        # Add the job after creation if provided
        if job is not None:
            if isinstance(job, (list, tuple)):
                jobs = Job.objects.filter(id__in=job)
                if jobs.exists():
                    timeline.job.set(jobs)
            else:
                try:
                    job_obj = Job.objects.get(id=job)
                    timeline.job.set([job_obj])
                except Job.DoesNotExist:
                    pass

        return timeline
    
class DailyEmailQuota(models.Model):
    company = models.ForeignKey(Company, verbose_name='company', on_delete=models.CASCADE)
    user = models.ForeignKey(Account, verbose_name='user', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    daily_limit = models.IntegerField(default=2)  # Default daily limit
    emails_sent = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'user', 'date']
        verbose_name = 'Daily Email Quota'
        verbose_name_plural = 'Daily Email Quotas'

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.emails_sent}/{self.daily_limit}"

    @property
    def emails_remaining(self):
        return max(0, self.daily_limit - self.emails_sent)

    @property
    def can_send_emails(self):
        return self.emails_sent < self.daily_limit

    @staticmethod
    def get_or_create_quota(user, company):
        """Get or create today's quota for a user and company"""
        from datetime import date
        quota, created = DailyEmailQuota.objects.get_or_create(
            company=company,
            user=user,
            date=date.today(),
            defaults={'daily_limit': 500, 'emails_sent': 0}
        )
        return quota

    @staticmethod
    def can_send_bulk_emails(user, company, email_count):
        """Check if user can send specified number of emails"""
        quota = DailyEmailQuota.get_or_create_quota(user, company)
        return quota.emails_remaining >= email_count

    @staticmethod
    def consume_quota(user, company, email_count):
        """Consume email quota for sending emails"""
        quota = DailyEmailQuota.get_or_create_quota(user, company)
        if quota.emails_remaining >= email_count:
            quota.emails_sent += email_count
            quota.save()
            return True
        return False

    @staticmethod
    def get_remaining_emails(user, company):
        """Get remaining emails for today"""
        quota = DailyEmailQuota.get_or_create_quota(user, company)
        return quota.emails_remaining

class SavedJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Account, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('candidate', 'job')

class CandidateResume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    resume = models.FileField(upload_to='media/resumes/')
    # resume = models.FileField(
    #     upload_to='candidates/resumes',
    #     storage=CompanyFileStorage(),
    #     null=True,
    #     blank=True
    # )
    extracted_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CandidateProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Account, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='media/profile_photos/', null=True, blank=True)
    # profile_photo = models.ImageField(
    #     upload_to='candidates/profile_photos',
    #     storage=CompanyFileStorage(),
    #     null=True,
    #     blank=True
    # )
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RJMSAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(Candidate, on_delete=models.SET_NULL, null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)
    # sms_score = models.IntegerField(default=0)
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CoresignalPreview(models.Model):
    coresignal_id = models.CharField(max_length=255, unique=True)
    data = models.JSONField()
    is_list = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CoresignalCandidateStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coresignal_candidate = models.ForeignKey(CoresignalPreview,on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=255, choices=[("sortlisted", "Sortlisted"), ("rejected", "Rejected")])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CoresignalCandidateVisiteCompany(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, verbose_name="Company", on_delete=models.CASCADE)
    visitescandidatelist = models.ManyToManyField(CoresignalPreview, verbose_name="Visited Candidates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def __str__(self):
    #     return f"{self.company.name if self.company else 'Unknown Company'} - Visited Candidates"
