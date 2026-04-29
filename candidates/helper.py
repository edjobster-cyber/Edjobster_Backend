from collections import namedtuple
import email
from math import degrees
import base64
import re
from unicodedata import category
from venv import create
from account import serializer
from account.models import Account, Company, TokenEmailVerification, TokenResetPassword
import candidates
import job
from job.models import Job, JobNotes
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import authenticate
from common.utils import isValidUuid, getErrorResponse, getDomainFromEmail
from common.models import Country, NoteType, State, City
import json
from settings.models import Degree, Department, Pipeline, Webform, UnsubscribeLink
from .models import Candidate, CandidateExperience, CandidateQualification, Note, ResumeFiles, ApplicantWebForm, EmailSettings, Candidatewithoutlogin, Skill, SubjectSpecialization, CandidateTimeline,SavedJob,CandidateResume,CandidateProfile
from .serializer import CandidateExperienceSerializer, CandidateListSerializer, CandidateDetailsSerializer, CandidateQualificationSerializer, NoteSerializer, EmailSettingsSerializer, SkillSerializer, SubjectSpecializationSerializer, CandidateTimelineSerializer, CandidateSerializer,SavedJobSerializer,CandidateResumeSerializer,CandidateProfileSerializer
from common.encoder import decode
from django.utils.dateparse import parse_date
from common.utils import parseDate
from datetime import date, datetime, timedelta    
from django.conf import settings
import requests
from django.core.paginator import Paginator
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Candidate, SavedJob
from job.serializer import JobNotesSerializer, getCandidateApplyJobCareerSerializer,JobSearchSerializer
from django.db.models import Q
from common.mail_utils import CandidateBulkMailer
from django.core.mail import get_connection
from django.db.models import Count
from django.db.models import Avg, F, Q as djQ
from django.utils import timezone

PAGE_SIZE = 30

def applyJob(request):

    data = request.data

    first_name = data.get('first_name', None)
    middle_name = data.get('middle_name', None)
    last_name = data.get('last_name', None)
    job_id = data.get('job_id', None)
    phone = data.get('phone', None)

    # Making phone compulsary
    mobile = data.get('mobile', None)
    if mobile is None or len(mobile)!=10:
        return getErrorResponse("Please provide candidate Mobile No.")

    if Candidate.objects.filter(mobile = mobile).exists():
        return getErrorResponse("Canidate with this Mobile No. is already registered")

    # removing duplicate entries
    email = data.get('email', None)
    if email is None or len(str(email).strip())==0:
        return getErrorResponse("Please provide candidate email")

    if Candidate.objects.filter(email=email).exists() or Candidate.objects.filter(alternate_email=email).exists():
        return getErrorResponse("Canidate with this email is already registered")
    
    email_alt = data.get('email_alt', None)
    marital_status = data.get('marital_status', None)
    date_of_birth = data.get('date_of_birth', None)
    last_applied = data.get('last_applied', None)

    street = data.get('street', None)
    pincode = data.get('pincode', None)
    city = data.get('city', None)
    state_id = data.get('state_id', None)

    exp_years = data.get('exp_years', 0)
    exp_months = data.get('exp_months', 0)
    qualification = data.get('qualification', None)
    cur_job = data.get('cur_job', None)
    cur_employer = data.get('cur_employer', None)
    certifications = data.get('certifications', None)
    fun_area = data.get('fun_area', None)
    subjects = data.get('subjects', None)
    skills = data.get('skills', None)

    if not job_id:
        return getErrorResponse('Job id required')

    job = Job.getById(int(job_id))
    if not job:
        return getErrorResponse('Invalid Job')

    if not first_name:
        return getErrorResponse('First name required')
    if not last_name:
        return getErrorResponse('Last name required')
    # if not mobile:
    #     return getErrorResponse('mobile required')
    # if not email:
    #     return getErrorResponse('email required')
    # if not date_of_birth:
    #     return getErrorResponse('Date of birth required')

    # dob = parseDate(date_of_birth)
    # if not dob:
    #     return getErrorResponse('Invalid date of birth')
    
    # age = ((date.today() - dob).days) / 365
    # print('Age', age)

    # if age < 18:
    #     return getErrorResponse("You are under age!")

    # if not marital_status:
    #     return getErrorResponse('Marital status required')

    # if marital_status not in Candidate.MARITAL_STATUS_LIST:
    #     return getErrorResponse('Invalid marital status')

    # if not street:
    #     return getErrorResponse('Street required')          
    # if not pincode:
    #     return getErrorResponse('pincode required')  
     
    # if int(pincode) != pincode and len(str(pincode)) != 6:
    #     return getErrorResponse('invalid pincode')   
    # if not city:
    #     return getErrorResponse('city required')          
    # if not state_id:
    #     return getErrorResponse('state required')     

    # state = State.getById(state_id)       
    # if not state:
    #     return getErrorResponse('invalid state')     

    # if not exp_years :
    #     return getErrorResponse('Experience year required')     

    # if not qualification:
    #     return getErrorResponse('qualification required')    

    # if qualification not in Candidate.QUALIFICATION_LIST:
    #     return getErrorResponse('Invalid Qualification')    

    candidate = Candidate()
        
    if request.FILES != None:
        print("files")
        print(request.FILES)
        if 'resume' in request.FILES:
            resume = request.FILES['resume']
            candidate.resume = resume
            url = ''
            filename = ''
            if candidate == None:
                resume = ResumeFiles()
                resume.resume = resume
                resume.save()
                # For production
                # url = settings.RESUME_FILE_URL+resume.resume.name[11:]

                # For developement
                url = str(resume.resume.path)
                filename = resume.resume.name

            else:
                # For production
                # url = settings.RESUME_FILE_URL+candidate.resume.name[13:]

                # For developement
                url = settings.RESUME_URL_ROOT+str(candidate.resume.name)
                filename = candidate.resume.name

                
            # For production
            # parse = {
            #     "url": url,
            #     "userkey": settings.RESUME_PARSE_KEY,
            #     "version": settings.RESUME_PARSE_VERSION,
            #     "subuserid": settings.RESUME_PARSE_USER,
            # }

            with open(url, "rb") as pdf_file:
                encoded_resume = base64.b64encode(pdf_file.read())

            encoded_resume = str(encoded_resume)
            encoded_resume = encoded_resume[2:len(encoded_resume)-1]

            # For development
            parse = {
                "filename": str(filename),
                "filedata": str(encoded_resume),
                "userkey": settings.RESUME_PARSE_KEY,
                "version": settings.RESUME_PARSE_VERSION,
                "subuserid": settings.RESUME_PARSE_USER,
            }

            response = requests.post(settings.RESUME_PARSE_BINARY_URL, data=json.dumps(parse))

            if response.status_code == 200:
                res = response.json()
                if 'error' in res:
                    error = res.get('error')
                    return getErrorResponse(str(error.get('errorcode'))+": "+error.get('errormsg'))

                candidate.resume_parse_data = res
                
            else:
                return getErrorResponse('Failed to parse resume')

    candidate.first_name = first_name
    candidate.last_name = last_name
    candidate.middle_name = middle_name
    candidate.email = email
    candidate.alternate_email = email_alt
    candidate.phone = phone
    candidate.mobile = mobile
    candidate.marital_status = marital_status
    # candidate.date_of_birth = dob
    # candidate.age = age
    candidate.last_applied = last_applied
    candidate.street = street
    candidate.last_applied = last_applied
    candidate.street = street
    candidate.pincode = pincode
    candidate.city = city
    candidate.state = state_id
    # candidate.country = ''
    candidate.exp_years = exp_years
    candidate.exp_months = exp_months
    candidate.qualification = qualification            
    candidate.cur_job = cur_job            
    candidate.cur_employer = cur_employer            
    candidate.certifications = certifications            
    candidate.fun_area = fun_area            
    candidate.subjects = subjects            
    candidate.skills = skills
    candidate.job = job

    candidate.save()

    return {
        'code': 200,
        'msg': 'Job application submitted successfully!',
        'data': CandidateDetailsSerializer(candidate).data,
    }            

def getApplications(request):

    company = Company.getByUser(request.user)
    job_id = request.GET.get('job')
    if not job_id:
        return getErrorResponse('Job id required')

    job = Job.getByIdAndCompany((job_id), company)        
    if not job:
        return getErrorResponse('Job not found')

    page_no = request.GET.get('page', 1)  

    try:
        page_no = int(page_no)
    except Exception as e:
        print(e)
        page_no = 1
    
    candidates = Candidate.getByJob(job=job)

    candidates = Paginator(candidates, PAGE_SIZE)

    pages = candidates.num_pages

    if pages >= page_no:
        p1 = candidates.page(page_no)
        lst = p1.object_list
        serializer = CandidateListSerializer(lst, many=True)

        return {
            'code': 200,
            'list': serializer.data,
            'current_page': page_no,
            'total_pages': pages
        }        
    else:
        return getErrorResponse('Page not available')

def deleteApplication(request):
    candidate_id = request.GET.get('id')
    if not candidate_id:
        return getErrorResponse('Invalid request')

    company = Company.getByUser(request.user)

    candidate = Candidate.getByIdAndCompany(candidate_id, company)

    if candidate:
        candidate.delete()

        return {
            'code': 200,
            'msg': 'Candidate deleted successfully'
        }
    
    return getErrorResponse('Candidate not found')

def candidateDetails(request):
    candidate_id = request.GET.get('id')

    if not candidate_id:
        return getErrorResponse('Invalid request')

    # candidate = Candidate.getByIdAndCompany(candidate_id, request.user.company_id)
    candidate = get_object_or_404(Candidate, id=candidate_id)

    if not candidate:
        return getErrorResponse('Candidate not found')

    serializer = CandidateDetailsSerializer(candidate)

    # candidates = Candidate.objects.filter(job__company=request.user.company).order_by('id')
    prev_candidate = Candidate.objects.filter(Q(id__lt=candidate.id) & Q(job__company=request.user.company_id)).last()
    next_candidate = Candidate.objects.filter(Q(id__gt=candidate.id) & Q(job__company=request.user.company_id)).first()
    
    return {
        'code': 200,
        'data': serializer.data,
        'previous_id': prev_candidate.id if prev_candidate else None,
        'next_id': next_candidate.id if next_candidate else None,
    }


