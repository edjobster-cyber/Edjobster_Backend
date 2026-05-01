from letters.models import LetterSettings
from letters.models import LetterCreditWallet
from settings.models import PlanFeatureCredit
from settings.models import CreditWallet
from settings.models import BilingHistory
from settings.models import PlanPricing,Subscription
from django.contrib.auth.models import make_password

from job.decorators import check_subscription_and_credits, deduct_credit_decorator
from .models import Account, Company, TokenEmailVerification, TokenResetPassword, CareerSiteCompanyDetail, CaptureLead, LeadToken
from .serializer import AccountSerializer, CompanySerializer, MemberSerializer, CareerSiteCompanyDetailSerializer, CandidateSignUpSerializer,CaptureLeadSerializer
from common.mail_utils import EmailVerificationMailer, ResetPasswordMailer
from common.encoder import decode
from common.utils import isValidUuid, getDomainFromEmail
from common.models import City
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
import os
from candidates.models import *
from django.core.mail import send_mail, get_connection
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from .zoho_client import ZohoCRMClient
from .models import ZohoCRMHistory

def checkCompany(request):

    email = request.GET.get('email', None)

    if not email:
        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    if Account.getByEmail(email):
        return {
            'code': 400,
            'msg': 'Email already exists'
        } 

    domain = getDomainFromEmail(email)

    if not domain:
        return {
            'code': 400,
            'msg': 'Invalid email address'
        }

    company = Company.getByDomain(email)

    if company:
        return {
            'code': 200,
            'msg': 'Company is already exists',
            'data': {
                'name': company.name,
                'domain': company.domain,
            }
        }
    return {
        'code': 200,
        'msg': 'New account'
    }

def signupUserAccount(request):

    data = request.data

    firstName = data.get('first_name', None)
    lastName = data.get('last_name', None)
    mobile = data.get('mobile', None)
    email = data.get('email', None)

    if not firstName or not lastName or not mobile or not email:

        return {
            'code': 400,
            'msg': 'invalid request'
        }

    domain = getDomainFromEmail(email)

    if not domain:
        return {
            'code': 400,
            'msg': 'Invalid email address'
        }

    if Account.getByMobile(mobile):
        return {
            'code': 400,
            'msg': 'Mobile already exists'
        }

    if Account.getByEmail(email):
        return {
            'code': 400,
            'msg': 'Email already exists'
        } 

    account = Account()
    account.first_name = firstName
    account.last_name = lastName
    account.mobile = mobile
    account.email = email
    account.role = [Account.USER]
    account.username = email

    account.is_staff = False
    account.is_active = True
    account.is_superuser = False
    account.verified = False
    account.save()       

    token = TokenEmailVerification.createToken(account)
    sendMail = EmailVerificationMailer(token)
    sendMail.start()

    data = {
        'code': 200,
        'msg': 'Account created successfully. We have sent you email to verify your account.',
    }

    return data        

def signUpAccount(request):

    data = request.data
    role = data.get('role', None)
    firstName = data.get('first_name', None)
    lastName = data.get('last_name', None)
    mobile = data.get('mobile', None)
    email = data.get('email', None)
    companyName = data.get('company', None)

    password = data.get('password', None)
    address = data.get('address', None)
    landmark = data.get('landmark', None)

    if not firstName or not lastName or not mobile or not email or not companyName or not address or not landmark:

        return {
            'code': 400,
            'msg': 'invalid request'
        }

    domain = getDomainFromEmail(email)

    if not domain:
        return {
            'code': 400,
            'msg': 'Invalid email address'
        }

    account = None

    if Account.getByMobile(mobile):
        return {
            'code': 400,
            'msg': 'Mobile already exists'
        }

    if Account.getByEmail(email):
        return {
            'code': 400,
            'msg': 'Email already exists'
        }

    account = Account()
    account.first_name = firstName
    account.last_name = lastName
    account.mobile = mobile
    account.email = email
    account.role = [role.upper()]
    account.username = email
    account.set_password(password)
    account.is_staff = False
    account.is_active = True
    account.is_superuser = False
    account.verified = False
    account.save()

    account.company_id = companyName
    account.save()

    token = TokenEmailVerification.createToken(account)
    sendMail = EmailVerificationMailer(token)
    sendMail.start()

    data = {
        'code': 200,
        'msg': 'Account created successfully. We have sent you email to verify your account.',
    }

    return data

def signUpCandidate(request):
    """
    Helper function to create a new candidate account
    
    Args:
        request: Django request object containing candidate data
        
    Returns:
        dict: Response with status code and message
    """
    data = request.data.copy()
    data['role'] = [Account.CANDIDATE]
    data['verified'] = True
    # Ensure username is set to email and not empty
    if not data.get('username'):
        data['username'] = data.get('email', '')  # Use email as username if username not provided
    
    # Check if email already exists
    if Account.objects.filter(email=data.get('email')).exists():
        if Account.objects.filter(email=data.get('email'), role=Account.CANDIDATE).exists():
            return {
                'code': 400,
                'msg': 'Email already exists. Please use a different email or login.'
            }
        else:
            return {
                'code': 400,
                'msg': 'Email already exists for Ats. Please use a different email or login.'
            }
            # Email exists but is for a different role, allow creation
            pass
    
    # Validate input data using serializer
    serializer = CandidateSignUpSerializer(data=data)
    if not serializer.is_valid():
        return {
            'code': 400,
            'msg': 'Invalid data provided',
            'errors': serializer.errors
        }
    
    try:
        # Ensure email is available in data
        if not data.get('email'):
            return {
                'code': 400,
                'msg': 'Email is required'
            }
            
        # Set username to email if not provided
        if not data.get('username'):
            data['username'] = data['email']
            
        # Create the candidate account
        candidate = serializer.save()
        
        # Generate email verification token
        token = TokenEmailVerification.createToken(candidate)
        
        # Send verification email
        email_data = {
            'email_backend': settings.EMAIL_BACKEND,
            'email_host': settings.EMAIL_HOST,
            'email_port': settings.EMAIL_PORT,
            'sender_mail': settings.EMAIL_HOST_USER,
            'auth_password': settings.EMAIL_HOST_PASSWORD,
            'email_ssl': settings.EMAIL_SSL,
            'email_tls': settings.EMAIL_TLS,
        }

        sendMail = EmailVerificationMailer(token, email_data, candidate.email, candidate.password)
        sendMail.start()
        
        return {
            'code': 200,
            'msg': 'Account created successfully',
            'data': {
                'id': str(candidate.account_id),
                'email': candidate.email,
                'name': f"{candidate.first_name} {candidate.last_name}"
            }
        }
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error creating candidate account: {str(e)}")
        return {
            'code': 500,
            'msg': 'An error occurred while creating the candidate account. Please try again.'
        }

def directSignUp(request):
    data = request.data
    company_name = data.get('company_name')
    designation_name = data.get('designation')
    email = data.get('email')
    full_name = data.get('full_name', '')
    password = data.get('password')
    phone = data.get('phone')

    # Basic validation
    if not all([company_name, email, password]):
        return {'code': 400, 'msg': 'Company name, email and password are required'}

    if Account.getByEmail(email):
        return {'code': 400, 'msg': 'Email already exists'}

    # Split full name
    name_parts = full_name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    try:
        # Create Company
        # Note: address is required by model, using a default if not provided
        address = data.get('address', 'Not Provided')
        company = Company.objects.create(
            name=company_name,
            phone=phone or '',
            email=email,
            address=address,
            is_ai_letter_site=True,
            domain=getDomainFromEmail(email)
        )

        # Create Default Designation and Department
        from settings.models import Designation, Department
        dept = Department.objects.create(company=company, name="Admin")
        desig = Designation.objects.create(company=company, name=designation_name or "Manager")

        # Create Account
        account = Account()
        account.first_name = first_name
        account.last_name = last_name
        account.email = email
        account.username = email
        account.mobile = phone
        account.role = [Account.ADMIN]
        account.set_password(password)
        account.company_id = company.id
        account.department = dept.id
        account.designation = desig.id
        account.is_active = True
        account.verified = True
        account.start_trial(14)
        account.save()

        # Link admin to company
        company.admin = account
        company.save()

        return {
            'code': 200,
            'msg': 'Account and Company created successfully',
            'data': {
                'account_id': str(account.account_id),
                'company_id': str(company.id)
            }
        }
    except Exception as e:
        print(f"Error in directSignUp: {str(e)}")
        return {'code': 500, 'msg': 'An error occurred during sign up. Please check if all required fields are provided.'}

