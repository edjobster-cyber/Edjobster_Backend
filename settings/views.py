from pandas.io.clipboard import is_available
from settings.models import BillingCycle
import email.header
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.utils.text import slugify
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from job.decorators import check_subscription_and_credits, deduct_credit_decorator
from .import helper
from .models import (BilingHistory, CreditWallet, EmailTemplate, FeatureUsage, PlanFeatureCredit, PlanPricing, QRModel, Testimonials, Plan, Payment, Subscription, 
    RazorpaySettings, ShortLink, LinkdingCompanyid, CandidateEvaluationCriteria, JobBoardList, JobBoard, Feature, AddonPlan, CreditHistory)
from .serializer import (AddonPlanSerializer, EmailTemplateSerializer, FeatureSerializer, TestimonialsSerializer, PaymentSerializer, 
    SubscriptionSerializer, ShortLinkSerializer, QRModelSerializer, LinkdingCompanyidSerializer,
    CandidateEvaluationCriteriaSerializer, JobBoardListSerializer, JobBoardSerializer, CreditWalletSerializer, PlanFeatureCreditSerializer, CreditHistorySerializer, BilingHistorySerializer)
from common.utils import makeResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.core.exceptions import ImproperlyConfigured
from candidates.models import *

class LocationsApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getLocations(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveLocation(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteLocation(request)
        return makeResponse(data)    
    
class LocationsCareerApi(APIView):

    def get(self, request, pk=None):
        data = helper.getLocationsCareer(pk)
        return makeResponse(data)    

from rest_framework import mixins, generics
from .models import Location
from .serializer import LocationSerializer

class LocationsDetailApi(mixins.RetrieveModelMixin, generics.GenericAPIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Location.objects.all()
    serializer_class = LocationSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class DepartmentApi(APIView):

    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getDepartments(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveDepartment(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteDepartment(request)
        return makeResponse(data)                

class DesignationApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getDesignations(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveDesignation(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteDecignation(request)
        return makeResponse(data)             

class DegreeApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getDegrees(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveDegree(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteDegree(request)
        return makeResponse(data)                     

class PipelineDetails(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getPipelineStageDetails(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.savePipelineStatus(request)
        return makeResponse(data)

class PipelineStageApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getPipelineStages(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.savePipelineStage(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deletePipelineStage(request)
        return makeResponse(data)             

class PipelinesApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getPipelines(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.savePipeline(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deletePipeline(request)
        return makeResponse(data)                     

from rest_framework import mixins, generics
from .models import Pipeline, PipelineStage
from .serializer import PipelineSerializer, PipelineStageSerializer

class PipelinesDetailApi(mixins.RetrieveModelMixin, generics.GenericAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    lookup_field = 'id'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)  

class PipelineStageUpdate(
    mixins.RetrieveModelMixin,
    generics.UpdateAPIView
    ):
    queryset = PipelineStage.objects.all()
    serializer_class = PipelineStageSerializer
    lookup_field = "id"

    def perform_update(self, serializer):
        instance = serializer.save()


class PipelineStageDelete(mixins.RetrieveModelMixin,generics.DestroyAPIView):
    # queryset = PipelineStage.objects.all()
    # serializer_class = PipelineStageSerializer
    # lookup_field = "id"
      def delete(self,request):
           return helper.deletePipelineStage(request=request)
    # def perform_destroy(self, instance):
    #     super().perform_destroy(instance)

class PipelinesDetailCompanyApi(mixins.RetrieveModelMixin, generics.GenericAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    lookup_field = 'company'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)  

class JobAssociatePipelineStagesApi(APIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        data = helper.getJobAssociatedPipelineStages(request)
        return makeResponse(data)

class EmailFieldApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getEmailFileds(request)
        return makeResponse(data)

class EmailCategoryApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getEmailCategories(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveEmailCategory(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteEmailCategory(request)
        return makeResponse(data)   

class EmailTemplateApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getEmailTemplates(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveEmailTemplate(request)
        return makeResponse(data)

    def put(self, request):
        data = helper.UpdateEmailTemplate(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteEmailTemmplate(request)
        return makeResponse(data)           

class EmailTemplateDetailApi(mixins.RetrieveModelMixin, generics.GenericAPIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    
class ModuleTypesApi(APIView):

    def get(self, request):
        data = helper.getModulesTypes(request)
        return makeResponse(data)
    
class ModuleApi(APIView):

    def get(self, request):
        data = helper.getModules(request)
        return makeResponse(data)
    
    @check_subscription_and_credits('Custom_Fields')
    @deduct_credit_decorator('Custom_Fields')
    def post(self,self_or_request, request):
        data = helper.saveModule(request)
        return Response(data)

    def put(self,request):
        data , status = helper.saveModule(request)
        return Response(data,status)

    def delete(self, request):
        data = helper.deleteModule(request)
        return makeResponse(data) 
    
class ModuleCompanyApi(APIView):
    
    def get(self,request):
        data =helper.getModuleCompany(request)
        return Response(data)

class WebformApi(APIView):

    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getWebforms(request)
        return makeResponse(data)

    def post(self, request, *args, **kwargs):
        result = helper.saveWebForms(request)
        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            return Response(data, status=status_code)
        return Response(result, status=status.HTTP_200_OK)
    
    def put(self, request):
        result = helper.UpdateWebForms(request)
        if isinstance(result, tuple) and len(result) == 2:
            data, status_code = result
            return Response(data, status=status_code)
        return Response(result, status=status.HTTP_200_OK)
    def delete(self, request):
        data = helper.deleteWebforms(request)
        return makeResponse(data)                   

class WebformFieldsApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getWebformFields(request)
        return makeResponse(data)        

class ModuleTypesJobApi(APIView):

    def get(self,request):
        data = helper.getModulesTypesJob(request)
        return makeResponse(data)

class ContactsApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getContacts(request)
        return makeResponse(data)

    def post(self, request):
        data = helper.saveContacts(request)
        return makeResponse(data)

    def delete(self, request):
        data = helper.deleteContacts(request)
        return makeResponse(data)
    
    def update(self,request):
        data = helper.updateContacts(request)
        return makeResponse(data)
    
class TestimonialsRUDView(generics.RetrieveUpdateDestroyAPIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Testimonials.objects.all()
    serializer_class = TestimonialsSerializer


class TestimonialsCView(generics.ListCreateAPIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Testimonials.objects.all()
    serializer_class = TestimonialsSerializer

class TemplateVariablesApi(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getTemplateVariables(request)
        return makeResponse(data)
    
    def put(self, request):
        data = helper.saveTemplateVariables(request)
        return makeResponse(data)
    
# @api_view(['POST'])
# def create_order(request):
#     plan_id = request.data.get('plan_id')
#     plan = Plan.objects.get(id=plan_id)
#     if plan.offer:
#         try:
#             offer_percentage = Decimal(plan.offer)
#             discounted_price = plan.price * (1 - offer_percentage / Decimal(100))
#             offer_price = discounted_price * Decimal('1.18')
#             offer_price = int(offer_price) + Decimal('0.99')
#         except ValueError:
#             offer_price = plan.price  # Fallback to plan.price if offer is invalid
#             offer_price = int(offer_price) + Decimal('0.99')
#     else:
#         offer_price = plan.price  # Fallback to plan.price if no offer
#         offer_price = int(offer_price) + Decimal('0.99')
        

#     amount = float(offer_price * 100)
    
#     # Determine Razorpay mode from Django settings (default to 'test')
#     RAZORPAY_MODE = getattr(settings, 'RAZORPAY_MODE', 'test')
    
#     try:
#         if RAZORPAY_MODE == 'live':
#             RAZORPAY_KEY_ID = settings.RAZORPAY_LIVE_MODE_KEY_ID
#             RAZORPAY_KEY_SECRET = settings.RAZORPAY_LIVE_MODE_KEY_SECRET
#         else:
#             RAZORPAY_KEY_ID = settings.RAZORPAY_TEST_MODE_KEY_ID
#             RAZORPAY_KEY_SECRET = settings.RAZORPAY_TEST_MODE_KEY_SECRET
#     except ImproperlyConfigured as e:
#         raise ImproperlyConfigured(f"Environment variable error: {e}")
    
#     client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

#     payment = client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})

#     payment_obj = Payment(
#         razorpay_order_id=payment['id'],
#         amount=amount / 100  # Convert to rupees
#     )
#     payment_obj.save()

#     serializer = PaymentSerializer(payment_obj)

#     data = {
#         'payment': serializer.data,
#         'razorpay_key_id': RAZORPAY_KEY_ID,
#     }
#     return Response(data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def create_order(request):
    """
    Create payment order for either plan or addon purchase
    Payload types:
    1. Plan purchase: {"payment_type": "plan", "plan_id": 1, "billing_cycle": 1}
    2. Addon purchase: {"payment_type": "addon", "addon_id": 1}
    """
    payment_type = request.data.get('payment_type', 'plan')
    
    if payment_type == 'plan':
        plan_id = request.data.get('plan_id')
        billing_cycle_id = request.data.get('billing_cycle')
        
        if not plan_id or not billing_cycle_id:
            return Response(
                {'error': 'Both plan_id and billing_cycle are required for plan purchase'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            plan_pricing = PlanPricing.objects.select_related('plan', 'billing_cycle').get(
                plan_id=plan_id,
                billing_cycle_id=billing_cycle_id
            )
        except PlanPricing.DoesNotExist:
            return Response(
                {'error': 'Plan pricing not found for the given plan and billing cycle'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate the final price for plan
        if plan_pricing.offer:
            try:
                offer_percentage = Decimal(plan_pricing.offer)
                discounted_price = plan_pricing.price * (1 - offer_percentage / Decimal(100))
                final_price = discounted_price * Decimal('1.18')  # Adding 18% GST
            except (ValueError, TypeError):
                final_price = plan_pricing.price
                final_price = int(final_price) * Decimal('1.18')
        else:
            final_price = plan_pricing.price
            final_price = int(final_price) * Decimal('1.18')
        
        # Prepare response data
        item_data = {
            'id': plan_pricing.plan.id,
            'name': plan_pricing.plan.name,
            'description': plan_pricing.plan.description,
            'type': 'plan'
        }
        billing_cycle_data = {
            'id': plan_pricing.billing_cycle.id,
            'name': plan_pricing.billing_cycle.name,
            'duration_months': plan_pricing.billing_cycle.duration_in_months
        }
        
    elif payment_type == 'addon':
        addon_id = request.data.get('plan_id')
        
        if not addon_id:
            return Response(
                {'error': 'plan_id is required for addon purchase'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            addon_plan = AddonPlan.objects.select_related('feature').get(id=addon_id, is_active=True)
        except AddonPlan.DoesNotExist:
            return Response(
                {'error': 'Addon plan not found or inactive'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate the final price for addon
        if addon_plan.offer_price:
            final_price = addon_plan.offer_price * Decimal('1.18')  # Adding 18% GST
        else:
            final_price = addon_plan.price * Decimal('1.18')  # Adding 18% GST
        
        # Prepare response data
        item_data = {
            'id': addon_plan.id,
            'name': addon_plan.name,
            'description': addon_plan.description,
            'type': 'addon',
            'credits': addon_plan.credits
        }
        feature_data = {
            'id': addon_plan.feature.id,
            'name': addon_plan.feature.name,
            'code': addon_plan.feature.code
        }
        billing_cycle_data = None
        
    else:
        return Response(
            {'error': 'Invalid payment_type. Must be "plan" or "addon"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    amount = float(final_price * 100)  # Convert to paise for Razorpay
    
    # Determine Razorpay mode from Django settings
    RAZORPAY_MODE = getattr(settings, 'RAZORPAY_MODE', 'test')
    
    try:
        if RAZORPAY_MODE == 'live':
            RAZORPAY_KEY_ID = settings.RAZORPAY_LIVE_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_LIVE_MODE_KEY_SECRET
        else:
            RAZORPAY_KEY_ID = settings.RAZORPAY_TEST_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_TEST_MODE_KEY_SECRET
    except ImproperlyConfigured as e:
        return Response(
            {'error': f'Payment configuration error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    try:
        # Create Razorpay client
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        
        # Create order in Razorpay
        payment = client.order.create({
            'amount': int(amount),  # Razorpay expects amount in paise as integer
            'currency': 'INR',
            'payment_capture': '1'
        })
        
        # Save payment details
        payment_obj = Payment(
            payment_type=payment_type,
            razorpay_order_id=payment['id'],
            amount=amount / 100  # Convert back to rupees for storage
        )
        
        if payment_type == 'plan':
            payment_obj.plan_pricing = plan_pricing
        elif payment_type == 'addon':
            payment_obj.addon_plan = addon_plan
            
        payment_obj.save()
        
        # Build response data
        data = {
            'payment': {
                'id': payment_obj.id,
                'payment_type': payment_obj.payment_type,
                'razorpay_order_id': payment_obj.razorpay_order_id,
                'amount': str(payment_obj.amount),
                'created_at': payment_obj.created_at.isoformat()
            },
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'order_id': payment['id'],
            'amount': amount / 100,
            'currency': 'INR',
            'item': item_data
        }
        
        if payment_type == 'plan':
            data['billing_cycle'] = billing_cycle_data
        elif payment_type == 'addon':
            data['feature'] = feature_data
        
        return Response(data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Error creating order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(['POST'])
def payment_success(request):
    RAZORPAY_MODE = getattr(settings, 'RAZORPAY_MODE', 'test')
    try:
        if RAZORPAY_MODE == 'live':
            RAZORPAY_KEY_ID = settings.RAZORPAY_LIVE_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_LIVE_MODE_KEY_SECRET
        else:
            RAZORPAY_KEY_ID = settings.RAZORPAY_TEST_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_TEST_MODE_KEY_SECRET
    except ImproperlyConfigured as e:
        raise ImproperlyConfigured(f"Environment variable error: {e}")
    
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    response = request.data

    params_dict = {
        'razorpay_order_id': response.get('razorpay_order_id'),
        'razorpay_payment_id': response.get('razorpay_payment_id'),
        'razorpay_signature': response.get('razorpay_signature')
    }

    try:
        client.utility.verify_payment_signature(params_dict)
        payment = Payment.objects.get(razorpay_order_id=response.get('razorpay_order_id'))
        payment.razorpay_payment_id = response.get('razorpay_payment_id')
        payment.razorpay_signature = response.get('razorpay_signature')
        payment.save()

        # Get user and company
        user = request.user
        try:
            company = Company.objects.get(id=user.company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Handle different payment types
        if payment.payment_type == 'plan':
            return _handle_plan_payment(payment, user, company, request)
        elif payment.payment_type == 'addon':
            return _handle_addon_payment(payment, user, company, request)
        else:
            return Response(
                {'error': 'Invalid payment type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Payment success error: {str(e)}", exc_info=True)
        return Response(
            {'status': f'Payment verification failed: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def custom_credit_order_create(request):

    feature_code = request.data.get('feature_code')
    credits = request.data.get("credits")
    
    if not feature_code or not credits:
        return Response(
            {'error': 'feature_code and credits are required for purchase'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        feature = Feature.objects.get(code=feature_code)
    except Feature.DoesNotExist:
        return Response(
            {'error': 'Feature not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        credits_val = int(credits)
    except (TypeError, ValueError):
        return Response(
            {'error': 'Invalid credits'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate the final price for addon
    if feature.price:
        price = Decimal(str(credits_val)) * Decimal(str(feature.price)) 
        final_price = price * Decimal('1.18')  # Adding 18% GST
    else:
        return Response(
            {'error': 'Price not set for this feature'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    item_data = {
        'id': feature.id,
        'name': feature.name,
        'description': feature.description,
        'type': 'custom_addon',
        'credits': credits_val
    }
        
    
    amount = float(final_price * 100)  # Convert to paise for Razorpay
    
    # Determine Razorpay mode from Django settings
    RAZORPAY_MODE = getattr(settings, 'RAZORPAY_MODE', 'test')
    
    try:
        if RAZORPAY_MODE == 'live':
            RAZORPAY_KEY_ID = settings.RAZORPAY_LIVE_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_LIVE_MODE_KEY_SECRET
        else:
            RAZORPAY_KEY_ID = settings.RAZORPAY_TEST_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_TEST_MODE_KEY_SECRET
    except ImproperlyConfigured as e:
        return Response(
            {'error': f'Payment configuration error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    try:
        # Create Razorpay client
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        
        # Create order in Razorpay
        payment = client.order.create({
            'amount': int(amount),  # Razorpay expects amount in paise as integer
            'currency': 'INR',
            'payment_capture': '1'
        })
        
        # Save payment details
        payment_obj = Payment(
            payment_type="custom_addon",
            razorpay_order_id=payment['id'],
            amount=amount / 100  # Convert back to rupees for storage
        )
        
        payment_obj.save()
        
        # Build response data
        data = {
            'payment': {
                'id': payment_obj.id,
                'payment_type': payment_obj.payment_type,
                'razorpay_order_id': payment_obj.razorpay_order_id,
                'amount': str(payment_obj.amount),
                'created_at': payment_obj.created_at.isoformat()
            },
            'razorpay_key_id': RAZORPAY_KEY_ID,
            'order_id': payment['id'],
            'amount': amount / 100,
            'currency': 'INR',
            'item': item_data
        }
        
        return Response(data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Error creating order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def custom_addon_payment_success(request):
    RAZORPAY_MODE = getattr(settings, 'RAZORPAY_MODE', 'test')
    try:
        if RAZORPAY_MODE == 'live':
            RAZORPAY_KEY_ID = settings.RAZORPAY_LIVE_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_LIVE_MODE_KEY_SECRET
        else:
            RAZORPAY_KEY_ID = settings.RAZORPAY_TEST_MODE_KEY_ID
            RAZORPAY_KEY_SECRET = settings.RAZORPAY_TEST_MODE_KEY_SECRET
    except ImproperlyConfigured as e:
        raise ImproperlyConfigured(f"Environment variable error: {e}")
    
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    response = request.data

    params_dict = {
        'razorpay_order_id': response.get('razorpay_order_id'),
        'razorpay_payment_id': response.get('razorpay_payment_id'),
        'razorpay_signature': response.get('razorpay_signature')
    }

    try:
        client.utility.verify_payment_signature(params_dict)
        payment = Payment.objects.get(razorpay_order_id=response.get('razorpay_order_id'))
        payment.razorpay_payment_id = response.get('razorpay_payment_id')
        payment.razorpay_signature = response.get('razorpay_signature')
        payment.save()

        # Get user and company
        user = request.user
        try:
            company = Company.objects.get(id=user.company_id)
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Handle different payment types
        if payment.payment_type == 'custom_addon':
            return _handle_custom_addon_payment(payment, user, company, request)
        else:
            return Response(
                {'error': 'Invalid payment type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Payment success error: {str(e)}", exc_info=True)
        return Response(
            {'status': f'Payment verification failed: {str(e)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    

def _handle_plan_payment(payment, user, company, request):
    """Handle successful plan payment"""
    plan_pricing = payment.plan_pricing
    plan = plan_pricing.plan
    
    # Calculate final price for billing history
    if plan_pricing.offer:
        try:
            offer_percentage = Decimal(plan_pricing.offer)
            discounted_price = plan_pricing.price * (1 - offer_percentage / Decimal(100))
            offer_price = discounted_price * Decimal('1.18')  # Adding 18% GST
            offer_price = int(offer_price) + Decimal('0.99')
        except (ValueError, TypeError):
            offer_price = plan_pricing.price
            offer_price = int(offer_price) + Decimal('0.99')
    else:
        offer_price = plan_pricing.price
        offer_price = int(offer_price) + Decimal('0.99')
    
    final_price = offer_price
        
    # Get or create subscription
    subscriptions = Subscription.objects.filter(company=company)
    if subscriptions.exists():
        subscription = subscriptions.first()
        subscription.plan_pricing = plan_pricing
        subscription.is_active = True
        subscription.end_date = timezone.now() + timezone.timedelta(days=30)  # Set 30 days from now
        subscription.save()
        created = False
        
        # If there are multiple subscriptions for some reason, deactivate the older ones
        if subscriptions.count() > 1:
            subscriptions.exclude(id=subscription.id).update(is_active=False)
    else:
        subscription = Subscription.objects.create(
            company=company,
            plan_pricing=plan_pricing,
            is_active=True,
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        created = True

    # Create billing history for the transaction
    BilingHistory.objects.create(
        company=company,
        plan_pricing=plan_pricing,
        feature=None,
        transaction_type="plan_allocation",
        price=float(final_price),
        credit=None
    )

    # Update user trial status if needed
    if hasattr(user, 'is_trial') and user.is_trial:
        user.is_trial = False
        if hasattr(user, 'role'):
            user.role = [Account.ADMIN]
        user.save()

    # Get all feature credits for the plan
    plan_features = PlanFeatureCredit.objects.filter(plan=plan)
    
    # Remove existing features from CreditWallet that are not in the new plan
    plan_feature_ids = plan_features.values_list('feature_id', flat=True)
    CreditWallet.objects.filter(company=company).exclude(feature_id__in=plan_feature_ids).delete()
    
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

    return Response({
        'status': 'Payment successful',
        'payment_type': 'plan',
        'subscription_id': subscription.id,
        'plan_id': plan.id,
        'credits_added': plan_features.count()
    }, status=status.HTTP_200_OK)

def _handle_addon_payment(payment, user, company, request):
    """Handle successful addon payment"""
    addon_plan = payment.addon_plan
    feature = addon_plan.feature
    
    # Calculate final price for billing history
    if addon_plan.offer_price:
        final_price = addon_plan.offer_price * Decimal('1.18')  # Adding 18% GST
    else:
        final_price = addon_plan.price * Decimal('1.18')  # Adding 18% GST

    # Create billing history for the addon transaction
    BilingHistory.objects.create(
        company=company,
        plan_pricing=None,
        feature=feature,
        transaction_type="addon",
        price=float(final_price),
        credit=addon_plan.credits
    )

    # Update or create credit wallet entry for the addon feature
    credit_wallet, created = CreditWallet.objects.get_or_create(
        company=company,
        feature=feature,
        defaults={
            'total_credit': 0,
            'used_credit': 0,
            'isdayli': feature.isdayli,
            'iscredit': feature.iscredit,
            'iswithoutcredit': feature.iswithoutcredit
        }
    )
    
    # Add addon credits to existing wallet
    credit_wallet.total_credit += addon_plan.credits
    credit_wallet.save()

    return Response({
        'status': 'Payment successful',
        'payment_type': 'addon',
        'addon_id': addon_plan.id,
        'addon_name': addon_plan.name,
        'credits_added': addon_plan.credits,
        'feature_name': feature.name
    }, status=status.HTTP_200_OK)

def _handle_custom_addon_payment(payment, user, company, request):
    """Handle successful custom addon payment"""
    feature_code = request.data.get('feature_code')
    credits = request.data.get('credits')

    if not feature_code or not credits:
        return Response(
            {'error': 'feature_code and credits are required to complete the payment'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        feature = Feature.objects.get(code=feature_code)
    except Feature.DoesNotExist:
        return Response(
            {'error': 'Feature not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        credits_val = int(credits)
    except (TypeError, ValueError):
        return Response(
            {'error': 'Invalid credits value'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create billing history for the custom addon transaction
    BilingHistory.objects.create(
        company=company,
        plan_pricing=None,
        feature=feature,
        transaction_type="custom_addon",
        price=float(payment.amount),
        credit=credits_val
    )

    # Update or create credit wallet entry for the custom addon feature
    credit_wallet, created = CreditWallet.objects.get_or_create(
        company=company,
        feature=feature,
        defaults={
            'total_credit': 0,
            'used_credit': 0,
            'isdayli': feature.isdayli,
            'iscredit': feature.iscredit,
            'iswithoutcredit': feature.iswithoutcredit
        }
    )
    
    # Add addon credits to existing wallet
    credit_wallet.total_credit += credits_val
    credit_wallet.save()

    return Response({
        'status': 'Payment successful',
        'payment_type': 'custom_addon',
        'credits_added': credits_val,
        'feature_name': feature.name
    }, status=status.HTTP_200_OK)


class BillingPlanView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getBillingPlans(request)
        return makeResponse(data)
    
class CurrentSubscriptionView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = helper.getCurrentSubscription(request)
        if data:
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'No active subscription found.'}, status=status.HTTP_404_NOT_FOUND)
        
from concurrent.futures import ThreadPoolExecutor
from django.http import JsonResponse
import imaplib
import email

class GmailReceiveEmailView2:
    def fetch_received_emails(self, request, target_email):
        try:
            data = request.data
            account = request.user
            
            email_data = EmailSettings.objects.filter(Q(user_id=account.pk) | Q(company=request.user.company_id)).order_by('-created_at').first()
            if email_data is None:
                return Response({'code': 403, 'message': 'EmailSmtp for the user does not exist.'}, status=403)
            
            sender_mail = email_data.sender_mail
            auth_password = email_data.auth_password
            
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(sender_mail, auth_password)
            mail.select('inbox')  # Select the inbox for received emails

            search_criteria = f'(OR FROM "{target_email}" TO "{target_email}")'
            result, data = mail.search(None, search_criteria)

            email_list = []  # Initialize email list

            if result == 'OK':
                # Get the list of email IDs
                mail_ids = data[0].split()
                
                if not mail_ids:
                    # Return an empty list or None if no emails are found
                    return Response(None)

                # Decode each mail ID from bytes to string
                mail_ids = [id.decode('utf-8') for id in mail_ids]

                # Fetch emails in a batch instead of one by one
                email_id_string = ','.join(mail_ids)  # Join the email IDs as a string for fetching
                result, msg_data = mail.fetch(email_id_string, '(RFC822)')

                if result == 'OK':
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            raw_email = response_part[1]
                            msg = email.message_from_bytes(raw_email)

                            # Decode the email subject
                            subject = email.header.decode_header(msg['subject'])[0][0]
                            if isinstance(subject, bytes):
                                subject = subject.decode('utf-8', errors='replace')

                            # Decode the sender email
                            from_email = email.header.decode_header(msg['from'])[0][0]
                            if isinstance(from_email, bytes):
                                from_email = from_email.decode('utf-8', errors='replace')

                            to_email = email.header.decode_header(msg['to'])[0][0]
                            if isinstance(to_email, bytes):
                                to_email = to_email.decode('utf-8', errors='replace')
                                
                            date = email.header.decode_header(msg['date'])[0][0]
                            if isinstance(date, bytes):
                                date = date.decode('utf-8', errors='replace')

                            # Extract the email body (plain text or first part)
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    content_disposition = str(part.get("Content-Disposition"))

                                    if content_type == "text/plain" and "attachment" not in content_disposition:
                                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode('utf-8', errors='replace')

                            # Append the filtered email information
                            email_list.append({
                                'subject': subject,
                                'from': from_email,
                                'to': to_email,
                                'date': date,
                                'body': body  # Limit body length for performance (first 200 chars)
                            })
                
            mail.logout()  # Logout from IMAP server
            return Response(email_list if email_list else None)

        except imaplib.IMAP4.error as e:
            return {"error": f"IMAP error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

class GmailSentEmailView2:
    def fetch_sent_emails(self, request, target_email):
        try:
            data = request.data
            account = request.user
            
            email_data = EmailSettings.objects.filter(user_id=account.pk).order_by('-created_at').first()
            if email_data is None:
                return Response({'code': 403, 'message': 'EmailSmtp for the user does not exist.'}, status=403)

            sender_mail = email_data.sender_mail
            auth_password = email_data.auth_password
            
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(sender_mail, auth_password)

            email_list = []

            # Try to select the Sent Mail folder
            try:
                mail.select('"[Gmail]/Sent Mail"')
            except:
                try:
                    mail.select('"[Gmail]/Sent"')
                except:
                    return Response({"error": "Could not find Sent Mail folder"}, status=400)

            search_criteria = f'(TO "{target_email}")'
            result, data = mail.search(None, search_criteria)

            if result == 'OK':
                mail_ids = data[0].split()

                for num in mail_ids:
                    result, msg_data = mail.fetch(num, '(RFC822)')
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject = email.header.decode_header(msg['subject'])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode('utf-8', errors='replace')

                    from_email = email.header.decode_header(msg['from'])[0][0]
                    if isinstance(from_email, bytes):
                        from_email = from_email.decode('utf-8', errors='replace')

                    to_email = email.header.decode_header(msg['to'])[0][0]
                    if isinstance(to_email, bytes):
                        to_email = to_email.decode('utf-8', errors='replace')
                        
                    date = email.header.decode_header(msg['date'])[0][0]
                    if isinstance(date, bytes):
                        date = date.decode('utf-8', errors='replace')

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='replace')

                    email_list.append({
                        'subject': subject,
                        'from': from_email,
                        'to': to_email,
                        'date': date,
                        'body': body,
                    })

            mail.logout()  # Logout from IMAP server
            return Response(email_list)

        except imaplib.IMAP4.error as e:
            return {"error": f"IMAP error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}


class GmailAllEmailsView(APIView):
    def get(self, request, id):
        try:
            from candidates.models import Candidate, Mail
            candidate = Candidate.objects.get(id=id)
            
            # Safely get target email
            target_email = candidate.email
            if not target_email and candidate.webform_candidate_data:
                target_email = candidate.webform_candidate_data.get('Personal Details', {}).get('email')
                
            if not target_email:
                return JsonResponse({"error": "Candidate email not found."}, status=400)

            # Fetch sent emails (emails where candidate is the receiver)
            sent_emails_qs = Mail.objects.filter(receiver__contains=[target_email]).order_by('-date_time')
            sent_emails = []
            for m in sent_emails_qs:
                sent_emails.append({
                    'subject': m.subject,
                    'from': m.from_email or (m.sender.email if m.sender else ""),
                    'to': ", ".join(m.receiver) if m.receiver else "",
                    'date': m.date_time.strftime('%a, %d %b %Y %H:%M:%S %z'),
                    'body': m.body
                })
                
            # Fetch received emails (emails where candidate is the sender/from_email)
            received_emails_qs = Mail.objects.filter(from_email=target_email).order_by('-date_time')
            received_emails = []
            for m in received_emails_qs:
                received_emails.append({
                    'subject': m.subject,
                    'from': m.from_email,
                    'to': ", ".join(m.receiver) if m.receiver else "",
                    'date': m.date_time.strftime('%a, %d %b %Y %H:%M:%S %z'),
                    'body': m.body
                })

            response_data = {
                'received_emails': received_emails if received_emails else None,
                'sent_emails': sent_emails if sent_emails else None
            }

            return JsonResponse(response_data)

        except Candidate.DoesNotExist:
            return JsonResponse({"error": "Candidate not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
             
class DesignationCareerApi(APIView):

    def get(self, request):
        data = helper.getDesignationsCareer(request)
        return makeResponse(data)
    
class DegreeCareerApi(APIView):

    def get(self, request):
        data = helper.getDegreesCareer(request)
        return makeResponse(data)
    
class EmailCredentialsApi(APIView):

    def get(self, request):
        data = helper.getEmailCredentials(request)
        return makeResponse(data)
    
class OrganizationalEmailApi(APIView):

    def get(self, request):
        data = helper.getOrganizationalEmails(request)
        return Response(data)
    
    def post(self, request):
        data = helper.saveOrganizationalEmail(request)
        return Response(data)
    
    def delete(self,request,id):
        data = helper.deleteOrganizationalEmail(request,id)
        return Response(data)

class UnsubscribeEmailTokenApi(APIView):
    def get(self, request, token):
        data = helper.saveUnsubscribeEmailTokenLink(request, token)
        return render(request, 'unsubscribe_confirmation.html')
    
class UnsubscribeLinkApi(APIView):

    def get(self, request):
        data = helper.getUnsubscribeLinks(request)
        return Response(data)
    
    def post(self, request):
        data = helper.saveUnsubscribeLink(self, request)
        return Response(data)  

class AttachmentCategoryApi(APIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        data = helper.getAttachmentCategories(request)
        return makeResponse(data)  

def redirect_short_url(request, code):
    try:
        obj = get_object_or_404(ShortLink, code=code)
        # Clean up the URL
        url = obj.long_url.strip()
        
        # Remove any leading 'http://' or 'https://' if they appear multiple times
        while url.startswith(('http://', 'https://')):
            if url.startswith('http://'):
                url = url[7:]
            elif url.startswith('https://'):
                url = url[8:]
        
        # Ensure the URL has a scheme (default to http:// if not present)
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        return redirect(url)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error redirecting short URL {code}: {str(e)}")
        raise Http404("Short URL not found")

class ShortUrlApi(APIView):
    def get(self, request, id):
        data = get_object_or_404(ShortLink, job_id=id)
        serializer = ShortLinkSerializer(data, context={'request': request})
        return Response(serializer.data)

class QRModelApi(APIView):
    def get(self, request, id):
        qr = get_object_or_404(QRModel, job_id=id)
        serializer = QRModelSerializer(qr, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CandidateEvaluationCriteriaView(APIView):
    """
    API View for managing Candidate Evaluation Criteria
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return queryset filtered by company"""
        return CandidateEvaluationCriteria.objects.get(company=self.request.user.company_id)

    def get(self, request, id=None):
        """
        Get a single evaluation criteria by ID or list all criteria for the company
        """
        try:
            if id:
                criteria = self.get_queryset().get(id=id)
                serializer = CandidateEvaluationCriteriaSerializer(criteria)
                return Response(serializer.data)
            else:
                criteria = self.get_queryset()
                serializer = CandidateEvaluationCriteriaSerializer(criteria)
                return Response(serializer.data)
        except CandidateEvaluationCriteria.DoesNotExist:
            return Response(
                {"error": "Candidate evaluation criteria not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Create a new evaluation criteria"""
        try:
            data = request.data.copy()
            data['company'] = request.user.company.id
            
            serializer = CandidateEvaluationCriteriaSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, id=None):
        """Update an existing evaluation criteria"""
        if not id:
            return Response(
                {"error": "ID is required for update"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            criteria = CandidateEvaluationCriteria.objects.get(id=id)
            serializer = CandidateEvaluationCriteriaSerializer(criteria, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CandidateEvaluationCriteria.DoesNotExist:
            return Response(
                {"error": "Candidate evaluation criteria not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, id=None):
        """Delete an evaluation criteria"""
        if not id:
            return Response(
                {"error": "ID is required for deletion"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            criteria = self.get_queryset().get(id=id)
            criteria.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CandidateEvaluationCriteria.DoesNotExist:
            return Response(
                {"error": "Candidate evaluation criteria not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LinkedinCompanyidAPI(APIView):
    """
    API view for managing Linkding company IDs
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get queryset with optional filtering by company
        """
        queryset = LinkdingCompanyid.objects.select_related('company').filter(is_active=True)
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset

    def get(self, request, id=None):
        """
        Get a single Linkding company ID or list all
        """
        try:
            if id:
                # Get single instance
                instance = get_object_or_404(LinkdingCompanyid, id=id, is_active=True)
                serializer = LinkdingCompanyidSerializer(instance)
                return Response(True, 'Linkding company ID retrieved successfully', serializer.data)
            else:
                # List all
                queryset = self.get_queryset()
                serializer = LinkdingCompanyidSerializer(queryset, many=True)
                return Response(serializer.data)
        except Exception as e:
            return Response(False, str(e), None, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        Create a new Linkding company ID
        """
        try:
            data = request.data
            user = request.user
            company = Company.getByUser(user)
            data["company"] = company.id
            
            # Check if company already has a Linkding ID
            existing_record = LinkdingCompanyid.objects.filter(company=company, is_active=True).first()
            
            if existing_record:
                # Update existing record
                serializer = LinkdingCompanyidSerializer(existing_record, data=data, partial=True)
                success_msg = 'Linkding company ID updated successfully'
                success_status = status.HTTP_200_OK
            else:
                # Create new record
                serializer = LinkdingCompanyidSerializer(data=data)
                success_msg = 'Linkding company ID created successfully'
                success_status = status.HTTP_201_CREATED
            
            if serializer.is_valid():
                serializer.save()
                return Response(
                    data={
                        'code': 200,
                        'data': serializer.data,
                        'msg': success_msg
                    },
                    status=success_status
                )
            return Response(
                data={
                    'code': 400,
                    'errors': serializer.errors,
                    'msg': 'Validation error'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                data={
                    'code': 400,
                    'errors': str(e),
                    'msg': 'An error occurred'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request, id):
        """
        Update an existing Linkding company ID
        """
        try:
            instance = get_object_or_404(LinkdingCompanyid, id=id, is_active=True)
            serializer = LinkdingCompanyidSerializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return makeResponse(True, 'Linkding company ID updated successfully', serializer.data)
            return makeResponse(False, 'Validation error', serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return makeResponse(False, str(e), None, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        """
        Soft delete a Linkding company ID by setting is_active to False
        """
        try:
            instance = get_object_or_404(LinkdingCompanyid, id=id, is_active=True)
            instance.is_active = False
            instance.save()
            return makeResponse(True, 'Linkding company ID deleted successfully', None, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return makeResponse(False, str(e), None, status=status.HTTP_400_BAD_REQUEST)


class JobBoardListApi(APIView):
    def get(self, request):
        job_board_list = JobBoardList.objects.all()
        serializer = JobBoardListSerializer(job_board_list, many=True)
        return Response(serializer.data)
    
class JobBoardApi(APIView):
    def get(self, request):
        company = Company.getByUser(request.user)
        job_board = JobBoard.objects.get(company=company)
        serializer = JobBoardSerializer(job_board)
        return Response(serializer.data)
    
    def post(self, request):
        user = request.user
        company = Company.getByUser(user)
        data = request.data.copy()
        data["company"] = company.id
        action = data.pop('action', 'add')  # Default to 'add' if action not specified
        
        # Check if a JobBoard already exists for this company
        job_board = JobBoard.objects.filter(company=company).first()
        
        if job_board:
            # Get existing job board lists
            existing_lists = list(job_board.job_board_list.values_list('id', flat=True))
            
            # Get job board lists from request
            lists_to_modify = data.get('job_board_lists', [])
            
            if action == 'add':
                # For 'add' action, combine and remove duplicates
                combined_lists = list(set(existing_lists + lists_to_modify))
                data['job_board_lists'] = combined_lists
            elif action == 'remove':
                # For 'remove' action, remove the specified lists
                data['job_board_lists'] = [x for x in existing_lists if x not in lists_to_modify]
            else:
                return Response(
                    {"error": "Invalid action. Use 'add' or 'remove'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update existing record
            serializer = JobBoardSerializer(job_board, data=data, partial=True)
        else:
            if action == 'remove':
                return Response(
                    {"error": "Cannot remove lists from a non-existent job board."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Create new record
            data["job_board_list"] = data.get('job_board_lists', [])
            serializer = JobBoardSerializer(data=data)
            
        if serializer.is_valid():
            job_board = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, id):
        job_board = get_object_or_404(JobBoard, id=id)
        serializer = JobBoardSerializer(job_board, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, id):
        job_board = get_object_or_404(JobBoard, id=id)
        job_board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CreditWalletAPI(APIView):
    """
    API to check credit wallet balance for features
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, feature_code=None, feature_usage=None):
        try:
            user = request.user
            company = user.company_id

            # If feature_code is provided, filter by that feature
            if feature_usage:
                feature_usage_obj = FeatureUsage.objects.get(code=feature_usage)
                
            if feature_code:
                try:
                    feature = Feature.objects.get(code=feature_code)
                    credit_wallet = CreditWallet.objects.filter(
                        company=company,
                        feature=feature
                    ).first()
                    avelible_credit= credit_wallet.total_credit- credit_wallet.used_credit
                    if not credit_wallet or avelible_credit < feature_usage_obj.used_credit:
                        return Response(
                            {'detail': 'No credit wallet found for this feature.',"is_available":False, "required_credit":feature_usage_obj.used_credit,
                            "avelible_credit":avelible_credit},
                            status=status.HTTP_402_PAYMENT_REQUIRED
                        )
                    
                    serializer = CreditWalletSerializer(credit_wallet)
                    return Response({"data":serializer.data,"is_available":True,"required_credit":feature_usage_obj.used_credit,"avelible_credit":avelible_credit})
                
                except Feature.DoesNotExist:
                    return Response(
                        {'detail': 'Feature not found.',"is_available":False,"required_credit":feature_usage_obj.used_credit,"avelible_credit":avelible_credit},
                        status=status.HTTP_402_PAYMENT_REQUIRED
                    )
            
            # If no feature_code, return all credit wallets for the company
            credit_wallets = CreditWallet.objects.filter(company=company)
            serializer = CreditWalletSerializer(credit_wallets, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

from common.file_utils import calculate_company_storage_usage
from .decorators import check_feature_availability

class CheckFeatureAvailability(APIView):
    """
    API to check if a feature is available for a specific plan
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @check_feature_availability()
    def get(self, request, feature_code=None):
        """
        Check if a feature is available for the user's plan and company.
        Uses the @check_feature_availability decorator to handle all checks.
        """
        # If we reach here, all checks passed and the feature is available
        return Response(
            {'detail': 'Feature is available for this plan.', 'isAvailable': True},
            status=status.HTTP_200_OK
        )


from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid
from django.conf import settings

class temp(APIView):
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    # @calculate_company_storage_usage
    def get(self, request):
        plan = Plan.objects.all().values()
        billingCycle = BillingCycle.objects.all().values()
        planPricing =PlanPricing.objects.all().values()
        feature = Feature.objects.all().values()
        planFeatureCredit=PlanFeatureCredit.objects.all().values()
        featureUsage=FeatureUsage.objects.all().values()
        """
        Get the total size of a company's uploads folder.
        Query params:
        - company_id: The ID of the company (defaults to 095d7759-75cf-4d90-b7e3-59e51d3a7c52 if not provided)
        """
        return Response({
        'message': 'Your response data',
        "plan":plan,
        'billingCycle':billingCycle,
        'planPricing':planPricing,
        "feature":feature,
        'planFeatureCredit':planFeatureCredit,
        "featureUsage" :featureUsage
        # The decorator will add 'storage_info' to this response
    })

class AddonPlanListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        code= request.query_params.get('code')
        print(code)
        if code:
            addon_plans = AddonPlan.objects.filter(is_active=True , feature__code=code)
        else:
            addon_plans = AddonPlan.objects.filter(is_active=True , feature__code="AI_CREDITS")
        serializer = AddonPlanSerializer(addon_plans, many=True)
        return Response(serializer.data)

class PlanFeatureCreditAPIView(APIView):
    """
    GET API for PlanFeatureCredit model
    Returns all plan feature credits with related plan and feature details
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request,plan_id):
        """
        Get all plan feature credits
        Optional query parameters:
        - plan_id: Filter by specific plan ID
        - feature_id: Filter by specific feature ID
        """
        queryset = PlanFeatureCredit.objects.filter(plan__id=plan_id)
        
        # Apply filters if provided
        # plan_id = request.query_params.get('plan_id')
        # feature_id = request.query_params.get('feature_id')
        
        # if plan_id:
        #     queryset = queryset.filter(plan_id=plan_id)
        # if feature_id:
        #     queryset = queryset.filter(feature_id=feature_id)
        
        serializer = PlanFeatureCreditSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CreditHistoryAPIView(APIView):
    """
    API to fetch credit history
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            # company = "095d7759-75cf-4d90-b7e3-59e51d3a7c52"
            company=user.company_id 
            
            credit_history = CreditHistory.objects.filter(company=company, feature__code="AI_CREDITS").order_by('-created_at')
            wallet = CreditWallet.objects.filter(company=company, feature__code="AI_CREDITS").first()
            total_credit = wallet.total_credit if wallet else 0
            
            used_credit = 0
            for i in credit_history:
                used_credit += i.credit
            
            
            serializer = CreditHistorySerializer(credit_history, many=True)
            return Response({"data": serializer.data, "total_credit": total_credit,"available_credit":total_credit-wallet.used_credit, "used_credit": used_credit}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class BillingHistoryAPIView(APIView):
    """
    API to fetch billing history
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            company = user.company_id
            
            billing_history = BilingHistory.objects.filter(company=company).order_by('-created_at')
            serializer = BilingHistorySerializer(billing_history, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

