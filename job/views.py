import email
from os import extsep
from xml.dom import minidom

from settings.models import CreditHistory, FeatureUsage, Subscription
from settings.decorators import check_subscription_and_credits_for_ai, handle_ai_credits
from job.serializer import JobsSerializer , AssesmentSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework import mixins, generics
from .import helper
from common.utils import makeResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from settings.models import CreditWallet, Webform
from .models import Job, Assesment, Company, JobTimeline
from settings.models import Location, PipelineStage
from account.models import Account
from .serializer import *
from candidates.models import *
from candidates.serializer import CandidateDetailsSerializer
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from datetime import datetime, date, timedelta
from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect, render
from job import models
from rest_framework.decorators import action
from django.db.models import Q
import re
from rest_framework_xml.renderers import XMLRenderer
from django.utils.encoding import smart_str
from django.utils import timezone
from xml.dom.minidom import Document
from django.conf import settings
from django.http import HttpResponse, JsonResponse
import json
from django.db import IntegrityError
from django.db.models import TextField, IntegerField
from django.db.models import Value
from django.db.models import F
from django.db.models.functions import Cast
from django.db.models import Case, When, Sum
# job/pagination.py
from rest_framework.pagination import PageNumberPagination
from django.db.models.expressions import RawSQL
from rest_framework.pagination import PageNumberPagination
from functools import lru_cache