from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

def signInAccount(request):

    username = request.data.get('username')
    password = request.data.get('password')
    role = request.data.get('role')
    site = request.data.get('site')
    token = request.data.get('token')
    
    user = None
    
    # Direct JWT token login - if token provided, authenticate directly
    if token:
        # try:
        access_token = AccessToken(token)
        user_id = access_token.get('user_id')
        # print("access_token payload:", access_token.payload)
        # print("user_id:", user_id)
        if user_id:
            user = Account.objects.get(id=user_id)
            print("user:", user)
        # except (TokenError, InvalidToken, Exception) as e:
        #     return {
        #         'code': 400,
        #         'msg': 'Invalid or expired access token'
        #     }
        
        if not user:
            return {
                'code': 400,
                'msg': 'User not found for the provided token'
            }
    else:
        # Normal username/password login
        if not username or not password:
            return {
                'code': 400,
                'msg': 'username and password required'
            }
        user = authenticate(request, username=username, password=password)

        if not user:
            return {
                'code': 400,
                'msg': 'Invalid username and password'
            }
    # print(Account.CANDIDATE in user.role)
    if role:
        if Account.CANDIDATE not in user.role and role == "C":
            return {
                'code': 400,
                'msg': 'Invalid username and password'
            }
    else:
        if Account.CANDIDATE in user.role:
            return {
                'code': 400,
                'msg': 'Invalid username and password'
            }

    if not user.verified:
        token = TokenEmailVerification.createToken(user)
        sendMail = EmailVerificationMailer(token)
        sendMail.start()
        return {
            'code': 403,
            'msg': 'Your account is not verified. Please verify your email address'
        }

    if not user.is_active:
        return {
            'code': 400,
            'msg': 'Your account is not active. Please contact support for more details'
        }

    serialized_account = AccountSerializer(user)

    company = Company.getById(user.company_id)

    serialized_company = CompanySerializer(company)
    first_login = True if (getattr(user, 'last_login', None) is None and Account.TRIALUSER in user.role) else False
    needs_company_details = False
    if not user.is_superuser and company:
        if not company.is_app_site and site == "is_app_site":
            company.is_app_site = True
            company.save()
            try:
                from settings.models import PlanPricing, Subscription, BilingHistory, PlanFeatureCredit, CreditWallet
                free_plan_pricing = PlanPricing.objects.filter(price=0).first()
                
                if free_plan_pricing:
                    # Create subscription for the free plan
                    subscription = Subscription.objects.create(
                        company=company,
                        plan_pricing=free_plan_pricing,
                        is_active=True,
                        end_date=timezone.now() + timezone.timedelta(days=14)  # 14 days for free plan
                    )
                    
                    # Create billing history for the free plan allocation
                    BilingHistory.objects.create(
                        company=company,
                        plan_pricing=free_plan_pricing,
                        feature=None,
                        transaction_type="plan_allocation",
                        price=0,
                        credit=None
                    )
                    
                    # Get all feature credits for the free plan
                    plan_features = PlanFeatureCredit.objects.filter(plan=free_plan_pricing.plan)
                    
                    # Update or create credit wallet entries for each feature
                    for plan_feature in plan_features:
                        if plan_feature:
                            CreditWallet.objects.update_or_create(
                                company=company,
                                feature=plan_feature.feature,
                                defaults={
                                    'total_credit': plan_feature.credit_limit,
                                    'used_credit': 0,
                                    'isdayli': plan_feature.feature.isdayli,
                                    'iscredit': plan_feature.feature.iscredit,
                                    'iswithoutcredit': plan_feature.feature.iswithoutcredit
                                }
                            )
                    
                    # Start trial and update role if it's the first time
                    if Account.TRIALUSER in user.role:
                        user.role = [Account.ADMIN]
                        user.start_trial(14)
                        user.save()
                        
            except Exception as e:
                print(f"Error initializing app site billing: {str(e)}")

        if not company.is_ai_letter_site and (site == "is_ai_letter_site" or site == "ai_letter_site"):
            company.is_ai_letter_site = True
            company.save()
            try:
                from letters.models import LetterCreditWallet
                wallet, created = LetterCreditWallet.objects.get_or_create(
                    company=company,
                    defaults={'total_credits': 10}
                )
                # If logging in for the first time on ai_letter_site and we are a trial user, start trial
                if Account.TRIALUSER in user.role:
                    # For ai_letter_site, we also start the 14 day trial as it's their "first time login"
                    user.start_trial(14)
                    user.save()
            except Exception as e:
                print(f"Error initializing ai letter site billing: {str(e)}")

    if company:
        missing_fields = [
            not bool(company.name),
            not bool(company.website),
            # not bool(company.description),
            not bool(company.address),
            not bool(company.phone),
            not bool(company.email),
            company.city is None,
            company.state is None,
            company.country is None,
        ]
        needs_company_details = any(missing_fields)

    try:
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
    except Exception:
        pass

    refresh = RefreshToken.for_user(user)
    access = AccessToken.for_user(user)

    data = {
        'code': 200,
        'refresh': str(refresh),
        'access': str(access),
        'account': serialized_account.data,
        'company': serialized_company.data,
        'first_login': first_login,
        'needs_company_details': needs_company_details,
        "is_superuser": user.is_superuser,
    }

    return data


def getAccountProfile(request):

    account = request.user

    serialized_account = AccountSerializer(account).data

    print('company', account.company_id)
    company = Company.getById(account.company_id)
    print('company', company)
    serialized_company = CompanySerializer(company)

    data = {
        'code': 200,
        'account': serialized_account,
        'company': serialized_company.data,
    }

    return data

def getCompanyCareerInfo(request):
    
    companies = Company.objects.all()
    serialized_companies = CompanySerializer(companies, many=True, context={'request': request})
    data = {
        'code': 200,
        'companies': serialized_companies.data,
    }
    return data
    

def getCompanyInfo(request):
    
    account = request.user
    role = 'superuser' if account.is_superuser else 'admin' if Account.ADMIN in account.role else 'trialuser' if Account.TRIALUSER in account.role else 'user'

    if account.is_superuser:
        # Fetch all companies if the user is a superuser
        companies = Company.objects.all()
        serialized_companies = CompanySerializer(companies, many=True, context={'request': request})
        data = {
            'code': 200,
            'role': role,
            'companies': serialized_companies.data,
        }
    else:
        # Fetch only the user's company
        company_id = request.GET.get('id', None)
        if company_id is None:
            company_id = account.company_id

        company = Company.getById(company_id)
        serialized_company = CompanySerializer(company, context={'request': request})
        print('company', serialized_company.data)
        data = {
            'code': 200,
            'role': role,
            'companies': serialized_company.data,
        }

    return data

