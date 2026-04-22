from pstats import Stats
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView

from job.decorators import check_subscription_and_credits, deduct_credit_decorator
from .import helper
from common.utils import makeResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from account import serializer
from account.models import *
from .zoho_client import ZohoCRMClient

class AccountSignUpApi(APIView):

    def post(self, request):
        data = helper.signUpAccount(request)
        return makeResponse(data)

class DirectSignUpApi(APIView):
    def post(self, request):
        data = helper.directSignUp(request)
        return Response(data)

class CandidateSignUpApi(APIView):
    def post(self, request):
        data = helper.signUpCandidate(request)
        return Response(data)

class CreateCaptureLeadApi(APIView):
    def post(self, request):
        data = helper.create_capture_lead(request)
        return makeResponse(data)
    
class LeadVerifyApi(APIView):
    def get(self, request):
        data = helper.verify_lead_token(request)
        return makeResponse(data)
    
    def post(self, request):
        data, status = helper.lead_token_regenerate(request)
        return Response(data, status=status)

class CreateTrialUserFromLeadApi(APIView):
    def post(self, request):
        data = helper.create_trial_user_from_lead(request)
        return makeResponse(data)

class CaptureLeadsListApi(APIView):
    def get(self, request):
        data = helper.list_capture_leads(request)
        return Response(data)

class TrialUsersListApi(APIView):
    def get(self, request):
        data = helper.list_trial_users(request)
        return makeResponse(data)

class TrialUserReminderApi(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, account_id=None):
        """
        Get trial user reminder information
        
        Parameters:
        - account_id (optional): UUID of the trial user. If not provided, returns all trial users.
        
        Returns:
        - For single user (with account_id):
            {
                'account_id': str,
                'first_name': str,
                'last_name': str,
                'email': str,
                'company_id': str or None,
                'trial_start': datetime,
                'trial_end': datetime,
                'is_trial': bool,
                'trial_active': bool,
                'remaining_days': int,
                'reminder_status': {
                    'seven_days': bool,  # True if 7 or fewer days remaining
                    'three_days': bool,  # True if 3 or fewer days remaining
                    'one_day': bool,     # True if 1 or fewer days remaining
                    'expired': bool      # True if trial has expired
                }
            }
            
        - For all users (without account_id):
            [
                {same as single user object above},
                ...
            ]
        """
        account_id = request.user.account_id
        data = helper.get_trial_user_reminder(request, account_id)
        return makeResponse(data)

class ProfileApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        data = helper.getAccountProfile(request)

        return makeResponse(data)

    def put(self, request):
        data = helper.updateAccount(request)
        return makeResponse(data)


class AccountSignInApi(APIView):

    def post(self, request):
        data = helper.signInAccount(request)
        return makeResponse(data)


class ForgotPasswordApi(APIView):

    def post(self, request):
        data = helper.forgotPasswordAccount(request)
        return makeResponse(data)


class UpdateAccountApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.updateAccount(request)
        return makeResponse(data)


class UpdatePhotoApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.updatePhoto(request)
        return makeResponse(data)

class UpdateMemberPhotoApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.updateMemberPhoto(request)
        return makeResponse(data)

class UpdateMemberRoleApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.updateMemberRole(request)
        return makeResponse(data)

class UpdateLogoApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.updateLogo(request)
        return makeResponse(data)


class CompanyInfoApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getCompanyInfo(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.updateCompanyInfo(request)
        return makeResponse(data)
    
class CompanyInfoCareerApi(APIView):

    def get(self, request):
        data = helper.getCompanyCareerInfo(request)
        return makeResponse(data)


class MobileApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        data = helper.updateMobile(request)
        return makeResponse(data)


class CheckMobileApi(APIView):

    def post(self, request):
        data = helper.checkMobile(request)
        return makeResponse(data)


class CheckEmailApi(APIView):

    def post(self, request):
        data = helper.checkEmail(request)
        return makeResponse(data)


class CheckTokenApi(APIView):

    def post(self, request):
        data = helper.checkEmail(request)
        return makeResponse(data)


class ActvateAccountApi(APIView):

    def post(self, request):
        data = helper.activateAccount(request)
        return makeResponse(data)

class ApproveAccountApi(APIView):

    def post(self, request):
        data = helper.approveMember(request)
        return makeResponse(data)

class VerifyTokenApi(APIView):

    def get(self, request):
        data = helper.verifyToken(request)
        return makeResponse(data)


class ResetPasswordApi(APIView):

    def post(self, request):
        data = helper.resetPassword(request)
        return makeResponse(data)


class ChangePasswordApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.changePassword(request)
        return makeResponse(data)


class MembersApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.listMembrs(request)
        return makeResponse(data)
    
    def post(self, request, *args, **kwargs):
        data, status = helper.addMember(request)
        return Response(data,status=status)

    def delete(self, request):
        data = helper.deleteMember(request)
        return makeResponse(data)

class UpdateMemberApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.updateMember(request)
        return makeResponse(data)

class PhotoUpdateApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.updatePhoto(request)
        return makeResponse(data)

class ActivateMemberApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.activateMember(request)
        return makeResponse(data)


class DeleteMemberApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = helper.deleteMember(request)
        return makeResponse(data)
    
class CompanyMembersApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.companyMembers(request)
        return makeResponse(data)

# class ApproveUser(APIView):
#     authentication_classes = [JWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         data = helper.approveVerifyMember(request)
#         return makeResponse(data)

class GetCompany(APIView):
    
    def get(self, request):
        # company_id = request.query_params.get('id', None)
        data = helper.getCompany(request)
        return makeResponse(data)

class GetAllCompany(APIView):
    
    def get(self, request):
        company_id = request.query_params.get('id', None)
        data = helper.getAllCompany(request, company_id)
        return makeResponse(data)
    
class GetAllCompanyCarrer(APIView):
    
    def get(self, request):
        company_id = request.query_params.get('id', None)
        data = helper.getAllCompanyCareer(request, company_id)
        return makeResponse(data)

    
class AddCompany(APIView):
    
    def get(self, request):
        data = helper.getPerticularCompanyInfo(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.addCompany(request)
        return makeResponse(data)
    
class CareersiteCompanyDetailsApi(APIView):
    
    def get(self, request):
        data = helper.getCareersiteCompanyDetailInfo(request)
        return makeResponse(data)
    
    def post(self, request):
        data, errors = helper.createCareersiteCompanyDetail(request.data)
        if errors:
            return makeResponse({'code': 400, 'msg': errors})
        return makeResponse({'code': 200, 'data': data})
         
    def put(self, request):
        data = helper.updateCareersiteCompanyDetailInfo(request)
        return makeResponse(data)
    
class ZohoSyncView(APIView):
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        module = request.data.get('module', 'Leads')

        # Build Zoho records from Account users
        # accounts = Account.objects.filter(is_superuser=False).order_by('id')

        records = []
        for acc in accounts:
            # Resolve company name if available
            company_name = None
            if acc.company_id:
                company = Company.getById(acc.company_id)
                if company:
                    company_name = company.name

            last_name = acc.last_name or acc.first_name or 'Unknown'

            record = {
                "Last_Name": last_name,
                "First_Name": acc.first_name or "",
                "Email": acc.email or "",
                "Phone": acc.mobile or "",
                "Company": company_name or "",
                "Lead_Source": "Edjobster Account",
            }

            # Zoho Leads require at least Last_Name; we also skip empty emails if you want
            records.append(record)

        if not records:
            return Response({'detail': 'No account records to sync'}, status=status.HTTP_200_OK)

        client = ZohoCRMClient()
        try:
            result = client.bulk_create(module, records)
        except Exception as exc:
            return Response({'detail': 'Failed to sync with Zoho', 'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result, status=status.HTTP_201_CREATED)


class ZohoSyncAPiView(APIView):
    def get(self, request):
        
        synced_lead_ids = ZohoCRMHistory.objects.exclude(
            lead__isnull=True
        ).values_list('lead_id', flat=True)

        unsynced_capture_leads = CaptureLead.objects.exclude(
            id__in=synced_lead_ids
        )

        for data in unsynced_capture_leads:
            print(data.fullname)
            try:
                zoho_client = ZohoCRMClient()
                
                # Split full name into first and last names
                full_name = data.fullname.strip().split(' ', 1)
                first_name = full_name[0] if full_name else ''
                last_name = full_name[1] if len(full_name) > 1 else first_name
                
                # Prepare lead data for Zoho CRM
                lead_data = {
                    'First_Name': first_name,
                    'Last_Name': last_name,
                    'Email': data.email,
                    'Phone': data.phone,
                    'Company': data.company or '',
                    'Lead_Source': 'Website',
                    'Lead_Type': 'Event',  # Changed to 'Event' as requested
                    'Designation': data.designation or '',
                    'Trial_Status': str(data.is_trial),
                }
                
                # Remove empty values
                # lead_data = {k: v for k, v in lead_data.items() if v}
                lead_data = {k: v for k, v in lead_data.items() if v or k == 'Trial_Status'}
                
                # Send to Zoho CRM
                zoho_response = zoho_client.create_lead(lead_data)
                
                # print("Zoho response........:", zoho_response)
                
                # If successful, save to ZohoCRMHistory
                if zoho_response and 'data' in zoho_response and len(zoho_response['data']) > 0:
                    zoho_lead_id = None
                    try:
                        # Extract ID from the response structure
                        zoho_lead_id = zoho_response['data'][0].get('details', {}).get('id')
                        if zoho_lead_id:
                            ZohoCRMHistory.objects.create(
                                lead=data,  # Link to CaptureLead instead of ContactDetails
                                zohocrmid=zoho_lead_id,
                                leadtype='Event'  # Set leadtype to 'Event'
                            )
                    except (AttributeError, KeyError, IndexError) as e:
                        print(f"Error extracting Zoho CRM ID from response: {str(e)}")
            
            except Exception as e:
                # Log the error but don't fail the request
                print(f"Error sending data to Zoho CRM: {str(e)}")
                # You might want to log this to your error tracking system
            # logger.error(f"Zoho CRM sync failed for lead {email}: {str(e)}")
        return Response("ok")