class AssesmentCategoryApi(APIView):

    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)
        data = helper.getAssesmentCategories(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveAssesmentCategory(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteAssesmentCategory(request)
        return makeResponse(data)    


class AssismentDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Assesment.objects.all()
    serializer_class = AssesmentSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
    def put(self, request, pk):
        try:
            assessment = Assesment.objects.get(id=pk)
        except Assesment.DoesNotExist:
            return Response({'detail': 'Assessment not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if name is being updated and if it already exists for the company
        new_name = request.data.get('name')
        if new_name and new_name != assessment.name:
            if Assesment.objects.filter(company=assessment.company, name=new_name).exists():
                return Response(
                    {'msg': 'An assessment with this name already exists for your company. Please choose a different name.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Deserialize the data and perform the update
        serializer = AssesmentSerializer(assessment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AssesmentQuestionApi(APIView):

    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getAssesmentDetails(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveAssesmentQuestion(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteAssesmentQuestion(request)
        return makeResponse(data)    

class AssesmentApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):        
        user = request.user

        if user.is_superuser:
            queryset = Assesment.objects.all().order_by('-updated')
        else:
            queryset = Assesment.objects.filter(company__id=user.company_id).order_by('-updated')

        from_date = request.query_params.get('from', None)
        to_date = request.query_params.get('to', None)
        name = request.query_params.get('name', None)
        category = request.query_params.get('category', None)
        owner = request.query_params.get('owner', None)

        if from_date:
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
            queryset = queryset.filter(updated__gte=from_date)
        if to_date:
            to_date = datetime.strptime(to_date, '%Y-%m-%d')
            to_date = to_date + timedelta(days=1)
            queryset = queryset.filter(updated__lte=to_date)
        if name:
            queryset = queryset.filter(name__icontains=name)
        if category:
            queryset = queryset.filter(category__name__icontains=category)
        if owner:
            queryset = queryset.filter(company__admin__username__icontains=owner)

        if not any([from_date, to_date, name, category, owner]):
            data = helper.getAssesments(request)
            return makeResponse(data)
        
        serializer = AssesmentSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
        

    def post(self, request):
        data = helper.saveAssesment(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteAssesment(request)
        return makeResponse(data)           
    
class AssesmentCareerApi(APIView):    

    def get(self, request, pk):
        data = helper.getAssesmentCareer(request, pk)
        return Response(data)
    

class JobsList(mixins.ListModelMixin,
                  generics.GenericAPIView):
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        user = request.user

        if user.is_superuser:
            queryset = Job.objects.all().order_by('-updated')
        else:
            queryset = Job.objects.filter(company__id=user.company_id).distinct().order_by('-updated')           
                
        # from_date = request.query_params.get('from', None)
        # to_date = request.query_params.get('to', None)
        # join_date = request.query_params.get('join_date', None)
        # title = request.query_params.get('title', None)
        # skill = request.query_params.get('skill', None)
        # education = request.query_params.get('education', None)
        # status = request.query_params.get('status', None)
        # experience = request.query_params.get('experience', None)        

        # if from_date:
        #     from_date = datetime.strptime(from_date, '%Y-%m-%d')
        #     queryset = queryset.filter(updated__gte=from_date)
        # if to_date:
        #     to_date = datetime.strptime(to_date, '%Y-%m-%d')
        #     to_date = to_date + timedelta(days=1)
        #     queryset = queryset.filter(updated__lte=to_date)
        # if join_date:
        #     join_date = datetime.strptime(join_date, '%Y-%m-%d')
        #     queryset = queryset.filter(created__date=join_date)
        # if title:
        #     queryset = queryset.filter(title__icontains=title)
        # if skill:
        #     queryset = queryset.filter(speciality__icontains=skill)
        # if education:
        #     queryset = queryset.filter(educations__icontains=education)
        # if status:
        #     queryset = queryset.filter(job_status__icontains=status)
        # if experience:
        #     queryset = queryset.filter(exp_max__lte=experience)
            
        # if not any([from_date, to_date, title, skill, education,status,experience]):
        #     data = helper.getJobList(request)
        #     return Response(data.data)
        serializer = JobsSerializer(queryset, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
    

class JobsDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):    
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    queryset = Job.objects.all()
    serializer_class = JobsSerializer

    def get(self, request, *args, **kwargs):
        job = self.get_object()
        serializer = self.get_serializer(job)
        data = serializer.data
        # data['department'] = job.department.id if job.department else None 
        # data['members'] = serializer.get_members(job)
        data['locations'] = serializer.get_location(job)
        
        # Giving the pipeline stage info as well 
        
        candidates = Candidate.getByJob(job=job)

        # pipeline_stage_stats = {}
        pipeline_stage_status_stats = {}

        for candidate in candidates:

            # For pipeline stage list
            if candidate.pipeline_stage:
                if str(candidate.pipeline_stage).lower() in pipeline_stage_status_stats.keys():
                    pipeline_stage_status_stats[str(candidate.pipeline_stage).lower()] += 1
                else:
                    pipeline_stage_status_stats[str(candidate.pipeline_stage).lower()] = 1

            # For pipeline stage status
            if candidate.pipeline_stage_status:
                if str(candidate.pipeline_stage_status).lower() in pipeline_stage_status_stats.keys():
                    pipeline_stage_status_stats[str(candidate.pipeline_stage_status).lower()] += 1
                else:
                    pipeline_stage_status_stats[str(candidate.pipeline_stage_status).lower()] = 1
        
        # data["pipeline_stage_stats"] = pipeline_stage_stats
        data["pipeline_stage_status_stats"] = pipeline_stage_status_stats
        
        return Response(data)
    
class TemplateJobsDetail(mixins.RetrieveModelMixin, generics.GenericAPIView):    
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    queryset = TemplateJob.objects.all()
    serializer_class = TemplateJobSerializer

    def get(self, request, *args, **kwargs):
        TemplateJob = self.get_object()
        serializer = self.get_serializer(TemplateJob)
        data = serializer.data
        # data['department'] = job.department.id if job.department else None 
        data['members'] = serializer.get_members(TemplateJob)
        data['locations'] = serializer.get_location(TemplateJob)
        
        return Response(data)
    
class JobsCandidates(mixins.RetrieveModelMixin, generics.GenericAPIView):    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Job.objects.all()
    serializer_class = JobsSerializer

    def get_candidate(self, job):
        if job:
            candidate = Candidate.objects.filter(job=job.id)
            return candidate
        return None
    
    def get(self, request, *args, **kwargs):
        job = self.get_object()
        candidates = self.get_candidate(job)
       
        candidate_data=[] 
        for candidate in candidates:
            data = CandidateDetailsSerializer(candidate).data
            candidate_data.append(data)
        return Response(candidate_data)

class JobApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getJobs(request)
        return makeResponse(data)

    def post(self, request):
        # data = helper.saveJob(request)
        # return makeResponse(data)
        response ,status = helper.saveJob(request)
        
        # if response['code'] == 200:
            # job_data = response['msg']  # Assuming this contains the job details
        
            # zwayam_response = helper.post_job_to_zwayam(job_data)

            # if zwayam_response.status_code == 200:
            #     return makeResponse({'code': 200, 'msg': 'Job posted to Zwayam successfully.'})
            # else:
            #     return makeResponse({'code': zwayam_response.status_code, 'msg': 'Failed to post job to Zwayam.'})

        return Response(response, status=status)

    def delete(self, request, pk):
        try:
            job = Job.objects.get(id=pk)
            job.candidates.clear()
            job.delete()
            return makeResponse({'code': 200, 'msg': 'Job deleted successfully.'})
        except Job.DoesNotExist:
            return makeResponse({'code': 404, 'msg': 'Job not found.'})
        
    def put(self, request, pk):
        try:
            job = Job.objects.get(id=pk)
        except Job.DoesNotExist:
            return Response({'detail': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # owner_data = request.data.pop('owner', None)
        address_data = request.data.pop('address', None)
        education_data = request.data.pop('education', None)
        member_ids_data = request.data.pop('member_ids', None)
        
        serializer = JobsSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            
            # if owner_data:
            #     owner_instance = Account.objects.get(account_id=owner_data)
            #     job.owner = owner_instance
                
            if address_data:
                try:
                    location = Location.objects.get(pk=address_data)
                    job.location = location
                except Location.DoesNotExist:
                    return Response({'detail': 'Location not found'}, status=status.HTTP_400_BAD_REQUEST)
            
            if education_data:
                job.educations = education_data
                
            if member_ids_data:
                if isinstance(member_ids_data, list):
                    job.members = member_ids_data
                else:
                    return Response({'detail': 'Invalid member_ids data'}, status=status.HTTP_400_BAD_REQUEST)
                
            serializer.save()
            JobTimeline.log_activity(job=job, activity_type= 'JOB_UPDATED', title= 'Job Updated',description=f"Job updated by {request.user.first_name if request.user and hasattr(request.user, 'first_name') else 'Unknown'}", performed_by=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        print("Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   
    
class TemplateJobApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        data = helper.getTemplateJobs(request, pk)
        return makeResponse(data)

    def post(self, request):
        data = helper.publishedTemplateJobs(request)
        return makeResponse(data)

    def delete(self, request, pk=None):
        data = helper.deleteTemplateJobs(request, pk)
        return makeResponse(data)
    
class DraftSaveJobApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        data = helper.getDraftJobs(request, pk)
        return makeResponse(data)

    def post(self, request):
        data = helper.SaveDraftJobs(self,request)
        return Response(data)
    
    def delete(self, request, pk=None):
        data = helper.deleteDraftJob(request, pk)
        return makeResponse(data)
    
class JobUpload_documentApi(APIView):
    
    def get(self, request,pk=None):
        data = helper.getJobDocument(request,pk)
        return makeResponse(data)

    def post(self, request):
        data = helper.uploadJobDocument(request)
        return makeResponse(data)  
    
    def delete(self, request):
        data = helper.deleteJobDocument(request)
        return makeResponse(data)
    
class JobsDetailCareer(APIView):
    
    def get(self, request, pk=None):
        data = helper.getJobsDetailCareer(request, pk)
        return Response(data)

class JobUpload_AssesmentApi(APIView):
    
    def post(self, request):
        data = helper.addExistingAssesment(request)
        return makeResponse(data) 
    
    def delete(self, request):
        data = helper.deleteJobAssesment(request)
        return makeResponse(data)
    
class CloneJobApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        data = helper.cloneJob(request, job_id)
        return makeResponse(data)    

class CreateJobApi(APIView):
    def post(self, request):

        data = request.data
        print(data)

        title = data['title']
        vacancies = data['vacancies']
        department = data['department']
        owner = data['owner']
        assesment = data['assesment']
        member_ids = data['member_ids']
        type = data['type']
        nature = data['nature']
        education = data['education']
        speciality = data['speciality']
        description = data['description']
        exp_min = data['exp_min']
        exp_max = data['exp_max']
        salary_min = data['salary_min']
        salary_max = data['salary_max']
        salary_type = data['salary_type']
        currency = data['currency']
        city = data['city']
        state = data['state']
        job_boards = data['job_boards']
        pipeline = data['pipeline']
        active = data['active']
        status = data['status']
        webform_id = data['webform_id']

        job = Job(title= title,vacancies = vacancies, department = department, owner = owner, assesment = assesment , type = type , nature = nature ,speciality = speciality , description = description , exp_max = exp_max , exp_min = exp_min , salary_min = salary_min , salary_max = salary_max , salary_type = salary_type , currency = currency , city = city , state = state ,job_boards = job_boards , pipeline = pipeline ,active = active , webform_id = webform_id, job_status = status )
        job.save()

        return makeResponse(data)

class JobDetailsApi(APIView):

    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getJobDetails(request)
        return makeResponse(data)

class BoardApi(APIView):

    def post(self, request):
        data = helper.getJobsBoard(request)
        return makeResponse(data)     

class JobCandidateList(APIView):

    def get(self, request):
        data = helper.getJobCandidateList(request) 
        return makeResponse(data)  


class JobNotesApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getAllNotes(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveNote(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteNote(request)
        return makeResponse(data)
    
    def put(self, request):
        data = helper.updateNote(request)
        return makeResponse(data)
    
class JobTaskOptionsView(APIView):
    def get(self, request, *args, **kwargs):
        # Prepare the options data
        options = {
            "priority_fields": dict(PRIORITY_FIELDS),
            "task_repeat": dict(TASK_REPEAT),
            "task_alert": dict(TASK_ALERT),
            "status_fields": dict(STATUS_FIELDS),
            "currency": dict(CURRENCY),
        }
        # Return the options as JSON response
        return Response(options) 
    
class JobTaskListCreateView(APIView):
    def get(self, request, id, *args, **kwargs):
        tasks = Tasks.objects.filter(job__id=id)
        serializer = JobTaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = JobTaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            job = Job.objects.get(id=request.data['job'])
            JobTimeline.log_activity(job=job, activity_type= 'TASK_CREATED', title= 'Task Created',description=f"Task created by {request.user.first_name if request.user and hasattr(request.user, 'first_name') else 'Unknown'}", performed_by=request.user, related_task=serializer.instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
        
    def put(self, request, id, *args, **kwargs):
        try:
            task = Tasks.objects.get(id=id)
        except Tasks.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = JobTaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id, *args, **kwargs):
        try:
            task = Tasks.objects.get(id=id)
        except Tasks.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        
        task.delete()
        return Response({"message": "Task deleted"}, status=status.HTTP_204_NO_CONTENT)

class JobMarkTaskCompletedView(APIView):
    def post(self, request, id, *args, **kwargs):
        try:
            task = Tasks.objects.get(id=id)
            task.completed = True
            task.status = 'COMPLETED'
            task.save()
            return Response({'status': 'success', 'message': 'Task marked as completed'}, status=status.HTTP_200_OK)
        except Tasks.DoesNotExist:
            return Response({'status': 'error', 'message': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        
class JobEventOptionsView(APIView):
    def get(self, request, *args, **kwargs):
        # Prepare the options data
        options = {
            "meeting_venue": dict(MEETING_VENUE),
            "related_to": dict(RELATED_TO),
            "repeat_fields": dict(REPEAT_FIELDS),
            "reminder_fields": dict(REMINDER_FIELDS),
            "todo_type": dict(TODO_TYPE),
            "currency": dict(CURRENCY),
        }
        # Return the options as JSON response
        return Response(options)
        
class JobEventListCreateView(APIView):
    def get(self, request, id, *args, **kwargs):
        events = Events.objects.filter(job__id=id)
        serializer = JobEventSerializer(events, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = JobEventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            job = Job.objects.get(id=request.data['job'])
            JobTimeline.log_activity(job=job, activity_type= 'EVENT_CREATED', title= 'Event Created',description=f"Event created by {request.user.first_name if request.user and hasattr(request.user, 'first_name') else 'Unknown'}", performed_by=request.user, related_event=serializer.instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id, *args, **kwargs):
        try:
            event = Events.objects.get(id=id)
        except Events.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = JobEventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, *args, **kwargs):
        try:
            event = Events.objects.get(id=id)
        except Events.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

        event.delete()
        return Response({"message": "Event deleted"}, status=status.HTTP_204_NO_CONTENT)

class JobCallOptionsView(APIView):
    def get(self, request, *args, **kwargs):
        # Prepare the options data
        options = {
            "call_type": dict(CALL_TYPE_CHOICES),
            "call_purpose": dict(CALL_PURPOSE_CHOICES),
            "call_status": dict(CALL_STATUS),
            "reminder_fields": dict(CALL_REMINDER_FIELDS),
            "todo_type": dict(TODO_TYPE),
        }
        # Return the options as JSON response
        return Response(options)

class JobCallListCreateView(APIView):
    def get(self, request, id, *args, **kwargs):
        calls = Call.objects.filter(posting_title__id=id)
        serializer = JobCallSerializer(calls, many=True)
        return Response(serializer.data)

    # def post(self, request, *args, **kwargs):
    #     serializer = JobCallSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        owner_id = request.data.get('owner')
        if owner_id:
            try:
                owner_instance = Account.objects.get(account_id=owner_id)
                request.data['owner'] = owner_instance.pk  # Assign only the primary key
            except Account.DoesNotExist:
                return Response({'error': 'Owner not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = JobCallSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            job = Job.objects.get(id=request.data['posting_title'])
            JobTimeline.log_activity(job=job, activity_type= 'CALL_CREATED', title= 'Call Created',description=f"Call created by {request.user.first_name if request.user and hasattr(request.user, 'first_name') else 'Unknown'}", performed_by=request.user, related_call=serializer.instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id, *args, **kwargs):
        try:
            call = Call.objects.get(id=id)
        except Call.DoesNotExist:
            return Response({"error": "Call not found"}, status=status.HTTP_404_NOT_FOUND)
        
        owner_id = request.data.get('owner')
        if owner_id:
            try:
                owner_instance = Account.objects.get(account_id=owner_id)
                request.data['owner'] = owner_instance.pk  # Assign only the primary key
            except Account.DoesNotExist:
                return Response({'error': 'Owner not found'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = JobCallSerializer(call, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, *args, **kwargs):
        try:
            call = Call.objects.get(id=id)
        except Call.DoesNotExist:
            return Response({"error": "Call not found"}, status=status.HTTP_404_NOT_FOUND)

        call.delete()
        return Response({"message": "Call deleted"}, status=status.HTTP_204_NO_CONTENT)

class JobStats(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getJobStats(request)
        return makeResponse(data)
    
    def post(self, request):
        data = helper.updateJobStats(request)
        return makeResponse(data)


class DashboardJobStats(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):    
        data = helper.getDashboardJobStats(request) 
        return makeResponse(data)
    
class AgeJobView(APIView):
    def get(self,request):
        headers = helper.get_age_job_count(request)
        return Response({"headers":headers})

class JobStatusStats(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getJobStatusStats(request)
        return makeResponse(data)


class JobsCandidatesByStatus(mixins.RetrieveModelMixin, generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Job.objects.all()
    serializer_class = JobsSerializer

    def get_candidate(self, job, status):
        if job:
            # Filter candidates based on job ID and status
            candidates = Candidate.objects.filter(job=job.id, pipeline_stage=status).order_by('-updated')
            return candidates
        return None
    
    def get(self, request, job_id, status, *args, **kwargs):
        job = get_object_or_404(Job, pk=job_id)
        candidates = self.get_candidate(job, status)
       
        candidate_data = [] 
        for candidate in candidates:
            data = CandidateDetailsSerializer(candidate).data
            candidate_data.append(data)
        return Response(candidate_data)
    
class AssociateJobApplyGet(APIView):
    def get(self,request,candidate_id):
        data = helper.AssociateJobApplyGet(self,request,candidate_id)
        return data

class JobSQLQueryView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            data = request.data
            query = data.get('query')
            if query:
                query = query.replace('%', '')

            # Use Django ORM to filter jobs
            jobs = models.Job.objects.select_related('company', 'location', 'pipeline', 'webform','department','assesment','owner','created_by')
            
            if not user.is_superuser:
                jobs = jobs.filter(company__id=user.company_id)

            if query:
                # Replace logical operators with Python's operators
                query = query.replace(" AND ", " and ").replace(" OR ", " or ")
                
                # Parse and construct the Q object
                q_object = self.construct_q_object(query)
                
                # Apply the Q object to filter jobs
                jobs = jobs.filter(q_object)

            results = jobs.values(
                'id', 'company__name', 'title', 'vacancies', 'department__name', 'owner__first_name', 'assesment__name',
                'members', 'type', 'nature', 'educations', 'speciality', 'description',
                'exp_min', 'exp_max', 'salary_min', 'salary_max', 'salary_type', 'currency',
                'job_status', 'location__address', 'created_by__first_name', 'document', 'job_boards',
                'pipeline__name', 'active', 'updated', 'created', 'webform__name', 'published'
            )

            results_list = list(results)

            return Response({'result': results_list}, status=status.HTTP_200_OK)
        except Exception as e:
            # Return all jobs in case of an error
            jobs = models.Job.objects.select_related('company', 'location', 'pipeline', 'webform').values(
                'id', 'company__name', 'title', 'vacancies', 'department__name', 'owner__first_name', 'assesment__name',
                'members', 'type', 'nature', 'educations', 'speciality', 'description',
                'exp_min', 'exp_max', 'salary_min', 'salary_max', 'salary_type', 'currency',
                'job_status', 'location__name', 'created_by__first_name', 'document', 'job_boards',
                'pipeline__name', 'active', 'updated', 'created', 'webform__name', 'published'
            )
            results_list = list(jobs)
            return Response({'result': results_list, 'error': str(e)}, status=status.HTTP_200_OK)

    def construct_q_object(self, query):
        # Tokenize the query using regex to handle nested conditions and operators
        tokens = re.split(r'(\(|\)|\s+and\s+|\s+or\s+)', query)
        tokens = [token for token in tokens if token.strip()]

        # Stack to manage nested conditions and Q objects
        stack = []
        current_q = None
        current_operator = None

        for token in tokens:
            token = token.strip().lower()

            if token == '(':
                stack.append((current_q, current_operator))
                current_q = None
                current_operator = None
            elif token == ')':
                temp_q = current_q
                if stack:
                    current_q, current_operator = stack.pop()
                    if current_operator == 'and':
                        current_q &= temp_q
                    elif current_operator == 'or':
                        current_q |= temp_q
                    else:
                        current_q = temp_q
            elif token == 'and':
                current_operator = 'and'
            elif token == 'or':
                current_operator = 'or'
            else:
                match = re.match(r"(\w+)\s+(like|not like|=|<>|>|>=|<|<=|startwith|endwith|IS NULL|IS NOT NULL)\s+('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|[^\s]+)", token, re.IGNORECASE)
                if match:
                    field, operator, value = match.groups()
                    value = value.strip().strip("'")
                    
                    # Map field names to Django ORM fields
                    if field in ['company', 'location', 'pipeline', 'webform', 'department', 'assesment']:
                        field = f"{field}__name"
                    elif field in ['owner','created_by']:
                        field = f"{field}__first_name"
                    
                    # Construct the condition Q object
                    if operator == 'like':
                        condition = Q(**{f"{field}__icontains": value})
                    elif operator == 'not like':
                        condition = ~Q(**{f"{field}__icontains": value})
                    elif operator == '=':
                        condition = Q(**{f"{field}__iexact": value})
                    elif operator == '<>':
                        condition = ~Q(**{f"{field}__iexact": value})
                    elif operator == '>':
                        condition = Q(**{f"{field}__gt": value})
                    elif operator == '>=':
                        condition = Q(**{f"{field}__gte": value})
                    elif operator == '<':
                        condition = Q(**{f"{field}__lt": value})
                    elif operator == '<=':
                        condition = Q(**{f"{field}__lte": value})
                    elif operator == 'startwith':
                        condition = Q(**{f"{field}__istartswith": value})
                    elif operator == 'endwith':
                        condition = Q(**{f"{field}__iendswith": value})
                    elif operator == 'is null':
                        condition = Q(**{f"{field}__isnull": True})
                    elif operator == 'is not null':
                        condition = ~Q(**{f"{field}__isnull": True})

                    # Apply the current operator
                    if current_q is None:
                        current_q = condition
                    elif current_operator == 'and':
                        current_q &= condition
                    elif current_operator == 'or':
                        current_q |= condition

                    current_operator = None

        return current_q if current_q else Q()
        
class AssesmentSQLQueryView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            data = request.data
            query = data.get('query')
            if query:
                query = query.replace('%', '')
            # Use Django ORM to filter assessments
            assessments = models.Assesment.objects.select_related('company', 'category', 'created_by')
            
            if not user.is_superuser:
                assessments = assessments.filter(company__id=user.company_id)

            if query:
                # Replace logical operators with Python's operators
                query = query.replace(" AND ", " and ").replace(" OR ", " or ")
                
                # Parse and construct the Q object
                q_object = self.construct_q_object(query)
                
                # Apply the Q object to filter assessments
                assessments = assessments.filter(q_object)

            results = assessments.values(
                'id', 'company__name', 'category__name', 'name', 'form','company__admin__username',
                'created_by__first_name', 'updated', 'created'
            )

            results_list = list(results)

            return Response({'result': results_list}, status=status.HTTP_200_OK)
        except Exception as e:
            # Return all assessments in case of an error
            assessments = models.Assesment.objects.select_related('company', 'category', 'created_by').values(
                'id', 'company__name', 'category__name', 'name', 'form','company__admin__username',
                'created_by__first_name', 'updated', 'created'
            )
            results_list = list(assessments)
            return Response({'result': results_list, 'error': str(e)}, status=status.HTTP_200_OK)

    def construct_q_object(self, query):
        # Tokenize the query using regex to handle nested conditions and operators
        tokens = re.split(r'(\(|\)|\s+and\s+|\s+or\s+)', query)
        tokens = [token for token in tokens if token.strip()]

        # Stack to manage nested conditions and Q objects
        stack = []
        current_q = None
        current_operator = None

        for token in tokens:
            token = token.strip().lower()

            if token == '(':
                stack.append((current_q, current_operator))
                current_q = None
                current_operator = None
            elif token == ')':
                temp_q = current_q
                if stack:
                    current_q, current_operator = stack.pop()
                    if current_operator == 'and':
                        current_q &= temp_q
                    elif current_operator == 'or':
                        current_q |= temp_q
                    else:
                        current_q = temp_q
            elif token == 'and':
                current_operator = 'and'
            elif token == 'or':
                current_operator = 'or'
            else:
                match = re.match(r"(\w+)\s+(like|not like|=|<>|>|>=|<|<=|startwith|endwith|IS NULL|IS NOT NULL)\s+('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|[^\s]+)", token, re.IGNORECASE)
                if match:
                    print("match",match)
                    field, operator, value = match.groups()
                    value = value.strip().strip("'")
                    
                    # Map field names to Django ORM fields
                    if field in ['company', 'category']:
                        field = f"{field}__name"
                    elif field == 'created_by':
                        field = 'created_by__first_name'
                    
                    # Construct the condition Q object
                    if operator == 'like':
                        condition = Q(**{f"{field}__icontains": value})
                    elif operator == 'not like':
                        condition = ~Q(**{f"{field}__icontains": value})
                    elif operator == '=':
                        condition = Q(**{f"{field}__iexact": value})
                    elif operator == '<>':
                        condition = ~Q(**{f"{field}__iexact": value})
                    elif operator == '>':
                        condition = Q(**{f"{field}__gt": value})
                    elif operator == '>=':
                        condition = Q(**{f"{field}__gte": value})
                    elif operator == '<':
                        condition = Q(**{f"{field}__lt": value})
                    elif operator == '<=':
                        condition = Q(**{f"{field}__lte": value})
                    elif operator == 'startwith':
                        condition = Q(**{f"{field}__istartswith": value})
                    elif operator == 'endwith':
                        condition = Q(**{f"{field}__iendswith": value})
                    elif operator == 'is null':
                        condition = Q(**{f"{field}__isnull": True})
                    elif operator == 'is not null':
                        condition = ~Q(**{f"{field}__isnull": True})

                    # Apply the current operator
                    if current_q is None:
                        current_q = condition
                    elif current_operator == 'and':
                        current_q &= condition
                    elif current_operator == 'or':
                        current_q |= condition

                    current_operator = None

        return current_q if current_q else Q()
        


class JobByCompanyApi(APIView):
    def get(self, request, pk=None, *args, **kwargs):
            job = models.Job.objects.filter(company__id=pk,job_status=Job.IN_PROGRESS).order_by('-created')
            serializer = JobsSerializer(job, many=True)
            
            return Response(serializer.data)

class LatestJobsView(APIView):
    def get(self, request):
        
        # Start with all published jobs
        jobs = Job.objects.filter(published=True, job_status=Job.IN_PROGRESS).order_by('-created_by')[:4]

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
                'company_name': job.company.name if job.company else None,
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

        return Response(jobs_data)  
        
class CountList(APIView):
    def get(self, request):
        jobs_count = Job.objects.count()
        candidates_count = Candidate.objects.count()
        companies_count = Company.objects.count()
        
        # New applications per day (today)
        today = timezone.now().date()
        applications_today = Candidate.objects.filter(created__date=today).count()

        data = {
            'total_jobs': jobs_count,
            'total_candidates': candidates_count,
            'total_companies': companies_count,
            'applications_today': applications_today,
        }
        
        return Response(data)


class DailyCreatedJobsCount(APIView):
    def get(self, request):
        from job.helper import get_daily_created_jobs
        data = get_daily_created_jobs(request)
        return Response(data)

class JobTimelineView(APIView):
    def get(self,request,job_id):
        data = helper.JobTimelineView(self,request,job_id)
        return data

# class JobListView(APIView):
#     renderer_classes = [XMLRenderer]

#     def get(self, request, format=None):
#         jobs = Job.getAll()
#         serializer = JobsSerializer(jobs, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

class JobListView(APIView):
    def get(self, request, format=None):
        # jobs = Job.objects.filter(published=True, job_status=Job.IN_PROGRESS)
        jobs = Job.objects.filter(
            published=True, 
            job_status=Job.IN_PROGRESS,
            job_boards__contains=['talent']
        )

        doc = Document()
        root = doc.createElement('jobs')
        doc.appendChild(root)

        for job in jobs:
            job_el = doc.createElement('job')
            # Normalize dynamic_job_data to a dict (some rows may store it as a JSON string)
            raw_dynamic = job.dynamic_job_data
            if isinstance(raw_dynamic, str):
                try:
                    raw_dynamic = json.loads(raw_dynamic)
                except Exception:
                    raw_dynamic = {}
            elif raw_dynamic is None:
                raw_dynamic = {}

            def ensure_dict(value):
                return value if isinstance(value, dict) else {}

            dynamic_data = ensure_dict(raw_dynamic.get('Create Job', {}))
            dynamic_address_data = ensure_dict(raw_dynamic.get('Address Information', {}))
            description = ensure_dict(raw_dynamic.get('Description Information', {}))
            # Safely extract description information with fallbacks
            description_data = ensure_dict(description.get('description', {}))
            job_description = description_data.get('job_description', '')
            requirements = description_data.get('requirements', '')
            benefits = description_data.get('benefits', '')
            
            forment_description = f"Description: {job_description} Requirements:{requirements} Benefits:{benefits}"
            
            def _cdata(tag, text):
                el = doc.createElement(tag)
                el.appendChild(doc.createCDATASection(str(text or '')))
                job_el.appendChild(el)

            # 1) IDs and URLs
            _cdata('id', job.id)
            title_value = dynamic_data.get('title') or ''
            _cdata('url', f"{settings.JOB_URL}/jobs/{job.id}?platform=talent")
            _cdata('url_apply', f"{settings.JOB_URL}/jobs/{job.id}?platform=talent")

            # 2) Core fields
            _cdata('title', dynamic_data.get('title', ''))
            _cdata('content', forment_description)

            # 3) category / subcategory
            _cdata('category', ensure_dict(dynamic_data.get('department', {})).get('name', ''))
            _cdata('subcategory', '')  # no subcategory in your model
            
            # 4) company & location
            _cdata('company', job.company.name if job.company else '')
            _cdata('city',    ensure_dict(dynamic_address_data.get('city', {})).get('name', ''))
            _cdata('zipcode', dynamic_address_data.get('pincode', ''))
            # region = "City, State"
            region_parts = []
            city_name = ensure_dict(dynamic_address_data.get('city', {})).get('name', '')
            state_name = ensure_dict(dynamic_address_data.get('state', {})).get('name', '')
            if city_name: region_parts.append(city_name)
            if state_name: region_parts.append(state_name)
            _cdata('region', ", ".join(region_parts))
            
            _cdata('country', ensure_dict(dynamic_address_data.get('country', {})).get('name', ''))

            # 5) salary / job type / vacancies
            salary_min = dynamic_data.get('salary_min', '')
            salary_max = dynamic_data.get('salary_max', '')
            currency = dynamic_data.get('currency', '')
            salary_type = str(dynamic_data.get('salary_type', 'month') or 'month').lower()
            salary = (f"{currency} {salary_min} - {salary_max} per {salary_type}"
                      if salary_min and salary_max else
                      "Not specified")
            _cdata('salary', salary)
            _cdata('jobtype', dynamic_data.get('type', ''))
            _cdata('num_vacancies', dynamic_data.get('vacancies', ''))

            # map Physical/Remote to "not remote"/"remote"
            remote_flag = 'remote' if str(dynamic_data.get('nature', '') or '').lower() == 'remote' else 'not remote'
            _cdata('remote', remote_flag)

            # 6) company logo URL (no CDATA, per your example)
            logo_el = doc.createElement('company_logo_url')
            logo_url = ''  # No logo URL in dynamic data
            logo_el.appendChild(doc.createTextNode(logo_url))
            job_el.appendChild(logo_el)

            # 7) publication date in DD/MM/YYYY HH:MM:SS
            pub_str = job.created.strftime('%d/%m/%Y %H:%M:%S')
            _cdata('publication', pub_str)

            root.appendChild(job_el)

        xml_bytes = doc.toprettyxml(indent='  ', encoding='utf-8')
        return HttpResponse(
            xml_bytes,
            content_type='application/xml; charset=utf-8'
        )
 
class AdzunaJobListView(APIView):
    def get(self, request, format=None):
        jobs = Job.objects.filter(published=True, job_status=Job.IN_PROGRESS,job_boards__contains=['adzuna'])

        doc = Document()
        root = doc.createElement('jobs')
        doc.appendChild(root)

        for job in jobs:
            job_el = doc.createElement('job')
            # Normalize dynamic_job_data to a dict (some rows may store it as a JSON string)
            raw_dynamic = job.dynamic_job_data
            if isinstance(raw_dynamic, str):
                try:
                    raw_dynamic = json.loads(raw_dynamic)
                except Exception:
                    raw_dynamic = {}
            elif raw_dynamic is None:
                raw_dynamic = {}

            def ensure_dict(value):
                return value if isinstance(value, dict) else {}

            # Map country names/variants to the required two-letter code
            def country_to_code(value: str) -> str:
                allowed_codes = {
                    'AU', 'AT', 'BE', 'BR', 'CA', 'CH', 'FR', 'DE', 'ES', 'IN',
                    'IT', 'MX', 'NL', 'NZ', 'PL', 'SG', 'ZA', 'UK', 'US'
                }
                if not value:
                    return ''
                v = str(value).strip()
                # If already a permitted code, return as uppercase
                if v.upper() in allowed_codes:
                    return v.upper()
                vl = v.lower()
                name_map = {
                    'australia': 'AU',
                    'austria': 'AT',
                    'belgium': 'BE',
                    'brazil': 'BR',
                    'canada': 'CA',
                    'switzerland': 'CH',
                    'france': 'FR',
                    'germany': 'DE',
                    'spain': 'ES',
                    'india': 'IN',
                    'italy': 'IT',
                    'mexico': 'MX',
                    'netherlands': 'NL',
                    'the netherlands': 'NL',
                    'new zealand': 'NZ',
                    'poland': 'PL',
                    'singapore': 'SG',
                    'south africa': 'ZA',
                    'united kingdom': 'UK',
                    'great britain': 'UK',
                    'england': 'UK',
                    'scotland': 'UK',
                    'wales': 'UK',
                    'northern ireland': 'UK',
                    'united states': 'US',
                    'united states of america': 'US',
                    'usa': 'US',
                    'u.s.a.': 'US',
                }
                return name_map.get(vl, '')

            dynamic_data = ensure_dict(raw_dynamic.get('Create Job', {}))
            dynamic_address_data = ensure_dict(raw_dynamic.get('Address Information', {}))
            description = ensure_dict(raw_dynamic.get('Description Information', {}))
            # Safely extract description information with fallbacks
            description_data = ensure_dict(description.get('description', {}))
            job_description = description_data.get('job_description', '')
            requirements = description_data.get('requirements', '')
            benefits = description_data.get('benefits', '')
            
            forment_description = f"Description: {job_description} Requirements:{requirements} Benefits:{benefits}"
            
            def _cdata(tag, text):
                el = doc.createElement(tag)
                el.appendChild(doc.createCDATASection(str(text or '')))
                job_el.appendChild(el)

            # 1) IDs and URLs
            _cdata('id', job.id)
            title_value = dynamic_data.get('title') or ''
            _cdata('url', f"{settings.JOB_URL}/jobs/{job.id}?platform=adzuna")
            # _cdata('url_apply', f"{settings.JOB_URL}/jobs/Careers/{job.id}/{str(title_value).replace(' ', '%20')}?platform=adzuna")

            # 2) Core fields
            _cdata('title', dynamic_data.get('title', ''))
            _cdata('description', forment_description)

            # 3) category / subcategory
            _cdata('category', ensure_dict(dynamic_data.get('department', {})).get('name', ''))
            # _cdata('subcategory', '')  # no subcategory in your model
            
            # 4) company & location
            _cdata('company', job.company.name if job.company else '')
            # _cdata('city',    ensure_dict(dynamic_address_data.get('city', {})).get('name', ''))
            _cdata('postcode', dynamic_address_data.get('pincode', ''))
            # region = "City, State"
            region_parts = []
            city_name = ensure_dict(dynamic_address_data.get('city', {})).get('name', '')
            state_name = ensure_dict(dynamic_address_data.get('state', {})).get('name', '')
            country_name = ensure_dict(dynamic_address_data.get('country', {})).get('name', '')
            try:
                location_id = ensure_dict(dynamic_address_data.get('location', {})).get('id', '')
                location_obj = Location.objects.get(id=location_id)
                if location_obj: region_parts.append(location_obj.address)
            except:
                location_obj = None

            if city_name: region_parts.append(city_name)
            if state_name: region_parts.append(state_name)
            if country_name: region_parts.append(country_name)
            _cdata('location', ", ".join(region_parts))
            
            # Output required two-letter country code (e.g., AU, UK, US)
            _cdata('country', country_to_code(country_name))

            # 5) salary / job type / vacancies
            salary_min = dynamic_data.get('salary_min', '')
            salary_max = dynamic_data.get('salary_max', '')
            currency = dynamic_data.get('currency', '')
            salary_type = str(dynamic_data.get('salary_type', 'month') or 'month').lower()
            salary = (f"{currency} {salary_min} - {salary_max} per {salary_type}"
                      if salary_min and salary_max else
                      "Not specified")
            _cdata('salary', salary)
            _cdata('salary_min', salary_min)
            _cdata('salary_max', salary_max)
            _cdata('salary_frequency', salary_type)
            _cdata('salary_currency', currency)
            _cdata('contract_time', dynamic_data.get('type', ''))
            _cdata('num_vacancies', dynamic_data.get('vacancies', ''))

            # map Physical/Remote to "not remote"/"remote"
            remote_flag = 'Remote' if str(dynamic_data.get('nature', '') or '').lower() == 'remote' else 'Not-Remote'
            _cdata('remote', remote_flag)

            # 6) company logo URL (no CDATA, per your example)
            logo_el = doc.createElement('company_logo_url')
            logo_url = ''  # No logo URL in dynamic data
            logo_el.appendChild(doc.createTextNode(logo_url))
            job_el.appendChild(logo_el)

            # 7) publication date in DD/MM/YYYY HH:MM:SS
            pub_str = job.created.strftime('%d/%m/%Y %H:%M:%S')
            _cdata('date', pub_str)

            root.appendChild(job_el)

        xml_bytes = doc.toprettyxml(indent='  ', encoding='utf-8')
        return HttpResponse(
            xml_bytes,
            content_type='application/xml; charset=utf-8'
        )
   
   
   
class WhatjobsListView(APIView):
    def get(self, request, format=None):
        jobs = Job.objects.filter(published=True, job_status=Job.IN_PROGRESS,job_boards__contains=['what_job'])
        # If JSON format requested, return Whatjobs JSON schema
        if (request.GET.get('format') or '').lower() == 'json':
            results = []

            for job in jobs:
                raw_dynamic = job.dynamic_job_data
                if isinstance(raw_dynamic, str):
                    try:
                        raw_dynamic = json.loads(raw_dynamic)
                    except Exception:
                        raw_dynamic = {}
                elif raw_dynamic is None:
                    raw_dynamic = {}

                def ensure_dict(value):
                    return value if isinstance(value, dict) else {}

                dynamic_data = ensure_dict(raw_dynamic.get('Create Job', {}))
                dynamic_address_data = ensure_dict(raw_dynamic.get('Address Information', {}))
                description = ensure_dict(raw_dynamic.get('Description Information', {}))
                description_data = ensure_dict(description.get('description', {}))

                job_description = description_data.get('job_description', '')
                requirements = description_data.get('requirements', '')
                benefits = description_data.get('benefits', '')
                full_description = f"Description: {job_description} Requirements:{requirements} Benefits:{benefits}"

                city_name = ensure_dict(dynamic_address_data.get('city', {})).get('name', '')
                state_name = ensure_dict(dynamic_address_data.get('state', {})).get('name', '')
                country_code = ensure_dict(dynamic_address_data.get('country', {})).get('code', '') or ensure_dict(dynamic_address_data.get('country', {})).get('iso_code', '')
                address = ensure_dict(dynamic_address_data.get('location', {})).get('name', '')

                title_value = dynamic_data.get('title') or ''
                job_url = f"{settings.JOB_URL}/jobs/{job.id}?platform=whatjobs"

                salary_min = dynamic_data.get('salary_min', '')
                salary_max = dynamic_data.get('salary_max', '')
                salary_type_raw = str(dynamic_data.get('salary_type', 'month') or 'month').lower()

                # Map salary type to an example numeric code if needed (fallback to 3 as example)
                salary_type_code = {
                    'year': 1,
                    'annual': 1,
                    'month': 3,
                    'weekly': 4,
                    'week': 4,
                    'day': 5,
                    'hour': 6
                }.get(salary_type_raw, 3)

                company_name = job.company.name if job.company else ''
                company_description = getattr(job.company, 'description', '') if job.company else ''
                company_email = job.company.email if job.company and getattr(job.company, 'email', None) else ''

                # Build skills list if available
                skills = []
                if isinstance(dynamic_data.get('skills', []), list):
                    skills = dynamic_data.get('skills', [])
                elif dynamic_data.get('skills'):
                    skills = [str(dynamic_data.get('skills'))]

                # Employment type defaults
                type_value = str(dynamic_data.get('type', '') or '').lower()
                period = 'permanent'

                results.append({
                    'command': 'add',
                    'countryCode': country_code,
                    'jobIdent': str(job.id),
                    'jobTitle': title_value,
                    'city': city_name,
                    'state': state_name,
                    'jobLocationAddress': address,
                    'zip': dynamic_address_data.get('pincode', ''),
                    'jobPaymentRangeFrom': str(salary_min) if salary_min is not None else '',
                    'jobPaymentRangeTo': str(salary_max) if salary_max is not None else '',
                    'salaryDisplayType': 99,
                    'jobPaymentRangeType': salary_type_code,
                    'jobSupplementPayOptions': 4,
                    'jobWorkFrom': 5,
                    'jobStartType': 2,
                    'jobStartByDate': job.created.strftime('%Y-%m-%d') if getattr(job, 'created', None) else '',
                    'jobEmploymentType': 1,
                    'jobEmploymentSubType': 4,
                    'jobScheduleType': 1,
                    'jobScheduleTypeOther': '',
                    'jobPeriod': period,
                    'jobLength': 0,
                    'companyName': company_name,
                    'companyDescription': company_description or '',
                    'jobOpeningCount': getattr(job, 'vacancies', 1) or 1,
                    'jobSector': ensure_dict(dynamic_data.get('department', {})).get('name', ''),
                    'jobDescription': full_description,
                    'jobCommunicationMail': company_email,
                    'jobCommunicationURL': job_url,
                    'jobReferenceId': str(job.id),
                    'jobSkills': skills,
                })

            return JsonResponse(results, safe=False)

        # Default: XML response (existing behavior)
        doc = Document()
        root = doc.createElement('jobs')
        doc.appendChild(root)

        for job in jobs:
            job_el = doc.createElement('job')
            job_el.setAttribute('id', str(job.id))
            # Normalize dynamic_job_data to a dict (some rows may store it as a JSON string)
            raw_dynamic = job.dynamic_job_data
            if isinstance(raw_dynamic, str):
                try:
                    raw_dynamic = json.loads(raw_dynamic)
                except Exception:
                    raw_dynamic = {}
            elif raw_dynamic is None:
                raw_dynamic = {}

            def ensure_dict(value):
                return value if isinstance(value, dict) else {}

            dynamic_data = ensure_dict(raw_dynamic.get('Create Job', {}))
            dynamic_address_data = ensure_dict(raw_dynamic.get('Address Information', {}))
            description = ensure_dict(raw_dynamic.get('Description Information', {}))
            # Safely extract description information with fallbacks
            description_data = ensure_dict(description.get('description', {}))
            job_description = description_data.get('job_description', '')
            requirements = description_data.get('requirements', '')
            benefits = description_data.get('benefits', '')
            
            forment_description = f"Description: {job_description} Requirements:{requirements} Benefits:{benefits}"
            
            def _cdata(tag, text):
                el = doc.createElement(tag)
                el.appendChild(doc.createCDATASection(str(text or '')))
                job_el.appendChild(el)

            # Build normalized address/location string
            region_parts = []
            city_name = ensure_dict(dynamic_address_data.get('city', {})).get('name', '')
            state_name = ensure_dict(dynamic_address_data.get('state', {})).get('name', '')
            country_name = ensure_dict(dynamic_address_data.get('country', {})).get('name', '')
            address = ensure_dict(dynamic_address_data.get('location', {})).get('name', '')
            if address: region_parts.append(address)
            if city_name: region_parts.append(city_name)
            if state_name: region_parts.append(state_name)
            if country_name: region_parts.append(country_name)
            location_str = ", ".join(region_parts)

            # Title and URL
            title_value = dynamic_data.get('title') or ''
            job_url = f"{settings.JOB_URL}/jobs/{job.id}?platform=whatjobs"
            
            _cdata('url', job_url)

            # Salary fields
            salary_min = dynamic_data.get('salary_min', '')
            salary_max = dynamic_data.get('salary_max', '')
            currency = (dynamic_data.get('currency', '') or '').lower()
            salary_type_raw = str(dynamic_data.get('salary_type', 'month') or 'month').lower()
            # Map to requested vocabulary where possible
            salary_type_out = {
                'year': 'annum',
                'yearly': 'annum',
                'annual': 'annum',
                'month': 'month',
                'monthly': 'month',
                'week': 'week',
                'weekly': 'week',
                'day': 'day',
                'daily': 'day'
            }.get(salary_type_raw, salary_type_raw)

            # Job type/status
            type_value = str(dynamic_data.get('type', '') or '').lower()
            job_status_out = 'full-time' if type_value in ['full time', 'full_time', 'full-time', 'fulltime'] else (
                'part-time' if type_value in ['part time', 'part_time', 'part-time', 'parttime'] else '')
            # Not available in model; default to permanent unless specified elsewhere
            job_type_out = 'permanent'

            # Company details
            company_name = job.company.name if job.company else ''
            company_email = job.company.email if job.company and getattr(job.company, 'email', None) else ''

            # Write requested Whatjobs tags
            _cdata('reference', job.id)
            _cdata('command', 'add')
            _cdata('company_email', company_email)
            _cdata('company_name', company_name)
            # _cdata('company_hash', '')
            _cdata('title', title_value)
            _cdata('description', forment_description)
            # _cdata('industry', ensure_dict(dynamic_data.get('department', {})).get('name', ''))
            _cdata('job_type', job_type_out)
            _cdata('job_status', job_status_out)
            _cdata('weeks_to_advertise', '1')
            _cdata('application_email', company_email)
            _cdata('application_url', job_url)
            _cdata('salary_type', salary_type_out)
            _cdata('salary_from', salary_min)
            _cdata('salary_to', salary_max)
            _cdata('salary_currency', currency)
            # _cdata('salary_benefits', benefits)
            # _cdata('location', location_str)
            _cdata('state', state_name)
            _cdata('city', city_name)
            _cdata('postcode', dynamic_address_data.get('pincode', ''))
           
            root.appendChild(job_el)

        xml_bytes = doc.toprettyxml(indent='  ', encoding='utf-8')
        return HttpResponse(
            xml_bytes,
            content_type='application/xml; charset=utf-8'
        )
   
class LinkedInJobFeedView(APIView):
    """
    Generates an XML feed of jobs in LinkedIn's preferred format.
    """
    def get(self, request, format=None):
        jobs = Job.objects.filter(
            published=True,
            job_status=Job.IN_PROGRESS,
            # job_boards__contains=['linkedin']
        )

        doc = Document()
        source = doc.createElement("source")
        doc.appendChild(source)

        # Add lastBuildDate
        last_build_date = doc.createElement('lastBuildDate')
        last_build_date.appendChild(
            doc.createTextNode(datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'))
        )
        source.appendChild(last_build_date)

        # ---- Helper CDATA creator ----
        def _cdata(tag, text):
            el = doc.createElement(tag)
            el.appendChild(doc.createCDATASection(str(text or "")))
            return el

        # ------------------------------
        #     BUILD JOB ELEMENTS
        # ------------------------------
        for job in jobs:
            # Skip jobs without a company
            if not job.company:
                continue
                
            # Skip jobs without an active linkding_id
            try:
                linkding_company = job.company.linkding_ids.filter(is_active=True).first()
                if not linkding_company or not linkding_company.linkding_id:
                    continue
                linkding_id = linkding_company.linkding_id
            except Exception:
                continue

            # Normalize dynamic data
            def safe_dict(value):
                return value if isinstance(value, dict) else {}

            dynamic_data = safe_dict(job.dynamic_job_data.get("Create Job", {}))
            dynamic_address = safe_dict(job.dynamic_job_data.get("Address Information", {}))
            description_info = safe_dict(job.dynamic_job_data.get("Description Information", {}))

            job_el = doc.createElement("job")

            # ---- Basic fields ----
            job_el.appendChild(_cdata("partnerJobId", job.id))
            job_el.appendChild(_cdata("company", job.company.name))
            job_el.appendChild(_cdata("companyId", str(linkding_id)))
            job_el.appendChild(_cdata("title", dynamic_data.get("title", "")))

            # ---- Description ----
            desc_block = safe_dict(description_info.get("description", {}))

            # Build the description parts
            desc_parts = [desc_block.get('job_description', '')]

            # Add requirements if they exist
            requirements = desc_block.get('requirements', '').strip()
            if requirements:
                desc_parts.append(f"Requirements:\n{requirements}")

            # Add benefits if they exist
            benefits = desc_block.get('benefits', '').strip()
            if benefits:
                desc_parts.append(f"Benefits:\n{benefits}")

            # Join all non-empty parts with double newlines
            full_desc = '\n\n'.join(part for part in desc_parts if part)

            job_el.appendChild(_cdata("description", full_desc))

            # ---- Apply URL ----
            job_url = f"{settings.JOB_URL}/jobs/{job.id}?source=linkedin"
            job_el.appendChild(_cdata("applyUrl", job_url))

            # ---- Location ----
            city = safe_dict(dynamic_address.get("city", {})).get("name", "")
            state = safe_dict(dynamic_address.get("state", {})).get("name", "")
            country = safe_dict(dynamic_address.get("country", {})).get("name", "")
            postal = dynamic_address.get("pincode", "")

            loc_str = ", ".join([x for x in [city, state, country] if x])

            job_el.appendChild(_cdata("location", loc_str))
            job_el.appendChild(_cdata("city", city))
            job_el.appendChild(_cdata("state", state))
            job_el.appendChild(_cdata("country", country.upper()))
            job_el.appendChild(_cdata("postalCode", postal))

            job_el.appendChild(_cdata("workplaceTypes", "On-site"))

            # ---- Experience Level ----
            exp_min = int(dynamic_data.get("exp_min", 0) or 0)

            if exp_min >= 8:
                exp_level = "DIRECTOR_LEVEL"
            elif exp_min >= 5:
                exp_level = "SENIOR_LEVEL"
            elif exp_min >= 2:
                exp_level = "MID_SENIOR_LEVEL"
            else:
                exp_level = "ENTRY_LEVEL"

            job_el.appendChild(_cdata("experienceLevel", exp_level))

            # ---- Job Types (correct LinkedIn format) ----
            job_type_raw = (dynamic_data.get("type") or "").lower()

            if "full" in job_type_raw:
                jt = "FULL_TIME"
            elif "part" in job_type_raw:
                jt = "PART_TIME"
            elif "contract" in job_type_raw:
                jt = "CONTRACT"
            elif "intern" in job_type_raw:
                jt = "INTERNSHIP"
            else:
                jt = "FULL_TIME"
            job_el.appendChild(_cdata("jobTypes", jt))
            # # jobtypes_el = doc.createElement("jobTypes")
            # jt_el = doc.createElement("jobType")
            # jt_el.appendChild(doc.createCDATASection(jt))
            # # jobtypes_el.appendChild(jt_el)
            # # job_el.appendChild(jobtypes_el)

            # ---- Skills ----
            if hasattr(job, "skills"):
                skills = job.skills.all()[:10]
                if skills:
                    skills_el = doc.createElement("skills")
                    for skill in skills:
                        skill_el = doc.createElement("skill")
                        skill_el.appendChild(doc.createCDATASection(skill.name))
                        skills_el.appendChild(skill_el)
                    job_el.appendChild(skills_el)

            # ---- Salary ----
            salary_min = dynamic_data.get("salary_min")
            salary_max = dynamic_data.get("salary_max")
            currency = (dynamic_data.get("currency") or "USD").upper()

            if salary_min or salary_max:
                salaries_el = doc.createElement("salaries")
                salary_el = doc.createElement("salary")

                if salary_max:
                    high = doc.createElement("highEnd")
                    amt = doc.createElement("amount")
                    amt.appendChild(doc.createCDATASection(str(salary_max)))
                    high.appendChild(amt)

                    cur = doc.createElement("currencyCode")
                    cur.appendChild(doc.createTextNode(currency))
                    high.appendChild(cur)
                    salary_el.appendChild(high)

                if salary_min:
                    low = doc.createElement("lowEnd")
                    amt = doc.createElement("amount")
                    amt.appendChild(doc.createCDATASection(str(salary_min)))
                    low.appendChild(amt)

                    cur = doc.createElement("currencyCode")
                    cur.appendChild(doc.createTextNode(currency))
                    low.appendChild(cur)
                    salary_el.appendChild(low)

                period = doc.createElement("period")
                period.appendChild(doc.createCDATASection("YEARLY"))
                salary_el.appendChild(period)

                type_el = doc.createElement("type")
                type_el.appendChild(doc.createCDATASection("BASE_SALARY"))
                salary_el.appendChild(type_el)

                salaries_el.appendChild(salary_el)
                job_el.appendChild(salaries_el)

            # ---- Job Posting Availability ----
            job_el.appendChild(_cdata("jobPostingAvailability", "PUBLIC"))

            # Attach job
            source.appendChild(job_el)

        xml_bytes = doc.toprettyxml(indent="  ", encoding="utf-8")
        return HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")


class IndeedJobFeedView(APIView):
    """
    Generates an XML feed of jobs in Indeed's preferred format.
    """
    def get(self, request, format=None):
        # Get active jobs
        jobs = Job.objects.filter(
        published=True,
        job_status=Job.IN_PROGRESS,
        )

        doc = minidom.Document()

        # root <source>
        source = doc.createElement("source")
        doc.appendChild(source)

        # helper for CDATA
        def _cdata(tag, text):
            el = doc.createElement(tag)
            el.appendChild(doc.createCDATASection(str(text or "")))
            return el

        # Required metadata
        source.appendChild(_cdata("publisher", "Edjobster"))
        source.appendChild(_cdata("publisherurl", "https://www.edjobster.com"))
        source.appendChild(_cdata(
            "lastBuildDate",
            datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        ))

        def safe_dict(v):
            return v if isinstance(v, dict) else {}

        for job in jobs:
            job_el = doc.createElement("job")

            dyn = safe_dict(job.dynamic_job_data.get("Create Job", {}))
            address = safe_dict(job.dynamic_job_data.get("Address Information", {}))
            desc_info = safe_dict(job.dynamic_job_data.get("Description Information", {}))

            desc_block = safe_dict(desc_info.get("description", {}))
            html_description = desc_block.get("job_description", "")  # this must be HTML!

            # Requirements
            if desc_block.get("requirements"):
                html_description += f"<h3>Requirements:</h3><p>{desc_block['requirements']}</p>"

            # Benefits
            if desc_block.get("benefits"):
                html_description += f"<h3>Benefits:</h3><p>{desc_block['benefits']}</p>"

            # title
            job_title = dyn.get("title", job.title or "No Title")
            job_el.appendChild(_cdata("title", job_title))

            # publish date
            pub_date = job.created or timezone.now()
            job_el.appendChild(_cdata("date", pub_date.strftime('%a, %d %b %Y %H:%M:%S GMT')))

            # reference ID
            job_el.appendChild(_cdata("referencenumber", f"job{job.id}"))

            # job URL (must include source=Indeed)
            job_url = f"{settings.JOB_URL}/jobs/{job.id}?source=Indeed"
            job_el.appendChild(_cdata("url", job_url))

            # company
            company_name = job.company.name if job.company else ""
            job_el.appendChild(_cdata("company", company_name))

            # sourcename (must remain same across all jobs of same org)
            job_el.appendChild(_cdata("sourcename", company_name))

            # location formatting
            def loc_value(v):
                if isinstance(v, dict) and "name" in v:
                    return v["name"]
                return v or ""

            city = loc_value(address.get("city", ""))
            state = loc_value(address.get("state", ""))
            country = loc_value(address.get("country", ""))
            postal = loc_value(address.get("pincode", ""))

            job_el.appendChild(_cdata("city", city))
            job_el.appendChild(_cdata("state", state))
            job_el.appendChild(_cdata("country", country))
            job_el.appendChild(_cdata("postalcode", postal))

            # street address (must contain street + city + region)
            street_raw = address.get("address_line_1") or ""
            street_full = f"{street_raw}, {city}, {state} {postal}".strip().strip(",")

            if street_raw:
                job_el.appendChild(_cdata("streetaddress", street_full))

            # email (optional)
            if job.company and job.company.email:
                job_el.appendChild(_cdata("email", job.company.email))

            # description (must be HTML)
            job_el.appendChild(_cdata("description", html_description))

            # salary formatting per rules
            salary_min = dyn.get("salary_min")
            salary_max = dyn.get("salary_max")
            salary_type = dyn.get("salary_type", "").lower()  # year, month, hour
            salary_map = {
                "daily": "per day",
                "weekly": "per week",
                "monthly": "per month",
                "yearly": "per year",
            }

            salary_type = (dyn.get("salary_type") or "").lower()
            pay_period = salary_map.get(salary_type, "")



            if salary_min or salary_max:
                s_min = str(salary_min).replace(",", "") if salary_min else ""
                s_max = str(salary_max).replace(",", "") if salary_max else ""

                # Currency symbol
                currency_type = dyn.get("currency", "").upper()
                currency_map = {
                    "USD": "$",
                    "INR": "₹",
                    "EUR": "€",
                    "GBP": "£",
                }
                currency_symbol = currency_map.get(currency_type, "")

                salary_val = ""

                # Build salary value based on min/max
                if s_min and s_max:
                    salary_val = f"{currency_symbol}{s_min}-{currency_symbol}{s_max}"
                elif s_min:
                    salary_val = f"{currency_symbol}{s_min}"
                elif s_max:
                    salary_val = f"{currency_symbol}{s_max}"


                if salary_val and pay_period:
                    job_el.appendChild(_cdata("salary", f"{salary_val} {pay_period}"))

            # education
            if dyn.get("educations"):
                job_el.appendChild(_cdata("education", dyn["educations"]))

            # jobtype
            jtype = dyn.get("type", "").lower()
            if "part" in jtype:
                job_el.appendChild(_cdata("jobtype", "parttime"))
            else:
                job_el.appendChild(_cdata("jobtype", "fulltime"))

            # category (optional)
            if dyn.get("speciality"):
                job_el.appendChild(_cdata("category", dyn["speciality"]))

            # experience (must follow: "5+ years", "3-5 years")
            try:
                exp_min = int(float(dyn.get("exp_min") or 0))
                exp_max = int(float(dyn.get("exp_max") or 0))

                if exp_min and exp_max:
                    exp_text = f"{exp_min}-{exp_max} years"
                elif exp_min:
                    exp_text = f"{exp_min}+ years"
                elif exp_max:
                    exp_text = f"Up to {exp_max} years"
                else:
                    exp_text = ""

                if exp_text:
                    job_el.appendChild(_cdata("experience", exp_text))

            except Exception as e:
                print("Experience error:", e)

            # expiration date = 30 days after publish
            expiration = (pub_date + timedelta(days=30)).strftime('%a, %d %b %Y')
            job_el.appendChild(_cdata("expirationdate", expiration))

            # remote type
            if job.nature == Job.REMOTE:
                job_el.appendChild(_cdata("remotetype", "Fully remote"))

            source.appendChild(job_el)

        xml_bytes = doc.toprettyxml(indent="  ", encoding="utf-8")
        return HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")


class PostJobFreeView(APIView):
    """
    Generates an XML feed of jobs in PostJobFree format.
    """
    def get(self, request, format=None):
        # Get active jobs
        jobs = Job.objects.filter(
            published=True,
            job_status=Job.IN_PROGRESS,
            # job_boards__contains=['linkedin']
        )
        
        # Create XML document
        doc = minidom.Document()
        
        # Create root element
        root = doc.createElement('source')
        doc.appendChild(root)
        
        # Add metadata
        def _cdata(tag, text):
            el = doc.createElement(tag)
            el.appendChild(doc.createCDATASection(str(text)))
            return el
        
        root.appendChild(_cdata('publisher', 'PostJobFree.com'))
        root.appendChild(_cdata('publisherurl', 'https://www.postjobfree.com'))
        root.appendChild(_cdata('timezone', 'UTC'))
        root.appendChild(_cdata('lastBuildDate', timezone.now().strftime('%m/%d/%Y %I:%M:%S %p')))

        def safe_dict(value):
                return value if isinstance(value, dict) else {}        
        # Add jobs
        # Location - Use dynamic_address if available, otherwise fall back to job.location
        def get_location_value(value):
            if isinstance(value, dict) and 'name' in value:
                return value['name']
            return value or ""

        for job in jobs:
            job_el = doc.createElement('job')

            dynamic_data = safe_dict(job.dynamic_job_data.get("Create Job", {}))
            dynamic_address = safe_dict(job.dynamic_job_data.get("Address Information", {}))
            description_info = safe_dict(job.dynamic_job_data.get("Description Information", {}))

            desc_block = safe_dict(description_info.get("description", {}))
            desc_parts = [desc_block.get('job_description', '')]

            # Add requirements if they exist
            requirements = desc_block.get('requirements', '').strip()
            if requirements:
                desc_parts.append(f"Requirements:\n{requirements}")

            # Add benefits if they exist
            benefits = desc_block.get('benefits', '').strip()
            if benefits:
                desc_parts.append(f"Benefits:\n{benefits}")

            # Join all non-empty parts with double newlines
            full_desc = '\n\n'.join(part for part in desc_parts if part)
            
            # Job title
            job_title = dynamic_data.get('title', job.title if hasattr(job, 'title') else 'No Title')
            job_el.appendChild(_cdata('title', job_title))
            
            # Posting date
            created_date = job.created.strftime('%Y-%m-%dT%H:%M:%S')
            job_el.appendChild(_cdata('date', created_date))
            
            # Generate a reference number (using job ID or creating a unique string)
            ref_number = f"job{job.id}"
            job_el.appendChild(_cdata('referencenumber', ref_number))
            
            # Job URL
            job_url = f"{settings.JOB_URL}/jobs/{job.id}?source=postjobfree"
            job_el.appendChild(_cdata('url', job_url))
            
            # Company
            company_name = job.company.name if job.company else ""
            job_el.appendChild(_cdata('company', company_name))
            
            # Location - Use dynamic_address if available, otherwise fall back to job.location
            if dynamic_address:
                job_el.appendChild(_cdata('city', get_location_value(dynamic_address.get('city', ''))))
                job_el.appendChild(_cdata('state', get_location_value(dynamic_address.get('state', ''))))
                job_el.appendChild(_cdata('country', get_location_value(dynamic_address.get('country', ''))))
                job_el.appendChild(_cdata('postalcode', get_location_value(dynamic_address.get('pincode', ''))))
            
            # Job description
            description = job.description or ""
            job_el.appendChild(_cdata('description', full_desc))
            
            # Salary (if available)
            salary_min = dynamic_data.get('salary_min', '')
            salary_max = dynamic_data.get('salary_max', '')
            currency = dynamic_data.get('currency', '')
            salary = f"{salary_min} - {salary_max} {currency}" if salary_min and currency else ""
            job_el.appendChild(_cdata('salary', salary))
            
            root.appendChild(job_el)
        
        # Convert to XML string
        xml_bytes = doc.toprettyxml(indent="  ", encoding="utf-8")
        return HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")

# def job_detail(request, job_id):
#     job = get_object_or_404(Job, id=job_id)
#     print("job",job.dynamic_job_data)
#     return render(request, 'job_detail.html', {'job': job.dynamic_job_data})
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    data = job.dynamic_job_data or {}

    # normalize keys (replace spaces with underscores)
    normalized = {
        key.replace(" ", "_"): value
        for key, value in data.items()
    }
    
    # Add the created date and targetdate (90 days from creation) to the normalized data
    normalized['created'] = job.created
    normalized['targetdate'] = job.created + timedelta(days=90) if job.created else None
    
    apply_url = f'{settings.JOB_URL}/jobs/{job_id}'
    return render(request, 'job_detail.html', {'job': normalized, "apply_url": apply_url})

    
from rest_framework.parsers import MultiPartParser
from django.core.files.storage import default_storage
import xml.etree.ElementTree as ET
from settings.models import Department, Pipeline, Webform, Location
from django.core.exceptions import ValidationError

# class JobUploadView(APIView):
#     parser_classes = [MultiPartParser]

#     def post(self, request, format=None):
#         # Get the uploaded file from request
#         file_obj = request.FILES['file']
        
#         # Save the file temporarily
#         file_path = default_storage.save(file_obj.name, file_obj)
        
#         # Parse the XML file
#         tree = ET.parse(file_path)
#         root = tree.getroot()
        
#         # Iterate over each job entry in the XML
#         for job_elem in root.findall('job'):
#             job_data = {
#                 'company_id': job_elem.find('company_id').text,
#                 'title': job_elem.find('title').text,
#                 'vacancies': job_elem.find('vacancies').text,
#                 'department_id': job_elem.find('department_id').text,
#                 'owner_id': job_elem.find('owner_id').text,
#                 'type': job_elem.find('type').text,
#                 'nature': job_elem.find('nature').text,
#                 'educations': job_elem.find('educations').text,
#                 'speciality': job_elem.find('speciality').text,
#                 'description': job_elem.find('description').text,
#                 'exp_min': job_elem.find('exp_min').text,
#                 'exp_max': job_elem.find('exp_max').text,
#                 'salary_min': job_elem.find('salary_min').text,
#                 'salary_max': job_elem.find('salary_max').text,
#                 'salary_type': job_elem.find('salary_type').text,
#                 'currency': job_elem.find('currency').text,
#                 'job_status': job_elem.find('job_status').text,
#                 'location_id': job_elem.find('location_id').text,
#                 'created_by_id': job_elem.find('created_by_id').text,
#                 'pipeline_id': job_elem.find('pipeline_id').text,
#             }

#             # Create a Job object and save it
#             job = Job(**job_data)
#             job.save()

#         return Response({"message": "Jobs uploaded successfully"}, status=status.HTTP_201_CREATED)

class JobUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        xml_data = """
        <jobs>
            <job>
                <company_id>6bb02cdb-113c-442c-a843-8b789700439f</company_id>
                <title>Software Engineer</title>
                <vacancies>5</vacancies>
                <department_id>11</department_id>
                <owner_id>23</owner_id>
                <type>FULL_TIME</type>
                <nature>Physical</nature>
                <educations>Bachelors</educations>
                <speciality>Backend Development</speciality>
                <description>Develop backend services</description>
                <exp_min>3</exp_min>
                <exp_max>5</exp_max>
                <salary_min>50000</salary_min>
                <salary_max>80000</salary_max>
                <salary_type>MONTHLY</salary_type>
                <currency>USD</currency>
                <job_status>In Progress</job_status>
                <location_id>1</location_id>
                <created_by_id>1</created_by_id>
                <pipeline_id>3</pipeline_id>
            </job>
        </jobs>
        """
        # Parse the XML data from the string
        root = ET.fromstring(xml_data)
        
        # Iterate over each job entry in the XML
        for job_elem in root.findall('job'):
            try:
                # Fetch foreign key objects using the provided IDs
                company = Company.objects.get(id=job_elem.find('company_id').text)
                department = Department.objects.get(id=job_elem.find('department_id').text)
                owner = Account.objects.get(id=job_elem.find('owner_id').text)
                location = Location.objects.get(id=job_elem.find('location_id').text)
                created_by = Account.objects.get(id=job_elem.find('created_by_id').text)
                pipeline = Pipeline.objects.get(id=job_elem.find('pipeline_id').text)
                
                job_data = {
                    'company': company,
                    'title': job_elem.find('title').text,
                    'vacancies': job_elem.find('vacancies').text,
                    'department': department,
                    'owner': owner,
                    'type': job_elem.find('type').text,
                    'nature': job_elem.find('nature').text,
                    'educations': job_elem.find('educations').text,
                    'speciality': job_elem.find('speciality').text,
                    'description': job_elem.find('description').text,
                    'exp_min': job_elem.find('exp_min').text,
                    'exp_max': job_elem.find('exp_max').text,
                    'salary_min': job_elem.find('salary_min').text,
                    'salary_max': job_elem.find('salary_max').text,
                    'salary_type': job_elem.find('salary_type').text,
                    'currency': job_elem.find('currency').text,
                    'job_status': job_elem.find('job_status').text,
                    'location': location,
                    'created_by': created_by,
                    'pipeline': pipeline,
                    'job_boards': [],  # Provide an empty list as default value
                }

                # Create a Job object and save it
                job = Job(**job_data)
                job.save()

            except Company.DoesNotExist:
                return Response({"error": "Company not found"}, status=status.HTTP_400_BAD_REQUEST)
            except Department.DoesNotExist:
                return Response({"error": "Department not found"}, status=status.HTTP_400_BAD_REQUEST)
            except Account.DoesNotExist:
                return Response({"error": "Owner or Created by Account not found"}, status=status.HTTP_400_BAD_REQUEST)
            except Location.DoesNotExist:
                return Response({"error": "Location not found"}, status=status.HTTP_400_BAD_REQUEST)
            except Pipeline.DoesNotExist:
                return Response({"error": "Pipeline not found"}, status=status.HTTP_400_BAD_REQUEST)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Jobs uploaded successfully"}, status=status.HTTP_201_CREATED)
    
# Add this import at the top of your views.py
import requests
class AdzunaJobApi(APIView):
    def get(self, request):
        app_id = '0fdf56c0'  # Replace with your actual API ID
        app_key = '23109f6e489b06da350fcff8c4abfd40'  # Replace with your actual API Key
        base_url = 'http://api.adzuna.com/v1/api/jobs/gb/search/{page}?app_id={app_id}&app_key={app_key}&results_per_page=100&content-type=application/json'
        
        all_jobs = []
        page = 1

        try:
            while True:
                url = base_url.format(page=page, app_id=app_id, app_key=app_key)
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
                jobs = data.get('results', [])
                if not jobs:
                    break  # No more jobs to fetch
                
                all_jobs.extend(jobs)
                
                # Check if we've reached the last page
                if page >= data.get('pages', 1):
                    break
                
                page += 1

            return Response(all_jobs, status=status.HTTP_200_OK)
        
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)      
        
class LinkedInCallbackView(APIView):
    def post(self, request):
        access_token ="AQUf0MjQK9L_rlKCgMP7fZ1ZhsYh5gpYcIKP7tCtGiABzOQPrVLOG_3WJUTirrKSipIaUkbNKwM3-9VMSDPeRvuGCol73Oi1dH8qiQhubnWGe6QeNunilbjcZrTF5v4COBhC6FYW5i7cYZdUGqa1KC6lGrVWTnXq8FwRtykeQv0upjyTVSxJ-USxAQWSH0A_1AjTjOMJ7_FpaC9bY8qnc_-opwfY0FcJk1I9emLLvkZ8pvpYDV6IvRJ7MoJMFoXp6keF3qwecSdzTJQozk78faj-iEG-9__Rwki174_1DcVEYaCck1oMzuBtwUGJpqZXc3alA6aQPhhu3V5MEX-jWB8zWAfcdg"
        sub="mQfPqtFNYL" 
        
        # Set the URL and headers
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            'Authorization': f'Bearer {access_token}',  # Correctly format the access token
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json',
        }

        # Prepare the payload
        payload = {
            "author": "urn:li:person:mQfPqtFNYL",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": "Be the Catalyst for Change! Hiring for #VicePrincipal\n\n We're looking for a Vice Principal to guide our school towards academic excellence. As a key leader, you'll drive curriculum development, oversee daily operations, and mentor staff for continuous improvement.\n\n Salary Range: ₹50,000 - ₹80,000\n\n Opportunity to make a lasting impact in a supportive educational environment.\n\n Apply via: https://lnkd.in/dZPdcddfc  VPP5n\n or Scan QR code\n\n  #EducationLeadership #SchoolAdmin #VicePrincipalJobs #LeadershipRoles"
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # Make the POST request to LinkedIn
        response = requests.post(url, headers=headers, json=payload)
        print("Post response:", response.json())

        if response.status_code == 201:
            return Response({"message": "Post created successfully."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": response.json()}, status=response.status_code)
        
class NaukriJobPostingAPI(APIView):

    def post_to_naukri(self, request):
        api_key = 'YOUR_NAUKRI_API_KEY'
        base_url = 'https://api.naukri.com/v1/jobposting'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        job_data = {
        "title": "Software Engineer",
        "description": "We are looking for a skilled Software Engineer.",
        "location": "Bangalore",
        "experience": "3-5 years",
        "salary": "50000-80000",
        "type": "Full-time",
        # Add other required fields as per Naukri's API documentation
        }
        response = requests.post(base_url, headers=headers, json=job_data)
        return response.json()
    
class JobBoardView(APIView):
    def get(self, request):
        data = helper.JobBoardList(request)
        return data
    def post(self,request):
        data = helper.JobBoardSave(self,request)
        return data
    
class GoogleJobList(APIView):
    def get(self,request):
        data = helper.GoogleJobList(self,request)
        return data
    
class AssessmentJsonDataView(APIView):
    def get(self,request):
        data =Assesment.objects.all()
        serializer = AssessmentJsonDataSerializer(data,many=True)
        return Response(serializer.data)


class AIJobDescriptionGenerateApi(APIView):
    """
    Class-based API for generating AI-powered job descriptions
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    @check_subscription_and_credits_for_ai(feature_code="AI_CREDITS", usage_code="Generate_Job_Description")
    @handle_ai_credits(feature_code="AI_CREDITS", usage_code="Generate_Job_Description")
    def post(self, request):
        """
        Generate AI-powered job description, requirements, and benefits
        
        Expected payload:
        {
            "job_title": "Senior Software Engineer",
            "exp_min": "3",
            "exp_max": "7", 
            "salary_min": "70000",
            "salary_max": "120000",
            "department": "Engineering",
            "skills": ["React", "Node.js", "Python"],
            "custom_prompt": "Remote-friendly company",
            "educations": "JuniorCollege",
            "custom_prompt": "Remote-friendly company"
        }
        """        
        # try:
            # Validate request data
        if not request.data:
            return Response({
                'success': False,
                'message': 'No data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract and validate required fields
        job_title = request.data.get('job_title', '').strip()
        if not job_title:
            return Response({
                'success': False,
                'message': 'Job title is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare data for AI service
        job_data = {
            'job_title': job_title,
            'exp_min': request.data.get('exp_min', ''),
            'exp_max': request.data.get('exp_max', ''),
            'salary_min': request.data.get('salary_min', ''),
            'salary_max': request.data.get('salary_max', ''),
            'department': request.data.get('department', ''),
            'skills': request.data.get('skills', []),
            'custom_prompt': request.data.get('custom_prompt', ''),
            'educations': request.data.get('educations', ''),
            'currency': request.data.get('currency', '')
        }
        
        # Initialize AI service and generate content
        from .services import AIJobDescriptionService
        ai_service = AIJobDescriptionService()
        result = ai_service.generate_job_description(job_data)
        
        if result['success']:
            return Response({
                'success': True,
                'data': result['data'],
                "ai_respons":result,
                'message': 'Job description generated successfully'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': f'AI generation failed: {result.get("error", "Unknown error")}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # except Exception as e:
        #     return Response({
        #         'success': False,
        #         'message': 'An unexpected error occurred. Please try again.'
        #     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIServiceStatusApi(APIView):
    """
    Class-based API for checking AI service status
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Check AI service status and available features
        """
        try:
            # Simple health check
            return Response({
                'success': True,
                'message': 'AI service is running',
                'features': [
                    'Job Description Generation',
                    'Requirements Generation', 
                    'Benefits Generation',
                    'Assessment Questions Generation'
                ],
                'model': 'gpt-4o-mini-2024-07-18',
                'version': '1.0.0'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': 'AI service is unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class AIJobAssessmentsGenerateApi(APIView):
    """
    Class-based API for generating AI-powered assessment questions based on job details
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @check_subscription_and_credits_for_ai(feature_code="AI_CREDITS", usage_code="Generate_Assessment_Questionaire")
    @handle_ai_credits(feature_code="AI_CREDITS", usage_code="Generate_Assessment_Questionaire")
    def post(self, request):
        """
        Generate AI-powered assessment questions based on job details
        
        Expected payload:
        {
            "job_title": "Senior Software Engineer",
            "department": "Engineering",
            "educations": "JuniorCollege",
            "exp_min": "3",
            "exp_max": "7", 
            "salary_min": "70000",
            "salary_max": "120000",
            "skills": ["React", "Node.js", "Python"],
            "description": "Job description text",
            "custom_prompt": "Additional requirements"
            "currency": "INR"
            "salary_min": "70000",
            "salary_max": "120000"
        }
        """
        try:
            # Validate request data
            if not request.data:
                return Response({
                    'success': False,
                    'message': 'No data provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract and validate required fields
            job_title = request.data.get('job_title', '').strip()
            if not job_title:
                return Response({
                    'success': False,
                    'message': 'Job title is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare data for AI service
            job_data = {
                'job_title': job_title,
                'department': request.data.get('department', ''),
                'educations': request.data.get('educations', ''),
                'exp_min': request.data.get('exp_min', ''),
                'exp_max': request.data.get('exp_max', ''),
                'salary_min': request.data.get('salary_min', ''),
                'salary_max': request.data.get('salary_max', ''),
                'skills': request.data.get('skills', []),
                'description': request.data.get('description', ''),
                'custom_prompt': request.data.get('custom_prompt', ''),
                'currency': request.data.get('currency', '')
            }
            
            # Initialize AI service and generate questions
            from .services import AIAssessmentQuestionService
            ai_service = AIAssessmentQuestionService()
            result = ai_service.generate_assessment_questions(job_data)
            
            if result['success']:
                return Response({
                    'success': True,
                    'data': result['data'],
                    'usage': result.get('usage'),
                    'pricing': result.get('pricing'),
                    'ai_response':result,
                    'message': 'Assessment questions generated successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': f'AI generation failed: {result.get("error", "Unknown error")}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AIJobDescriptionGenerateMainApi(APIView):
    """
    Class-based API for generating AI-powered job descriptions
    """
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Generate AI-powered job description, requirements, and benefits
        
        Expected payload:
        {
            "job_title": "Senior Software Engineer",
            "exp_min": "3",
            "exp_max": "7", 
            "salary_min": "70000",
            "salary_max": "120000",
            "department": "Engineering",
            "skills": ["React", "Node.js", "Python"],
            "custom_prompt": "Remote-friendly company",
            "educations": "JuniorCollege",
            "custom_prompt": "Remote-friendly company"
        }
        """
        try:
            # Validate request data
            if not request.data:
                return Response({
                    'success': False,
                    'message': 'No data provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract and validate required fields
            # Fix the syntax and call hr_services saveContactDetails
            from hr_services.models import ContactDetails
            contact_data = {
                "full_name": request.data.get("full_name", ""),
                "email": request.data.get("email", ""),
                "mobile_number": request.data.get("mobile_number", ""),
                "company_name": request.data.get("company_name", ""),
                "message": request.data.get("message", ""),
                "platform": "Jd Generator",
            }

            email = contact_data["email"]
            mobile = contact_data["mobile_number"]

            try:
                contact = ContactDetails.objects.filter(email=email).first() or \
                        ContactDetails.objects.filter(mobile_number=mobile).first()
                if contact:
                    if not contact.Jd_create >=3:
                            # Update existing contact
                                contact.Jd_create += 1
                                contact.full_name = contact_data["full_name"] or contact.full_name
                                contact.company_name = contact_data["company_name"] or contact.company_name
                                contact.message = contact_data["message"] or contact.message
                                contact.platform = contact_data["platform"]
                                contact.save()
                                print("ℹ️ Existing contact updated and count incremented.")
                    else:
                        return Response({
                        'success': False,
                        'message': 'You create meximum 3 time'
                        })
                            # # Create new contact
                            # ContactDetails.objects.create(**contact_data)
                            # print("✅ New contact created.")
                else: 
                    # Create new contact
                    ContactDetails.objects.create(**contact_data)
                    print("✅ New contact created.")

            except IntegrityError as e:
                print(f"❌ Integrity Error: {e}")
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
            job_title = request.data.get('job_title', '').strip()
            if not job_title:
                return Response({
                    'success': False,
                    'message': 'Job title is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare data for AI service
            job_data = {
                'job_title': job_title,
                'exp_min': request.data.get('exp_min', ''),
                'exp_max': request.data.get('exp_max', ''),
                'salary_min': request.data.get('salary_min', ''),
                'salary_max': request.data.get('salary_max', ''),
                'department': request.data.get('department', ''),
                'skills': request.data.get('skills', []),
                'custom_prompt': request.data.get('custom_prompt', ''),
                'educations': request.data.get('educations', ''),
                'currency': request.data.get('currency', '')
            }
            
            # Initialize AI service and generate content
            from .services import AIJobDescriptionService
            ai_service = AIJobDescriptionService()
            result = ai_service.generate_job_description(job_data)
            
            if result['success']:
                return Response({
                    'success': True,
                    'data': result['data'],
                    'message': 'Job description generated successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': f'AI generation failed: {result.get("error", "Unknown error")}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


# class SmartJobSearchAPIView(APIView):
#     """
#     Smart job search that understands queries like:
#     ?q=python 3 year delhi
#     """
#     # permission_classes = [AllowAny]

#     def parse_query(self, query):
#         """Extracts skill, experience, and location from user query."""
#         words = query.lower().split()

#         # Extract experience like '3 year' or '3 years'
#         exp_match = re.search(r'(\d+)\s*(year|years|yr|yrs)?', query.lower())
#         exp = int(exp_match.group(1)) if exp_match else None

#         # Remove that part from query
#         if exp:
#             query = re.sub(r'\d+\s*(year|years|yr|yrs)?', '', query.lower()).strip()

#         # Extract potential location (e.g., delhi, mumbai, pune, etc.)
#         # We'll detect last word as location (heuristic)
#         loc = words[-1] if len(words) > 1 else None

#         # Remaining text as skill or keyword
#         skill = query.replace(loc or '', '').strip() if loc else query

#         return {
#             "exp": exp,
#             "skill": skill.strip(),
#             "loc": loc.strip() if loc else None
#         }

#     def get(self, request):
#         q = request.query_params.get('q')
#         if not q:
#             return Response({"error": "Please provide a search query (?q=python 3 year delhi)."},
#                             status=status.HTTP_400_BAD_REQUEST)

#         parsed = self.parse_query(q)
#         exp = parsed["exp"]
#         skill = parsed["skill"]
#         loc = parsed["loc"]

#         qs = Job.objects.all().annotate(_data_text=Cast('dynamic_job_data', TextField()))

#         # Skill / Keyword search (title, speciality, description)
#         if skill:
#             qs = qs.filter(_data_text__icontains=skill)

#         # Location search (city or state name)
#         if loc:
#             qs = qs.filter(_data_text__icontains=loc)

#         # Experience filter using exp_min / exp_max
#         try:
#             qs = qs.annotate(
#                 exp_min_int=Cast(RawSQL("(dynamic_job_data->'Create Job'->>'exp_min')", ()), IntegerField()),
#                 exp_max_int=Cast(RawSQL("(dynamic_job_data->'Create Job'->>'exp_max')", ()), IntegerField())
#             )

#             if exp:
#                 qs = qs.filter(Q(exp_min_int__lte=exp), Q(exp_max_int__gte=exp))
#         except Exception:
#             pass

#         paginator = StandardResultsSetPagination()
#         page = paginator.paginate_queryset(qs, request)
#         serializer = JobSearchSerializer(page, many=True)

#         return paginator.get_paginated_response({
#             "query_understood_as": parsed,
#             "results": serializer.data
#         })


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'page_size'
                                                                        
# class SmartJobSearchAPIView(APIView):
#     """
#     Smart job search with fuzzy matching for typos like 'dhile' -> 'Delhi'
#     """
#     # permission_classes = [AllowAny]

#     def parse_query(self, query):
#         """Extract skill, experience, and location from query text."""
#         exp_match = re.search(r'(\d+)\s*(year|years|yr|yrs)?', query.lower())
#         exp = int(exp_match.group(1)) if exp_match else None
#         if exp:
#             query = re.sub(r'\d+\s*(year|years|yr|yrs)?', '', query.lower()).strip()

#         words = query.lower().split()
#         loc = words[-1] if len(words) > 1 else None
#         skill = query.replace(loc or '', '').strip() if loc else query
#         return {"exp": exp, "skill": skill.strip(), "loc": loc.strip() if loc else None}

#     def get(self, request):
#         q = request.query_params.get('q')
#         if not q:
#             return Response({"error": "Please provide a query (?q=python 3 year delhi)."},
#                             status=status.HTTP_400_BAD_REQUEST)

#         parsed = self.parse_query(q)
#         exp, skill, loc = parsed["exp"], parsed["skill"], parsed["loc"]

#         qs = Job.objects.all().annotate(_data_text=Cast('dynamic_job_data', TextField()))

#         # 🔹 Fuzzy keyword search for skills and titles
#         if skill:
#             qs = qs.annotate(similarity=_('not used'))
#             qs = qs.filter(similarity__gt=0.2).order_by('-similarity')

#         # 🔹 Fuzzy match for location (city/state)
#         if loc:
#             qs = qs.annotate(loc_similarity=_('not used'))
#             qs = qs.filter(loc_similarity__gt=0.2).order_by('-loc_similarity')

#         # 🔹 Experience filter
#         qs = qs.annotate(
#             exp_min_int=Cast(RawSQL("(dynamic_job_data->'Create Job'->>'exp_min')", ()), IntegerField()),
#             exp_max_int=Cast(RawSQL("(dynamic_job_data->'Create Job'->>'exp_max')", ()), IntegerField())
#         )
#         if exp:
#             qs = qs.filter(Q(exp_min_int__lte=exp), Q(exp_max_int__gte=exp))

#         paginator = StandardResultsSetPagination()
#         page = paginator.paginate_queryset(qs, request)
#         serializer = JobSearchSerializer(page, many=True)

#         return paginator.get_paginated_response({
#             "query_understood_as": parsed,
#             "results": serializer.data
#         })


class SmartJobSearchAPIView(APIView):
    """
    API View for smart job searching with natural language processing capabilities.
    Supports searching by skills, experience, and location with fuzzy matching.
    """
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    # Trigram-free implementation; no extension checks needed

    @lru_cache(maxsize=1)
    def _known_locations(self):
        """Return a lowercase set of known city/state names from jobs."""
        try:
            qs = Job.objects.filter(Q(published=True) | Q(job_status=Job.IN_PROGRESS)).annotate(
                job_city=RawSQL("(dynamic_job_data->'Address Information'->'city'->>'name')", (), output_field=TextField()),
                job_state=RawSQL("(dynamic_job_data->'Address Information'->'state'->>'name')", (), output_field=TextField()),
            ).values_list('job_city', 'job_state')
            locs = set()
            for c, s in qs:
                if c:
                    locs.add(str(c).strip().lower())
                if s:
                    locs.add(str(s).strip().lower())
            return locs
        except Exception:
            return set()

    def parse_query(self, query: str) -> dict:
        """
        Parse the search query to extract skill, experience, and location.
        
        Args:
            query: The raw search query string
            
        Returns:
            dict: Parsed components with keys 'exp', 'skill', 'loc'
        """
        if not query or not isinstance(query, str):
            return {"exp": None, "skill": "", "loc": None}
            
        query = query.strip().lower()
        if not query:
            return {"exp": None, "skill": "", "loc": None}

        # Extract experience
        exp_match = re.search(r'(\d+)\s*(?:year|years|yr|yrs)?\b', query)
        exp = int(exp_match.group(1)) if exp_match else None
        
        # Remove experience from query if found
        if exp_match:
            query = query.replace(exp_match.group(0), '').strip()

        # Handle explicit pattern: "<skill> in <location>"
        loc = None
        in_split = re.split(r"\s+in\s+", query)
        if len(in_split) >= 2:
            # Use the last segment as location, rest joined as skill candidate
            left = " in ".join(in_split[:-1]).strip()
            right = in_split[-1].strip()
            if right:
                loc = right
                query = left

        # Try quoted location first (at end) if not found
        loc_match = re.search(r'"([^"]+)"$', query)
        if loc_match:
            loc = loc_match.group(1).strip()
            # strip the quoted part from query
            query = re.sub(r'\s*"[^"]+"\s*$', '', query).strip()

        # Tokenize remaining words
        tokens = [t for t in re.split(r"\s+", query) if t]
        # Remove common stopwords that are noise in skill (e.g., "in", "at")
        stopwords = {"in", "at", "near", "around", "for", "to", "on", "of", "with", "from"}
        tokens = [t for t in tokens if t not in stopwords]
        # If no quoted location, detect via known locations
        if loc is None and tokens:
            known = self._known_locations()
            # Find the longest token that matches a known location
            # Prefer last token if multiple match
            candidate_loc = None
            for tok in tokens:
                if tok.lower() in known:
                    candidate_loc = tok
            if candidate_loc:
                loc = candidate_loc
                tokens = [t for t in tokens if t != candidate_loc]

        skill = " ".join(tokens).strip()

        return {
            "exp": exp,
            "skill": skill if skill else None,
            "loc": loc if loc and loc != skill else None,
            "title": skill if skill else None
        }

    def get_queryset(self):
        """Base queryset with common annotations."""
        from django.db.models.functions import Coalesce, NullIf
        
        return Job.objects.filter(published=True).annotate(
            job_title=Coalesce(
                NullIf(RawSQL("(dynamic_job_data->'Create Job'->>'title')", ()), Value('')),
                Value(None, output_field=TextField()),
                output_field=TextField()
            ),
            job_speciality=Coalesce(
                NullIf(RawSQL("(dynamic_job_data->'Create Job'->>'speciality')", ()), Value('')),
                Value(None, output_field=TextField()),
                output_field=TextField()
            ),
            job_city=Coalesce(
                NullIf(RawSQL("(dynamic_job_data->'Address Information'->'city'->>'name')", ()), Value('')),
                Value(None, output_field=TextField()),
                output_field=TextField()
            ),
            job_state=Coalesce(
                NullIf(RawSQL("(dynamic_job_data->'Address Information'->'state'->>'name')", ()), Value('')),
                Value(None, output_field=TextField()),
                output_field=TextField()
            ),
            exp_min_int=Cast(
                NullIf(RawSQL("(dynamic_job_data->'Create Job'->>'exp_min')", ()), Value('')),
                IntegerField(null=True)
            ),
            exp_max_int=Cast(
                NullIf(RawSQL("(dynamic_job_data->'Create Job'->>'exp_max')", ()), Value('')),
                IntegerField(null=True)
            )
        )

    def filter_by_skill(self, queryset, skill: str):
        """Filter queryset by keywords (space-separated) across multiple fields with fuzzy ranking."""
        if not skill:
            return queryset

        keywords = [k for k in re.split(r"\s+", skill.strip()) if k]
        if not keywords:
            return queryset

        # Build base filter: at least one keyword appears in any field
        regex = r"(" + "|".join(re.escape(k) for k in keywords) + ")"
        qs = queryset.filter(
            Q(job_title__iregex=regex) |
            Q(job_speciality__iregex=regex) |
            Q(job_city__iregex=regex) |
            Q(job_state__iregex=regex)
        )

        # For ranking: count how many UNIQUE keywords matched (across all fields)
        # Per token, annotate a boolean hit if it appears in ANY of the fields
        per_token_hits = {}
        for idx, token in enumerate(keywords):
            key = f"kw{idx}"
            condition = (
                Q(job_title__icontains=token) |
                Q(job_speciality__icontains=token) |
                Q(job_city__icontains=token) |
                Q(job_state__icontains=token)
            )
            per_token_hits[f"hit_{key}"] = Case(
                When(condition, then=1), default=0, output_field=IntegerField()
            )

        qs = qs.annotate(**per_token_hits)

        # match_count = number of unique keywords matched
        match_count = None
        for name in per_token_hits.keys():
            match_count = (match_count + Sum(name)) if match_count is not None else Sum(name)

        # Optional tie-breaker: total_hits across fields to slightly favor broader presence
        # Count occurrences per field per token (0/1) and sum them
        tie_break_annotations = {}
        for idx, token in enumerate(keywords):
            key = f"kw{idx}"
            tie_break_annotations[f"hit_title_{key}"] = Case(
                When(job_title__icontains=token, then=1), default=0, output_field=IntegerField()
            )
            tie_break_annotations[f"hit_spec_{key}"] = Case(
                When(job_speciality__icontains=token, then=1), default=0, output_field=IntegerField()
            )
            tie_break_annotations[f"hit_city_{key}"] = Case(
                When(job_city__icontains=token, then=1), default=0, output_field=IntegerField()
            )
            tie_break_annotations[f"hit_state_{key}"] = Case(
                When(job_state__icontains=token, then=1), default=0, output_field=IntegerField()
            )

        qs = qs.annotate(**tie_break_annotations)

        total_hits = None
        for name in tie_break_annotations.keys():
            total_hits = (total_hits + Sum(name)) if total_hits is not None else Sum(name)

        if match_count is not None:
            qs = qs.annotate(match_count=match_count)
        if total_hits is not None:
            qs = qs.annotate(total_hits=total_hits)

        # Order by: most keywords matched first, then broader presence
        return qs.order_by('-match_count', '-total_hits')

    def filter_by_location(self, queryset, location: str):
        """Filter queryset by location with fuzzy matching."""
        if not location:
            return queryset
            
        # Trigram-free location filter and ranking
        return queryset.filter(
            Q(job_city__icontains=location) | Q(job_state__icontains=location)
        ).annotate(
            loc_hit=Case(
                When(job_city__icontains=location, then=1), default=0, output_field=IntegerField()
            ) + Case(
                When(job_state__icontains=location, then=1), default=0, output_field=IntegerField()
            )
        ).order_by('-loc_hit')

    def filter_by_experience(self, queryset, exp_years: int):
        """Filter queryset by experience range."""
        if not exp_years or not isinstance(exp_years, int):
            return queryset
            
        return queryset.filter(
            Q(exp_min_int__isnull=True) | Q(exp_min_int__lte=exp_years),
            Q(exp_max_int__isnull=True) | Q(exp_max_int__gte=exp_years)
        )

    def get(self, request):
        """
        Handle GET request for job search.
        
        Query Params:
            q: Search query (e.g., "python developer 3 years delhi")
        """
        try:
            q = (request.query_params.get('search') or request.query_params.get('q') or '').strip()
            if not q:
                # No query provided: return all published jobs
                queryset = self.get_queryset().order_by('-id')
                serializer = JobSearchSerializer(queryset, many=True)
                return Response({
                    "query_understood_as": {"exp": None, "skill": None, "loc": None, "title": None},
                    "results": serializer.data
                })

            # Parse query
            parsed = self.parse_query(q)

            # Build base queryset with annotations
            queryset = self.get_queryset()

            # Build boolean hit annotations without narrowing to intersection
            skill_q = Q()
            if parsed['skill']:
                keywords = [k for k in re.split(r"\s+", parsed['skill'].strip()) if k]
                if keywords:
                    # Skill should match only title/speciality
                    cond = Q()
                    for token in keywords:
                        cond |= (
                            Q(job_title__icontains=token) |
                            Q(job_speciality__icontains=token)
                        )
                    skill_q = cond

            loc_q = Q()
            if parsed['loc']:
                loc_q = Q(job_city__icontains=parsed['loc']) | Q(job_state__icontains=parsed['loc'])

            # Build rank expressions
            skill_rank_expr = Value(0, output_field=IntegerField())
            if parsed['skill'] and 'keywords' in locals() and keywords:
                for token in keywords:
                    skill_rank_expr = skill_rank_expr + (
                        Case(When(job_title__icontains=token, then=1), default=0, output_field=IntegerField()) +
                        Case(When(job_speciality__icontains=token, then=1), default=0, output_field=IntegerField())
                    )

            loc_rank_expr = Value(0, output_field=IntegerField())
            if parsed['loc']:
                location = parsed['loc']
                loc_rank_expr = (
                    Case(When(job_city__icontains=location, then=1), default=0, output_field=IntegerField()) +
                    Case(When(job_state__icontains=location, then=1), default=0, output_field=IntegerField())
                )

            # Annotate hits (avoid empty Q() in When by using Value(0) when absent)
            annotations = {}
            if parsed['skill'] and not skill_q.children == []:
                annotations['skill_hit'] = Case(When(skill_q, then=1), default=0, output_field=IntegerField())
            else:
                annotations['skill_hit'] = Value(0, output_field=IntegerField())

            if parsed['loc'] and not loc_q.children == []:
                annotations['loc_hit'] = Case(When(loc_q, then=1), default=0, output_field=IntegerField())
            else:
                annotations['loc_hit'] = Value(0, output_field=IntegerField())

            queryset = queryset.annotate(**annotations).annotate(
                both_hit=F('skill_hit') * F('loc_hit')
            ).annotate(
                skill_rank=skill_rank_expr,
                loc_rank=loc_rank_expr
            )

            # Experience filter (applied to all tiers)
            try:
                exp_value = parsed.get('exp')
                if exp_value is not None and str(exp_value).strip() and str(exp_value).isdigit():
                    exp_value = int(exp_value)
                    if exp_value >= 0:  # Ensure non-negative experience
                        queryset = self.filter_by_experience(queryset, exp_value)
            except (ValueError, TypeError) as e:
                # Log the error for debugging
                print(f"Error processing experience value: {e}")
                # Skip the experience filter if there's an error

            # Only include rows that match either skill or location (or both)
            if parsed['skill'] and parsed['loc']:
                queryset = queryset.filter(Q(skill_hit__gt=0) | Q(loc_hit__gt=0))
            elif parsed['skill']:
                queryset = queryset.filter(skill_hit__gt=0)
            elif parsed['loc']:
                queryset = queryset.filter(loc_hit__gt=0)

            # Order: both matches first, then stronger title/speciality matches, then location strength
            queryset = queryset.order_by('-both_hit', '-skill_rank', '-loc_rank', '-id')

            # Serialize and return all results
            serializer = JobSearchSerializer(queryset, many=True)
            return Response({
                "query_understood_as": parsed,
                "results": serializer.data
            })
            
        except Exception as e:
            import traceback
            error_detail = str(e)
            # Log the full traceback for debugging
            print(f"Error in SmartJobSearchAPIView: {error_detail}")
            print(traceback.format_exc())
            return Response(
                {"error": "An error occurred while processing your request. Please try again."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Related Jobs API
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class RelatedJobsAPIView(APIView):
    """
    API endpoint to get jobs related to a title by matching any words in the title (case-insensitive, partial match).
    POST {"title": "Python Django Developer", "id": 90}
    Returns: List of serialized jobs found (excluding the job with the provided id).
    """
    def post(self, request):
        title = request.data.get('title', '')
        job_id = request.data.get('id', None)  # Get the job ID to exclude
        
        if not title:
            return Response({'error': 'Title is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Split title by spaces, remove empty, dedupe
        keywords = list(set([k.strip() for k in title.split() if k.strip()]))
        if not keywords:
            return Response({'error': 'No valid keywords from title.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Start with all published jobs, exclude the current job if id is provided
        jobs = Job.objects.filter(published=True, job_status=Job.IN_PROGRESS)
        
        # Exclude the job with the provided id
        if job_id:
            jobs = jobs.exclude(id=job_id)
        
        # Helper function to safely get nested dict data
        def ensure_dict(value):
            return value if isinstance(value, dict) else {}
        
        # Filter jobs based on dynamic_job_data["Create Job"]["title"] containing any keyword
        filtered_jobs = []
        title_lower = title.lower()
        
        for job in jobs:
            dj = job.dynamic_job_data if isinstance(job.dynamic_job_data, dict) else {}
            cj = ensure_dict(dj.get('Create Job'))
            job_title = str(cj.get('title', '')).lower()
            
            # Check if any keyword from the search title appears in the job title
            if any(keyword.lower() in job_title for keyword in keywords):
                filtered_jobs.append(job)
        
        # Serialize the results
        serializer = JobsSerializer(filtered_jobs, many=True)
        return Response({'related_jobs': serializer.data})
    
class test(APIView):
    def get(self,request):
        from .ZwayamJobPost import handle
        handle(311, "12dfdfsfsaf")
        return Response("test")

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Sitemap: https://jobs.edjobster.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")