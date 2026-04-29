from job.models import Assesment
from interview.models import Interview
from datetime import datetime, timedelta, time
from django.db.models import Q
from .models import Country, NoteType, State, City, CompanyTags
from .serializer import CountrySerializer, NoteTypeSerializer, StateSerializer, CitySerializer, CompanyTagsSerializer
from common import serializer
from .mail_utils import CandidateMailer
from django.http import HttpResponse
from candidates.models import Mail, Candidate, EmailSettings, CandidateTimeline
from job.models import JobTimeline
from account.models import Company
from django.utils import timezone

def getAllData():

    countryList = Country.getAll()

    countries = CountrySerializer(countryList, many=True)

    stateList = State.getAll()

    states = StateSerializer(stateList, many=True)

    cityList = City.getAll()

    cities = CitySerializer(cityList, many=True)

    return {
        'code': 200,
        'countries': countries.data,
        'states': states.data,
        'cities': cities.data,
    }


def getCountries(request):

    countryList = Country.getAll()
    countries = CountrySerializer(countryList, many=True)
    return {
        'code': 200,
        'countries': countries.data,
    }


def getStatesForCountry(request):

    id = request.GET.get('id', None)
    query = request.GET.get('query', None)
    if not id and not query:
        return {
            'code': 400,
            'msg': 'Country id required'
        }

    if id:
        stateList = State.getByCountry(id)

    if query:
        stateList = State.search(query)
    states = StateSerializer(stateList, many=True)
    return {
        'code': 200,
        'states': states.data,
    }


def getCitiesForState(request):

    id = request.GET.get('id', None)
    query = request.GET.get("query", None)

    if not id and not query:
        return {
            'code': 400,
            'msg': 'State info required'
        }

    if id:
        cityList = City.getByState(id)

    if query:
        cityList = City.search(query)

    cities = CitySerializer(cityList, many=True)
    return {
        'code': 200,
        'cities': cities.data,
    }


def getNoteTypes(request):

    notes = NoteType.getAll()
    serializer = NoteTypeSerializer(notes, many=True)

    return {
        'code': 200,
        'types': serializer.data,
    }


def getCompanyTags(request):

    tags = CompanyTags.getAll()
    serializer = CompanyTagsSerializer(tags, many=True)

    return {
        'code': 200,
        'types': serializer.data,
    }


def sendCandidateMail(request):

    data = request.data
    account = request.user
    try:
        email_data = EmailSettings.objects.filter(user_id=account.pk).order_by('-created_at').first()
        
        if email_data is None:
            return {
                'code': 403,
                'message': 'EmailSmtp for the user does not exist.',
            }
        
        emails = data.get('emails', None) 
        emails = list(emails.split(","))
        
        candidate_id = data.get('candidate_id')
        candidate = Candidate.objects.get(id=candidate_id)
        
        placeholders = data.get('placeholders', [])
        
        job = candidate.job.all()
        
        # Try to get specific interview by interview_id if provided, else all interviews for the candidate
        interview_id = data.get('interview_id')
        if interview_id:
            try:
                from interview.models import Interview as InterviewModel
                interview = InterviewModel.objects.filter(id=interview_id)
            except Exception:
                interview = InterviewModel.objects.filter(candidate=candidate)
        else:
            from interview.models import Interview as InterviewModel
            interview = InterviewModel.objects.filter(candidate=candidate)
        
        assessment = [j.assesment for j in job if getattr(j, 'assesment', None)]

        mail_instance = Mail()
        mail_instance.sender = account
        mail_instance.receiver = emails
        mail_instance.subject = data.get('subject')
        mail_instance.body = data.get('body')
        mail_instance.save()

        sendMail = CandidateMailer(account, data, emails, email_data, candidate, placeholders, job, interview, assessment)
        sendMail.start()
        
        return {
            'code': 200,
            'message': 'mail sent',
        }
    except EmailSettings.DoesNotExist:
        print("EmailSettings for the user does not exist.")
        return {
            'code': 500,
            'message': 'EmailSettings for the user does not exist.',
        }