def updateCompanyInfo(request):

    account = request.user

    if not account or (not any(r in [Account.ADMIN, Account.TRIALUSER] for r in account.role) and not account.is_superuser):
        return {
            'code': 400,
            'msg': 'Access denied!'
        }

    data = request.data
    companyId = data.get('companyId', None)
    # print(companyId)
    if not companyId:
        companyId = account.company_id
    
    if not companyId:
        return {
            'code': 400,
            'msg': 'Company ID is required!'
        }
    print('companyId', companyId)
    company = Company.getById(companyId)
    print('company', company)
    if not company:
        return {
            'code': 400,
            'msg': 'Company not found!'
        }
        
    companyName = data.get('company', None)
    website = data.get('website', None)
    description = data.get('description', None)
    pincode = data.get('pincode', None)
    gstNo = data.get('gst_no', None)
    locLat = data.get('loc_lat', None)
    locLon = data.get('loc_lon', None)
    address = data.get('address', None)
    sector =data.get("sector", None)
    landmark = data.get('landmark', None)
    tag = data.get('tag', None)
    cityId = data.get('city_id', None)
    linkedin = data.get('linkedin', None)
    facebook = data.get('facebook', None)
    twitter = data.get('twitter', None)
    instagram = data.get('instagram', None)
    logo = data.get('logo', None)
    banner = data.get('banner',None)

    # if not companyName or not pincode or not address or not landmark or not cityId or not website or not description:
    if not companyName or not address:
        return {
            'code': 400,
            'msg': 'invalid request'
        }

    account = None

    # mCity = City.getById(cityId)

    # if not mCity:
    #     return {
    #         'code': 400,
    #         'msg': 'City not found'
    #     }

    # mState = mCity.state
    # mCountry = mState.country

    if tag:
        company.tag = tag
    
    company.name = companyName
    company.website = website
    company.description = description
    company.pincode = pincode
    company.gst_no = gstNo
    company.loc_lat = locLat
    company.loc_lon = locLon
    company.address = address
    company.sector = sector
    company.landmark = landmark
    # company.state = mState
    # company.country = mCountry
    # company.city = mCity
    company.linkedin = linkedin
    company.facebook = facebook
    company.twitter = twitter
    company.instagram = instagram
    if hasattr(logo, 'file'):  # Check if it's an InMemoryUploadedFile or TemporaryUploadedFile
        company.logo = logo

    if hasattr(banner, 'file'):  # Check if it's an InMemoryUploadedFile or TemporaryUploadedFile
        company.banner = banner
        
    company.save()

    companyData = CompanySerializer(company)
    return {
        'code': 200,
        'company': companyData.data,
    }
    
def getPerticularCompanyInfo(request):
    company_id = request.GET.get('id', None)
    company = Company.getById(company_id)
    serialized_company = CompanySerializer(company, context={'request': request})
    
    data = {
        'code': 200,
        'companies': serialized_company.data,
    }

    return data

def addCompany(request):
    data = request.data
    # admin = data.get('admin', None)

    # if not admin:
    #     return {
    #         'code': 400,
    #         'msg': 'invalid request'
    #     }

    # admin = Account.getById(account_id=admin)
    
    # if not admin:
    #     return {
    #         'code': 400,
    #         'msg': 'invalid User'
    #     }

    companyName = data.get('company', None)
    website = data.get('website', None)
    description = data.get('description', None)
    pincode = data.get('pincode', None)
    gstNo = data.get('gst_no', None)
    locLat = data.get('loc_lat', None)
    locLon = data.get('loc_lon', None)
    address = data.get('address', None)
    landmark = data.get('landmark', None)
    tag = data.get('tag', None)
    cityId = data.get('city', None)
    domain = data.get('domain', None)
    phone = data.get('phone', None)
    email = data.get('email', None)
    
    # existing_company = Company.objects.filter(admin_id=admin).first()

    # if existing_company:
    #     # Return information about the existing company
    #     return {
    #         'code': 400,
    #         'msg': 'Company with this user Exists'
    #     }
    # print('info', companyName, pincode, address, landmark, cityId)

    if not companyName or not pincode or not address or not landmark or not cityId or not website or not description or not email:

        return {
            'code': 400,
            'msg': 'invalid request'
        }


    mCity = City.getById(cityId)

    if not mCity:
        return {
            'code': 400,
            'msg': 'City not found'
        }

    mState = mCity.state
    mCountry = mState.country

    company = Company()

    if tag:
        company.tag = [tag]
    
    # company.admin = admin
    company.name = companyName
    company.website = website
    company.description = description
    company.pincode = pincode
    company.gst_no = gstNo
    company.loc_lat = locLat
    company.loc_lon = locLon
    company.address = address
    company.landmark = landmark
    company.state = mState
    company.country = mCountry
    company.city = mCity
    company.domain = domain
    company.phone = phone
    company.email = email
    logo = request.FILES['logo']
    if logo:
        company.logo = logo
    company.save()
    

    companyData = CompanySerializer(company)

    return {
        'code': 200,
        'company': companyData.data,
    }

def updateAccount(request):

    account = request.user

    data = request.data

    first_name = data.get('first_name', None)
    last_name = data.get('last_name', None)
    mobile = data.get('mobile', None)
    email = data.get('email', None)

    if not first_name or not last_name or not email or not mobile:

        return{
            'code': 404,
            'msg': 'Invalid Request !!!'
        }

    account.first_name = first_name
    account.last_name = last_name

    if mobile:
        new_account = Account.getByMobile(mobile)

        if new_account:
            if new_account.id != account.id:
                return{
                    'code': 404,
                    'msg': 'Mobile Number Already Exist !!! '
                }

    new_account = Account.getByEmail(email)
    if new_account:
        if account.id != new_account.id:
            return {
                'code': 400,
                'msg': 'Email Already Exist !!! '
            }

    account.email = email
    account.username = email
    account.mobile = mobile
    account.save()

    return{
        'code': 200,
        'account': {
            'first_name': account.first_name,
            'last_name': account.last_name,
            'email': account.email,
            'mobile': account.mobile,
        }
    }


def updateMobile(request):

    data = request.data

    account = request.user

    mobile = data.get('mobile', None)

    if not mobile:
        return{
            'code': 400,
            'msg': ' Access denied'
        }

    if not account:

        return{
            'code': 404,
            'msg': 'Account not found !!! '
        }

    new_account = Account.getByMobile(mobile)

    if new_account:

        if new_account.id != account.id:

            return{
                'code': 404,
                'msg': 'Ooppsss , Mobile Number Already Exist !!! '
            }

    account.username = mobile

    account.save()

    return{
        'code': 200,
        'msg': 'Mobile number is succesfully Updated'
    }

def updateLogo(request):

    account = request.user

    if Account.ADMIN not in account.role:
        return {
            'code': 400,
            'msg': 'Access Denied!'
        }

    company = Company.getById(account.company_id)

    if not company:
        return {
            'code': 400,
            'msg': 'Company doest exists!'
        }

    logo = request.FILES.get('logo')
    if logo:

        try:
            if company.logo != None:
                if os.path.isfile(company.logo.path):
                    os.remove(company.logo.path)
        except Exception:
            pass
        company.logo = logo
        company.save()

        return {
            'code': 200,
            'msg': 'Logo updated successfully'
        }
    else:
        company.logo=logo
        company.save()
        return {
            'code': 200,
            'msg': 'Logo Remove successfully'
        }
    return {
        'code': 400,
        'msg': 'Bad request'
    }


def checkMobile(request):

    data = request.data

    account = request.user

    mobile = data.get('mobile', None)
    exists = data.get('exists', False)

    if not mobile:
        return{
            'code': 400,
            'msg': ' Access denied'
        }

    new_account = Account.getByMobile(mobile)

    msg = ''
    code = 0
    if new_account:
        if exists:
            code = 200
        else:
            code = 400

        msg = 'Mobile already exist'
    else:
        if exists:
            code = 400
        else:
            code = 200

        msg = 'Account not exists'

    return {
        'code': code,
        'msg': msg
    }