def updateApplication(request):

    data = request.data

    candidate_id = data.get('id', None)
    first_name = data.get('first_name', None)
    middle_name = data.get('middle_name', None)
    last_name = data.get('last_name', None)
    job_id = data.get('job_id', None)
    phone = data.get('phone', None)
    mobile = data.get('mobile', None)
    email = data.get('email', None)
    email_alt = data.get('email_alt', None)
    marital_status = data.get('marital_status', None)
    date_of_birth = data.get('date_of_birth', None)
    last_applied = data.get('last_applied', None)

    street = data.get('street', None)
    pincode = data.get('pincode', None)
    city = data.get('city', None)
    state_id = data.get('state_id', None)

    exp_years = data.get('exp_years', None)
    exp_months = data.get('exp_months', 0)
    qualification = data.get('qualification', None)
    cur_job = data.get('cur_job', None)
    cur_employer = data.get('cur_employer', None)
    certifications = data.get('certifications', None)
    fun_area = data.get('fun_area', None)
    subjects = data.get('subjects', None)
    skills = data.get('skills', None)

    if not candidate_id:
        return getErrorResponse('Invalid request')


    # company = request.data.get('company')
    # company = Company.getById(company)

    company = Company.getByUser(request.user)
    candidate = Candidate.getByIdAndCompany(candidate_id, company)
    
    if not candidate:
        return getErrorResponse('candidate not found')

    if not job_id:
        return getErrorResponse('Job id required')

    job = Job.getById(job_id)
    if not job:
        return getErrorResponse('Invalid Job')

    if not first_name:
        return getErrorResponse('First name required')
    if not last_name:
        return getErrorResponse('Last name required')
    if not date_of_birth:
        return getErrorResponse('Date of birth required')
    if not marital_status:
        return getErrorResponse('Marital status required')
    if not street:
        return getErrorResponse('Street required')          
    if not pincode:
        return getErrorResponse('pincode required')  
     
    if len(pincode) != 6:
        print(pincode, len(pincode))
        return getErrorResponse('invalid pincode')   
    if not city:
        return getErrorResponse('city required')          
    if not state_id:
        return getErrorResponse('state required')     

    state = State.getById(state_id)       
    if not state:
        return getErrorResponse('invalid state')     

    if int(exp_years) != exp_years:
        return getErrorResponse('Experience year required')     

    if exp_months:
        if exp_months != int(exp_months):
            return getErrorResponse('invalid experience months')   

    if not qualification:
        return getErrorResponse('qualification required')    

    if candidate.email != email:
        candidate = Candidate.getByEmail(job=job, email=email)
        if candidate:
            return getErrorResponse("Email already exists for other candidate")
    if Candidate.getByPhone(job=job, mobile=mobile):
        return getErrorResponse("Mobile already exists for other candidate")

    if request.FILES != None:
        print("files")
        print(request.FILES)
        if 'resume' in request.FILES:
            resume = request.FILES['resume']
            candidate.resume = resume
            url = ''
            filename = ''
            if candidate == None:
                resume = ResumeFiles()
                resume.resume = resume
                resume.save()
                # For production
                # url = settings.RESUME_FILE_URL+resume.resume.name[11:]

                # For developement
                url = settings.RESUME_URL_ROOT+str(resume.resume.name)
                filename = resume.resume.name

            else:
                # For production
                # url = settings.RESUME_FILE_URL+candidate.resume.name[13:]

                # For developement
                url = settings.RESUME_URL_ROOT+str(candidate.resume.name)
                filename = candidate.resume.name

                
            # For production
            # parse = {
            #     "url": url,
            #     "userkey": settings.RESUME_PARSE_KEY,
            #     "version": settings.RESUME_PARSE_VERSION,
            #     "subuserid": settings.RESUME_PARSE_USER,
            # }

            with open(url, "rb") as pdf_file:
                encoded_resume = base64.b64encode(pdf_file.read())

            encoded_resume = str(encoded_resume)
            encoded_resume = encoded_resume[2:len(encoded_resume)-1]

            # For development
            parse = {
                "filename": str(filename),
                "filedata": str(encoded_resume),
                "userkey": settings.RESUME_PARSE_KEY,
                "version": settings.RESUME_PARSE_VERSION,
                "subuserid": settings.RESUME_PARSE_USER,
            }

            response = requests.post(settings.RESUME_PARSE_BINARY_URL, data=json.dumps(parse))

            if response.status_code == 200:
                res = response.json()
                if 'error' in res:
                    error = res.get('error')
                    return getErrorResponse(str(error.get('errorcode'))+": "+error.get('errormsg'))

                candidate.resume_parse_data = res
                
            else:
                return getErrorResponse('Failed to parse resume')


    candidate.first_name = first_name            
    candidate.last_name = last_name            
    candidate.middle_name = middle_name            
    candidate.email = email            
    candidate.alternate_email = email_alt            
    candidate.phone = phone            
    candidate.mobile = mobile            
    candidate.marital_status = marital_status            
    candidate.date_of_birth = date_of_birth            
    candidate.last_applied = last_applied            
    candidate.street = street            
    candidate.last_applied = last_applied            
    candidate.street = street            
    candidate.pincode = pincode            
    candidate.city = city            
    candidate.state = state            
    candidate.country = state.country          
    candidate.exp_years = exp_years            
    candidate.exp_months = exp_months            
    candidate.qualification = qualification            
    candidate.cur_job = cur_job            
    candidate.cur_employer = cur_employer            
    candidate.certifications = certifications            
    candidate.fun_area = fun_area            
    candidate.subjects = subjects            
    candidate.skills = skills
    print(candidate, 'candidate here')
    candidate.save()

    return {
        'code': 200,
        'msg': 'Job application submitted sucessfully!'
    }                

def updateResume(request):

    data = request.data

    candidate_id = data.get('id', None)

    if not candidate_id:
        return getErrorResponse('Invalid request')

    company = Company.getByUser(request.user)
    candidate = Candidate.getByIdAndCompany(candidate_id, company)
    
    if not candidate:
        return getErrorResponse('candidate not found')

    print("files")
    print(request.FILES)

    if request.FILES != None:
 
        if 'resume' in request.FILES:
            resume = request.FILES['resume']
            candidate.resume = resume    
            candidate.save()
            data = parseResume(request, candidate)
            if data.get('code') == 200:
                candidate.resume_parse_data = data.get('data')

            candidate.save()

            return {
                'code': 200,
                'msg': 'Resume updated!'
            }         
    return getErrorResponse('Resume required!')                       

def parseResume(request, candidate=None):

    if request.FILES != None:
        print("files")
        print(request.FILES)
        if 'resume' in request.FILES:
            file = request.FILES['resume']
            url = ''
            filename = ''
            if candidate == None:
                resume = ResumeFiles()
                resume.resume = file
                resume.save()
                # For production
                # url = settings.RESUME_FILE_URL+resume.resume.name[11:]

                # For developement
                url = str(resume.resume.path)
                filename = resume.resume.name

            else:
                # For production
                # url = settings.RESUME_FILE_URL+candidate.resume.name[13:]

                # For developement
                url = settings.RESUME_URL_ROOT+str(candidate.resume.name)
                filename = candidate.resume.name

                
            # For production
            # parse = {
            #     "url": url,
            #     "userkey": settings.RESUME_PARSE_KEY,
            #     "version": settings.RESUME_PARSE_VERSION,
            #     "subuserid": settings.RESUME_PARSE_USER,
            # }

            with open(url, "rb") as pdf_file:
                encoded_resume = base64.b64encode(pdf_file.read())

            encoded_resume = str(encoded_resume)
            encoded_resume = encoded_resume[2:len(encoded_resume)-1]

            # For development
            parse = {
                "filename": str(filename),
                "filedata": str(encoded_resume),
                "userkey": settings.RESUME_PARSE_KEY,
                "version": settings.RESUME_PARSE_VERSION,
                "subuserid": settings.RESUME_PARSE_USER,
            }

            response = requests.post(settings.RESUME_PARSE_BINARY_URL, data=json.dumps(parse))

            if response.status_code == 200:
                res = response.json()
                if 'error' in res:
                    error = res.get('error')
                    return getErrorResponse(str(error.get('errorcode'))+": "+error.get('errormsg'))

                return {
                    'code': 200,
                    'data': res
               } 
                
            else:
                return getErrorResponse('Failed to parse resume')

    return getErrorResponse('Resume required!')          

def getAllNotes(request):
    
    candidate_id = request.GET.get('candidate')
    company = Company.getByUser(request.user)
    # company = request.GET.get('company')
    # company = Company.getById(company)
    
    if not candidate_id:
        return getErrorResponse('Invalid request')

    candidate = Candidate.getByIdAndCompany(candidate_id, company)

    if not candidate:
        return getErrorResponse('Candidate not found')

    return {
        'code': 200,
        'notes': getNotesForCandidate(candidate)
    }

def getNotesForCandidate(candidate):
    notes = Note.getForCandidate(candidate)
    serializer = NoteSerializer(notes, many=True)
    return serializer.data

# def saveNote(request):

#     data = request.data

#     candidate_id = data.get('candidate')
#     if not candidate_id:
#         return getErrorResponse('Invalid request')

#     print("user______",request.user)
#     company = Company.getByUser(request.user)
#     print("company ______",company)
    
#     # company = data.get('company', None)
#     # company = Company.getById(company)

#     candidate = Candidate.getByIdAndCompany(candidate_id, company)

#     if not candidate:
#         return getErrorResponse('Candidate not found')    

#     text = data.get('note', None)        
#     if not text:
#         return getErrorResponse('Note text required')    

#     id = data.get('id', None)
#     if id:
#         note = Note.getById(id, candidate)
#         if not note:
#             return getErrorResponse('Note not found')
#     else:
#         note = Note()

#     note.note = text
#     note.candidate = candidate
#     note.save()

#     return {
#         'code': 200,
#         'msg': 'Note added successfully',
#         'notes': getNotesForCandidate(candidate)
#     }
    
def saveNote(request):
    data = request.data

    candidate_id = data.get('candidate')
    add_to_job_opening = data.get('addToJobOpening', False)
    if not candidate_id:
        return getErrorResponse('Invalid request')

    company = Company.getByUser(request.user)

    candidate = Candidate.getByIdAndCompany(candidate_id, company)

    if not candidate:
        return getErrorResponse('Candidate not found')    

    text = data.get('note', None)        
    if not text:
        return getErrorResponse('Note text required')    

    id = data.get('id', None)
    if id:
        note = Note.getById(id, candidate)
        if not note:
            return getErrorResponse('Note not found')
    else:
        note = Note()

    note.note = text
    note.candidate = candidate
    note.save()
    
    CandidateTimeline.log_activity(
        candidate=candidate,
        activity_type='NOTE_ADDED',
        title='Note Added',
        description=text[:100] + '...' if len(text) > 100 else text,
        related_note=note,
        performed_by=request.user
    )

    response = {
        'code': 200,
        'msg': 'Note added successfully',
        'notes': getNotesForCandidate(candidate)
    }

    # If add_to_job_opening is True and the candidate has a job, add note to job as well
    if add_to_job_opening and candidate.job:
        job_note = JobNotes()
        job_note.note = text
        job_note.job = candidate.job
        job_note.added_by = request.user
        job_note.save()

        response['msg'] = 'Note added to both candidate and job successfully'
        response['job_notes'] = getNotesForJob(candidate.job)
    elif add_to_job_opening:
        response['msg'] = 'Note added to candidate only (no associated job)'

    return response

def getNotesForJob(job):
    notes = JobNotes.getForJob(job)
    serializer = JobNotesSerializer(notes, many=True)
    return serializer.data
    
    
def updateNote(request):
    data = request.data
    note_id = data.get('id')
    if not note_id:
        return getErrorResponse('Invalid request')

    company = Company.getByUser(request.user)
    note = Note.getByIdAndCompany(note_id, company)

    if not note:
        return getErrorResponse('Note not found')

    text = data.get('note', None)
    if not text:
        return getErrorResponse('Note text required')

    note.note = text
    note.save()

    return {
        'code': 200,
        'msg': 'Note updated successfully',
        'notes': getNotesForCandidate(note.candidate)
    }

    