def returnXML(request):
    xml_data = '''<xml version=\"1.0\" encoding=\"utf-8\">
        <source>
            <job>
                <referencenumber><![CDATA[123456]]></referencenumber>
                <title><![CDATA[Assistant]]></title>
                <company><![CDATA[My Company]]></company>
                <city><![CDATA[Bhopal]]></city>
                <state><![CDATA[Madhyapradesh]]></state>
                <country><![CDATA[India]]></country>
                <dateposted><![CDATA[2019-09-14T12:00:00Z]]></dateposted>
                <url><![CDATA[https://app.edjobster.com]]></url>
                <description><![CDATA[We're looking for employer with 3+ years of experience...]]></description>
                <jobtype><![CDATA[Full time]]></jobtype>
                <benefit><![CDATA[Certificate]]></benefit>
                <category><![CDATA[Engineering]]></category>
                <logo><![CDATA[https://app.edjobster.com/logo]]></logo>
                <talent-apply-data>
                    <![CDATA[talent-apply-posturl=http://www.company1.com/process-applications&talent-apply-questions=http://www.company1a.com/process-applications/questions]]>
                </talent-apply-data>
                <experience> <experience_max> <![CDATA[5]]> </experience_max> <experience_min> <![CDATA[1]]> </experience_min> <period> <![CDATA[year]]> </period> </experience>
            </job>
        </source>'''

    return HttpResponse(xml_data, content_type='application/xml')