def checkEmail(request):

    data = request.data

    account = request.user

    email = data.get('email', None)

    if not email:
        return{
            'code': 400,
            'msg': ' Access denied'
        }

    new_account = Account.getByEmail(email)

    if new_account:
        return {
            'code': 400,
            'msg': 'Email Already Exist !!!'
        }

    return {
        'code': 200,
        'msg': 'Email not registerd'

    }


def resetPassword(request):

    account = request.user
    data = request.data
    token = data.get('token', None)
    password = data.get('password', None)

    if not token or not password:

        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    try:
        tokenId = decode(token)
    except:
        return {
            'code': 400,
            'msg': 'Bad request'
        }


    if not isValidUuid(tokenId):
        return {
            'code': 400,
            'msg': 'Bad request'
        }

    token = TokenResetPassword.getByTokenId(tokenId)

    if not token:
        return {
            'code': 400,
            'msg': 'Bad request'
        }

    account = token.user
    account.set_password(password)
    account.save()
    token.delete()

    return{
        'code': 200,
        'msg': 'New password Set succesfully',
    }


def changePassword(request):

    account = request.user
    data = request.data

    old_password = data.get('old_password', None)
    new_password = data.get('new_password', None)

    if not old_password or not new_password:

        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    if not account.check_password(old_password):

        return {
            "code": 400,
            "msg": "Old password doesnt match"
        }

    account.set_password(new_password)

    account.save()

    return{
        'code': 200,
        'msg': 'New password Set succesfully',
    }


def forgotPasswordAccount(request):
    data = request.data

    email = data.get('email', None)
    role = data.get("role",None)
    if not email:

        return {
            'code': 400,
            'msg': 'Invalid request'
        }

    account = Account.getByEmail(email)
    print(account)
    if not account:
        return {
            'code': 400,
            'msg': 'Account not found !!!'
        }
        
    # If role is not provided, use the account's role
    if not role:
        if Account.CANDIDATE in account.role:
            role = "C"
        else:
            role = "E"  # Default to employer role if not specified and not a candidate
    
    # Validate role access
    if Account.CANDIDATE not in account.role and role == "C":
        return {
            'code': 400,
            'msg': 'This account is not available on this platform for employer access'
        }
    
    mailer = ResetPasswordMailer(TokenResetPassword.createToken(account), role)
    
    mailer.start()
    return {
        'code': 200,
        'msg': 'We have sent you email to reset password.'
    }
    
    
def listMembrs(request):
    account = request.user
    if account.is_superuser:
        members = Account.objects.all()
    else:
        if Account.ADMIN in account.role or account.is_trial:
            members = Account.objects.filter(company_id=account.company_id)
        else:
            members = Account.objects.none()

    accountSerializer = AccountSerializer(members, many=True)

    return {
        'code': 200,
        'list': accountSerializer.data
    }


def list_capture_leads(request):
    """
    List all captured leads with pagination and filtering
    
    Query Parameters:
    - page: Page number (default: 1)
    - limit: Number of items per page (default: 10)
    - status: Filter by status (optional)
    - search: Search by name or email (optional)
    
    Returns:
    - List of captured leads with pagination info
    """
    data = CaptureLead.objects.exclude(
        email__in=Account.objects.values_list('email', flat=True)
    )
    

    # data = CaptureLead.objects.all()

    # Apply search filter if provided
    # search_query = request.GET.get('search', '').strip()
    # if search_query:
    #     data = data.filter(
    #         Q(fullname__icontains=search_query) | 
    #         Q(email__icontains=search_query) |
    #         Q(company__icontains=search_query)
    #     )
    
    # # Apply status filter if provided
    # status_filter = request.GET.get('status')
    # if status_filter:
    #     data = data.filter(status=status_filter)

    # Serialize the data
    serializer = CaptureLeadSerializer(data, many=True)
    
    return serializer.data 
        


def list_trial_users(request):
    now = timezone.now()
    users = Account.objects.filter(is_trial=True)
    data = []
    for u in users:
        remaining_days = 0
        active = False
        if u.trial_end:
            delta = u.trial_end - now
            # Calculate full days remaining (floor, not negative)
            remaining_days = max(0, delta.days)
            active = delta.total_seconds() > 0
        data.append({
            'account_id': str(u.account_id) if hasattr(u, 'account_id') else None,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'email': u.email,
            'company_id': str(u.company_id) if u.company_id else None,
            'trial_start': u.trial_start,
            'trial_end': u.trial_end,
            'is_trial': u.is_trial,
            'trial_active': active,
            'remaining_days': remaining_days,
        })
    return {
        'code': 200,
        'list': data
    }

def get_trial_user_reminder(request, account_id=None):
    """
    Get trial user reminder information.
    If account_id is provided, returns details for that specific user.
    If no account_id, returns all trial users with reminder info.
    """
    now = timezone.now()
    
    # If specific account_id is provided
    if account_id:
        try:
            user = Account.objects.get(account_id=account_id, is_trial=True)
        except Account.DoesNotExist:
            return {
                'code': 404,
                'msg': 'Trial user not found'
            }
            
        remaining_days = 0
        active = False
        if user.trial_end:
            delta = user.trial_end - now
            remaining_days = max(0, delta.days)
            active = delta.total_seconds() > 0
            
            # Determine reminder status
            reminder_status = {
                'seven_days': remaining_days <= 7,
                'three_days': remaining_days <= 3,
                'one_day': remaining_days <= 1,
                'expired': not active
            }
        
        return {
            'code': 200,
            'data': {
                'account_id': str(user.account_id),
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'company_id': str(user.company_id) if user.company_id else None,
                'trial_start': user.trial_start,
                'trial_end': user.trial_end,
                'is_trial': user.is_trial,
                'trial_active': active,
                'remaining_days': remaining_days,
                'reminder_status': reminder_status
            }
        }
    
    # If no account_id provided, return all trial users
    users = Account.objects.filter(is_trial=True)
    result = []
    
    for user in users:
        remaining_days = 0
        active = False
        if user.trial_end:
            delta = user.trial_end - now
            remaining_days = max(0, delta.days)
            active = delta.total_seconds() > 0
            
            reminder_status = {
                'seven_days': remaining_days <= 7,
                'three_days': remaining_days <= 3,
                'one_day': remaining_days <= 1,
                'expired': not active
            }
            
        result.append({
            'account_id': str(user.account_id) if hasattr(user, 'account_id') else None,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'company_id': str(user.company_id) if user.company_id else None,
            'trial_start': user.trial_start,
            'trial_end': user.trial_end,
            'is_trial': user.is_trial,
            'trial_active': active,
            'remaining_days': remaining_days,
            'reminder_status': reminder_status
        })
    
    return {
        'code': 200,
        'data': result
    }