def deleteNote(request):
    note_id = request.GET.get('id')
    
    if not note_id:
        return getErrorResponse('Invalid request')

    company = Company.getByUser(request.user)

    note = Note.getByIdAndCompany(note_id, company)

    if note:
        candidate = note.candidate
        note.delete()

        return {
            'code': 200,
            'msg': 'Note deleted successfully',
            'notes': getNotesForCandidate(candidate)
        }
    
    return getErrorResponse('Note not found')


def applyWebformJob(request):

    data = request.data

    print('data', request.data)

    webform_id = data.get('webform_id', None)

    if not webform_id: 
        return getErrorResponse('Webform id required!')

    job_id = data.get('job_id', None)
    if not job_id: 
        return getErrorResponse('Job id required!')


    job = Job.getById(job_id)
    if not job:
        return getErrorResponse('Invalid Job')

    webform = Webform.getById(webform_id, job.company)
    if not webform:
        return getErrorResponse('Invalid Webform')

    first_name = data.get('first_name', None)

    middle_name = data.get('middle_name', None)
    last_name = data.get('last_name', None)
    phone = data.get('phone', None)
    mobile = data.get('mobile', None)
    email = data.get('email', None)
    email_alt = data.get('email_alt', None)
    marital_status = data.get('marital_status', None)
    date_of_birth = data.get('date_of_birth', None)
    last_applied = data.get('last_applied', None)

    street = data.get('street', None)
    pincode = data.get('pincode', None)
    city = data.get('city', None)
    state_id = data.get('state_id', None)

    exp_years = data.get('exp_years', None)
    exp_months = data.get('exp_months', 0)
    qualification = data.get('qualification', None)
    cur_job = data.get('cur_job', None)
    cur_employer = data.get('cur_employer', None)
    certifications = data.get('certifications', None)
    fun_area = data.get('fun_area', None)
    subjects = data.get('subjects', None)
    skills = data.get('skills', None)
    gender = data.get('gender', None)
    age = data.get('age', 0)

    if not webform.form:
        return getErrorResponse('Invalid Webform')

    for item in webform.form:
        print('item', item.get('value', None))
        value = item.get('value', None)
        type = item.get('type', None)
        if value:
            if type == 'file':
                if request.FILES == None or value not in request.FILES:           
                    return getErrorResponse(item.get('name', None)+' is required')
            elif not data.get(value, None):
                return getErrorResponse(item.get('name', None)+' is required')
            
            if 'marital_status' == value:
                if marital_status not in Candidate.MARITAL_STATUS_LIST:
                    return getErrorResponse('Invalid marital status')   
            if 'dob' == value:             
                dob = parseDate(date_of_birth)
                if not dob:
                    return getErrorResponse('Invalid date of birth')
                
                age = ((date.today() - dob).days) / 365
                print('Age', age)

                if age < 18:
                    return getErrorResponse("You are under age!")
            if 'pincode' == value:
                if int(pincode) != pincode and len(str(pincode)) != 6:
                    return getErrorResponse('invalid pincode')   
            if 'qualification' == value:
                if qualification not in Candidate.QUALIFICATION_LIST:
                    return getErrorResponse('Invalid Qualification')   
            if 'gender' == value:
                if gender not in Candidate.GENDER_LIST:
                    return getErrorResponse('Invalid Gender')   
            if 'age' == value:
                if int(age) != age and (int(age) < 18 or int(age) > 75):
                    return getErrorResponse('invalid age')       
            if 'state' == value:
                state = State.getById(state_id)       
                if not state:
                    return getErrorResponse('invalid state')                                                          
    
    if not age:
        if date_of_birth:
            age = ((date.today() - date_of_birth).days) / 365
            print('Age', age)

    candidate = Candidate()
        
    if request.FILES != None:
        print("files")
        print(request.FILES)
        if 'resume' in request.FILES:
            resume = request.FILES['resume']
            candidate.resume = resume    

    candidate.first_name = first_name            
    candidate.last_name = last_name            
    candidate.middle_name = middle_name            
    candidate.email = email            
    candidate.alternate_email = email_alt            
    candidate.phone = phone            
    candidate.mobile = mobile            
    candidate.marital_status = marital_status            
    candidate.date_of_birth = date_of_birth            
    candidate.age = age            
    candidate.last_applied = last_applied            
    candidate.street = street            
    candidate.last_applied = last_applied            
    candidate.street = street            
    candidate.pincode = pincode            
    candidate.city = city 

    if state:           
        candidate.state = state            
        candidate.country = state.country          
    
    candidate.exp_years = exp_years            
    candidate.exp_months = exp_months            
    candidate.qualification = qualification            
    candidate.cur_job = cur_job            
    candidate.cur_employer = cur_employer            
    candidate.certifications = certifications            
    candidate.fun_area = fun_area            
    candidate.subjects = subjects            
    candidate.skills = skills
    candidate.job = job
    candidate.webform = webform

    candidate.save()
    print("Candidate created")

    return {
        'code': 200,
        'msg': 'Job application submitted sucessfully!',
        'data': CandidateDetailsSerializer(candidate)
    }            


def getCandidates(request):
    user = request.user
    company = Company.getByUser(user)
    
    if not company and not user.is_superuser:
        return getErrorResponse('Company required')

    # page_no = request.GET.get('page', 1)  

    # try:
    #     page_no = int(page_no)
    # except Exception as e:
    #     print(e)
    #     page_no = 1
    today = timezone.now().date()
    if user.is_superuser:
        candidates = Candidate.objects.all().order_by('-updated')
    else:
        # candidates = Candidate.objects.filter(job__company=company).distinct().order_by('-id')
        candidates = Candidate.objects.filter((Q(job__company=company) | Q(company=company)) & Q(updated__date__lte=today.date())).distinct().order_by('-updated')
    
    # candidates = Paginator(candidates, PAGE_SIZE)

    # pages = candidates.num_pages

    # if pages >= page_no:
        # p1 = candidates.page(page_no)
        # lst = p1.object_list
    serializer = CandidateListSerializer(candidates, many=True)

    return {
        'code': 200,
        'list': serializer.data,
        # 'current_page': page_no,
        # 'total_pages': pages
    }        
    # else:
    #     return getErrorResponse('Given page not available')


def createCandidate(request):
    
    company = Company.getByUser(request.user)
    
    if not company:
        return getErrorResponse('Company required')

    job_id = request.data.get("job_id")
    job = Job.getByIdAndCompany(job_id, company)
    if not job:
        return getErrorResponse('job_id is missing or incorrect')
    
    email = request.data.get("email")
    if email is None or len(str(email).strip())==0:
        return getErrorResponse("Please provide candidate email")

    if Candidate.objects.filter(email=email).exists() or Candidate.objects.filter(alternate_email=email).exists():
        return getErrorResponse("Canidate with this email is already registered")


    webform_id = request.data.get("webform_id", None)
    form_filled = request.data.get("form_filled", None)

    if webform_id != None:
        if form_filled != None:
            empty_webform = Webform.getById(webform_id, company)
            filled_webform = Webform()
            filled_webform.company = company
            filled_webform.form = form_filled

        else:    
            return getErrorResponse('Please provide filled form data')

    if request.FILES['resume']:
        file = request.FILES['resume']
        url = ''
        filename = ''
        resume = ResumeFiles()
        resume.resume = file
        resume.save()
        # For production
        # url = settings.RESUME_FILE_URL+resume.resume.name[11:]

        # For developement
        url = str(resume.resume.path)
        filename = resume.resume.name

        print(url, filename)

        # url = 'https://196034-584727-raikfcquaxqncofqfm.stackpathdns.com/wp-content/uploads/2022/02/Stockholm-Resume-Template-Simple.pdf'
        
        with open(url, "rb") as pdf_file:
            encoded_resume = base64.b64encode(pdf_file.read())

        encoded_resume = str(encoded_resume)
        encoded_resume = encoded_resume[2:len(encoded_resume)-1]

        # For development
        parse = {
            "filename": str(filename),
            "filedata": str(encoded_resume),
            "userkey": settings.RESUME_PARSE_KEY,
            "version": settings.RESUME_PARSE_VERSION,
            "subuserid": settings.RESUME_PARSE_USER,
        }

        response = requests.post(settings.RESUME_PARSE_BINARY_URL, data=json.dumps(parse))
        # response = requests.post(settings.RESUME_PARSE_URL, data=json.dumps(apiParserBody))
        
        if response.status_code == 200:
                res = response.json()
                if 'error' in res:
                    error = res.get('error')
                    print("Resume parsing API didn't return a valid response")
                    return getErrorResponse(str(error.get('errorcode'))+": "+error.get('errormsg'))
                else:
                    if getCandidateFromResumeJson(res)['code'] == 200:
                        candidate = getCandidateFromResumeJson(res)['candidate']
                    else:
                        return {
                            'code': 400,
                            'msg': 'Something went wrong while parsing data from JSON'
                        }
                    candidate.job = job
                    candidate.resume = file
                    candidate.resume_parse_data = res
                    candidateExperiences = getCandidateExperiencesFromResumeJson(res)
                    try:
                        with transaction.atomic():
                            filled_webform.save()
                            candidate.webform = filled_webform
                            candidate.email = email
                            candidateExperiences = getCandidateExperiencesFromResumeJson(res)
                            candidateQualifications = getCandidateQualificationsFromResumeJson(res)
                            candidate.save()

                            for candidateExperience in candidateExperiences:
                                candidateExperience.candidate = candidate
                                candidateExperience.save()
                            
                            for candidateQualification in candidateQualifications:
                                candidateQualification.candidate = candidate
                                candidateQualification.save()
                            
                            candidateSerialized = CandidateDetailsSerializer(candidate)
                            candidateExperiencesSerialized = CandidateExperienceSerializer(candidateExperiences,many = True)
                            candidateQualificationsSerialized = CandidateQualificationSerializer(candidateQualifications,many = True)
                            return {
                                'code': 200,
                                'msg': 'Candidate created successfully',
                                'candidate': candidateSerialized.data,
                                'candidateExp':  candidateExperiencesSerialized.data,
                                'candidateQual': candidateQualificationsSerialized.data
                            }

                    except Exception as e:
                        print("some error occurred while saving the candidate")
                        print(e)
                        return getErrorResponse('Failed to parse resume and create candidate ' + str(e))

        return getErrorResponse("Resume parsing API didn't return a valid response")
    return getErrorResponse('Resume required!')

