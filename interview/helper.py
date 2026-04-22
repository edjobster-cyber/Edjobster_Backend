from account import serializer
from account.models import Account, Company
from job.models import Job, JobTimeline
from common.utils import isValidUuid, getErrorResponse
from settings.models import EmailTemplate, Location
from .models import Candidate, Interview
from .serializer import  InterviewDetailsSerializer, InterviewListSerializer
import json
from candidates.models import EmailSettings, CandidateTimeline
from .mail_utils import InterviewMailer
from settings.models import Contacts
from datetime import datetime, time, timedelta
from django.utils import timezone

def calculate_duration(time_start, time_end):
    """Calculate duration between two time values"""
    if not time_start or not time_end:
        return None

    try:
        # Convert time strings to datetime objects for calculation
        start_datetime = datetime.combine(datetime.today(), time_start)
        end_datetime = datetime.combine(datetime.today(), time_end)

        # Calculate difference
        duration = end_datetime - start_datetime

        # Format as HH:MM:SS
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{hours} hours {minutes} minutes"
    except (ValueError, TypeError):
        return None

def scheduleInterview(request):

    data = request.data

    job_id = data.get('job', None)
    candidate_id = data.get('candidate', None)
    title = data.get('title', None)
    type = data.get('type', None)
    date = data.get('date', None)
    time_start = data.get('time_start', None)
    time_end = data.get('time_end', None)
    location_id = data.get('location', None)
    interviewers = data.get('interviewers', None)
    email_temp_id = data.get('email_template', None)
    email_sub = data.get('email_sub', None)
    email_msg = data.get('email_msg', None)
    interview_id = data.get('id', None)
    send_email = data.get('send_email', None)
    placeholders = data.get('placeholders', [])
    dynamic_interview_data = data.get('dynamic_interview_data', {})
    
    if not job_id:
        return getErrorResponse('Job required')

    job = Job.getById(job_id)
    
    if not job or not job.published:
        return getErrorResponse('Invalid or Unpublished Job Select')

    if not candidate_id:
        return getErrorResponse('Candidate required')
    
    candidate = Candidate.getById(candidate_id)
    if not candidate:
        return getErrorResponse('Candidate not found')

    if not title:
        return getErrorResponse('title required')

    # if not type or type not in Interview.INTEVIEW_TYPE_LIST:
    if not type:
        return getErrorResponse('Select interview type')

    if not date:
        return getErrorResponse('Interview date required')

    if not time_start:
        return getErrorResponse('Interview start time required')

    if not time_end:
        return getErrorResponse('Interview end time required')

    location = None
    company = Company.getByUser(request.user)
    # company = request.data.get('company')
    # company = Company.getById(company)
    if type == Interview.IN_PERSON: 
        if not location_id:
            return getErrorResponse('Interview location is required for In person interview')
        location = Location.getById(location_id, company)
        print(location, 'location here')
        if not location:
            return getErrorResponse('Location not found')
    accounts = []
    
    if interviewers:
            try:
                if isinstance(interviewers, (int, str)):
                    interviewers = [interviewers]
                # Handle JSON string or list
                interviewers = json.loads(interviewers) if isinstance(interviewers, str) else interviewers
                
                for user_id in interviewers:
                    user = Contacts.getById(user_id, company)
                    if user:
                        accounts.append(user)
            except:
                return getErrorResponse('Invalid interviewers data')

    if not email_temp_id:
        return getErrorResponse('Email template required')

    email_template = EmailTemplate.getById(email_temp_id, company)
    if not email_template:
        return getErrorResponse('Email template not found')       
    
    # if not email_sub:
    #     return getErrorResponse('Email subject required')  

    # if not email_msg:
    #     return getErrorResponse('Email message required')           
     
    interview = None

    if interview_id:
        interview = Interview.getById(interview_id, job)
        if not interview:
            return getErrorResponse('Interview not found')
    else:
        interview = Interview()

    if request.FILES != None:
        print("files")
        print(request.FILES)
        if 'attachment' in request.FILES:
            document = request.FILES['attachment']
            interview.document = document    

    interview.title = title
    interview.job = job
    interview.candidate = candidate
    # updating pipeline stage
    candidate.pipeline_stage = 'Interview'
    candidate.pipeline_stage_status = 'Interview Scheduled'
    interview.date = date
    interview.time_start = time_start
    interview.time_end = time_end
    interview.email_temp = email_template
    interview.email_sub = email_sub
    interview.email_msg = email_msg
    interview.location = location
    # interview.interviewers = accounts
    interview.company = company
    # interview.type = type

    # Ensure dynamic_interview_data includes proper Schedule section with date and time
    if dynamic_interview_data:
        # Update or create Schedule section with model date/time fields
        schedule_data = dynamic_interview_data.get('Schedule', {})
        schedule_data.update({
            'date': date,
            'time': time_start,
            'end_time': time_end,
            'duration': calculate_duration(time_start, time_end) if time_start and time_end else None,
            'time_zone': {
                'id': 'Asia/Calcutta',
                'name': 'Asia/Calcutta'
            }
        })
        dynamic_interview_data['Schedule'] = schedule_data
    else:
        # Create new dynamic_interview_data with Schedule section
        dynamic_interview_data = {
            'Schedule': {
                'date': date,
                'time': time_start,
                'end_time': time_end,
                'duration': calculate_duration(time_start, time_end) if time_start and time_end else None,
                'time_zone': {
                    'id': 'Asia/Calcutta',
                    'name': 'Asia/Calcutta'
                }
            }
        }

    interview.dynamic_interview_data = dynamic_interview_data

    candidate.save()
    interview.save()

    if accounts:
        interview.interviewers.set(accounts)

    CandidateTimeline.log_activity(candidate, 'INTERVIEW_SCHEDULED', 'Interview Scheduled', performed_by=request.user, interview=interview)
    JobTimeline.log_activity(job=job,candidate=candidate, activity_type= 'INTERVIEW_SCHEDULED', title= 'Interview Scheduled',description=f"Interview scheduled", performed_by=request.user, interview=interview)

    sendInterviewMail(request.user, interview, candidate, email_template, email_sub, email_msg, placeholders)

    return {
        'code': 200,
        'msg': 'Interview scueduled sucessfully!'
    }
    