def get_combined_timeline(request):
    """
    Get combined timeline activities from both CandidateTimeline and JobTimeline
    
    Args:
        days (int, optional): Number of days to look back for activities. Defaults to 7.
        company_id (int, optional): Filter by company ID
        
    Returns:
        dict: Combined timeline data
    """

    user = request.user
    company = Company.getByUser(user)
    today = timezone.now()

    # Get days parameter from query string
    try:
        days_param = request.GET.get('days', '0')
        if days_param.isdigit():
            days = int(days_param)
            if days == 0:  # Today only
                days = 1
                start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            elif days == 1:  # Yesterday only
                days = 1
                start_date = (today - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                start_date = (today - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)  # Include today
        else:
            days = 1
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    except (TypeError, ValueError):
        days = 1
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)

    if company:
        candidate_activities = CandidateTimeline.objects.filter(
            Q(job__company_id=company.id) |
            Q(candidate__job__company_id=company.id)
        ).distinct()
        job_activities = JobTimeline.objects.filter(
            Q(job__company_id=company.id) |
            Q(candidate__job__company_id=company.id)
        ).distinct()
    elif request.user.is_superuser:
        candidate_activities = CandidateTimeline.objects.all()
        job_activities = JobTimeline.objects.all()
    
    # Apply date filter if period is specified
    if start_date:
        candidate_activities = candidate_activities.filter(
            activity_date__gte=start_date,
            activity_date__lte=today.replace(hour=23, minute=59, second=59, microsecond=999999)
        )
        job_activities = job_activities.filter(
            activity_date__gte=start_date,
            activity_date__lte=today.replace(hour=23, minute=59, second=59, microsecond=999999)
        )
    
    # Combine and sort activities
    all_activities = []
    
    # Process candidate activities
    for activity in candidate_activities:
        job = activity.job.first()
        all_activities.append({
            'id': f"candidate_{activity.id}",
            'type': 'candidate',
            'activity_type': activity.activity_type,
            'title': activity.title,
            'description': activity.description,
            'performed_by': activity.performed_by_name or (activity.performed_by.get_full_name() if activity.performed_by else None),
            'activity_date': activity.activity_date,
            'candidate': {
                'id': activity.candidate_id,
                'name': f"{activity.candidate.first_name} {activity.candidate.last_name}"
            } if activity.candidate else None,
            'job': {
                'id': job.id if job else None,
                'dynamic_job_data': {
                    'address_information': {
                        'city': getattr(job, 'city', None),
                        'state': getattr(job, 'state', None)
                    } if hasattr(job, 'city') or hasattr(job, 'state') else None,
                    'Create Job': {
                        'type': getattr(job, 'job_type', None),
                        'owner': getattr(job, 'owner', None),
                        'title': job.dynamic_job_data['Create Job'].get('title', 'No title')
                    } if hasattr(job, 'job_type') or hasattr(job, 'owner') or hasattr(job, 'title') else None,
                    'currency': getattr(job, 'currency', None),
                    'department': getattr(job, 'department', None),
                    'educations': getattr(job, 'educations', None),
                    'experience': {
                        'min': getattr(job, 'exp_min', None),
                        'max': getattr(job, 'exp_max', None)
                    } if hasattr(job, 'exp_min') or hasattr(job, 'exp_max') else None,
                    'members': getattr(job, 'members', None),
                    'nature': getattr(job, 'nature', None),
                    'salary': {
                        'min': getattr(job, 'salary_min', None),
                        'max': getattr(job, 'salary_max', None),
                        'type': getattr(job, 'salary_type', None)
                    } if hasattr(job, 'salary_min') or hasattr(job, 'salary_max') or hasattr(job, 'salary_type') else None,
                    'speciality': getattr(job, 'speciality', None)
                } if job else None
            } if job else None,
            'related_data': {
                'note': activity.related_note_id,
                'task': activity.related_task_id,
                'event': activity.related_event_id,
                'call': activity.related_call_id,
                'interview': activity.interview_id,
                'document': activity.document
            },
            'status_change': {
                'old': activity.old_status,
                'new': activity.new_status,
                'pipeline_stage': activity.pipeline_stage,
                'pipeline_stage_status': activity.pipeline_stage_status
            } if any([activity.old_status, activity.new_status, activity.pipeline_stage, activity.pipeline_stage_status]) else None
        })
    
    # Process job activities
    for activity in job_activities:
        job = activity.job
        all_activities.append({
            'id': f"job_{activity.id}",
            'type': 'job',
            'activity_type': activity.activity_type,
            'title': activity.title,
            'description': activity.description,
            'performed_by': activity.performed_by_name or (activity.performed_by.get_full_name() if activity.performed_by else None),
            'activity_date': activity.activity_date,
            'job': {
                'id': activity.job_id,
                'dynamic_job_data': {
                    'address_information': {
                        'city': getattr(job, 'city', None),
                        'state': getattr(job, 'state', None)
                    } if hasattr(job, 'city') or hasattr(job, 'state') else None,
                    'Create Job': {
                        'type': getattr(job, 'job_type', None),
                        'owner': getattr(job, 'owner', None),
                        'title': job.dynamic_job_data['Create Job'].get('title', 'No title')
                    } if hasattr(job, 'job_type') or hasattr(job, 'owner') or hasattr(job, 'title') else None,
                    'currency': getattr(job, 'currency', None),
                    'department': getattr(job, 'department', None),
                    'educations': getattr(job, 'educations', None),
                    'experience': {
                        'min': getattr(job, 'exp_min', None),
                        'max': getattr(job, 'exp_max', None)
                    } if hasattr(job, 'exp_min') or hasattr(job, 'exp_max') else None,
                    'members': getattr(job, 'members', None),
                    'nature': getattr(job, 'nature', None),
                    'salary': {
                        'min': getattr(job, 'salary_min', None),
                        'max': getattr(job, 'salary_max', None),
                        'type': getattr(job, 'salary_type', None)
                    } if hasattr(job, 'salary_min') or hasattr(job, 'salary_max') or hasattr(job, 'salary_type') else None,
                    'speciality': getattr(job, 'speciality', None)
                } if job else None
            } if activity.job_id else None,
            'candidate': {
                'id': activity.candidate_id,
                'name': f"{activity.candidate.first_name} {activity.candidate.last_name}" if activity.candidate else None
            } if activity.candidate_id else None,
            'related_data': {
                'note': activity.related_note_id,
                'task': activity.related_task_id,
                'event': activity.related_event_id,
                'call': activity.related_call_id,
                'interview': activity.interview_id,
                'document': activity.document
            },
            'status_change': {
                'old': activity.old_status,
                'new': activity.new_status,
                'pipeline_stage_status': activity.pipeline_stage_status
            } if any([activity.old_status, activity.new_status, activity.pipeline_stage_status]) else None
        })
    
    # Sort all activities by date (newest first)
    all_activities.sort(key=lambda x: x['activity_date'], reverse=True)
    
    return {
        'success': True,
        'count': len(all_activities),
        'period': {
            'start': start_date,
            'end': today
        },
        'results': all_activities
    }