def getCandidateFromResumeJson(res):
    try:
        candidate = Candidate()
        if res["ResumeParserData"]["Name"]:
            candidate.first_name = res["ResumeParserData"]["Name"]["FirstName"]
            candidate.middle_name = res["ResumeParserData"]["Name"]["MiddleName"]
            candidate.last_name = res["ResumeParserData"]["Name"]["LastName"]

        if len(res["ResumeParserData"]["PhoneNumber"]) > 0:
            candidate.phone = res["ResumeParserData"]["PhoneNumber"][0]["FormattedNumber"]
        
        if len(res["ResumeParserData"]["PhoneNumber"]) > 1:
            candidate.mobile = res["ResumeParserData"]["PhoneNumber"][1]["FormattedNumber"]

        if len(res["ResumeParserData"]["Email"]) > 0:
            candidate.email = res["ResumeParserData"]["Email"][0]["EmailAddress"]
        
        if len(res["ResumeParserData"]["Email"]) > 1:
            candidate.alternate_email = res["ResumeParserData"]["Email"][1]["EmailAddress"]

        if res["ResumeParserData"]["MaritalStatus"]:
            candidate.marital_status = res["ResumeParserData"]["MaritalStatus"]

        if res["ResumeParserData"]["Gender"]:
            candidate.gender = res["ResumeParserData"]["Gender"]

        if res["ResumeParserData"]["DateOfBirth"]:
            candidate.date_of_birth = datetime.strptime(res["ResumeParserData"]["DateOfBirth"], "%d/%m/%Y").strftime("%Y-%m-%d")

        # if len(res["ResumeParserData"]["Address"]) > 0:
        #     candidate.street = res["ResumeParserData"]["Address"][0]["Street"]
        #     candidate.pincode = res["ResumeParserData"]["Address"][0]["ZipCode"]
        #     candidate.city = res["ResumeParserData"]["Address"][0]["City"]
        #     candidate.state = res["ResumeParserData"]["Address"][0]["State"]
        #     candidate.country = res["ResumeParserData"]["Address"][0]["Country"]

        if res["ResumeParserData"]["WorkedPeriod"]:
            try:
                candidate.exp_years = int ( float(res["ResumeParserData"]["WorkedPeriod"]["TotalExperienceInYear"] ) )
            except Exception as e:
                print("Exception occurred while experience string conv to float")  
            try:
                candidate.exp_months = int (res["ResumeParserData"]["WorkedPeriod"]["TotalExperienceInMonths"])
            except Exception as e:
                print("Exception occurred while experience string conv to int")


        if res["ResumeParserData"]["Summary"]:
            candidate.cur_job = res["ResumeParserData"]["Summary"]

        if res["ResumeParserData"]["JobProfile"]:
            candidate.cur_job = res["ResumeParserData"]["JobProfile"]

        if res["ResumeParserData"]["CurrentEmployer"]:
            candidate.cur_employer = res["ResumeParserData"]["CurrentEmployer"]

        if res["ResumeParserData"]["Certification"]:
            candidate.certifications = res["ResumeParserData"]["Certification"]
        
        if res["ResumeParserData"]["Hobbies"]:
            candidate.fun_area = res["ResumeParserData"]["Hobbies"]
        
        if res["ResumeParserData"]["SkillKeywords"]:
            candidate.skills = res["ResumeParserData"]["SkillKeywords"]
        
        return {
            'code': 200,
            'candidate' : candidate
        }

    except Exception as e:
        print("Exception occured while parsing data from JSON")
        print(e)
        return {
            'code': 400,
            'msg': 'Something went wrong while parsing data from JSON'
        }
    


