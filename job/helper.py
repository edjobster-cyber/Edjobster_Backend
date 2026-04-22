
from django.shortcuts import get_object_or_404
from django.db.models import F
from account import serializer
from account.models import JOB_CATEGORIES, Account, Company, TokenEmailVerification, TokenResetPassword
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import authenticate
from common.encoder import decode
from common.utils import isValidUuid, getErrorResponse
from common.models import Country, State, City
import json, requests
from job.decorators import check_subscription_and_credits, deduct_credit_decorator
from settings.models import CreditHistory, CreditWallet, Degree, Department, Location, Pipeline, Webform
from candidates.models import Candidate, Note, Skill
from .models import AssesmentCategory, Assesment, AssesmentQuestion, Job, JobNotes, TemplateJob, JobBoard, JobTimeline, DraftSaveJob
from .serializer import AssesmentSerializer, AssesmentCategorySerializer, AssesmentQuestionListSerializer, AssesmentQuestionDetailsSerializer, JobListSerializer, JobDetailsSerializer, JobNotesSerializer, TemplateJobSerializer, JobsCarrerSerializer, JobBoardSerializer, JobTimelineSerializer, DraftSaveJobSerializer
from account.serializer import CompanySerializer
from django.core.paginator import Paginator
from settings.models import PipelineStage,Subscription
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status
from google.cloud import talent
from google.cloud.talent_v4beta1 import types
from google.oauth2 import service_account

PAGE_SIZE = 30
#ASSESMENT
def getAssesmentCategories(request):
    user = request.user

    role = 'superuser' if user.is_superuser else 'admin' if user.role == Account.ADMIN else 'user'
    if user.is_superuser:
        assesments = AssesmentCategory.objects.all()
    else:
        assesments = AssesmentCategory.objects.filter(Q(company__id=user.company_id) | Q(company__isnull=True))

    serializer = AssesmentCategorySerializer(assesments, many=True)

    return {
        'code': 200,
        'data': serializer.data,
        'role': role
    }    

def saveAssesmentCategory(request):

    company = Company.getByUser(request.user)    
    # company = data.get('company', company)   
    # company = Company.getById(company)    
      
    data = request.data    
    name = data.get('name', None)   

    if not name:
        return getErrorResponse('Category name required')

    id = data.get('id', None)

    if id:
        category = AssesmentCategory.getById(id, company)
        if not category:
            return getErrorResponse( 'Assesment category not found')

        if category.name != name and AssesmentCategory.getByName(name=name, company=company):
            return getErrorResponse('Assesment category with name '+name+' already exists.')
    else:
        if AssesmentCategory.getByName(name=name, company=company):
            return getErrorResponse('Assesment category with name '+name+' already exists.')

        category = AssesmentCategory()   
        category.company = company
    
    category.name = name
    category.save()

    return getAssesmentCategories(request)