def sendInterviewMail(account, interview, candidate, email_template, email_sub, email_msg, template_keys):
    email_data = EmailSettings.objects.filter(user_id=account.pk).order_by('-created_at').first()
    
    if email_data is None:
        return {
            'code': 403,
            'message': 'EmailSmtp for the user does not exist.',
        }
    placeholders = generate_placeholders(template_keys, interview, candidate, account)    
    
    sendMail = InterviewMailer(account, interview, email_data, candidate, placeholders)
    sendMail.start()

    return {
        'code': 200,
        'message': 'Mail sent',
    }     
    
def generate_placeholders(template_keys, interview, candidate, account):
    placeholders = {}
    # Mapping of model fields to placeholder keys
    model_mapping = {
        'interview': interview,
        'candidate': candidate,
        'user': account,
        'job': interview.job,
    }
    
    for key in template_keys:
        # Split the key to get the model and field
        parts = key.split('_')
        model_name = parts[0]
        field_name = '_'.join(parts[1:])
        
        # Get the model instance
        model_instance = model_mapping.get(model_name)
        
        if model_instance:
            if model_name == 'job' and field_name == 'company':
                value = model_instance.company.name if model_instance.company else ''
            elif model_name == 'interview' and field_name == 'location':
                value = model_instance.location.name if model_instance.location else ''
            elif model_name == 'interview' and field_name == 'interviewers':
                interviewers = model_instance.interviewers.all()
                value = ', '.join([f"{user.name} ({user.mobile}) ({user.email})" for user in interviewers if user])
            else:
                value = getattr(model_instance, field_name, '')
                if callable(value):
                    value = value()
            placeholders[key] = value
    
    return placeholders      

def getInterviews(request):
    user = request.user
    company = Company.getByUser(user)

    job_id = request.GET.get('job_id')
    candidate_id = request.GET.get('candidate_id')

    interviews = []

    if job_id:
        if user.is_superuser:
            job = Job.objects.get(id=job_id)
        else:
            job = Job.getByIdAndCompany(job_id, company)
        
        if not job:
            return getErrorResponse('Job not found')
        
        interviews = Interview.getByJob(job)
    
    elif candidate_id:
        if user.is_superuser:
            candidate = Candidate.objects.get(id=candidate_id)
        else:
            candidate = Candidate.getByIdAndCompany(candidate_id, company)
        
        if not candidate:
            return getErrorResponse('Candidate not found')
        
        interviews = Interview.getByCandidate(candidate)
    
    else:
        if user.is_superuser:
            interviews = Interview.objects.all().order_by('-updated')
        else:
            interviews = Interview.objects.filter(company=company).order_by('-updated')
            
    serializer = InterviewListSerializer(interviews, many=True)

    return {
        'code': 200,
        'list': serializer.data
    }

