from django.shortcuts import get_object_or_404
from .models import ContactDetails
from .serializer import ContactDetailsSerializer, ScheduleCallSerializer
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from account.zoho_client import ZohoCRMClient
from account.models import ZohoCRMHistory

def getContactDetails(self, request):
    data = ContactDetails.objects.all()
    serializer = ContactDetailsSerializer(data, many=True)
    return Response(serializer.data)
    
def saveContactDetails(self, request):
    data = request.data
    try:
        email=get_object_or_404(ContactDetails,email=data["email"])
        if email:
            return Response({"message":"You have already registered"})
    except:
        pass
    serializer = ContactDetailsSerializer(data=data)
    if serializer.is_valid():
        contact = serializer.save()

        # Send data to Zoho CRM
        try:
            zoho_client = ZohoCRMClient()
            
            # Split full name into first and last names
            full_name = data.get('full_name', '').strip().split(' ', 1)
            first_name = full_name[0] if full_name else ''
            last_name = full_name[1] if len(full_name) > 1 else first_name
            
            # Prepare lead data for Zoho CRM
            lead_data = {
                'First_Name': first_name,
                'Last_Name': last_name,
                'Email': data.get('email'),
                'Phone': data.get('mobile_number', ''),
                'Company': data.get('company_name', ''),
                'Lead_Source': data.get('platform',''),
                'Lead_Type': 'Contact Us',
                'Description': data.get('message', ''),
                'State': data.get('state', ''),
                'School_Institution_Name': data.get('institution_name', ''),
                'Designation': data.get('designation', '')
            }
            
            # Remove empty values
            lead_data = {k: v for k, v in lead_data.items() if v}
            
            # Send to Zoho CRM
            zoho_response = zoho_client.create_lead(lead_data)
            print("zoho_response1",zoho_response and 'data' in zoho_response and len(zoho_response['data']) > 0)
            
            # If successful, save to ZohoCRMHistory
            if zoho_response and 'data' in zoho_response and len(zoho_response['data']) > 0:
                zoho_lead_id = None
                print("zoho_response2",zoho_response)
                try:
                    # Extract ID from the response structure
                    zoho_lead_id = zoho_response['data'][0].get('details', {}).get('id')
                    if zoho_lead_id:
                        ZohoCRMHistory.objects.create(
                            contactus=contact,
                            zohocrmid=zoho_lead_id,
                            leadtype='Contact Us'
                        )
                except (AttributeError, KeyError, IndexError) as e:
                    print(f"Error extracting Zoho CRM ID from response: {str(e)}")
            
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error sending data to Zoho CRM: {str(e)}")
            # You might want to log this to your error tracking system
            # logger.error(f"Zoho CRM sync failed for contact {data.get('email')}: {str(e)}")

        return Response({"message":"Your message has been received. We will update you shortly."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def getScheduleCall(self, request):
    data = ScheduleCall.objects.all()
    serializer = ScheduleCallSerializer(data, many=True)
    return Response(serializer.data)

def saveScheduleCall(self, request):
    data = request.data
    serializer = ScheduleCallSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    