def getCandidateExperiencesFromResumeJson(res):

    if res["ResumeParserData"]["SegregatedExperience"]:
        candidateExperiences = []
        for experience in res["ResumeParserData"]["SegregatedExperience"]:
            candidateExperience = CandidateExperience()
            if experience["Employer"]["EmployerName"]:
                candidateExperience.employer = experience["Employer"]["EmployerName"]
            if experience["JobProfile"]:
                if experience["JobProfile"]["Title"]:
                    candidateExperience.jobProfile = experience["JobProfile"]["Title"]
                if experience["JobProfile"]["RelatedSkills"]:
                    candidateExperience.skills = getSkillsFromRelatedSkillsArray(experience["JobProfile"]["RelatedSkills"])
            if experience["Location"]:
                candidateExperience.city = experience["Location"]["City"]
                candidateExperience.state = experience["Location"]["State"]
                candidateExperience.country = experience["Location"]["Country"]
            if experience["StartDate"]:
                try:
                    candidateExperience.start_date = datetime.strptime(experience["StartDate"], "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    print("Start date not in desired format")    
            if experience["EndDate"]:
                try:
                    candidateExperience.end_date = datetime.strptime(experience["EndDate"], "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    print("End date not in desired format")
            if experience["JobDescription"]:
                candidateExperience.jobDescription = experience["JobDescription"]
            candidateExperiences.append(candidateExperience)
        
        return candidateExperiences
        
            

def getSkillsFromRelatedSkillsArray(relatedSkills):

    if relatedSkills:
        skillString = ''
        for skill in relatedSkills:
            skillString = skillString + skill["Skill"] + ', '
        return skillString


def getCandidateQualificationsFromResumeJson(res):

    if res["ResumeParserData"]["SegregatedQualification"]:
        qualifications = []
        for qualification in res["ResumeParserData"]["SegregatedQualification"]:
            candidateQualification = CandidateQualification()
            if qualification["Institution"]["Name"]:
                candidateQualification.institue_name = qualification["Institution"]["Name"]
            if qualification["Degree"]:
                candidateQualification.degree = qualification["Degree"]["DegreeName"]
            if qualification["Institution"]["Location"]:
                candidateQualification.city = qualification["Institution"]["Location"]["City"]
                candidateQualification.state = qualification["Institution"]["Location"]["State"]
                candidateQualification.country = qualification["Institution"]["Location"]["Country"]
            if qualification["StartDate"]:
                try:
                    candidateQualification.start_date = datetime.strptime(qualification["StartDate"], "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    print("Start date not in desired format")
            if qualification["EndDate"]:
                try:
                    candidateQualification.end_date = datetime.strptime(qualification["EndDate"], "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    print("End date not in desired format")
            if qualification["Aggregate"]:
                candidateQualification.grade = str (qualification["Aggregate"]["Value"])
                candidateQualification.gradeType = qualification["Aggregate"]["MeasureType"]
            qualifications.append(candidateQualification)
        return qualifications
                      

# def parseResume(request, candidate=None):

#     if request.FILES != None:
#         print("files")
#         print(request.FILES)
#         if 'resume' in request.FILES:
#             file = request.FILES['resume']

#             url = ''
#             if candidate == None:
#                 resume = ResumeFiles()
#                 resume.resume = file
#                 resume.save()
#                 url = settings.RESUME_TEMP_FILE_URL+resume.resume.name[11:]
#             else:
#                 url = settings.RESUME_FILE_URL+candidate.resume.name[13:]

#             parse = {
#                 "url": url,
#                 "userkey": settings.RESUME_PARSE_KEY,
#                 "version": settings.RESUME_PARSE_VERSION,
#                 "subuserid": settings.RESUME_PARSE_USER,
#             }
#             response = requests.post(settings.RESUME_PARSE_URL, data=json.dumps(parse))

#             if response.status_code == 200:
#                 res = response.json()
#                 if 'error' in res:
#                     error = res.get('error')
#                     return getErrorResponse(str(error.get('errorcode'))+": "+error.get('errormsg'))

#                 return {
#                     'code': 200,
#                     'data': res
#                 } 
#             return getErrorResponse('Failed to parse resume')

#     return getErrorResponse('Resume required!') 


# creating a Candidate using the online Form only and not the Resume Parser

def createCandidatewithoutResumeParser(request):

    account = request.user
    
    company = Company.getById(account.company_id)
    if not company:
        return {
            'code': 400,
            'msg': 'Company not found!'
        }

    data = request.data
    print(data)

    job_id = data.get('job_id')
    if not job_id: 
        return getErrorResponse('Bad request')
    
    job = Job.getById(job_id)
    if not job:
        return {
            'code': 400,
            'data': 'Job not found!'
        }

    # entering Candidate Details
    first_name = data.get('first_name')
    if not first_name or len(first_name)<3:
        return {
            'code': 400,
            'msg': 'Enter a valid First Name!'
        }
    
    # Middle Name and last name are optional
    middle_name = data.get('middle_name', None)
    last_name = data.get('last_name', None)

    
    # Checking the mobile number because yess, we are paranoid
    mobile = data.get('mobile', None)
    
    if not mobile or len(mobile)<10:
        return {
            'code': 400,
            'msg': 'Enter a valid Mobile Number!'
        }
    
    if Candidate.getByPhone(job=job, mobile=mobile).exists():
        return getErrorResponse("Mobile Number already exists for other candidate")

    # Checking and validating email because once again we will be acting paranoid!
    email = data.get('email', None)
    if not email or not getDomainFromEmail(email):
        return {
            'code': 400,
            'msg': 'Invalid email address'
        }
    if Candidate.getByEmail(job=job, email=email).exists():
        return getErrorResponse("Email already exists for other candidate")
    
    # optional
    email_alt = data.get('alt_email', None)
    if email_alt and not getDomainFromEmail(email):
        return {
            'code': 400,
            'msg': 'Invalid email address'
        }

    # Checing the oprions in Marital State, because yesss, this could be an error
    marital_status = data.get('marital_status', None)

    # Checking the gender options becauseeee yessss!!! we are paranoid
    gender = data.get('gender', None)

    bachlor_degree = data.get('bachlor_degree', None)
    if not bachlor_degree:
        return {
            'code': 400,
            'msg': 'Please select a bachlor degree!'
        }
    
    
    # front end select, so no validation required
    date_of_birth = data.get('date_of_birth', None)
    last_applied = data.get('last_applied', None)

    age =  data.get('age')
    if int(age)<18:
        return {
            'code': 400,
            'msg' : 'Candidate\'s age should be greater than 18 yrs!'
        }

    pincode = data.get('pincode', None)
    street = data.get('address', None)
    city = data.get('city', None)
    state = data.get('state', None)
    country = data.get('country', None)


    # These are optional fields
    exp_years = data.get('exp_years', None)
    exp_months = data.get('exp_months', None)
    admission_date = data.get('admission_date', None)
    graduation_date = data.get('graduation_date', None)
    resume = data.get('resume', None)    

    job_title = data.get('job_title', None)

    if not job_title:
        return {
            'code': 400,
            'msg': 'Job Title is required!'
        }
    
    alt_mobile = data.get('alt_mobile', None)
    professional_certificates = data.get('professional_certificates', None)
    job_role = data.get('job_role', None)
    carriculum_board = data.get('carriculum_board', None)
    functional_area = data.get('functional_area', None)
    notice_period = data.get('notice_period', None)
    highest_qualification = data.get('highest_qualification', None)
    current_job_title = data.get('current_job_title', None)
    current_job = data.get('current_job', None)
    current_employer = data.get('current_employer', None)
    certifications = data.get('certifications', None)
    subjects = data.get('subjects', None)
    skills = data.get('skills', None)
    summary = data.get('summary', None)

    # FINALLY, The moment where we create our candidate
    candidate = Candidate()
    candidate.job = job
    candidate.first_name = first_name

    candidate.job_title = job_title
    candidate.bachlor_degree = bachlor_degree
    
    if alt_mobile:
        candidate.alternate_mobile = alt_mobile
    
    if professional_certificates:
        candidate.professional_certificate = professional_certificates

    if job_role:
        candidate.job_role = job_role

    if carriculum_board:
        candidate.curriculum_board = carriculum_board

    if highest_qualification:
        candidate.highest_qualification = highest_qualification

    if functional_area:
        candidate.functional_area = functional_area

    if notice_period:
        candidate.notice_period = notice_period

    if current_job_title:
        candidate.current_job_title = current_job_title
    
    if current_job: 
        candidate.cur_job = current_job

    if current_employer:
        candidate.cur_employer = current_employer

    if certifications:
        candidate.certifications = certifications

    if subjects:
        candidate.subjects = subjects
    
    if skills:
        candidate.skills = skills
    
    if summary:
        candidate.summary = summary

    if resume:
        candidate.resume = resume

    if middle_name:
        candidate.middle_name = middle_name

    if last_name:
        candidate.last_name = last_name

    candidate.mobile = mobile
    candidate.email = email
    
    if email_alt: 
        candidate.alternate_email = email_alt

    if marital_status: 
        candidate.marital_status = marital_status
    
    if gender:
        gender = gender
    
    candidate.date_of_birth = date_of_birth
    candidate.age = age
    candidate.last_applied = last_applied
    candidate.pincode = pincode
    candidate.street = street
    candidate.city = city
    candidate.state = State.getById(state)
    candidate.country = Country.getById(country)

    if exp_months:
        candidate.exp_months = exp_months
    
    if exp_years:
        candidate.exp_years = exp_years
    
    if admission_date: 
        candidate.admission_date = admission_date

    if graduation_date:
        candidate.graduation_date = graduation_date
        
    candidate.save()

    candidate_id = Candidate.objects.filter().last()

    serializer = CandidateDetailsSerializer(candidate_id)

    return {
        'code': 200, 
        'data': "Candidate Created Successfully!!",
        'id': serializer.data
    }
    
def uploadCandidateDocument(request):
    candidate_id = request.data.get('candidate_id')
    document_type = request.data.get('document_type')
    
    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        return {"error": "Candidate not found", "status": status.HTTP_404_NOT_FOUND}

    if document_type and 'file' in request.FILES:
        file = request.FILES['file']
        if document_type == 'resume':
            candidate.resume = file
        elif document_type == 'cover_letter':
            candidate.cover_letter = file
        elif document_type == 'certificate':
            candidate.certificate = file
        else:
            return {"error": "Invalid document type", "status": status.HTTP_400_BAD_REQUEST}
    else:
        return {"error": "Document type or file not provided", "status": status.HTTP_400_BAD_REQUEST}

    try:
        candidate.save()
        CandidateTimeline.log_activity(candidate, 'DOCUMENT_UPLOADED', 'Document Uploaded',description=f"Document uploaded successfully",document=file.name, performed_by=request.user)
        return {"message": "Document uploaded successfully", "status": status.HTTP_200_OK}
    except Exception as e:
        return {"error": "Failed to save document", "status": status.HTTP_500_INTERNAL_SERVER_ERROR}

    
def deleteCandidateDocument(request):
    candidate_id = request.data.get('candidate_id')
    try:
        candidate = Candidate.objects.get(id=candidate_id)
    except Candidate.DoesNotExist:
        return {"error": "Candidate not found", "status": status.HTTP_404_NOT_FOUND}

    document_type = request.data.get('document_type')
    if document_type == 'resume':
        candidate.resume.delete(save=True)
    elif document_type == 'cover_letter':
        candidate.cover_letter.delete(save=True)
    elif document_type == 'certificate':
        candidate.certificate.delete(save=True)
    else:
        return {"error": "Invalid document type", "status": status.HTTP_400_BAD_REQUEST}

    return {"message": "Document deleted successfully", "status": status.HTTP_200_OK}


def updatePipelineStatus(request):
    account = request.user

    # Paranoid validation :p
    company = Company.getById(account.company_id)
    if not company:
        return {
            'code': 400,
            'msg': 'Company not found!'
        }
    
    data = request.data

    # Validating the candidate id 
    candidate_id = data.get('id')

    if not candidate_id: 
        return getErrorResponse('Bad request')

    candidate = Candidate.getByIdAndCompany(id=candidate_id, company=company)
    if not candidate:
        return {
            'code': 400,
            'data': 'Candidate not found!'
        }
    
    # Provide valid options from front end
    # candidate = Candidate()
    # candidate.pipeline_stage_status = data.get('pipeline_stage_status')
    # # Need validation
    # # 1. Selected pipeline stage status already exists and same with pipeline stage
    # candidate.pipeline_stage = data.get('pipeline_stage')
    
    # candidate.save()
    # update status of single candidate pipeline    
    # candidate.pipeline_stage_status = data.get('pipeline_stage_status')
    # candidate.pipeline_stage = data.get('pipeline_stage')
    CandidateTimeline.log_activity(candidate, 'STATUS_CHANGED', 'Candidate Pipeline Status Updated',description=f"Candidate Pipeline Status Updated",pipeline_stage_status=f"old: {candidate.pipeline_stage_status} new: {data.get('pipeline_stage_status')}",performed_by=request.user,pipeline_stage=data.get("pipeline_stage"))
    pipeline_stage_status = data.get('pipeline_stage_status')
    pipeline_stage = data.get('pipeline_stage')
    candidate.pipeline_stage_status = pipeline_stage_status
    candidate.pipeline_stage = pipeline_stage

    candidate.save()
    

    return {
        'code': 200, 
        'data': "Candidate Pipeline Updated Successfully!!"
    }

from settings.models import Webform
def saveApplicantWebForms(request):
    
    data = request.data    
    job_id = data.get('job', None)   
    candidate_id = data.get('candidate', None)   
    webform = data.get('webform', None)   
    assingment = data.get('assingment', None)
    form = data.get('form', None)   

    if not candidate_id:
        return {
            'code': 400,
            'msg': 'Candidate required'
        }

    if not job_id:
        return {
            'code': 400,
            'msg': 'Job required'
        }

    # if  not assingment:
    #     return {
    #         'code': 400,
    #         'msg': 'Invalid request'
    #     }        

    if not form:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }
    
    temp_form= json.dumps(form)
    form = json.loads(temp_form)
    job = Job(id=job_id)

    if not job:
        return {
            'code': 400,
            'msg': 'Job does not exist'
        }

    candidate = Candidate(id=candidate_id)
    if not candidate:
        return {
            'code': 400,
            'msg': 'Webform does not exist'
        }
    
    # try:
    instance = ApplicantWebForm()
    instance.job = job
    instance.candidate = candidate
    # if form:
    #     instance.form = json.loads(form)
    if assingment:
        temp_assignment = json.dumps(assingment)

        assingment = json.loads(temp_assignment)

        assingment_updated = []
        for question in assingment:
            question_type = question["type"]
            
            marks = 0
            
            if question_type == 'R':
                
                answer = question["answers"]
                options = question["options"]
                candidateAnswer = question["candidateAnswer"]

                idx = int(candidateAnswer)-1

                print(answer[1])
                marks = answer[idx]

                question["eval"] = marks
                assingment_updated.append(question)
            
            if question_type == 'C':
                
                answer = question["answers"]
                options = question["options"]
                candidateAnswer = question["candidateAnswer"]

                marks = 0
                for cid in candidateAnswer:
                    if cid:
                        idx = int(cid)-1
                        marks += int(answer[idx])

                question["eval"] = marks
                assingment_updated.append(question)
            
            if question_type == 'T':

                if len(question["candidateAnswer"][0])>0:
                    marks = question["marks"]
                
                question["eval"] = marks
                assingment_updated.append(question)

            if question_type == 'S':
                
                answer = question["answers"]
                options = question["options"]
                candidateAnswer = question["candidateAnswer"]

                idx = int(candidateAnswer)-1

                marks = answer[idx]

                question["eval"] = marks
                assingment_updated.append(question)

        instance.assingment = assingment_updated

    if webform:
        temp_webform = json.dumps(webform)
        instance.webform = json.loads(temp_webform)

    instance.form = form
    instance.save()
    
    return {
        'code': 200,
        'msg': 'Applicant webform created successfully',
    }

def assignJob(request):
    account = request.user

    # Paranoid validation :p
    company = Company.getById(account.company_id)
    if not company:
        return {
            'code': 400,
            'msg': 'Company not found!'
        }
    
    job_id = request.data.get('job', None)   
    candidate_id = request.data.get('candidate', None) 

    candidate = Candidate.getByIdAndCompany(id=candidate_id, company=company)
    if not candidate:
        return {
            'code': 400,
            'data': 'Candidate not found!'
        }
    job = Job.getById(int(job_id))
    if not job:
        return {
            'code': 400,
            'msg': 'Job does not exist'
        }
    
    candidate.job = job
    candidate.save()

    return {
        'code': 200,
        'msg': 'Updated Job of the candidate',
    }


def getCandidateStats(request):

    # paranoid company check 
    company = Company.getByUser(request.user)

    # company = request.GET.get('company')
    # company = Company.getById(company)

    if not company: 
        return getErrorResponse("Company not found!!")

    candidate = request.GET.get('candidate')
    candidate = Candidate.getById(candidate)
    if not candidate:
        return getErrorResponse('Invalid request')
    

    pipeline_stage_stats = {}
    pipeline_stage_status_stats = {}

    # For pipeline stage list
    if candidate.pipeline_stage:
        if str(candidate.pipeline_stage) in pipeline_stage_stats.keys():
            pipeline_stage_stats[str(candidate.pipeline_stage)] += 1
        else:
            pipeline_stage_stats[str(candidate.pipeline_stage)] = 1

    # For pipeline stage status
    if candidate.pipeline_stage_status:
        if str(candidate.pipeline_stage_status) in pipeline_stage_status_stats.keys():
            pipeline_stage_status_stats[str(candidate.pipeline_stage_status)] += 1
        else:
            pipeline_stage_status_stats[str(candidate.pipeline_stage_status)] = 1

    results = {}

    results['pipeline_stage_stats'] = pipeline_stage_stats
    results['pipeline_stage_status_stats'] = pipeline_stage_status_stats

    return {
        'code': 200,
        'data': results
    }

def get_hiring_funnel(request):
    """Aggregate hiring funnel metrics for the current company.

    Optional query params:
    - job: job id to scope candidates
    - from: YYYY-MM-DD (created/updated on/after)
    - to: YYYY-MM-DD (created/updated on/before)
    - days: number of days to look back from today (overrides from/to)
    """
    try:
        company = Company.getByUser(request.user)
        if not company:
            return getErrorResponse('Company not found')

        q = Candidate.objects.filter(
            Q(job__company=company) | Q(company=company)
        ).distinct()

        job_id = request.GET.get('job')
        if job_id:
            try:
                job = Job.objects.get(id=job_id, company=company)
                q = q.filter(job=job)
            except Job.DoesNotExist:
                return getErrorResponse('Job not found')

        # Handle days parameter first
        days = request.GET.get('days')
        today = timezone.now().date()
        
        if days and days.isdigit():
            days = int(days)
            if days == 0:  # Today only
                q = q.filter(created__date=today)
            elif days == 1:  # Yesterday only
                yesterday = today - timedelta(days=1)
                q = q.filter(created__date=yesterday)
            else:  # Default behavior for other day values
                from_date = today - timedelta(days=days)
                q = q.filter(created__date__gte=from_date)
        else:
            # Handle from/to dates if days is not provided
            from_str = request.GET.get('from')
            to_str = request.GET.get('to')
            if from_str:
                try:
                    dt = datetime.strptime(from_str, '%Y-%m-%d')
                    q = q.filter(created__date__gte=dt.date())
                except Exception:
                    pass
            if to_str:
                try:
                    dt = datetime.strptime(to_str, '%Y-%m-%d')
                    q = q.filter(created__date__lte=dt.date())
                except Exception:
                    pass

        # Rest of the function remains the same
        total_applications = q.count()
        screening = q.filter(pipeline_stage__in=['Screening', 'Associated-Screeening']).count()
        interviews = q.filter(pipeline_stage='Interview').count()
        offers = q.filter(pipeline_stage='Offered').count()
        hired = q.filter(pipeline_stage='Hired').count()

        def pct(n):
            return round((n / total_applications * 100.0), 2) if total_applications else 0.0

        data = {
            'counts': {
                'applications': total_applications,
                'screening': screening,
                'interviews': interviews,
                'offers': offers,
                'hired': hired,
            },
            'rates': {
                'applications': 100.0 if total_applications else 0.0,
                'screening': pct(screening),
                'interviews': pct(interviews),
                'offers': pct(offers),
                'hired': pct(hired),
            }
        }

        return {
            'code': 200,
            'data': data
        }
    except Exception as e:
        return getErrorResponse(str(e))

def get_hires_by_source(request):
    """Return counts of hired candidates grouped by source for the current company.

    Optional query params:
    - job: job id
    - from: YYYY-MM-DD
    - to: YYYY-MM-DD
    - days: number of days to look back from today (overrides from/to)
    """
    try:
        company = Company.getByUser(request.user)
        if not company:
            return getErrorResponse('Company not found')

        q = Candidate.objects.filter(
            Q(job__company=company)
        ).distinct()

        job_id = request.GET.get('job')
        if job_id:
            try:
                job = Job.objects.get(id=job_id, company=company)
                q = q.filter(job=job)
            except Job.DoesNotExist:
                return getErrorResponse('Job not found')

        # Handle days parameter first
        days = request.GET.get('days')
        today = timezone.now().date()
        
        if days and days.isdigit():
            days = int(days)
            if days == 0:  # Today only
                q = q.filter(created__date=today)
            elif days == 1:  # Yesterday only
                yesterday = today - timedelta(days=1)
                q = q.filter(created__date=yesterday)
            else:  # Default behavior for other day values
                from_date = today - timedelta(days=days)
                q = q.filter(created__date__gte=from_date)
        else:
            # Handle from/to dates if days is not provided
            from_str = request.GET.get('from')
            to_str = request.GET.get('to')
            if from_str:
                try:
                    dt = datetime.strptime(from_str, '%Y-%m-%d')
                    q = q.filter(created__date__gte=dt.date())
                except Exception:
                    pass
            if to_str:
                try:
                    dt = datetime.strptime(to_str, '%Y-%m-%d')
                    q = q.filter(created__date__lte(dt.date()))
                except Exception:
                    pass

        # Rest of the function remains the same
        def bucket(src):
            s = (src or '').strip().lower()
            if not s:
                return 'Others'
            if 'linkedin' in s:
                return 'LinkedIn'
            if 'referral' in s or 'refer' in s:
                return 'Referrals'
            if 'portal' in s or 'career' in s or 'company' in s:
                return 'Company Portal'
            if 'naukri' in s or 'indeed' in s or 'monster' in s or 'glassdoor' in s or 'job' in s or 'board' in s:
                return 'Job Boards'
            return 'Others'

        counts = {
            'LinkedIn': 0,
            'Job Boards': 0,
            'Referrals': 0,
            'Company Portal': 0,
            'Others': 0,
        }

        for c in q.values('id', 'source'):
            counts[bucket(c.get('source'))] += 1

        result = [
            { 'label': k, 'count': v }
            for k, v in counts.items()
        ]

        total = sum(counts.values())
        return {
            'code': 200,
            'data': {
                'total_hires': total,
                'by_source': result
            }
        }
    except Exception as e:
        return getErrorResponse(str(e))

def get_dashboard_cards(request):
    """Return four dashboard cards: active_jobs, new_candidates, offer_acceptance, time_to_hire.

    Optional query params:
    - from: YYYY-MM-DD (window start)
    - to: YYYY-MM-DD (window end)
    - days: number of days to look back from today (overrides from/to)
    - compare_from / compare_to for delta calculations (optional)
    """
    company = Company.getByUser(request.user)
    if not company:
        return getErrorResponse('Company not found')

    def parse_date_str(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except Exception:
            return None

    # Handle days parameter first
    days = request.GET.get('days')
    today = timezone.now().date()
    
    if days and days.isdigit():
        days = int(days)
        if days == 0:  # Today only
            from_date = today
            to_date = today
            previous_from_date = today - timedelta(days=1)
            previous_to_date = today - timedelta(days=1)
        elif days == 1:  # Yesterday only
            from_date = today - timedelta(days=1)
            to_date = today - timedelta(days=1)
            previous_from_date = today - timedelta(days=2)
            previous_to_date = today - timedelta(days=2)
        else:  # Default behavior for other day values
            from_date = today - timedelta(days=days)
            to_date = today
            previous_to_date = from_date - timedelta(days=1)
            previous_from_date = previous_to_date - timedelta(days=days)
    else:
        from_date = parse_date_str(request.GET.get('from'))
        to_date = parse_date_str(request.GET.get('to'))

    # Rest of the function remains the same
    from job.models import Job
    if request.user.is_superuser:
        active_jobs_qs = Job.objects.filter(job_status=Job.IN_PROGRESS)
    else:
        active_jobs_qs = Job.objects.filter(company=company, job_status=Job.IN_PROGRESS)
    active_jobs = active_jobs_qs.count()

    # New Candidates within window
    cand_qs = Candidate.objects.filter(djQ(job__company=company) | djQ(company=company)).distinct()
    cand_qs_current = cand_qs.filter(created__date__gte=from_date,created__date__lte=to_date)
    cand_qs_previous = cand_qs.filter(created__date__gte=previous_from_date,created__date__lte=previous_to_date)
    
    new_candidates = cand_qs_current.count()
    previous_new_candidates = cand_qs_previous.count()

    # Calculate percentage difference (New Candidates)

    if previous_new_candidates > 0:
        new_candidates_diff_percent = round(((new_candidates - previous_new_candidates) / previous_new_candidates) * 100, 2)
    else:
        new_candidates_diff_percent = 100.0 if new_candidates > 0 else 0.0


    # Offer Acceptance Rate
    offers_base_qs = Candidate.objects.filter(djQ(job__company=company) | djQ(company=company),pipeline_stage__in=['Offered', 'Hired']).distinct()

    # Current month offers
    offers_qs_current = offers_base_qs.filter(created__date__gte=from_date,created__date__lte=to_date)

    # Previous month offers
    offers_qs_previous = offers_base_qs.filter(created__date__gte=previous_from_date,created__date__lte=previous_to_date)

    offer_acceptance = offers_qs_current.count()
    previous_count = offers_qs_previous.count()
    if previous_count > 0:
        offer_acceptance_diff_percent = round(((offer_acceptance - previous_count) / previous_count) * 100, 2)
    else:
        offer_acceptance_diff_percent = 100.0 if offer_acceptance > 0 else 0.0
    # Offer acceptance percentage for current window
    total_offers_current = (
        offers_qs_current.filter(pipeline_stage='Offered').count() +
        offers_qs_current.filter(pipeline_stage='Hired').count()
    )
    accepted_offers_current = offers_qs_current.filter(pipeline_stage='Hired').count()
    offer_percent = round((accepted_offers_current / total_offers_current) * 100, 2) if total_offers_current else 0.0

    from .models import CandidateTimeline
    def calculate_time_to_hire(from_date, to_date):
        hired_timeline = CandidateTimeline.objects.filter(
            candidate__company=company,
            pipeline_stage='Hired',
            created__date__gte=from_date,
            created__date__lte=to_date
        )

        total_days = 0
        count_hires = 0

        for item in hired_timeline.values('candidate_id', 'created'):
            candidate_id = item['candidate_id']
            hired_date = item['created'].date() if hasattr(item['created'], 'date') else parse_date(str(item['created'])[:10])
            
            first_created = CandidateTimeline.objects.filter(
                candidate_id=candidate_id
            ).order_by('created').values_list('created', flat=True).first()

            if hired_date and first_created:
                start_date = first_created.date() if hasattr(first_created, 'date') else parse_date(str(first_created)[:10])
                if start_date:
                    total_days += max((hired_date - start_date).days, 0)
                    count_hires += 1

        avg_days = round(total_days / count_hires) if count_hires else 0
        return avg_days
        # --- Compute for both periods ---
    time_to_hire_days = calculate_time_to_hire(from_date, to_date)
    time_to_hire_previous = calculate_time_to_hire(previous_from_date, previous_to_date)

    # --- Compare ---
    if time_to_hire_previous > 0:
        time_to_hire_diff_percent = round(((time_to_hire_days - time_to_hire_previous) / time_to_hire_previous) * 100, 2)
    else:
        time_to_hire_diff_percent = 100.0 if time_to_hire_days > 0 else 0.0

    data = {
        'active_jobs': active_jobs,
        'new_candidates': {"new_candidates": new_candidates, "difference_percentage": new_candidates_diff_percent},
        'offer_acceptance': {"offer_acceptance": offer_percent, "difference_percentage": offer_acceptance_diff_percent},
        'time_to_hire_days': {'time_to_hire_days': time_to_hire_days, 'difference_percentage': time_to_hire_diff_percent},
        "day": days,
    }

    return {
        'code': 200,
        'data': data
    }

def updateCandidatePipelineStage(request):
    account = request.user
    # Paranoid validation :p
    company = Company.getById(account.company_id)
    if not company:
        return {
            'code': 400,
            'msg': 'Company not found!'
        }
    
    data = request.data

    # Validating the candidate id 
    candidate_id = data.get('id')

    if not candidate_id: 
        return getErrorResponse('Bad request')

    candidate = Candidate.getByIdAndCompany(id=candidate_id, company=company)
    if not candidate:
        return {
            'code': 400,
            'data': 'Candidate not found!'
        }
    
    # Provide valid options from front end
    status = data.get('status')
    # Need validation
    # 1. Selected pipeline stage status already exists and same with pipeline stage
    if status not in ["Associated-Screeening", "Applied", "Shortlisted", "Interview", "Offered", "Hired", "Onboarded"]:
        return getErrorResponse("Status is not valid, please select among \nAssociated-Screeening, Applied, Shortlisted, Interview, Offered, Hired, Onboarded\n")

    candidate.pipeline_stage = status
    candidate.pipeline_stage_status = status
    candidate.save()

    return {
        'code': 200, 
        'data': "Candidate Status Updated Successfully!!"
    }

def updateEmailSmtpSetting(request):
    email_setting_id = request.data.get('id')
    if not email_setting_id:
        return Response({"error": "ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        email_setting = EmailSettings.objects.get(id=email_setting_id, user_id=request.user)
    except EmailSettings.DoesNotExist:
        return Response({"error": "Email settings not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = EmailSettingsSerializer(email_setting, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def deleteEmailSmtpSetting(request, email_setting_id):
    if not email_setting_id:
        return Response({"error": "ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        email_setting = EmailSettings.objects.get(id=email_setting_id, user_id=request.user)
    except EmailSettings.DoesNotExist:
        return Response({"error": "Email settings not found."}, status=status.HTTP_404_NOT_FOUND)

    email_setting.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

def getSkills(request):
    skills = Skill.objects.all()
    serializer = SkillSerializer(skills, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }

def getSubjectSpecialization(request):
    subject_specialization = SubjectSpecialization.objects.all()
    serializer = SubjectSpecializationSerializer(subject_specialization, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }

def getCandidateApplyJobCareer(request,login_email):
    candidate = Candidate.objects.filter(resume_user=login_email).values('job')
    jobs = Job.objects.filter(id__in=candidate)

    def ensure_dict(value):
        return value if isinstance(value, dict) else {}

    def name_or_str(value):
        if isinstance(value, dict):
            return value.get('name', '')
        if isinstance(value, str):
            return value
        return ''

    # Prepare the response data
    jobs_data = []
    for job in jobs:
        dj = job.dynamic_job_data if isinstance(job.dynamic_job_data, dict) else {}
        cj = ensure_dict(dj.get('Create Job'))
        ai = ensure_dict(dj.get('Address Information'))
        di = ensure_dict(dj.get('Description Information'))

        jobs_data.append({
            'id': job.id,
            'title': cj.get('title', ''),
            'Experience': cj.get('exp_min', ''),
            'Experience_max': cj.get('exp_max', ''),
            'type': cj.get('type', ''),
            'location': name_or_str(cj.get('location')),
            'country': name_or_str(ai.get('country')),
            'state': name_or_str(ai.get('state')),
            'city': name_or_str(ai.get('city')),
            'department': name_or_str(cj.get('department')),
            'company': job.company.name if job.company else None,
            'company_id': job.company.id if job.company else None,
            'company_logo': job.company.logo.url if job.company and job.company.logo else None,
            'posted_date': job.created,
            'salary_max': cj.get('salary_max', ''),
            'salary_min': cj.get('salary_min', ''),
            'webform': job.webform.id if job.webform else None,
            'assesment': job.assesment.id if job.assesment else None,
            'pincode': ai.get('pincode', ''),
            'description': di.get('description', ''),
            'dynamic_job_data': dj if dj else None,
        })

    return {
        'code': 200,
        'data': jobs_data
    }
    
def getTimeLine(request,candidate_id):
    timeline = CandidateTimeline.objects.filter(candidate=candidate_id).order_by('-created')
    serializer = CandidateTimelineSerializer(timeline, many=True)
    return {
        'code': 200,
        'data': serializer.data
    }

def assignJobToCandidates(request):
    """
    Helper function to assign job to multiple selected candidates and update their pipeline status
    """
    try:
        data = request.data
        
        # Get required fields
        candidate_ids = data.get('candidate_ids', [])
        job_id = data.get('job_id')
        pipeline_stage_status = data.get('pipeline_stage_status')
        pipeline_stage = data.get('pipeline_stage')
        comments = data.get('comments', '')
        
        # Validate required fields
        if not candidate_ids:
            return getErrorResponse('Candidate IDs are required')
            
        if not job_id:
            return getErrorResponse('Job ID is required')
            
        if not pipeline_stage_status:
            return getErrorResponse('Pipeline stage status is required')
        
        # Get account and company validation
        account = request.user
        
        # Paranoid validation :p
        company = Company.getById(account.company_id)
        
        if not company:
            return getErrorResponse('Company not found')
        
        # Get job object and validate it belongs to the company
        try:
            job = Job.objects.get(id=job_id, company=company)
        except Job.DoesNotExist:
            return getErrorResponse('Job not found or does not belong to your company')
        
        # Validate each candidate belongs to the company
        validated_candidates = []
        for candidate_id in candidate_ids:
            candidate = Candidate.getByIdAndCompany(id=candidate_id, company=company)
            if not candidate:
                return getErrorResponse(f'Candidate with ID {candidate_id} not found or does not belong to your company')
            validated_candidates.append(candidate)
        
        if not validated_candidates:
            return getErrorResponse('No valid candidates found for your company')
        
        updated_candidates = []
        
        # Get performed_by safely
        performed_by = None
        if request.user and hasattr(request.user, 'account_id') and not request.user.is_anonymous:
            performed_by = request.user
        
        # Update each candidate
        for candidate in validated_candidates:
            # Add job to candidate
            candidate.job.add(job)
            
            # Update pipeline status
            candidate.pipeline_stage_status = pipeline_stage_status
            candidate.pipeline_stage = pipeline_stage
            
            candidate.save()
            
            # Log timeline activity
            CandidateTimeline.log_activity(
                candidate, 
                'CANDIDATE_JOB_ASSIGNED', 
                'Candidate Job Assigned',
                description=f"Job assigned with status '{pipeline_stage_status}'. {comments}".strip(),
                job=job_id, 
                performed_by=performed_by,
            )
            
            # Import JobTimeline for logging
            from job.models import JobTimeline
            
            # Log job timeline activity
            JobTimeline.log_activity(
                job=job,
                candidate=candidate, 
                activity_type='CANDIDATE_JOB_ASSIGNED', 
                title='Candidate Job Assigned',
                description=f"Candidate assigned with status '{pipeline_stage_status}'",
                performed_by=performed_by
            )
            
            updated_candidates.append({
                'id': candidate.id,
                'name': f"{candidate.first_name} {candidate.last_name}",
                'email': candidate.email,
                'pipeline_stage_status': candidate.pipeline_stage_status,
                'pipeline_stage': candidate.pipeline_stage
            })
        
        return {
            'code': 200,
            'msg': f'Successfully assigned job to {len(updated_candidates)} candidates',
            'data': {
                'job': {
                    'id': job.id,
                    'title': job.title
                },
                'updated_candidates': updated_candidates,
                'pipeline_stage_status': pipeline_stage_status,
                'pipeline_stage': pipeline_stage
            }
        }
        
    except Exception as e:
        return getErrorResponse(f'Error assigning job to candidates: {str(e)}')
    
def getCandidateBulkMail(request):
    
    data = request.data
    email_Settings = EmailSettings.objects.get(id=data.get('from'))
    tamplate_str = data.get('tamplate')
    email_tamplate = json.loads(tamplate_str)
    unsubscribe_link = data.get("unsubscribe_link")
    user = request.user
    company = Company.getByUser(user)
    
    attachment_file = request.FILES.get('attachment')
    attachment_content = None
    attachment_name = None
    attachment_category = data.get('attachment_category')
    attachment_subcategory = data.get('attachment_subcategory')
    
    if attachment_file:
        try:
            # Read the file content immediately while file is still open
            attachment_file.seek(0)
            attachment_content = attachment_file.read()
            attachment_name = attachment_file.name
            print(f"Read attachment: {attachment_name}, size: {len(attachment_content)} bytes")
        except Exception as e:
            print(f"Error reading attachment: {str(e)}")
            attachment_content = None
            attachment_name = None
    
    print(f"Attachment category: {attachment_category}")
    print(f"Attachment subcategory: {attachment_subcategory}")

    connection = get_connection(
            backend=email_Settings.email_backend,
            host=email_Settings.email_host,
            port=email_Settings.email_port,
            username=email_Settings.sender_mail,
            password=email_Settings.auth_password,
            use_ssl=email_Settings.email_ssl,
            use_tls=email_Settings.email_tls
        )
    try:
        connection.open()  # This will attempt to connect to the SMTP server
    except Exception as e:
        return {
            'code': 403,
            'data': "SMTP connection failed"
        }
    
    unsubscribeLink= ""
    if unsubscribe_link:
        unsubscribeLink = UnsubscribeLink.objects.get(company=company)
        
     # Fix candidate_id processing
    candidate_ids = data.get('candidate_id', [])
    
    # Handle different input formats
    if isinstance(candidate_ids, str):
        # If it's a comma-separated string, split it
        if ',' in candidate_ids:
            candidate_ids = [id.strip() for id in candidate_ids.split(',')]
        else:
            # If it's a single ID as string
            candidate_ids = [candidate_ids]
    elif not isinstance(candidate_ids, list):
        # If it's a single integer or other type, convert to list
        candidate_ids = [candidate_ids]
    
    for candidate_id in candidate_ids:
        try:
            # Convert to integer if it's a string
            if isinstance(candidate_id, str):
                candidate_id = int(candidate_id)
            
            candidate = Candidate.objects.get(id=candidate_id)
            
            job = candidate.job.all()
            
            # Only use webform_candidate_data email, no fallback
            if (hasattr(candidate, 'webform_candidate_data') and 
                candidate.webform_candidate_data and 
                "Personal Details" in candidate.webform_candidate_data and 
                "email" in candidate.webform_candidate_data["Personal Details"]):
                
                candidate_email = candidate.webform_candidate_data["Personal Details"]["email"]
                
                if email_Settings and candidate_email:
                    sendMail = CandidateBulkMailer(
                        emails=candidate_email,
                        message="candidate created", 
                        email_tamplate=email_tamplate, 
                        email_Settings=email_Settings, 
                        candidate=candidate,
                        job=job,
                        account=request.user,
                        unsubscribe_link=unsubscribeLink.body if unsubscribeLink else "",
                        attachment_content=attachment_content,
                        attachment_name=attachment_name,
                        attachment_category=attachment_category,
                        attachment_subcategory=attachment_subcategory
                    )
                    sendMail.start()
                else:
                    print(f"Skipping candidate {candidate_id}: Email settings missing")
            else:
                print(f"Skipping candidate {candidate_id}: No webform email data found")
                
        except Candidate.DoesNotExist:
            print(f"Candidate with ID {candidate_id} not found")
            continue
        except ValueError:
            print(f"Invalid candidate ID format: {candidate_id}")
            continue
        except Exception as e:
            print(f"Error processing candidate {candidate_id}: {str(e)}")
            continue

    return {
        'code': 200,
        'data': "success"
    }
    
def get_daily_candidate_counts(request):
    """
    Get daily created candidate counts and statistics for a given date range.
    
    Args:
        request: Django request object with optional 'days' query parameter
        
    Returns:
        dict: Contains daily counts, pipeline distribution, and totals
    """
    user = request.user
    company = Company.getByUser(user)
    today = timezone.now().date()
    
    # Get days parameter from query string
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
            days = 1
            start_date = today
    except (TypeError, ValueError):
        days = 1
        start_date = today
    
    # Base queryset for candidates
    if user.is_superuser:
        candidates = Candidate.objects.all()
    else:
        candidates = Candidate.objects.filter(job__company=company).distinct()
    # Get daily counts
    date_list = [start_date + timedelta(days=i) for i in range(days)]
    date_list.reverse()  # To show oldest to newest
    
    daily_counts = []
    for single_date in date_list:
        count = candidates.filter(created__date=single_date).count()
        daily_counts.append({
            'date': single_date,
            'count': count
        })
    
    # Get pipeline stage distribution for the time period
    pipeline_stages = [
        'Associated-Screeening',
        'Applied',
        'Shortlisted',
        'Interview',
        'Offered',
        'Hired',
        'Onboarded'
    ]
    
    pipeline_stats = []
    for stage in pipeline_stages:
        count = candidates.filter(
            pipeline_stage=stage,
            created__date__gte=start_date
        ).count()
        
        if count > 0:  # Only include stages with candidates
            pipeline_stats.append({
                'stage': stage,
                'count': count
            })
    
    # Get total candidates in the date range
    total_candidates = candidates.filter(created__date__gte=start_date).count()
    
    return {
        'days': days,
        'start_date': start_date,
        'end_date': today,
        'total_candidates': total_candidates,
        'daily_counts': daily_counts,
        'pipeline_distribution': pipeline_stats
    }

def getDailyEmailQuota(request):

    """Get daily email quota information for the current user"""
    from .models import DailyEmailQuota
    from account.models import Company
    
    user = request.user
    company = Company.getByUser(user)
    
    if not company:
        return {
            'code': 400,
            'data': "Company not found"
        }
    
    # Get or create today's quota
    quota = DailyEmailQuota.get_or_create_quota(user, company)
    
    return {
        'code': 200,
        'data': {
            'daily_limit': quota.daily_limit,
            'emails_sent': quota.emails_sent,
            'emails_remaining': quota.emails_remaining,
            'can_send_emails': quota.can_send_emails,
            'date': quota.date.strftime('%Y-%m-%d')
        }
    }

# def HiringStatusTimeLine(request, id):
#     # Validate input parameter
#     if not id:
#         return Response({"error": "Candidate ID is required"}, status=400)
    
#     try:
#         # Convert to integer if it's a string
#         candidate_id = int(id)
#     except (ValueError, TypeError):
#         return Response({"error": "Invalid candidate ID format"}, status=400)
    
#     # Validate candidate exists
#     try:
#         candidate = Candidate.objects.get(id=candidate_id)
#     except Candidate.DoesNotExist:
#         return Response({"error": "Candidate not found"}, status=404)
    
#     # Get hiring timeline data
#     hiring = CandidateTimeline.objects.filter(
#         Q(candidate=candidate_id) & Q(pipeline_stage__in=["Screening", "Applied", "Interview", "Offered", "Hired"])
#     ).values("pipeline_stage", "created")
    
#     if hiring:
#         STAGES = ["Screening", "Applied", "Interview", "Offered", "Hired"]
#         today_date = date.today()

#         # Step 1: find earliest created date for each stage
#         first_dates = {}
#         for item in hiring:
#             stage = item.get("pipeline_stage")
#             created = item.get("created")
#             if created:
#                 if hasattr(created, "date"):
#                     created_date = created.date()
#                 else:
#                     created_date = datetime.fromisoformat(str(created).replace("Z", "")).date()
#                 if stage not in first_dates or created_date < first_dates[stage]:
#                     first_dates[stage] = created_date

#         # Step 2: build output with correct day calculation
#         stage_map = {}
#         for idx, stage in enumerate(STAGES):
#             created_date = first_dates.get(stage)
#             if created_date:
#                 # Find next available stage with a date
#                 next_date = None
#                 for next_stage in STAGES[idx + 1:]:
#                     if next_stage in first_dates:
#                         next_date = first_dates[next_stage]
#                         break

#                 if next_date:
#                     day_diff = (next_date - created_date).days
#                 else:
#                     day_diff = (today_date - created_date).days

#                 stage_map[stage] = {
#                     "created": created_date.strftime("%Y-%m-%d"),
#                     "day": day_diff
#                 }
#         # Step 3: assign status
#         hired_exists = "Hired" in stage_map
#         latest_stage = None
#         if first_dates:
#             # If multiple stages have the same date, prefer the later stage in STAGES order
#             latest_stage = max(
#                 first_dates.items(),
#                 key=lambda x: (x[1], STAGES.index(x[0]))
#             )[0]
#         parsed_stages = []
#         for idx, stage in enumerate(STAGES):
#             stage_data = stage_map.get(stage)
#             if hired_exists:
#                 if stage == "Hired":
#                     status = "active"
#                 elif stage_data:
#                     status = "completed"
#                 else:
#                     status = "pending"
#             else:
#                 if latest_stage:
#                     latest_idx = STAGES.index(latest_stage)
#                     if idx < latest_idx:
#                         status = "completed"
#                     elif idx == latest_idx:
#                         status = "active"
#                     else:
#                         status = "pending"
#                 else:
#                     status = "pending"

#             parsed_stages.append({
#                 "label": stage,
#                 "day": stage_data["day"] if stage_data else None,
#                 "status": status
#             })

#         return Response(parsed_stages)
    
#     # Return empty timeline if no hiring data found
#     return Response([], status=200)


def HiringStatusTimeLine(request, id):
    STAGES = ["Screening", "Applied", "Interview", "Offered", "Hired"]
    today_date = date.today()

    # Fetch all timeline records for the candidate
    hiring = CandidateTimeline.objects.filter(
        Q(candidate=id) &
        Q(pipeline_stage__in=STAGES)
    ).order_by('-created')[:5].values("pipeline_stage", "created")

    if not hiring:
        return Response([])

    # Step 1: find the latest created datetime for each stage
    latest_datetimes = {}
    for item in hiring:
        stage = item["pipeline_stage"]
        created = item["created"]
        if created:
            # Use full datetime, not just date
            if isinstance(created, datetime):
                created_dt = created
            else:
                created_dt = datetime.fromisoformat(str(created).replace("Z", ""))
            # Keep the latest datetime if multiple records exist for the same stage
            if stage not in latest_datetimes or created_dt > latest_datetimes[stage]:
                latest_datetimes[stage] = created_dt

    # Step 2: find the overall latest stage (by datetime)
    latest_stage = max(latest_datetimes.items(), key=lambda x: x[1])[0]

    # Step 3: calculate day differences
    stage_map = {}
    for idx, stage in enumerate(STAGES):
        created_dt = latest_datetimes.get(stage)
        if created_dt:
            # Find next stage in STAGES that has a datetime
            next_dt = None
            for next_stage in STAGES[idx + 1:]:
                if next_stage in latest_datetimes:
                    next_dt = latest_datetimes[next_stage]
                    break
            day_diff = (next_dt.date() - created_dt.date()).days if next_dt else (today_date - created_dt.date()).days
            stage_map[stage] = {"created": created_dt.strftime("%Y-%m-%d"), "day": day_diff}

    # Step 4: assign status
    parsed_stages = []
    latest_idx = STAGES.index(latest_stage) if latest_stage else -1

    for idx, stage in enumerate(STAGES):
        stage_data = stage_map.get(stage)
        if idx < latest_idx:
            status = "completed"
        elif idx == latest_idx:
            status = "active"
        else:
            status = "pending"

        parsed_stages.append({
            "label": stage,
            "day": stage_data["day"] if (stage_data and (status == "active" or status == "completed")) else None,
            "status": status
        })

    return Response(parsed_stages)


def CandidateApplyJobCareer(request):
    candidate = Candidate.objects.filter(account=request.user).values("job")
    Jobs = Job.objects.filter(id__in=candidate) 
    serializer = JobSearchSerializer(Jobs,many=True)
    return serializer.data

def getSavedJob(request):
    try:
        # Get the candidate associated with the current user
        # candidate = Candidate.objects.get(account=request.user)
        candidate = get_object_or_404(Account, id=request.user.id)
        saved_jobs = SavedJob.objects.filter(candidate=candidate).values_list("job_id", flat=True)
        jobs = Job.objects.filter(id__in=saved_jobs)
        serializer = JobSearchSerializer(jobs, many=True)
        return {"data": serializer.data}, 200
    except Candidate.DoesNotExist:
        return {"error": "Candidate not found for this user"}, 404

def SaveJob(request):
    try:
        # Get the candidate associated with the current user
        candidate = get_object_or_404(Account, id=request.user.id)
    except Candidate.DoesNotExist:
        return {"error": "Candidate not found for this user"}, 404
        
    job_id = request.data.get("job_id")

    if not job_id:
        return {"error": "job_id is required"}, 400

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return {"error": "Job not found"}, 404

    # prevent duplicate
    if SavedJob.objects.filter(candidate=candidate, job=job).exists():
        return {"message": "Job already saved"}, 200

    saved = SavedJob.objects.create(candidate=candidate, job=job)
    serializer = SavedJobSerializer(saved)

    return {
        "message": "Job saved successfully",
        "data": serializer.data
    }, 201

def DeleteSavedJob(request,pk):
    try:
        # Get the candidate associated with the current user
        candidate = get_object_or_404(Account, id=request.user.id)
    except Candidate.DoesNotExist:
        return {"error": "Candidate not found for this user"}, 404
        
    try:
        job = Job.objects.get(id=pk)
    except Job.DoesNotExist:
        return {"error": "Job not found"}, 404

    saved = SavedJob.objects.get(candidate=candidate, job=job)
    saved.delete()
    
    return {
        "message": "Job deleted successfully",
    }, 200

def getCandidateResume(request):
    try:
        # Get the candidate associated with the current user
        candidate = CandidateResume.objects.filter(candidate=request.user)
    except CandidateResume.DoesNotExist:
        return {"error": "Candidate not found for this user"}, 404
    
    serializer = CandidateResumeSerializer(candidate,many=True)
    
    return {"data": serializer.data}, 200


def CreateCandidateResume(request):
    """
    Create a new candidate resume.
    The resume parsing will be handled by the post_save signal.
    """
    data = request.data
    data['candidate'] = request.user.id
    serializer = CandidateResumeSerializer(data=data)
    
    if serializer.is_valid():
        # The post_save signal will handle the resume parsing
        serializer.save()
        return {"message": "Resume updated successfully","data": serializer.data}, 201
    else:
        return {"error": serializer.errors}, 400

def UpdateCandidateResume(request, pk):
    """
    Update an existing candidate resume.
    The resume parsing will be handled by the post_save signal if the resume file changes.
    """
    try:
        # Get the candidate resume by ID
        candidate_resume = CandidateResume.objects.get(id=pk)
        
        # Verify the resume belongs to the current user
        if candidate_resume.candidate_id != request.user.id:
            return {"error": "You don't have permission to update this resume"}, 403
            
    except CandidateResume.DoesNotExist:
        return {"error": "Resume not found"}, 404
    
    serializer = CandidateResumeSerializer(candidate_resume, data=request.data, partial=True)
    
    if serializer.is_valid():
        # The post_save signal will handle resume parsing if the file was updated
        serializer.save()
        return {"message": "Resume updated successfully","data": serializer.data}, 201
    else:
        return {"error": serializer.errors}, 400

def DeleteCandidateResume(request,pk):
    try:
        # Get the candidate associated with the current user
        candidate = CandidateResume.objects.get(id=pk)
    except CandidateResume.DoesNotExist:
        return {"error": "Candidate not found for this user"}, 404
    
    candidate.delete()
    return {"message": "Resume deleted successfully"}, 200

def getCandidateProfile(request):
    try:
        # Get the candidate associated with the current user
        candidate = get_object_or_404(CandidateProfile, candidate=request.user)
    except CandidateProfile.DoesNotExist:
        return {"error": "Candidate not found for this user"}, 404
    
    serializer = CandidateProfileSerializer(candidate)
    
    return {"data": serializer.data}, 200

def CreateCandidateProfile(request):
    data = request.data
    data['candidate'] = request.user.id
    serializer = CandidateProfileSerializer(data=data)
    
    if serializer.is_valid():
        serializer.save()
        return {"message": "Profile updated successfully","data": serializer.data}, 201
    else:
        return {"error": serializer.errors}, 400
    
def UpdateCandidateProfile(request,pk):
    try:
        # Get the candidate associated with the current user
        candidate = CandidateProfile.objects.get(id=pk)
    except CandidateProfile.DoesNotExist:
        return {"error": "Candidate not found for this user "}, 404
    
    serializer = CandidateProfileSerializer(candidate, data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return {"message": "Profile updated successfully","data": serializer.data}, 201
    else:
        return {"error": serializer.errors}, 400

def DeleteCandidateProfile(request,pk):
    try:
        # Get the candidate associated with the current user
        candidate = CandidateProfile.objects.get(id=pk)
    except CandidateProfile.DoesNotExist:
        return {"error": "Candidate not found for this user"}, 404
    
    candidate.delete()
    return {"message": "Profile deleted successfully"}, 200
    