def deleteAssesmentCategory(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        category = AssesmentCategory.getById(id, company)
        if not category:
            return getErrorResponse('Assesment category not found')

        category.delete()
        return {
            'code': 200,
            'msg': 'Assesment category deleted succesfully!',
            'data': getAssesmentCategories(request)['data']
        }

    return getErrorResponse('Invalid request')

def getAssesments(request):

    user = request.user

    if user.is_superuser:
        assesments = Assesment.objects.all().order_by('-updated')
    else:
        assesments = Assesment.objects.filter(company__id=user.company_id).order_by('-updated')
    serializer = AssesmentSerializer(assesments, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }    

def saveAssesment(request):
    data = request.data    
    company = Company.getByUser(request.user)  
    created_by = request.user
      
    form = data.get('form', None)   
    dynamic_assessment_data = data.get("dynamic_assessment_data", None)
    name = data.get("name", None)
    category = data.get("category", None)

    category = get_object_or_404(AssesmentCategory, id=category)

    if not form:
        return {
            'code': 400,
            'msg': 'Empty Form'
        }
        
    # Check if assessment with same name already exists for this company
    if Assesment.objects.filter(company=company, name=name).exists():
        return {
            'code': 400,
            'msg': 'An assessment with this name already exists for your company. Please choose a different name.'
        }

    assesment = Assesment()   
    assesment.company = company
    assesment.created_by = created_by
    assesment.name = name
    assesment.category = category
    assesment.form = form
    assesment.dynamic_assessment_data = dynamic_assessment_data
    
    assesment.save()
    
    from .serializer import AssesmentSerializer
    serializer = AssesmentSerializer(assesment)
    return {
        'code': 200,
        'data': serializer.data
    }

def deleteAssesment(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        assesment = Assesment.getById(id, company)
        if not assesment:
            return getErrorResponse('Assesment not found')

        assesment.delete()
        return {
            'code': 200,
            'msg': 'Assesment deleted succesfully!',
            'data': getAssesments(request)['data']
        }

    return getErrorResponse('Invalid request') 


def getAssesmentDetails(request):

    company = Company.getByUser(request.user)
    id = request.GET.get('id')

    assesment = Assesment.getByAssessmentId(id=id)
    if not assesment:
        return getErrorResponse('Assesment not found')

    questions = AssesmentQuestion.getForAssesment(assesment=assesment)

    assesmentSerializer = AssesmentSerializer(assesment, many=False)
    questionSerializer = AssesmentQuestionDetailsSerializer(questions, many=True)

    return {
        'code': 200,
        'assesment': assesmentSerializer.data,
        'questions': questionSerializer.data
    }    

def getAssesmentQuestions(assesment):
    questions = AssesmentQuestion.getForAssesment(assesment=assesment)
    questionSerializer = AssesmentQuestionDetailsSerializer(questions, many=True)
    return {
        'code': 200,
        'questions': questionSerializer.data
    }  

def getAssesmentCareer(request,id):
    # Fetch assessment without company bound check for career/public use
    assesment = Assesment.getByAssessmentId(id)
    if not assesment:
        return getErrorResponse('Assesment not found')

    form = assesment.form or {}
    # questions = form.get('questions', []) if isinstance(form, dict) else []
    filtered_questions = []
    for q in form:
        if not isinstance(q, dict):
            continue
        options = q.get('options', [])
        # Keep only option label
        filtered_options = []
        if isinstance(options, list):
            for opt in options:
                if isinstance(opt, dict) and 'text' in opt:
                    filtered_options.append({'text': opt.get('text')})
        filtered_questions.append({
            'id': q.get('id'),
            'type': q.get('type'),
            'question': q.get('question'),
            'required': q.get('required', False),
            'options': filtered_options
        })

    return {
        'code': 200,
        'data': {
            'questions': filtered_questions
        }
    }

def saveAssesmentQuestion(request):

    company = Company.getByUser(request.user)
    assesment = request.data.get('assesment')

    assesment = Assesment.getById(id=assesment, company=company)
    if not assesment:
        return getErrorResponse( 'Assesment not found')
    
    data = request.data    
    type = data.get('type', None)   
    question_text = data.get('question', None)   

    if not question_text:
        return getErrorResponse('question required')
    
    if not type or type not in AssesmentQuestion.TYPES:
        return getErrorResponse('Invalid type')

    id = data.get('id', None)
        
    if id:
        question = AssesmentQuestion.getById(id, assesment)
        if not question:
            return getErrorResponse('Assesment question not found')
    else:
        question = AssesmentQuestion()   
        question.assesment = assesment

    if not type or not question or type not in AssesmentQuestion.TYPES:
        return getErrorResponse('Invalid request')

    if type == AssesmentQuestion.RADIO or type == AssesmentQuestion.SELECT:
        marks = data.get('marks', None)   
        answer = data.get('answer', None)   
        options = data.get('options', None)

        if not marks:
            return getErrorResponse('marks required')

        if not answer:
            return getErrorResponse('answer required')

        if not options or not isinstance(options, list):
            return getErrorResponse('options required')

        question.marks = marks
        question.answer = answer
        question.options = options
    
    elif type == AssesmentQuestion.CHECK:
        options = data.get('options', None)

        if not options or not isinstance(options, list):
            return getErrorResponse('options required')

        question.options = options  
    else:
        question.marks = 0
        question.answer = ""
        question.options = []

    question.type = type
    question.question = question_text
    question.save()

    return getAssesmentQuestions(assesment=assesment)

def deleteAssesmentQuestion(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        question = AssesmentQuestion.getByCompany(id, company)
        if not question:
            return getErrorResponse('Question not found')

        assesment = question.assesment
        question.delete()
        return {
            'code': 200,
            'msg': 'question deleted succesfully!',
            'data': getAssesmentQuestions(assesment)['questions']
        }

    return getErrorResponse('Invalid request')

#JOBS
def getJobsBoard(request):
    company_id = request.data.get('id')
    if not company_id:
        return getErrorResponse('Bad request')
    
    company = Company.getById(company_id)
    if not company:
        return getErrorResponse('company not found')

    company = Company.getByUser(request.user)
    jobs = Job.getForCompany(company=company)
    serializerJobs = JobListSerializer(jobs, many=True)
    serializerCompany = CompanySerializer(company)

    return {
        'code': 200,
        'company': serializerCompany.data,
        'jobs': serializerJobs.data
    }    

def getJobs(request):

    company = Company.getByUser(request.user)
    page_no = request.GET.get('page', 1)
    print(request.user)
    try:
        page_no = int(page_no)
    except Exception as e:
        print(e)
        page_no = 1
    
    jobs = Job.getForCompany(company=company)

    paginated_jobs = Paginator(jobs, PAGE_SIZE)

    pages = paginated_jobs.num_pages

    if pages >= page_no:
        p1 = paginated_jobs.page(page_no)
        lst = p1.object_list

        serializer = JobListSerializer(lst, many=True)

        return {
            'code': 200,
            'list': serializer.data,
            'current_page': page_no,
            'total_pages': pages
        }        
    else:
        return getErrorResponse('Page not available')

def getJobDetails(request):

    company = Company.getByUser(request.user)
    # company = request.GET.get('company', None)
    # company = re
    
    id = request.GET.get('id', None)
    if not id:
        return getErrorResponse('Invalid request')
 
    job = Job.getById(id)

    if not job:
        return getErrorResponse('Job not found')

    serializer = JobDetailsSerializer(job, many=False)
    data = {} 

    data["job info"] = serializer.data

    candidates = Candidate.getByJob(job=job)

    # pipeline_stage_stats = {}
    pipeline_stage_status_stats = {}

    for candidate in candidates:

        # For pipeline stage list
        if candidate.pipeline_stage:
            if str(candidate.pipeline_stage) in pipeline_stage_status_stats.keys():
                pipeline_stage_status_stats[str(candidate.pipeline_stage)] += 1
            else:
                pipeline_stage_status_stats[str(candidate.pipeline_stage)] = 1

        # For pipeline stage status
        if candidate.pipeline_stage_status:
            if str(candidate.pipeline_stage_status) in pipeline_stage_status_stats.keys():
                pipeline_stage_status_stats[str(candidate.pipeline_stage_status)] += 1
            else:
                pipeline_stage_status_stats[str(candidate.pipeline_stage_status)] = 1
    
    # data["pipeline_stage_stats"] = pipeline_stage_stats
    data["pipeline_stage_status_stats"] = pipeline_stage_status_stats
    
    return {
        'code': 200,
        'data': data
    }

@check_subscription_and_credits('JOB_POST')
@deduct_credit_decorator('JOB_POST')
def saveJob(self_or_request, request=None):
    # Handle both cases: called as instance method or standalone function
    if request is None:
        request = self_or_request
    else:
        self = self_or_request
        
    company = Company.getByUser(request.user)
        
    data = request.data

    id = data.get('id', None)

    if id:
        job = Job.getByIdAndCompany((id), company)
        if not company:
            return Response({'msg': 'Job not found'})
    else:
        job = Job()   
        job.company = company
    
    data = request.data    
    
    title = data.get('title', None)   
    vacancies = data.get('vacancies', None)   
    department_data = data.get('department', None)   
    owner_data = data.get('owner', None)   
    assesment_id = data.get('assessment', None)   
    member_ids = data.get('member_ids', None)   
    # type = data.get('type', None)   
    nature = data.get('nature', None)   
    education = data.get('education', None)   
    speciality = data.get('speciality', None)   
    description = data.get('description', None)   
    exp_min = data.get('exp_min', None)   
    exp_max = data.get('exp_max', None)   
    salary_min = data.get('salary_min', None)   
    salary_max = data.get('salary_max', None)   
    salary_type = data.get('salary_type', None)   
    currency = data.get('currency', None)   
    location = data.get('address', None) 
    job_board_ids = data.get('job_boards', None)   
    pipeline_id = data.get('pipeline', None)   
    active = data.get('active', None)
    webform_id = data.get('webform', None)
    status = data.get('status', None)
    published = data.get('published', None)
    dynamic_job_data = data.get('dynamic_job_data', None)
    draft_id =data.get("draftJobId",None)

    # if department_data:
    #     department_id = department_data.get('id') if isinstance(department_data, dict) else department_data
    #     department = Department.getByDid(department_id)
    #     if not department:
    #         return getErrorResponse('Department not found')
    #     job.department = department
    
    # if owner_data:
    #     owner_id = owner_data.get('account_id') if isinstance(owner_data, dict) else owner_data
    #     owner = Account.getById(owner_id)
    #     if not owner:
    #         return getErrorResponse('Owner not found')
    #     job.owner = owner

    assesment = None
    if assesment_id:
        assesment = Assesment.getById(assesment_id, company)
        if not assesment:
            return {'msg':'Assesment not found'}
        job.assesment = assesment
    else:
        job.assesment = None

    webform = None
    if webform_id:
        webform = Webform.getByWebformId(webform_id)
        if not webform:
            return {'msg':'Webform not found'}
        job.webform = webform
    else:
        job.webform = None

    if active == 1:
        active = True
    else:
        active = False
    if title:
        job.title = title
    if vacancies:
        job.vacancies = vacancies
    # if department:
    #     job.department = department
    # if owner:
    #     job.owner = owner
   
    job.assesment = assesment

    # if jobMembers:
    #     job.members = jobMembers
    # if specialitys:
    #     job.speciality = specialitys
    # if type:
    #     job.type = type
    if nature:
        job.nature = nature
    if education:
        job.educations = education
    if description:
        job.description = description
    if exp_min:
        job.exp_min = exp_min
    if exp_max:
        job.exp_max = exp_max
    if salary_min:
        job.salary_min = salary_min
    if salary_max:
        job.salary_max = salary_max
    if salary_type:
        job.salary_type = salary_type
    if currency:
        job.currency = currency
    if location:
        job.location = location
    job.created_by = request.user
    # if pipeline:
    #     job.pipeline = pipeline
    if active:
        job.active = active
    if job_board_ids:
        job.job_boards = job_board_ids
    job.webform = webform
    if status:
        job.job_status = status
    if dynamic_job_data:
        job.dynamic_job_data = dynamic_job_data

    if request.FILES != None:
        if 'document' in request.FILES:
            document = request.FILES['document']
            job.document = document    

    if published:
        job.published = published

    job.save()
    
    JobTimeline.log_activity(job= job, activity_type= 'JOB_CREATED', title= 'Job Created',description=f"Job created by {request.user.first_name if request.user and hasattr(request.user, 'first_name') else 'Unknown'}", performed_by=request.user)
    # if "Google" in job_board_ids:
    #     post_to_google_job(request,job.id)
    if draft_id:
        draft_job = get_object_or_404(DraftSaveJob, id=draft_id)
        draft_job.delete()

    # Deduct job credit (handled by the decorator)
    from rest_framework import status
    return {'msg': "Successfully saved job"},status.HTTP_200_OK
    # return {
    #     'code': 200,
    #     'msg': "Successfully saved job"
    # }
    
def post_job_to_zwayam(job_data):

    url = "https://api.zwayam.com/amplify/v2/jobs"
    
    payload = json.dumps({
        "title": job_data.title,  # Accessing title directly as an attribute
        "jobType": "hot",
        "description": job_data.description,  # Accessing description directly
        "minSalary": job_data.salary_min,  # Accessing minSalary directly
        "maxSalary": job_data.salary_max,  # Accessing maxSalary directly
        "salaryCurrency": job_data.currency,  # Accessing currency directly
        "industry": "Financial Services",  # Adjust as necessary
        "employmentType": job_data.type,  # Accessing type directly
        "orgName": job_data.company.name,  # Accessing company name directly
        "website": "https://yourcompanywebsite.com",  # Replace with actual website
        "minWorkExperience": job_data.exp_min,  # Accessing exp_min directly
        "maxWorkExperience": job_data.exp_max,  # Accessing exp_max directly
        "locations": [
            {
                "city": job_data.location.address,  # Accessing location address directly
                "state": job_data.location.state.name,  # Accessing state name directly
                "country": "India"  # Adjust as necessary
            }
        ],
        "keySkills": job_data.speciality,  # Assuming speciality is a list, keep it as is
        "notifyEmail": "testAmplify@yopmail.com",  # Replace with actual email
        "referenceCode": "12345"  # Adjust as necessary
    })

    headers = {
        'api_key': '<api_key>',  # Replace with actual API key
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)

    return response

def deleteJob(request): 

    id = request.GET.get('id', None)
    company = Company.getByUser(request.user)

    if id:
        job = Job.getByIdAndCompany((id), company)
        if not job:
            return getErrorResponse('Job not found')

        job.delete()
        return {
            'code': 200,
            'msg': 'Job deleted succesfully!',
            'data': getJobs(request)['data']
        }

    return getErrorResponse('Invalid request')  

def getJobsDetailCareer(request, pk=None):
    
    if pk is not None:
        if not isinstance(pk, int) or pk <= 0:
            return getErrorResponse('Invalid job id')
        try:
            job = Job.objects.get(id=pk, published=True)
        except Job.DoesNotExist:
            return {'code': 404, 'msg': 'Job not found'}
        serializer = JobsCarrerSerializer(job, context={'request': request})
    else:
        jobs = Job.objects.filter(published=True)
        serializer = JobsCarrerSerializer(jobs, many=True, context={'request': request})
    
    return {
        'code': 200,
        'data': serializer.data
    }

def getTemplateJobs(request, id=None):
    user = request.user
    
    if id:
        drafts = TemplateJob.getById(id=id)
        if not drafts:
            return getErrorResponse('Template Job not found')
        serializer = TemplateJobSerializer(drafts)
    else:        
        if user.is_superuser:
            drafts = TemplateJob.getAll()
        else:
            drafts = TemplateJob.objects.filter(Q(company__id=user.company_id) | Q(company__isnull=True))
        serializer = TemplateJobSerializer(drafts, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }
    
def publishedTemplateJobs(request):
    
    company = Company.getByUser(request.user)   

    data = request.data  
    id = data.get('id', None)

    if id:
        job = TemplateJob.getByIdAndCompany((id), company)
        if not company:
            return getErrorResponse( 'Job not found')
    else:
        job = TemplateJob()   
        job.company = company
    
    data = request.data    

    title = data.get('title', None)   
    vacancies = data.get('vacancies', None)   
    department_data = data.get('department', None)   
    owner_data = data.get('owner', None)   
    assesment_id = data.get('assesment', None)   
    member_ids = data.get('member_ids', None)   
    type = data.get('type', None)   
    nature = data.get('nature', None)   
    education = data.get('education', None)   
    speciality = data.get('speciality', None)   
    description = data.get('description', None)   
    exp_min = data.get('exp_min', None)   
    exp_max = data.get('exp_max', None)   
    salary_min = data.get('salary_min', None)   
    salary_max = data.get('salary_max', None)   
    salary_type = data.get('salary_type', None)   
    currency = data.get('currency', None)   
    location = data.get('address', None) 
    job_board_ids = data.get('job_boards', None)   
    pipeline_id = data.get('pipeline', None)   
    active = data.get('active', None)
    webform_id = data.get('webform', None)
    status = data.get('status', None)
    published = data.get('published', None)
    dynamic_job_data = data.get('dynamic_job_data', None)
    # if department_data:
    #     department_id = department_data.get('id') if isinstance(department_data, dict) else department_data
    #     department = Department.getByDid(department_id)
    #     if not department:
    #         return getErrorResponse('Department not found')
    #     job.department = department
    
    if owner_data:
        owner_id = owner_data.get('account_id') if isinstance(owner_data, dict) else owner_data
        owner = Account.getById(owner_id)
        if not owner:
            return getErrorResponse('Owner not found')
        job.owner = owner

    assesment = None
    if assesment_id:
        assesment = Assesment.getById(assesment_id, company)
        # if not assesment:
        #     return getErrorResponse('Assesment not found')
        job.assesment = assesment
    else:
        job.assesment = None


    jobMembers = []
    if member_ids:
        if not isinstance(member_ids, list):
            return getErrorResponse('Invalid members')
        for member in member_ids:
            user = Account.getById(member)
            if user:
                jobMembers.append(user.account_id)
                
    specialitys = []
    if speciality:
        if not isinstance(speciality, list):
            return getErrorResponse('Invalid speciality')
        for specialite in speciality:
            # user = Account.getById(member)
            specialitys.append(specialite)

    # if not type or not type in Job.TYPES:
    #     return getErrorResponse('invalid job type')

    # if not nature or not nature in Job.NATURES:
    #     return getErrorResponse('invalid job nature')

    # if not education :
    #     return getErrorResponse('Invalid education')
    
    # if not speciality:
    #     return getErrorResponse('Speciality required')

    # if not description:
    #     return getErrorResponse('Job description required')
    
    # if int(exp_min) != exp_min:
    #     return getErrorResponse('Minimum experience required')
    
    # if int(exp_max) != exp_max:
    #     return getErrorResponse('Maximum experience required')

    # if not salary_min:
    #     return getErrorResponse('Minimum salary required')

    # if not salary_max:
    #     return getErrorResponse('Maximum salary required')
    
    # if not salary_type or not salary_type in Job.PAY_TYPES:
    #     return getErrorResponse('invalid Pay type')

    # if not currency:
    #     return getErrorResponse('Currency required')

    # if not location:
    #     return getErrorResponse('Location required')    

    # location = Location.getById(location,company)
    # if not location:
    #     return getErrorResponse('Location not found')
 
    # #ADD JOB BOARDS ONCE READY
    pipeline_data = dynamic_job_data["Create Job"]["pipeline"]
    pipeline = Pipeline.getById(pipeline_data["id"], company)
    # if not pipeline:
    #     return getErrorResponse('Pipeline not found')          

    # if not active or int(active) not in [0 , 1]:
    #     return getErrorResponse('Active status required') 

    if active == 1:
        active = True
    else:
        active = False
    if title:
        job.title = title
    if vacancies:
        job.vacancies = vacancies
    # if department:
    #     job.department = department
    # if owner:
    #     job.owner = owner
   
    job.assesment = assesment

    if jobMembers:
        job.members = jobMembers
    if specialitys:
        job.speciality = specialitys
    if type:
        job.type = type
    if nature:
        job.nature = nature
    if education:
        job.educations = education
    if description:
        job.description = description
    if exp_min:
        job.exp_min = exp_min
    if exp_max:
        job.exp_max = exp_max
    if salary_min:
        job.salary_min = salary_min
    if salary_max:
        job.salary_max = salary_max
    if salary_type:
        job.salary_type = salary_type
    if currency:
        job.currency = currency
    if location:
        job.location = location
    job.created_by = request.user
    if pipeline:
        job.pipeline = pipeline
    if active:
        job.active = active
    if job_board_ids:
        job.job_boards = job_board_ids
    if webform_id:
        job.webform_id = webform_id
    if status:
        job.job_status = status
    if dynamic_job_data:
        job.dynamic_job_data = dynamic_job_data

    if request.FILES != None:
        print("files")
        print(request.FILES)
        if 'document' in request.FILES:
            document = request.FILES['document']
            job.document = document    

    if published:
        job.published = published

    job.save()

    return {
        'code': 200,
        'msg': 'Job saved successfully'
    }

def deleteTemplateJobs(request, id=None):
	user = request.user
	if not id:
		# Fallback to query param for consistency with other delete helpers
		id = request.GET.get('id', None)
	if not id:
		return getErrorResponse('Invalid request')

	# Superusers can delete any template by id; others restricted to their company
	if user.is_superuser:
		template = TemplateJob.getById(id=id)
	else:
		return getErrorResponse('Only superadmin has delete permission')

	if not template:
		return getErrorResponse('Template Job not found')

	template.delete()

	return {
		'code': 200,
		'msg': 'Template Job deleted successfully',
		'data': getTemplateJobs(request)['data']
	}

    
def getDraftJobs(request, id=None):
    user = request.user
    if id:
        data = DraftSaveJob.getById(id=id)
        if not data:
            return getErrorResponse('Draft Job not found')
        serializer=DraftSaveJobSerializer(data)
    else:
        if user.is_superuser:
            data = DraftSaveJob.getAll()
        else:
            data = DraftSaveJob.objects.filter(company__id=user.company_id)
        serializer=DraftSaveJobSerializer(data, many=True)
        
    return {
        'code': 200,
        'data': serializer.data
    }

def SaveDraftJobs(self, request):
        
    company = Company.getByUser(request.user)   

    data = request.data  
    id = data.get('id', None)

    if id:
        job = DraftSaveJob.getByIdAndCompany((id), company)
        if not company:
            return getErrorResponse( 'Job not found')
    else:
        job = DraftSaveJob()   
        job.company = company
    
    data = request.data    

    assesment_id = data.get('assesment', None)   
    webform_id = data.get('webform', None)
    published = data.get('published', None)
    dynamic_job_data = data.get('dynamic_job_data', None)

    assesment = None
    if assesment_id:
        assesment = Assesment.getById(assesment_id, company)
        job.assesment = assesment
    else:
        job.assesment = None
 
    job.assesment = assesment

    job.created_by = request.user
    
    if webform_id:
        job.webform_id = webform_id
 
    if dynamic_job_data:
        job.dynamic_job_data = dynamic_job_data

    job.save()

    return {
        'code': 200,
        'msg': 'DraftJob saved successfully'
    }
  
def deleteDraftJob(request, id=None):
	user = request.user
	if not id:
		# Fallback to query param for consistency with other delete helpers
		id = request.GET.get('id', None)
	if not id:
		return getErrorResponse('Invalid request')

	# Superusers can delete any draft by id; others restricted to their company
	if user.is_superuser:
		draft = DraftSaveJob.getById(id=id)
	else:
		company = Company.getByUser(user)
		draft = DraftSaveJob.getByIdAndCompany(id, company)

	if not draft:
		return getErrorResponse('Draft Job not found')

	draft.delete()

	return {
		'code': 200,
		'msg': 'Draft Job deleted successfully',
		'data': getDraftJobs(request)['data']
	}

def cloneJob(request, job_id):
    company = Company.getByUser(request.user)
    original_job = Job.getByIdAndCompany(job_id, company)
    if not original_job:
        return getErrorResponse('Job not published')

    # Create a new job instance
    job = Job()
    job.company = company
    job.title = original_job.title
    job.vacancies = original_job.vacancies
    job.department = original_job.department
    job.owner = original_job.owner
    job.assesment = original_job.assesment
    job.members = original_job.members
    job.type = original_job.type
    job.nature = original_job.nature
    job.educations = original_job.educations
    # job.speciality = original_job.speciality
    job.description = original_job.description
    job.exp_min = original_job.exp_min
    job.exp_max = original_job.exp_max
    job.salary_min = original_job.salary_min
    job.salary_max = original_job.salary_max
    job.salary_type = original_job.salary_type
    job.currency = original_job.currency
    job.location = original_job.location
    job.pipeline = original_job.pipeline
    job.active = original_job.active
    job.job_boards = original_job.job_boards
    job.webform = original_job.webform
    job.job_status = original_job.job_status
    job.created_by = request.user
    job.published = original_job.published

    if original_job.document:
        job.document = original_job.document

    job.save()
    
    job.speciality.set(original_job.speciality.all()) 

    return {
        'code': 200,
        'msg': 'Job cloned successfully',
        'id': job.id
    }

def getJobDocument(request,job_id):
    
    if request.user.is_superuser:
        # Superuser can access any job by ID
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return getErrorResponse('Job not found')
    else:
    
        company = Company.getByUser(request.user)
        if not company:
            return getErrorResponse('Company not found')

        try:
            job = Job.objects.get(id=job_id, company=company)
        except Job.DoesNotExist:
            return getErrorResponse('Job not found')

    return {
        'code': 200,
        'job_id': job.id,
        'document': job.document.url if job.document else None
    }  

def uploadJobDocument(request):
   
    data = request.data    
    job_id = data.get('jobId', None)
    
    company = Company.getByUser(request.user)
    if not company:
        return getErrorResponse('Company not found')

    try:
        job = Job.objects.get(id=job_id, company=company)
    except Job.DoesNotExist:
        return getErrorResponse('Job not found')

    if 'document' not in request.FILES:
        return getErrorResponse('No document uploaded')

    document = request.FILES['document']
    job.document = document
    job.save()
    
    JobTimeline.log_activity(job=job, activity_type='DOCUMENT_UPLOADED', title='Document Uploaded', description='Document uploaded successfully', performed_by=request.user, document=document.name)

    return {
        'code': 200,
        'msg': 'Document uploaded successfully',
        'job_id': job.id,
        'document': job.document.url if job.document else None
    }
    
def deleteJobDocument(request):
    
    data = request.data 
    job_id = data.get('jobId', None)
    
    company = Company.getByUser(request.user)
    if not company:
        return getErrorResponse('Company not found')
    
    try:
        job = Job.objects.get(id=job_id, company=company)
    except job.DoesNotExist:
        return getErrorResponse('Job not found')
    
    if not job.document:
        return getErrorResponse('No document found for this job')
    
    job.document.delete()
    job.document = None
    job.save()
    
    return {
        'code': 200,
        'msg': 'Document deleted successfully',
        'job_id':job_id
    }
    
def addExistingAssesment(request):
    data = request.data    
    job_id = data.get('jobId', None)
    assesment_id = data.get('assesmentId', None)
    
    company = Company.getByUser(request.user)
    if not company:
        return getErrorResponse('Company not found')

    try:
        job = Job.objects.get(id=job_id, company=company)
    except Job.DoesNotExist:
        return getErrorResponse('Job not found')

    try:
        assesment = Assesment.objects.get(id=assesment_id, company=company)
    except Assesment.DoesNotExist:
        return getErrorResponse('Assessment not found')

    job.assesment = assesment
    job.save()
    
    JobTimeline.log_activity(job=job, activity_type= 'JOB_ASSESSMENT_UPDATE', title= 'Job ASSESSMENT Updated', description=f"Job Assessment Update", performed_by=request.user)
    
    return {
        'code': 200,
        'msg': 'Assessment added to job successfully',
    }

def deleteJobAssesment(request):
    data = request.data    
    job_id = data.get('jobId', None)
    
    company = Company.getByUser(request.user)
    if not company:
        return getErrorResponse('Company not found')

    try:
        job = Job.objects.get(id=job_id, company=company)
    except Job.DoesNotExist:
        return getErrorResponse('Job not found')

    job.assesment = None
    job.save()
    
    return {
        'code': 200,
        'msg': 'Assessment removed from job successfully',
    }
    

def getJobCandidateList(request):
    company = Company.getByUser(request.user)
    if not company: 
        return getErrorResponse("Company not found!!")

    # Getting the final job list
    results = {}

    # Making the job dictionary
    jobs = Job.getForCompany(company=company)

    if not jobs: 
        return getErrorResponse("Job not found!!")

    job_map = {}
    

    for job in jobs:
        # Contains info of the candidates
        candidate_map = {}
        # Contains info of the job_candidate map
        job_candidates_map = {}
        job_map[job.id] = job.title
        candidates = Candidate.getByJob(job=job)

        if not candidates:
            return getErrorResponse("No Candidates applied for this job!")

        candidate_array = []
        for candidate in candidates:
            name = ""
            if candidate.first_name:
                name+=str(candidate.first_name)
            if candidate.middle_name:
                name = name + " " + str(candidate.middle_name)
            if candidate.last_name:
                name = name + " " + str(candidate.last_name)
            candidate_map[candidate.id] = name 
            candidate_array.append(candidate.id)
        job_candidates_map["candidates"] = candidate_array
        job_candidates_map["name"] = job.title
        # Final map
        results[job.id] = job_candidates_map


    return {
        'code': 200,
        'data': results
    }

def getAllNotes(request):
    job_id = request.GET.get('job')
    if not job_id:
        return getErrorResponse('Invalid request')
    
    if request.user.is_superuser:
        # Superuser can access any job by ID
        job = Job.objects.get(id=job_id)
    else:
        # Regular users can only access jobs associated with their company
        company = Company.getByUser(request.user)
        if not company:
            return getErrorResponse('Company not found')
        job = Job.getByIdAndCompany(job_id, company)
        
    if not job:
        return getErrorResponse('Job not found')

    notes = JobNotes.getForJob(job)
    serializer = JobNotesSerializer(notes, many=True)  

    return {
        'code': 200,
        'notes': serializer.data 
    }

def getNotesForJob(job):
    notes = JobNotes.getForJob(job)
    serializer = JobNotesSerializer(notes, many=True)  
    return serializer.data  

def saveNote(request):

    data = request.data

    job_id = data.get('job')
    if not job_id:
        return getErrorResponse('Invalid request')

    company = Company.getByUser(request.user)
    
    job= Job.getByIdAndCompany(job_id, company)

    if not job:
        return getErrorResponse('Job not found')    
     
    text = data.get('note', None)        
    if not text:
        return getErrorResponse('Note text required')    

    id = data.get('id', None)
    add_to_candidate = data.get('addToCandidates', False)

    if id:
        note = JobNotes.getById(id, job)
        if not note:
            return getErrorResponse('Note not found')
    else:
        note = JobNotes()

    note.added_by = request.user
    note.note = text
    note.job = job
    note.save()
    
    JobTimeline.log_activity( job=job, activity_type='NOTE_ADDED', title='Note Added', description=text[:100] + '...' if len(text) > 100 else text, performed_by=request.user )    
    
    if add_to_candidate:
        candidates = Candidate.objects.filter(job=job)
        for candidate in candidates:
            candidate_note = Note()
            candidate_note.candidate = candidate
            candidate_note.note = text
            candidate_note.save()

    return {
        'code': 200,
        'msg': 'Note added successfully',
        'notes': getNotesForJob(job)
    }
    
def updateNote(request):
    data = request.data

    note_id = data.get('id')
    if not note_id:
        return getErrorResponse('Invalid request')

    company = Company.getByUser(request.user)
    
    note = JobNotes.getByIdAndCompany(note_id, company)

    if not note or note.job.company != company:
        return getErrorResponse('Note not found')
    
    text = data.get('note', None)
    if not text:
        return getErrorResponse('Note text required')

    note.note = text
    note.save()

    return {
        'code': 200,
        'msg': 'Note updated successfully',
        'notes': getNotesForJob(note.job)
    }

def deleteNote(request):
    note_id = request.GET.get('id')
    if not note_id:
        return getErrorResponse('Invalid request')

    company = Company.getByUser(request.user)

    note = JobNotes.getByIdAndCompany(note_id, company)

    if note:
        job = note.job
        note.delete()

        return {
            'code': 200,
            'msg': 'Note deleted successfully',
            'notes': getNotesForJob(job)
        }
    
    return getErrorResponse('Note not found')


def getJobStats(request):

    job_id = request.GET.get('job')
    if not job_id:
        return getErrorResponse('Invalid request')
    
    if request.user.is_superuser:
        # Superuser can access any job by ID
        job = Job.objects.get(id=job_id)
    else:
        # Regular users can only access jobs associated with their company
        company = Company.getByUser(request.user)
        if not company: 
            return getErrorResponse("Company not found!!")
        # getting job 
        job = Job.getByIdAndCompany(job_id, company)

    if not job: 
        return getErrorResponse("Job not found!!")

    candidates = Candidate.getByJob(job=job)

    # pipeline_stage_stats = {}
    pipeline_stage_status_stats = {}
    no_of_candidates = 0

    for candidate in candidates:

        # For pipeline stage list
        if candidate.pipeline_stage:
            if str(candidate.pipeline_stage) in pipeline_stage_status_stats.keys():
                pipeline_stage_status_stats[str(candidate.pipeline_stage)] += 1
            else:
                pipeline_stage_status_stats[str(candidate.pipeline_stage)] = 1

        # For pipeline stage status
        if candidate.pipeline_stage_status:
            if str(candidate.pipeline_stage_status) in pipeline_stage_status_stats.keys():
                pipeline_stage_status_stats[str(candidate.pipeline_stage_status)] += 1
            else:
                pipeline_stage_status_stats[str(candidate.pipeline_stage_status)] = 1

        no_of_candidates += 1
        
    results = {}
    pipeline_stage_status_stats['no_of_candidates'] = no_of_candidates
    # results['pipeline_stage_stats'] = pipeline_stage_stats
    results['pipeline_stage_status_stats'] = pipeline_stage_status_stats
    results['job_status'] = job.job_status

    return {
        'code': 200,
        'data': results
    }

def getDashboardJobStats(request):
    user = request.user
    company = Company.getByUser(user)
    
    if not company and not user.is_superuser:
        return getErrorResponse("Company not found!!")

    # if user.is_superuser:
    #     jobs = Job.objects.all()
    # else:
    #     jobs = Job.getForCompany(company)
    # Support dynamic window via query param ?days=N (defaults to 30, min 1)
    days_param = request.GET.get('days')
    try:
        days = max(1, int(days_param))
    except (TypeError, ValueError):
        days = 30
    thirty_days_ago = timezone.now() - timedelta(days=days)
    if user.is_superuser:
        # jobs = Job.objects.filter(created__gte=thirty_days_ago)
        jobs = Job.objects.all()
    else:
        # jobs = Job.getForCompany(company).filter(created__gte=thirty_days_ago)
        jobs = Job.getForCompany(company)

    
    job_stats = []  # List to store job-specific statistics

    for job in jobs:
        candidates = Candidate.getByJob(job=job)
        pipeline_stages = PipelineStage.objects.all()
        pipeline_stage_stats = {str(stage): 0 for stage in pipeline_stages}

        for candidate in candidates:
            # For pipeline stage list
            if candidate.pipeline_stage:
                pipeline_stage = str(candidate.pipeline_stage)
                if pipeline_stage in pipeline_stage_stats:
                    pipeline_stage_stats[pipeline_stage] += 1

        total_candidates = sum(pipeline_stage_stats.values())

        job_stat = {
            'job_name': job.dynamic_job_data['Create Job']['title'],
            'job_id': job.id,
            'job_status': job.job_status,
            'pipeline_stage_stats': pipeline_stage_stats,
            'no_of_candidates': total_candidates
        }

        job_stats.append(job_stat)

    return {
        'code': 200,
        'data': job_stats
    }        

def get_daily_created_jobs(request):
    """
    Get daily created job counts and statistics for a given date range.
    
    Query params:
    - days: Number of days to look back (default: 7)
    """
    user = request.user
    company = Company.getByUser(user)
    today = timezone.now().date()
    
    # Get days parameter from query string, default to 7 if not provided
    try:
        days_param = request.GET.get('days', '0')
        if days_param.isdigit():
            days = int(days_param)
            if days == 0:  # Today only
                days = 1
                start_date = today
            elif days == 1:  # Yesterday only
                days = 1
                start_date = today - timedelta(days=1)
            else:
                start_date = today - timedelta(days=days-1)  # Include today
        else:
            days = 7
            start_date = today - timedelta(days=days-1)
    except (TypeError, ValueError):
        days = 7
        start_date = today - timedelta(days=days-1)
    
    # Fetch job counts for the specified number of days
    if user.is_superuser:
        counts = []
        for i in range(days):
            target_date = start_date + timedelta(days=i)
            count = Job.objects.filter(created__date=target_date).count()
            counts.append({'date': target_date, 'count': count})
        jobs = Job.objects.filter(created__date__gte=start_date).order_by("-created")
    else:
        counts = []
        for i in range(days):
            target_date = start_date + timedelta(days=i)
            count = Job.getForCompany(company).filter(created__date=target_date).count()
            counts.append({'date': target_date, 'count': count})
        jobs = Job.getForCompany(company).filter(created__date__gte=start_date).order_by("-created")
    
    # Fetch latest jobs for the company within the date range
    job_stats = []
    
    for job in jobs:
        candidates = Candidate.getByJob(job=job)
        pipeline_stages = PipelineStage.objects.all()
        pipeline_stage_stats = {str(stage): 0 for stage in pipeline_stages}

        for candidate in candidates:
            pipeline_stage = str(candidate.pipeline_stage)
            if candidate.pipeline_stage:
                pipeline_stage_stats[pipeline_stage] += 1
            else:
                pipeline_stage_stats[pipeline_stage] = 1

        total_candidates = sum(pipeline_stage_stats.values())
        job_stats.append({
            'job_name': job.dynamic_job_data['Create Job']['title'],
            'pipeline_stage_stats': total_candidates
        })
    
    return {
        'days': days,
        'start_date': start_date,
        'end_date': today,
        'counts': counts, 
        'job_stats': job_stats
    }

def get_age_job_count(request):
    user = request.user
    company = Company.getByUser(user)
    
    if user.is_superuser:
        jobs = Job.objects.all().order_by('-id').values('targetdate', 'startdate', 'vacancies', 'title','id','dynamic_job_data')
    else:
        jobs = Job.objects.filter(company=company).order_by('-id').values('targetdate', 'startdate', 'vacancies', 'title','id','dynamic_job_data')
        # jobs = Job.objects.filter(company=company).order_by('-id')[:9].values('targetDate', 'createtDate', 'vacancies', 'title','id')
    
    job_details = []
    if not jobs:  # Check if jobs is empty
        return {
            "average": {
                "no_of_positions": 0,
                "age_of_opened_jobs": 0,
                "delay": 0
            },
            "job_details": job_details  # Return empty list
        }

    for job in jobs:
        if job['startdate']:
            age_of_opened_jobs = (datetime.now().date() - job['startdate']).days
        else:
            age_of_opened_jobs=0
        if job['targetdate']:
            delay = (job['targetdate'] - datetime.now().date()).days
        else:
            delay=0
        
        job_details.append({
            "id":job['id'],
            "title": job['dynamic_job_data']['Create Job']['title'],
            "no_of_positions": job['vacancies'],
            "age_of_opened_jobs": age_of_opened_jobs,
            "delay": delay
        })
    
    avg_positions = sum(job['vacancies'] for job in jobs) / len(jobs) if jobs else 0
    avg_age_of_opened_jobs = sum(job['age_of_opened_jobs'] for job in job_details) / len(job_details) if job_details else 0
    avg_delay = sum(job['delay'] for job in job_details) / len(job_details) if job_details else 0

    return {
        "average": {
            "no_of_positions": int(avg_positions),
            "age_of_opened_jobs": avg_age_of_opened_jobs,
            "delay": avg_delay
        },
        "job_details": job_details
    }
    
def getJobStatusStats(request):
    # paranoid company check 
    company = Company.getByUser(request.user)

    if not company: 
        return getErrorResponse("Company not found!!")

    jobs = Job.getForCompany(company)

    if not jobs:
        return getErrorResponse("Company has no registered jobs!!")
    
    results = []

    for job in jobs:
        data = {}
        data["job_status"] = job.job_status
        data["job_id"] = job.id
        data["job_name"] = job.title
        data["job_vacancies"] = job.vacancies

        # appending data
        results.append(data)

    return {
        'code': 200,
        'data': results
    }
    
def updateJobStats(request):
    # paranoid company check 
    company = Company.getByUser(request.user)

    if not company: 
        return getErrorResponse("Company not found!!")

    job_id = request.data.get('job')
    
    if not job_id:
        return getErrorResponse('Invalid request')
    
    # getting job 
    job = Job.getByIdAndCompany(job_id, company)

    if not job: 
        return getErrorResponse("Job not found!!")

    job_status = request.data.get('status')

    if job_status not in ['In Progress', 'Filled', 'On Hold', 'Closed']:
        return {
            'code': 400,
            'msg': 'Invalid status'
        }
    JobTimeline.log_activity(job=job, activity_type= 'STATUS_CHANGED', title= 'Job Status Updated',description=f"Job status updated to {job_status}", performed_by=request.user, pipeline_stage_status=f"old: {job.job_status} new: {job_status}")

    job.job_status = job_status
    job.save()

    return {
        'code': 200,
        'data': "Updated job status successfully"
    }
    
def AssociateJobApplyGet(self, request, candidate_id):
    candidate = Candidate.objects.get(id=candidate_id)
    jobs = Job.objects.filter(id__in=candidate.job.values_list('id', flat=True))
    serializer = JobsSerializer(jobs, many=True)
    return Response(serializer.data)

from .serializer import JobsSerializer
def getJobList(request):
    user = request.user
    if user.is_superuser:
        jobs = Job.objects.all()
    else:
        company = Company.getById(user.company_id)
        jobs = Job.objects.filter(company=company)
    
    serializer = JobsSerializer(jobs, many=True)
    return serializer

def JobTimelineView(self,request,job_id):
    job = Job.objects.get(id=job_id)
    timeline = JobTimeline.objects.filter(job=job).order_by('-created')
    serializer = JobTimelineSerializer(timeline, many=True)
    return Response({
        'code': 200,
        'data': serializer.data
    })

# google job post job board 
def JobBoardList(request):
    job_board = JobBoard.objects.filter(company=request.user.company_id)
    serializer = JobBoardSerializer(job_board, many=True)
    return Response(serializer.data)

def JobBoardSave(self,request):

    data=request.data
    company=Company.getById(request.user.company_id)

    data['company']=company.id
    serializer=JobBoardSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        
        job_board=JobBoard.objects.filter(company=company, platform="Google").last()
        credentials = service_account.Credentials.from_service_account_file(job_board.credentials.path)
        client = talent.CompanyServiceClient(credentials=credentials)
        print("credentials",data)
        company = types.Company(
            display_name=data.get("name"),
            external_id=data.get("external"),  # A unique identifier for your system
            headquarters_address=data.get("address"),
            hiring_agency=False,
            website_uri=data.get("website"),
            career_site_uri=data.get("career_site"),
            size=types.CompanySize.SMALL
            )
        parent = f"projects/{job_board.project_id}"
        response = client.create_company(parent=parent, company=company)
        job_board.google_company_id = response.name.split('/')[-1]
        job_board.save()
        print("job_board",response.name.split('/')[-1])
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def post_to_google_job(request,id):
        # Extract job details from the request
        # job_data = request.data
        job = get_object_or_404(Job,id=id)

        job_board=JobBoard.objects.filter(company=request.user.company_id, platform="Google").last()
        credentials = service_account.Credentials.from_service_account_file(job_board.credentials.path)

        # Initialize the client
        client = talent.JobServiceClient(credentials=credentials)
        
        from django.conf import settings
        job_application_url = f"{settings.JOB_URL}/"
        if isinstance(job_application_url, bytes):
            job_application_url = job_application_url.decode("utf-8")
        uris = [job_application_url]
        application_info = {"uris": uris}
        addresses = [
            "1600 Amphitheatre Parkway, Mountain View, CA 94043",
            "111 8th Avenue, New York, NY 10011",
        ]
        # Define the job
        job = {
            "company": f"projects/{job_board.project_id}/companies/{job_board.google_company_id}",
            "requisition_id": f"job_{job.id}",
            "title": "Software Developer by Edjobster",
            "description": job.description,
            "job_level": types.JobLevel.ENTRY_LEVEL,
            "qualifications": job.educations,
            "responsibilities": job.department.name,
            "posting_publish_time": job.created,
            "posting_expire_time": job.targetdate,
            "application_info": application_info,
            "addresses": addresses,
            "language_code": "en-US",
        }

        # Create the job
        parent = f"projects/{job_board.project_id}"
        try:
            response = client.create_job(parent=parent, job=job)
            print(f"Created job: {response}")
            return Response({"message": "Job created and published successfully"})
        except Exception as e:
            print("Error in creating job",e)
            return Response({"message": e})


def GoogleJobList(self,request):

    job_board=JobBoard.objects.filter(company=request.user.company_id, platform="Google").last()
    credentials = service_account.Credentials.from_service_account_file(job_board.credentials.path)
    client = talent.JobServiceClient(credentials=credentials)
    parent = f"projects/{job_board.project_id}"  # Replace with your actual project ID

    # Optional: Add a filter to narrow down the jobs (e.g., filter by company)
    filter_query = f"companyName=\"projects/{job_board.project_id}/companies/{job_board.google_company_id}\""

    # List jobs (returns a ListJobsPager object)
    jobs_pager = client.list_jobs(parent=parent, filter=filter_query)
    data=[]
    for job in jobs_pager:
        data.append({
            "job_name": job.name,
            "job_title": job.title,
            "job_description": job.description,
            "job_company": job.company,
            "job_posting_publish_time": job.posting_publish_time,
            "job_posting_expire_time": job.posting_expire_time
        })
    return Response(data)

    # Fetch assessment without company bound check for career/public use
    assesment = Assesment.getByAssessmentId(id)
    if not assesment:
        return getErrorResponse('Assesment not found')

    form = assesment.form or {}
    # questions = form.get('questions', []) if isinstance(form, dict) else []
    filtered_questions = []
    for q in form:
        if not isinstance(q, dict):
            continue
        options = q.get('options', [])
        print(options)
        # Keep only option label
        filtered_options = []
        if isinstance(options, list):
            for opt in options:
                if isinstance(opt, dict) and 'text' in opt:
                    filtered_options.append({'text': opt.get('text')})
        filtered_questions.append({
            'id': q.get('id'),
            'type': q.get('type'),
            'question': q.get('question'),
            'required': q.get('required', False),
            'options': filtered_options
        })

    return {
        'code': 200,
        'data': {
            'questions': filtered_questions
        }
    }

import json
import requests
import logging
from django.conf import settings

def sector_normalize(text: str) -> str:
    """Normalize department names for matching"""
    return text.strip().lower()


SECTOR_MAP = {
    # 🎓 Education
    "english": "Education & Teaching",
    "math": "Education & Teaching",
    "science": "Education & Teaching",
    "hindi": "Education & Teaching",
    "teaching": "Education & Teaching",
    "admissions": "Education & Teaching",
    "lab": "Education & Teaching",
    "sports": "Education & Teaching",

    # 💼 HR & Admin
    "human resources": "Human Resources",
    "talent acquisition": "Recruitment Consultancy",
    "payroll": "Banking & Finance",
    "employee relations": "Human Resources",
    "compensation and benefits": "Human Resources",
    "workforce planning": "Management",
    "admin": "Administrative Assistance",
    "administration": "Administrative Assistance",

    # 💻 IT / Tech
    "information technology": "It",
    "software development": "It",
    "web development": "Creative & Digital",
    "mobile app development": "It",
    "cybersecurity": "Information Security",
    "cloud services": "It",
    "devops": "It",
    "data analytics": "AI & Emerging Technologies",
    "business analytics": "AI & Emerging Technologies",
    "help desk": "Customer Service & Helpdesk",
    "technical support": "Customer Service & Helpdesk",
    "network administration": "It",
    "systems administration": "It",
    "infrastructure": "It",

    # 📢 Marketing / Creative
    "marketing": "Marketing",
    "digital marketing": "Marketing",
    "brand management": "Marketing",
    "advertising": "Creative & Digital",
    "graphic design": "Creative & Digital",
    "social media management": "Creative & Digital",
    "content management": "Media",
    "creative services": "Creative & Digital",

    # 🛒 Sales
    "sales": "Sales",
    "direct sales": "Sales",
    "inside sales": "Sales",
    "channel sales": "Sales",
    "account management": "Sales",
    "sales engineering": "Sales",

    # 🚚 Logistics / Ops
    "logistics": "Logistics & Warehousing",
    "warehouse management": "Logistics & Warehousing",
    "inventory control": "Logistics & Warehousing",
    "supply chain management": "Logistics & Warehousing",
    "distribution": "Logistics & Warehousing",
    "operations": "Management",

    # 🏭 Engineering / Production
    "engineering": "Mechanical Engineering",
    "production": "Manufacturing & Production",
    "quality assurance": "Manufacturing & Production",
    "maintenance": "Maintenance",
    "field services": "Driving & Transport",

    # ⚖️ Legal / Compliance
    "legal": "Legal",
    "legal affairs": "Legal",
    "compliance": "Legal",
    "ethics and compliance": "Legal",
    "risk management": "Management",
    "internal audit": "Accounting",

    # 🏥 Facilities / Support
    "facilities management": "Cleaning & Sanitation",
    "house keeping": "Cleaning & Sanitation",
    "catering services": "Catering",
    "security": "Security Public Safety",
    "health and safety": "Security Public Safety",

    # 🔬 Research / Strategy
    "research and development": "Scientific Research & Development",
    "strategy": "Management Consultancy",
    "innovation lab": "AI & Emerging Technologies",
    "market research": "Marketing",
}


def find_job_sector(department_name: str) -> str:
    key = sector_normalize(department_name)
    return SECTOR_MAP.get(key, "Other")


logger = logging.getLogger(__name__)

def convert_job_to_whatjobs_format(job_data: dict,action) -> list:
    """
    Convert internal job data to WhatJobs ATS temp format
    """
    logger.info("Starting conversion of job data to WhatJobs format")
    # Extract the nested job data
    job_info = job_data.dynamic_job_data.get("Create Job", {})
    address_info = job_data.dynamic_job_data.get("Address Information", {})
    desc_info = job_data.dynamic_job_data.get("Description Information", {}).get("description", {})
    logger.info(f"..........c{job_data.company.name}")
    # Get location details
    city = address_info.get("city", {}).get("name", "")
    state = address_info.get("state", {}).get("name", "")
    country = address_info.get("country", {}).get("name", "")
    pincode = address_info.get("pincode", "")

    # Get salary details
    salary_min = job_info.get("salary_min", "0")
    salary_max = job_info.get("salary_max", "0")
    salary_type = "Monthly" if job_info.get("salary_type") == "Monthly" else "Yearly"

    # Get skills/speciality
    skills = job_info.get("speciality", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",")]
    
    # Get description
    description = desc_info.get("job_description", "") + "\n\n" + desc_info.get("requirements", "")

    payload = [
        {
            "command": action,
            "countryCode": "IN",
            "jobIdent": int(job_data.id),

            "jobTitle": job_info.get("title", ""),

            "city": city,
            "state": state,
            "jobLocationAddress": f"{city}, {state}, {country}",
            "zip": pincode,

            "jobWorkFrom": 2 if job_info.get("nature", "").lower() == "remote" else 1,

            "jobStartType": 1,  # Default to immediate start
            "jobStartByDate": datetime.now().strftime("%Y-%m-%d"),  # Set to current date

            "jobEmploymentType": 1 if job_info.get("type", "").lower() == "Full Time" else 2,  # Default to full-time
            "jobEmploymentSubType": 1 if job_info.get("type", "").lower() == "Full Time" else 2,  # Default to permanent

            "jobPeriod": "3",
            "jobLength": job_info.get("vacancies", "1"),

            "jobPaymentRangeFrom": str(salary_min),
            "jobPaymentRangeTo": str(salary_max),
            "salaryDisplayType": 1,  # Annual
            "jobPaymentRangeType": 1 if salary_type.lower() == "Daily" else 4 if salary_type.lower() == "Weekly" else 2 if salary_type.lower() == "Monthly" else 3 if salary_type.lower() == "Yearly" else 5 if salary_type.lower() == "Hour" else 2,  # 1: Daily, 2: Weekly, 3: Monthly, 4: Yearly, 5: Hour, default: Weekly

            "jobScheduleType": 1,  # Full-time
            "jobScheduleTypeOther": "",

            "companyName": job_data.company.name,
            "companyDescription": job_data.company.description if job_data.company and job_data.company.description else "A sample company description",

            "jobOpeningCount": int(job_info.get("vacancies", 1)),

            "jobSector": dict(JOB_CATEGORIES).get(job_data.company.sector, ""),
            # "jobSector": "Customer Service & Helpdesk",

            "jobDescription": description,

            "jobCommunicationMail": "info@gmail.com",  # Not provided in input
            "jobCommunicationURL": f'{settings.JOB_URL}/jobs/{job_data.id}',  # Not provided in input
            # "jobCommunicationURL":"https://staging-career.edjobster.com/jobs/327/",
            "jobReferenceId": str(job_info.get("id", "")),

            "jobSkills": skills,
        }
    ]
    logger.info("payload{payload}")
    return payload

