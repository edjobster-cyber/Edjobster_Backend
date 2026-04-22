from django.shortcuts import render
import os
from django.shortcuts import render, redirect
from django.contrib import messages, auth
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .import helper
from .utils import makeResponse
from django.conf import settings


class DataApi(APIView):
    def get(self, request):
        data = helper.getAllData()
        return makeResponse(data)
    

class CountryApi(APIView):
    def get(self, request):
        data = helper.getCountries(request)
        return makeResponse(data)


class StatesApi(APIView):
    def get(self, request):
        data = helper.getStatesForCountry(request)
        return makeResponse(data)


class CitiesApi(APIView):
    def get(self, request):
        data = helper.getCitiesForState(request)
        return makeResponse(data)

class NotesApi(APIView):
    def get(self, request):
        data = helper.getNoteTypes(request)
        return makeResponse(data)

class CompanyTagsApi(APIView):
    def get(self, request):
        data = helper.getCompanyTags(request)
        return makeResponse(data)

class SendMailApi(APIView):
    def post(self, request):
        data = helper.sendCandidateMail(request)
        return makeResponse(data)  

class ReturnXMLApi(APIView):
    def get(self, request):
        data = helper.returnXML(request)
        return data

class UnsubscribeEmailTemplateApi(APIView):
    def get(self, request, token):
        unsubscribe_link = f'{settings.API_URL}/settings/unsubscribe-email-token/{token}/'
        if token:
            return render(request, 'unsubscribe_email_template.html', {'unsubscribe_link': unsubscribe_link})

class CombinedTimelineAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
            timeline_data = helper.get_combined_timeline(request)
            return Response(timeline_data)
            
       