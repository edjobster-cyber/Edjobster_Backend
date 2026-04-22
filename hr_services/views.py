from rest_framework.views import APIView
from . import helper
from rest_framework.response import Response

# Create your views here.
class ContactDetailsView(APIView):
    def get(self, request):
        data = helper.getContactDetails(self, request)
        return data

    def post(self, request):
        data = helper.saveContactDetails(self, request)
        return data 

class ScheduleCallView(APIView):
    def get(self, request):
        data = helper.getScheduleCall(self, request)
        return data
    
    def post(self, request):
        data = helper.saveScheduleCall(self, request)
        return data