def delteInterview(request):

    company = Company.getByUser(request.user)
    interview_id = request.GET.get('id')
    
    if request.user.is_superuser:
        # Superuser can access any interview by ID
        interview = Interview.objects.get(id=interview_id)
    else:
        # Regular users can only access interviews associated with their company
        interview = Interview.getByIdAndCompany(interview_id, company)

    if interview:
        interview.delete()

        return {
            'code': 200,
            'msg': 'Interview deleted successfully'
        }
    
    return getErrorResponse('Interview not found')

def interviewDetails(request):

    company = Company.getByUser(request.user)
    interview_id = request.GET.get('id')
    
    if request.user.is_superuser:
        interview = Interview.objects.get(id=interview_id)
    else:
        interview = Interview.getByIdAndCompany(interview_id, company)    

    if not interview:
        return getErrorResponse('Interview not found')

    serializer = InterviewDetailsSerializer(interview)

    return {
        'code': 200,
        'data': serializer.data
    }
    
def updateInterviewDetails(request):
    
    interview_id = request.data.get('id')
    interviewers = request.data.get('interviewers')
    company = Company.getByUser(request.user)
    interview = Interview.getByIdAndCompany(interview_id, company)

    if not interview:
        return getErrorResponse({'code': 404, 'message': 'Interview not found'})
    
    if interviewers is not None:
        try:
            accounts = []
            # Handle single integer
            if isinstance(interviewers, int):
                user = Contacts.getById(interviewers, company)
                if user:
                    accounts = [user]
            # Handle list or string
            else:
                # Convert JSON string to list if needed
                interviewers = json.loads(interviewers) if isinstance(interviewers, str) else interviewers
                # Ensure interviewers is a list
                if not isinstance(interviewers, list):
                    interviewers = [interviewers]
                
                for user_id in interviewers:
                    user = Contacts.getById(user_id, company)
                    if user:
                        accounts.append(user)
            
            # Update interviewers
            interview.interviewers.set(accounts)
        except Exception as e:
            print(f"Error updating interviewers: {str(e)}")
            return getErrorResponse({'code': 400, 'message': 'Invalid interviewers data'})
        
    candidate_id = request.data.get('candidate')
    if candidate_id is not None:
        candidate = Candidate.getById(candidate_id)
        if not candidate:
            return getErrorResponse({'code': 400, 'message': 'Candidate not found'})
        interview.candidate = candidate
    
    location_id = request.data.get('location_id')
    if location_id is not None:
        location = Location.getById(location_id, company)
        if not location:
            return getErrorResponse({'code': 400, 'message': 'Location not found'})
        interview.location = location

    serializer = InterviewDetailsSerializer(interview, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return {
            'code': 200, 
            'data': serializer.data,
            'msg': 'Interview update sucessfully!'
        }
    return getErrorResponse({'code': 400, 'errors': serializer.errors})
    

def latestInterviewDetails(request):
    
    company = Company.getByUser(request.user)
    days_param = request.GET.get('days')
    # try:
    #     days = max(1, int(days_param))
    # except (TypeError, ValueError):
    #     days = 30
    # days_ago = timezone.now() - timedelta(days=days)
    
    if request.user.is_superuser:
        # interviews = Interview.objects.filter(created__gte=days_ago).order_by('-date','time_start')
        interviews = Interview.objects.all().order_by('-date','time_start')
    else:
        # interviews = Interview.objects.filter(created__gte=days_ago, company=company).order_by('-date', 'time_start')
        interviews =Interview.objects.filter(company=company).order_by('-date','time_start')

    if not interviews:
        return {
            'code': 200,
            'data': []
        }
    serializer = InterviewListSerializer(interviews, many=True)

    return {
        'code': 200,
        'data': serializer.data
    }   

def getJobInterviewsDetails(request):

    job_id = request.GET.get('id')
    
    interviews = []
    
    if job_id:
        if request.user.is_superuser:
            job = Job.objects.get(id=job_id)
        else:
            company = Company.getByUser(request.user)
            
            if not company:
                return getErrorResponse('Company not found')
            job = Job.getByIdAndCompany(job_id, company)
            
        if not job:
            return getErrorResponse('Interviews not found')
        
        interviews = Interview.getByJob(job)
    
    serializer = InterviewListSerializer(interviews, many=True)

    return {
        'code': 200,
        'list': serializer.data
    }
    
def getCandidateInterviewsDetails(request):

    candidate_id = request.GET.get('id')

    interviews = []

    if candidate_id:
        candidate = Candidate.getById(candidate_id)
        if not candidate:
            return getErrorResponse('Interviews not found')
        interviews = Interview.getByCandidate(candidate)
    
    serializer = InterviewListSerializer(interviews, many=True)

    return {
        'code': 200,
        'list': serializer.data
    }