def create_capture_lead(request):
    data = request.data
    company = data.get('company', None)
    fullname = data.get('fullname', None)
    email = data.get('email', None)
    phone = data.get('phone', None)
    designation = data.get('designation', None)
    platform = data.get('platform', None)
    source = data.get('source', None)

    if not fullname or not email or not phone:
        return {
            'code': 400,
            'msg': 'invalid request'
        }

    # Check if email already exists in accounts or captured leads
    if Account.objects.filter(email__iexact=email).exists() or CaptureLead.objects.filter(email__iexact=email).exists():
        return {
            'code': 400,
            'msg': 'email allready exist try another mail'
        }

    lead = CaptureLead()
    lead.company = company
    lead.fullname = fullname
    lead.email = email
    lead.phone = phone
    lead.designation = designation
    lead.save()
    
    # print("Lead fields:", lead.__dict__)

    # Send data to Zoho CRM
    try:
        zoho_client = ZohoCRMClient()
        
        # Split full name into first and last names
        full_name = fullname.strip().split(' ', 1)
        first_name = full_name[0] if full_name else ''
        last_name = full_name[1] if len(full_name) > 1 else first_name
        
        # Prepare lead data for Zoho CRM
        lead_data = {
            'First_Name': first_name,
            'Last_Name': last_name,
            'Email': email,
            'Phone': phone,
            'Company': company or '',
            'Lead_Source': source,
            'Lead_Type': platform,
            'Designation': designation or '',
            'Trial_Status': str(lead.is_trial),
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
                        lead=lead,  # Link to CaptureLead instead of ContactDetails
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
    
    LeadToken.objects.filter(lead__email=email).delete()
    token_obj = LeadToken.create_for_lead(lead)
    base_url = request.build_absolute_uri('/account/lead/verify/')
    # link = base_url + f"?token={token_obj.token}"
    if source == 'ai_letter_site':
        app_url = (getattr(settings, 'AI_LETTER_SITE_URL', os.environ.get('AI_LETTER_SITE_URL')))
        link = f"{app_url}/signin?iscreatepassword=true&token={token_obj.token}"
    else:
        app_url = (getattr(settings, 'APP_URL', os.environ.get('APP_URL')))
        link = f"{app_url}/login?iscreatepassword=true&token={token_obj.token}"

    # Prepare and send email in proper HTML format
    subject = "Complete Your Registration - Verify Your Email"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
    # Fallback to a generic from if settings not configured
    if not from_email:
        from_email = 'no-reply@edjobster.com'

    # Prepare context for the email template
    context = {
        # User information
        'fullname': fullname if fullname else 'there',
        'user_email': email,
        'company_name': getattr(lead, 'company', None),
        'designation': getattr(lead, 'designation', None),
        'img': 'https://api.edjobster.com/media/edjobster09.png',
        
        # Links
        'verification_link': link,
        'help_center_url': getattr(settings, 'HELP_CENTER_URL', 'https://edjobster.com/help'),
        'privacy_policy_url': getattr(settings, 'PRIVACY_POLICY_URL', 'https://edjobster.com/privacy'),
        'terms_url': getattr(settings, 'TERMS_URL', 'https://edjobster.com/terms'),
        
        # Support
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@edjobster.com'),
        
        # Social media links
        'social_links': {
            'linkedin': getattr(settings, 'LINKEDIN_URL', 'https://linkedin.com/company/edjobster'),
            'twitter': getattr(settings, 'TWITTER_URL', 'https://twitter.com/edjobster'),
            'facebook': getattr(settings, 'FACEBOOK_URL', 'https://facebook.com/edjobster'),
            'instagram': getattr(settings, 'INSTAGRAM_URL', 'https://instagram.com/edjobster'),
            'youtube': getattr(settings, 'YOUTUBE_URL', 'https://youtube.com/edjobster'),
        },
        
        # Metadata
        'current_year': timezone.now().year,
    }
    print(link,"link")
    msg_html = render_to_string("edjobster_signup_email.html", context)
    
    send_mail(
        subject=subject,
        message="Lead verification",
        from_email=from_email,
        recipient_list=[email],
        html_message=msg_html,
        fail_silently=False,
    )

    return {
        'code': 200,
        'data': {
            'lead_id': lead.id if hasattr(lead, 'id') else None,
            'token': token_obj.token,
            'link': link,
            'email_sent': True
        }
    }

def verify_lead_token(request):
    token = request.GET.get('token', None) or request.data.get('token', None)
    if not token:
        return {
            'code': 400,
            'msg': 'Bad request'
        }

    try:
        lt = LeadToken.objects.get(token=token)
    except LeadToken.DoesNotExist:
        return {
            'code': 404,
            'msg': 'Invalid link or you new email send plase chake'
        }

    if lt.is_expired():
        return {
            'code': 400,
            'msg': 'Link expired'
        }

    lead = lt.lead
    return {
        'code': 200,
        'data': {
            'lead': {
                'company': lead.company,
                'fullname': lead.fullname,
                'email': lead.email,
                'phone': lead.phone,
                'designation': lead.designation,
            },
            'valid': True
        }
    }

def _send_verification_email(lead, token):
    """Helper function to send verification email to lead"""
    try:
        # Get app URL and construct verification link
        app_url = getattr(settings, 'APP_URL', os.environ.get('APP_URL', 'https://edjobster.com'))
        link = f"{app_url.rstrip('/')}/login?iscreatepassword=true&token={token}"
        
        # Email configuration
        subject = "Complete Your Registration - Verify Your Email"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', 'no-reply@edjobster.com')
        
        if not from_email:
            error_msg = "Email configuration error: No DEFAULT_FROM_EMAIL or EMAIL_HOST_USER set"
            logger.error(error_msg)
            return False, error_msg
        
        # Prepare context for the email template
        context = {
            'fullname': getattr(lead, 'fullname', 'User'),
            'user_email': getattr(lead, 'email', ''),
            'company_name': getattr(lead, 'company', ''),
            'designation': getattr(lead, 'designation', ''),
            'img': f'{app_url.rstrip("/")}/static/account/images/edjobster09.png',
            'verification_link': link,
            'help_center_url': getattr(settings, 'HELP_CENTER_URL', 'https://edjobster.com/help'),
            'privacy_policy_url': getattr(settings, 'PRIVACY_POLICY_URL', 'https://edjobster.com/privacy'),
            'terms_url': getattr(settings, 'TERMS_URL', 'https://edjobster.com/terms'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@edjobster.com'),
            'social_links': {
                'linkedin': getattr(settings, 'LINKEDIN_URL', 'https://linkedin.com/company/edjobster'),
                'twitter': getattr(settings, 'TWITTER_URL', 'https://twitter.com/edjobster'),
                'facebook': getattr(settings, 'FACEBOOK_URL', 'https://facebook.com/edjobster'),
                'instagram': getattr(settings, 'INSTAGRAM_URL', 'https://instagram.com/edjobster'),
                'youtube': getattr(settings, 'YOUTUBE_URL', 'https://youtube.com/edjobster'),
            },
            'current_year': timezone.now().year,
        }
        
        # Render email template
        try:
            msg_html = render_to_string("edjobster_signup_email.html", context)
        except TemplateDoesNotExist as e:
            error_msg = f"Email template not found: {str(e)}"
            return False, error_msg
        # Send email
        try:
            send_mail(
                subject=subject,
                message=f"Please use this link to complete your registration: {link}",
                from_email=from_email,
                recipient_list=[getattr(lead, 'email', '')] if getattr(lead, 'email', '') else [],
                html_message=msg_html,
                fail_silently=False,
            )
            return True, None
            
        except Exception as e:
            error_msg = f"Failed to send email to {lead.email}. Error: {str(e)}"
            print(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Unexpected error in _send_verification_email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def lead_token_regenerate(request):
    # Get token from either GET or POST data
    token = request.GET.get('token') or (request.data.get('token') if hasattr(request, 'data') else None)
    id = request.GET.get('id') or (request.data.get('id') if hasattr(request, 'data') else None)
    if not id:
        if not token:
            return {"msg":"Token is required"}, 400
    if token:
        try:
            token_obj = LeadToken.objects.select_related('lead').get(token=token)
        except LeadToken.DoesNotExist:
            return {"msg":"Invalid or expired token"}, 404
        # If token is expired, generate a new one
        if token_obj.is_expired():
            if not token_obj.lead:
                return {"msg": "No lead associated with this token"},  400
                
            new_token = LeadToken.create_for_lead(token_obj.lead)
            
            # Delete the old token after successful creation of new one
            token_obj.delete()
            
            # Send verification email with the new token
            success, error_msg = _send_verification_email(token_obj.lead, new_token.token)
            
            if not success:
                return {"msg":"Failed to send verification email. Please try again later."}, 500
                
            return {"msg": "A new verification link has been sent to your email.", "status": 201}, 201
    elif id:
        try:
            token_obj = LeadToken.objects.get(lead=id)
        except LeadToken.DoesNotExist:
            return {"msg":"Invalid or expired token"}, 404
        # If token is expired, generate a new one
        if token_obj:
            if not token_obj.lead:
                return {"msg": "No lead associated with this token"},  400
                
            new_token = LeadToken.create_for_lead(token_obj.lead)
            
            # Delete the old token after successful creation of new one
            token_obj.delete()
            
            # Send verification email with the new token
            success, error_msg = _send_verification_email(token_obj.lead, new_token.token)
            if not success:
                return {"msg":"Failed to send verification email. Please try again later."}, 500
                
            return {"msg": "A new verification link has been sent to your email.", "status": 201}, 201
    # Token is still valid
    return  {"msg":"Token is still valid", "status":200}, 200

def create_trial_user_from_lead(request):
    data = request.data
    token = data.get('token')
    fullname = data.get('fullname')
    password = data.get('password')
    company_name = data.get('company')
    email_override = data.get('email')
    phone_override = data.get('phone')
    source = data.get('source')

    if not token or not fullname or not password or not company_name:
        return {
            'code': 400,
            'msg': 'fullname, password, company and token are required'
        }

    # Split fullname into first and last name (first token as first_name, rest as last_name)
    name_parts = fullname.strip().split(None, 1)
    first_name = name_parts[0] if len(name_parts) > 0 else ''
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    try:
        lt = LeadToken.objects.get(token=token)
    except LeadToken.DoesNotExist:
        return {
            'code': 400,
            'msg': 'Invalid link'
        }

    if lt.is_expired():
        return {
            'code': 400,
            'msg': 'Link expired'
        }

    lead = lt.lead
    email = email_override or lead.email
    phone = phone_override or lead.phone

    if not email:
        return {
            'code': 400,
            'msg': 'Email is required'
        }

    if Account.getByEmail(email):
        return {
            'code': 400,
            'msg': 'Account with this email already exists'
        }

    # Create minimal company honoring model constraints
    domain = getDomainFromEmail(email)
    if not domain:
        # Fallback domain from company name
        safe = (company_name or 'company').lower().replace(' ', '')
        domain = f"{safe}.com"

    company = Company()
    company.name = company_name
    company.domain = domain
    company.phone = phone or 'N/A'
    company.email = email
    company.address = 'N/A'
    if source:
        company.source = source
        if source == 'ai_letter_site':
            company.is_ai_letter_site =True
        else:
            company.is_app_site =True
    company.save()

    # Create trial user
    account = Account()
    account.first_name = first_name
    account.last_name = last_name
    account.mobile = phone
    account.email = email
    account.username = email
    account.role = [Account.TRIALUSER]
    account.set_password(password)
    account.is_staff = False
    account.is_active = True
    account.is_superuser = False
    account.verified = True
    account.company_id = company.id
    # Start 14-day trial
    try:
        account.start_trial(14)
    except Exception:
        # Fallback if method unavailable for any reason
        pass
    account.save()

    # Attach admin to company
    company.admin = account
    company.save()

    # Update the lead to mark it as a trial
    lead.is_trial = True
    lead.save()
    
    LetterSettings.objects.create(
        company=company,
        signatory_name=fullname,
        signatory_title="Admin",
        signatory_email=email,
        signatory_phone=phone,

        show_company_logo=True,
        show_company_name=True,
        show_release_date=True,
        show_address=True,
        show_contact_details=True,

    )

    # Check for free plans and create subscription if found
    try:
        from settings.models import PlanPricing, Subscription, BilingHistory, PlanFeatureCredit, CreditWallet
        from django.utils import timezone
        from decimal import Decimal
        
        if source != 'ai_letter_site':
            # Find any plan with price == 0
            free_plan_pricing = PlanPricing.objects.filter(price=0).first()
            
            if free_plan_pricing:
                # Create subscription for the free plan
                subscription = Subscription.objects.create(
                    company=company,
                    plan_pricing=free_plan_pricing,
                    is_active=True,
                    end_date=timezone.now() + timezone.timedelta(days=14)  # 14 days for free plan
                )
                
                # Create billing history for the free plan allocation
                BilingHistory.objects.create(
                    company=company,
                    plan_pricing=free_plan_pricing,
                    feature=None,
                    transaction_type="plan_allocation",
                    price=0,
                    credit=None
                )
                
                # Get all feature credits for the free plan
                plan_features = PlanFeatureCredit.objects.filter(plan=free_plan_pricing.plan)
                
                # Update or create credit wallet entries for each feature
                for plan_feature in plan_features:
                    if plan_feature:
                        CreditWallet.objects.update_or_create(
                            company=company,
                            feature=plan_feature.feature,
                            defaults={
                                'total_credit': plan_feature.credit_limit,
                                'used_credit': 0,
                                'isdayli': plan_feature.feature.isdayli,
                                'iscredit': plan_feature.feature.iscredit,
                                'iswithoutcredit': plan_feature.feature.iswithoutcredit
                            }
                        )
                
                # Update user role from TRIALUSER to ADMIN since they now have a subscription
                account.role = [Account.ADMIN]
                account.save()
        else:
            # AI Letter Site specific billing initialization
            from letters.models import LetterCreditWallet
            LetterCreditWallet.objects.get_or_create(
                company=company,
                defaults={'total_credits': 10}
            )
            
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error initializing billing: {str(e)}")
    
    try:
        # Find the Zoho CRM record for this lead
        zoho_history = ZohoCRMHistory.objects.filter(lead=lead).first()
        if zoho_history and zoho_history.zohocrmid:
            zoho_client = ZohoCRMClient()
            
            # Prepare the update data
            update_data = {
                'Trial_Status': str(lead.is_trial),
                'Trial_Start_Date': str(account.trial_start.strftime('%Y-%m-%d')) if account.trial_start else '',
                'Trial_Expiry_Date': str(account.trial_end.strftime('%Y-%m-%d')) if account.trial_end else ''
            }
            # update_data = {
            #     'Trial_Status': 'True',
            #     'Trial_Start_Date': '2025-11-18',
            #     'Trial_Expiry_Date': '2025-11-25'
            # }
            
            # Update the lead in Zoho CRM
            zoho_client.update_lead(zoho_history.zohocrmid, update_data)
            # print("Updated Zoho CRM lead", zoho_client.update_lead(zoho_history.zohocrmid, update_data))
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error updating Zoho CRM lead: {str(e)}")
    
    # Invalidate token
    lt.delete()

    return {
        'code': 200,
        'msg': 'Trial user and company created successfully',
        'data': {
            'account_id': str(account.account_id) if hasattr(account, 'account_id') else None,
            'email': account.email,
            'role': account.role,
            'company_id': str(company.id),
            'company_name': company.name
        }
    }

@check_subscription_and_credits(feature_code = "company_user")
@deduct_credit_decorator(feature_code="company_user")
def addMember(self, request):

    # Convert role to list if it's a string
    if 'role' in request.data and isinstance(request.data['role'], str):
        request.data['role'] = [request.data['role']]

    serializers = MemberSerializer(data=request.data)

    if serializers.is_valid():
        
        plain_password = request.data.get('password')
        user = serializers.save()
        # Send verification email using helper function
            
        if 'A' in user.role:
            company_id = request.data.get('company_id')
            if company_id:
                try:
                    company = Company.objects.get(id=company_id)
                    company.admin = user
                    company.save()
                except Company.DoesNotExist:
                    return Response(
                        {"message": "Company not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )
        email_result = send_verification_email(request, user, plain_password)

        if email_result['code'] == 403:
            return {"message": email_result['message']}, status.HTTP_403_FORBIDDEN

        return {
                "message": "User created successfully. " + email_result['message'],
                "user_id": user.account_id
            }, status.HTTP_201_CREATED

    return serializers.errors, status.HTTP_400_BAD_REQUEST


def updateMember(request):

    adminUser = request.user

    data = request.data

    print('updateMember', data)

    first_name = data.get('first_name', None)
    last_name = data.get('last_name', None)
    mobile = data.get('mobile', None)
    email = data.get('email', None)
    role = data.get('role', None)

    department = data.get('department', None)
    designation = data.get('designation', None)

    accountId = data.get('account_id', None)

    if not first_name or not last_name or not email or not accountId or role not in [Account.ADMIN, Account.USER] or not department or not designation:
        return{
            'code': 404,
            'msg': 'Invalid Request !!!'
        }

    if adminUser.role != Account.ADMIN:
        return {
            'code': 400,
            'msg': 'Only admin can add members'
        }

    account = Account.getById(accountId)
    if not account:
        return {
            'code': 400,
            'msg': 'Member not found'
        }

    account.first_name = first_name
    account.last_name = last_name

    if mobile:
        new_account = Account.getByMobile(mobile)

        if new_account:
            if new_account.id != account.id:
                return{
                    'code': 404,
                    'msg': 'Mobile Number Already Exist !!! '
                }

    new_account = Account.getByEmail(email)
    if new_account:
        if account.id != new_account.id:
            return {
                'code': 400,
                'msg': 'Email Already Exist !!! '
            }

    account.email = email
    account.username = email
    account.mobile = mobile
    account.role = role
    account.department = department
    account.designation = designation
    photo = None

    if request.FILES != None:
        if photo in request.FILES:
            photo = request.FILES['photo']
            try:
                if updateAccount.photo != None:
                    if os.path.isfile(updateAccount.photo.path):
                        os.remove(updateAccount.photo.path)
            except Exception:
                pass
            updateAccount.photo = photo

    account.save()

    return{
        'code': 200,
        'msg': 'Member details updated sucessfully!'
    }

def updatePhoto(request):

    account = request.user

    if request.FILES != None and 'photo' in request.FILES :
        photo = request.FILES['photo']
        if photo:
            try:
                if account.photo != None:
                    if os.path.isfile(account.photo.path):
                        os.remove(account.photo.path)
            except Exception:
                pass
            account.photo = photo
            account.save()

            return {
                'code': 200,
                'msg': 'Photo updated successfully'
            }

    return {
        'code': 400,
        'msg': 'Profile photo required'
    }

def updateMemberPhoto(request):

    adminUser = request.user

    if Account.ADMIN not in adminUser.role:
        return {
            'code': 400,
            'msg': 'access denied!'
        }

    accountId = request.data.get('account_id', None)
    if not accountId:
        return {
            'code': 400,
            'msg': 'Bad request!'
        }
    account = Account.getById(accountId)
    if not account:
        return {
            'code': 400,
            'msg': 'Member not found'
        }

    if request.FILES != None and 'photo' in request.FILES :
        photo = request.FILES['photo']
        if photo:
            try:
                if account.photo != None:
                    if os.path.isfile(account.photo.path):
                        os.remove(account.photo.path)
            except Exception:
                pass
            account.photo = photo
            account.save()

            return {
                'code': 200,
                'msg': 'Photo updated successfully'
            }

    return {
        'code': 400,
        'msg': 'Profile photo required'
    }    

def updateMemberRole(request):
    
    adminUser = request.user
    data = request.data
    print('activate >> ', data)

    role = data.get('role', None)
    accountId = data.get('account_id', None)

    if adminUser.role != Account.ADMIN:
        return {
            'code': 400,
            'msg': 'Only admin can add members'
        }

    print('activate >> ', adminUser.account_id, accountId)

    if not role or not accountId or role not in Account.ROLE_LIST:
        return {
            'code': 400,
            'msg': 'Bad request!'
        }

    account = Account.getById(accountId)
    if not account:
        return {
            'code': 400,
            'msg': 'Member not found'
        }

    print('activate >> ', adminUser, account)

    if adminUser == account:
        return {
            'code': 400,
            'msg': 'Cannot change role of yourself'
        }
    
    account.role = role

    return {
        'code': 200,
        'msg': 'Role updated successfully'
    }
    
def companyMembers(request):
    account = request.user
    if account.is_superuser:
        members = Account.objects.all()
    else:
        if Account.ADMIN in account.role:
            members = Account.objects.filter(company_id=account.company_id).exclude(id=account.id)
        else:
            members = Account.objects.none()

    accountSerializer = AccountSerializer(members, many=True)

    return {
        'code': 200,
        'list': accountSerializer.data
    }

def activateMember(request):

    adminUser = request.user
    data = request.data
    print('activate >> ', data)

    status = data.get('status', None)
    accountId = data.get('account_id', None)

    if Account.ADMIN not in adminUser.role:
        return {
            'code': 400,
            'msg': 'Only admin can activate members'
        }

    print('activate >> ', adminUser.account_id, accountId)

    if not status or not accountId:
        return {
            'code': 400,
            'msg': 'Bad request!'
        }

    account = Account.getById(accountId)
    if not account:
        return {
            'code': 400,
            'msg': 'Member not found'
        }

    print('activate >> ', adminUser, account)

    if adminUser == account:
        return {
            'code': 400,
            'msg': 'Cannot deactivate account of yourself'
        }

    if status not in ['A', 'D']:
        return {
            'code': 400,
            'msg': 'Invalid status'
        }

    msg = ''
    if status == 'A':
        msg = 'Account activated successfully!'
        account.is_active = True
    else:
        msg = 'Account deactivated successfully!'
        account.is_active = False

    account.save()

    return {
        'code': 200,
        'msg': msg
    }

def approveMember(request):

    adminUser = request.user
    data = request.data
    print('approveMember >> ', data)

    status = data.get('status', None)
    accountId = data.get('account_id', None)

    if Account.ADMIN not in adminUser.role:
        return {
            'code': 400,
            'msg': 'Only admin can approve members'
        }

    print('activate >> ', adminUser.account_id, accountId)

    if not status or not accountId:
        return {
            'code': 400,
            'msg': 'Bad request!'
        }

    account = Account.getById(accountId)
    if not account:
        return {
            'code': 400,
            'msg': 'Member not found'
        }

    print('activate >> ', adminUser, account)

    if adminUser == account:
        return {
            'code': 400,
            'msg': 'Cannot deactivate account of yourself'
        }

    if status not in ['A', 'D']:
        return {
            'code': 400,
            'msg': 'Invalid status'
        }

    msg = ''
    if status == 'A':
        msg = 'Account activated successfully!'
        account.verified = True
    else:
        msg = 'Account deactivated successfully!'
        account.verified = False

    account.save()

    return {
        'code': 200,
        'msg': msg
    }    


def deleteMember(request):
    adminUser = request.user
    account_id = request.GET.get('account_id', None)

    if Account.ADMIN not in adminUser.role:
        return {
            'code': 400,
            'msg': 'Only admin can delete members'
        }

    if not account_id:
        return {
            'code': 400,
            'msg': 'Bad request!'
        }

    if adminUser.account_id == account_id:
        return {
            'code': 400,
            'msg': 'Cannot delete account of yourself'
        }
    company = Company.getByUser(adminUser)
    account = Account.getByIdAndCompany(account_id, company)
    if not account:
        return {
            'code': 400,
            'msg': 'Member not found'
        }

    if account.company_id != adminUser.company_id:
        return {
            'code': 400,
            'msg': 'Access denied!'
        }

    account.delete()

    return {
        'code': 200,
        'msg': 'Member deleted successfully!'
    }


def activateAccount(request):

    tokenId = request.data.get('token')
    # password = request.data.get('password')

    print('token', tokenId)
    if not tokenId:
        return {
            'code': 400,
            'msg': 'Bad request'
        }

    try:
        tokenId = decode(tokenId)
    except:
        return {
            'code': 400,
            'msg': 'Bad request'
        }
    if not isValidUuid(tokenId):
        return {
            'code': 400,
            'msg': 'Bad request'
        }

    token = TokenEmailVerification.getByTokenId(tokenId)
    print("token", token)

    if not token:
        return {
            'code': 403,
            'msg': 'Account is already verified'
        }

    if token.user:
        user = token.user
        user.verified = True
        # user.set_password(password)
        user.save()
        token.delete()

        return {
            'code': 200,
            'msg': 'Your account has been successfully created, but it is not active yet. The admin of your institute needs to approve and activate your account. You can come back later to check or you can reach out to the admin to approve and activate your account'
        }

    return {
        'code': 400,
        'msg': 'Bad request!!'
    }


def verifyToken(request):
    tokenId = request.GET.get('token', None)

    print('token', tokenId)
    if tokenId:
        tokenId = decode(tokenId)

    if not isValidUuid(tokenId):
        return {
            'code': 400,
            'msg': 'Bad request'
        }

    token = TokenEmailVerification.getByTokenId(tokenId)
    print("token", token)

    if not token:
        return {
            'code': 400,
            'msg': 'Bad request!'
        }

    if token.user:
        user = token.user

        return {
            'code': 200,
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            }
        }

    return {
        'code': 400,
        'msg': 'Bad request!!'
    }


def activateEmail(tokenId):
    return TokenEmailVerification.getByTokenId(decode(tokenId))


def approveVerifyMember(request):

    adminUser = request.user
    data = request.data
    print('approving and Verifying >> ', data)

    status = data.get('status', None)
    accountId = data.get('account_id', None)

    if Account.ADMIN not in adminUser.role:
        return {
            'code': 400,
            'msg': 'Only admin can approve/verify members'
        }

    print('activate >> ', adminUser.account_id, accountId)

    if not status or not accountId:
        return {
            'code': 400,
            'msg': 'Bad request!'
        }

    account = Account.getById(accountId)
    if not account:
        return {
            'code': 400,
            'msg': 'Member not found'
        }

    print('activate >> ', adminUser, account)

    if adminUser == account:
        return {
            'code': 400,
            'msg': 'Cannot deactivate account of yourself'
        }

    if status not in ['A', 'D']:
        return {
            'code': 400,
            'msg': 'Invalid status'
        }

    msg = ''
    if status == 'A':
        msg = 'Account activated successfully!'
        account.approved = True
        account.verified = True
    else:
        msg = 'Account deactivated successfully!'
        account.approved = False
        account.verified = False

    account.save()

    return {
        'code': 200,
        'msg': msg
    } 
    
def send_verification_email(request, user, plain_password):
    email_user = request.user
    # If requester is superuser, use default SMTP from settings (no per-user EmailSettings)
    if getattr(email_user, 'is_superuser', False):
        email_data = None
    else:
        # Retrieve email settings for the user
        email_data = EmailSettings.objects.filter(user_id=email_user.pk).order_by('-created_at').first()
        if email_data is None:
            return {
                'code': 403,
                'message': 'EmailSmtp for the user does not exist.',
            }

    # Create a token for email verification
    token = TokenEmailVerification.createToken(user)

    # Send verification email using per-user settings if available, otherwise fallback to defaults
    sendMail = EmailVerificationMailer(token, email_data, user.email, plain_password)
    sendMail.start()

    return {
        'code': 200,
        'message': 'Verification email sent successfully.',
    }   
    
    
def getCompany(request):    
    user=request.user
    if user.is_superuser:
        company=Company.objects.all()
        serializer = CompanySerializer(company, many=True)
        data = serializer.data
        return {
            'code': 200,
            'allcompanies': data
        }
    else:
        company=Company.getByUser(user)
        serializer = CompanySerializer(company)
        data = serializer.data
        return {
            'code': 200,
            'company': data
        }

def getAllCompany(request, company_id=None):
    if company_id:
        # Fetch a specific company by ID
        company = Company.objects.filter(id=company_id).first()

        if not company:
            return {
                'code': 404,
                'msg': f'Company with ID {company_id} not found'
            }

        serializer = CompanySerializer(company, context={'request': request})
        data = serializer.data
        return {
            'code': 200,
            'company': data
        }
    else:
        # Fetch all companies
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True, context={'request': request})
        data = serializer.data
        return {
            'code': 200,
            'companies': data
        }


def getAllCompanyCareer(request, company_id=None):
    from job.models import Job
    if company_id:
        # Fetch a specific company by ID
        company = Company.objects.filter(id=company_id).first()

        if not company:
            return {
                'code': 404,
                'msg': f'Company with ID {company_id} not found'
            }

        serializer = CompanySerializer(company, context={'request': request})
        data = serializer.data
        # Add jobs_count without serializer change
        data['jobs_count'] = Job.objects.filter(company=company).count()
        return {
            'code': 200,
            'company': data
        }
    else:
        # Fetch companies with available jobs
        companies_with_jobs = Company.objects.filter(job__isnull=False).distinct()
        # companies_with_jobs=Company.objects.all()
        serializer = CompanySerializer(companies_with_jobs, many=True, context={'request': request})
        data = serializer.data
        # Add jobs_count to each company without modifying serializer
        for c, company_obj in zip(data, companies_with_jobs):
            c['jobs_count'] = Job.objects.filter(company=company_obj).count()
        return {
            'code': 200,
            'companies': data
        }
        
def getCareersiteCompanyDetailInfo(request):
    company_id = request.GET.get('id', None)
    if not company_id:
        return {
            'code': 400,
            'msg': 'Company ID is required'
        }

    try:
        company = Company.getById(company_id)
        company_data = CareerSiteCompanyDetail.objects.get_or_create(company=company)
    except CareerSiteCompanyDetail.DoesNotExist:
        return {
            'code': 404,
            'msg': 'Company data not found'
        }
    
    serialized_company = CareerSiteCompanyDetailSerializer(company_data, context={'request': request})
    data = {
        'code': 200,
        'companies_details': serialized_company.data,
    }
    return data

def createCareersiteCompanyDetail(data):
    serializer = CareerSiteCompanyDetailSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return serializer.data, None
    return None, serializer.errors

def updateCareersiteCompanyDetailInfo(request):
        company_id = request.GET.get('id', None)

        if not company_id:
            return {
                'code': 400, 
                'msg': 'Company ID is required'
            }

        try:
            company_data = CareerSiteCompanyDetail.objects.get(company_id=company_id)
        except CareerSiteCompanyDetail.DoesNotExist:
            return {
                'code': 404, 
                'msg': 'Company data not found'
            }
        serializer = CareerSiteCompanyDetailSerializer(company_data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return {
                'code': 200, 
                'msg': 'Company details updated successfully', 
                'data': serializer.data
            }
        return {
            'code': 400, 
            'msg': 'Invalid data', 
            'errors': serializer.errors
        }