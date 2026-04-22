from functools import wraps
import os
from django.contrib.auth import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from django.utils.text import slugify

from settings.models import CreditWallet, Feature, FeatureUsage, PlanFeatureCredit, Subscription, CreditHistory, Company
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied as DRF_PermissionDenied



# def check_feature_availability(feature_code_param=None):
#     """
#     Decorator to check if a feature is available for the user's company.
    
#     Usage: 
#     - @check_feature_availability()  # uses 'feature_code' from request.data by default
#     - @check_feature_availability('param_name')  # uses custom parameter name from request.data
#     - @check_feature_availability('FEATURE_CODE')  # uses hardcoded feature code
#     """
#     def decorator(view_func):
#         @wraps(view_func)
#         def wrapper(self, request, *args, **kwargs):
#             # If feature_code_param is None, it means we're using the default parameter name
#             if feature_code_param is None:
#                 feature_code = request.data.get('feature_code') or kwargs.get('feature_code')
#             # If feature_code_param is a string, check if it's a parameter name or a feature code
#             elif isinstance(feature_code_param, str):
#                 # If it's a parameter in request.data or kwargs, use that
#                 feature_code = request.data.get(feature_code_param) or kwargs.get(feature_code_param)
#                 # If not found, treat feature_code_param as the actual feature code
#                 if feature_code is None:
#                     feature_code = feature_code_param
#             
#             if not feature_code:
#                 return Response(
#                     {'message': 'Feature code is required.', 'isAvailable': False},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
# 
#             company = request.user.company_id
#             
#             # Check for active subscription
#             subscription = Subscription.objects.filter(company=company, is_active=True).first()
#             if not subscription:
#                 return Response(
#                     {'message': 'No active subscription found for this company.', 'isAvailable': False},
#                     status=status.HTTP_404_NOT_FOUND
#                 )
# 
#             # Check if feature exists
#             try:
#                 feature = Feature.objects.get(code=feature_code)
#             except Feature.DoesNotExist:
#                 return Response(
#                     {'message': 'Feature not found.', 'isAvailable': False},
#                     status=status.HTTP_404_NOT_FOUND
#                 )
#             
#             # Check if feature is in plan
#             plan_feature = PlanFeatureCredit.objects.filter(
#                 plan=subscription.plan_pricing.plan, 
#                 feature=feature
#             ).first()
#             
#             if not plan_feature:
#                 return Response(
#                     {'message': 'Feature not available for this plan.', 'isAvailable': False},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
# 
#             # Check credit wallet
#             credit_wallet = CreditWallet.objects.filter(
#                 company=company, 
#                 feature=feature
#             ).first()
#             print(credit_wallet)
#             if credit_wallet:  
#                 if not credit_wallet.iswithoutcredit:
#                     available_credit = credit_wallet.total_credit - credit_wallet.used_credit
#                     if available_credit <= 0:
#                         return Response(
#                             {'message': 'No credits available for this feature.', 'isAvailable': False},
#                             status=status.HTTP_403_FORBIDDEN
#                         )
#             else:
#                 return Response(
#                     {'message': 'This feature is not available for this plan.', 'isAvailable': False},
#                     status=status.HTTP_403_FORBIDDEN
#                 )
# 
#             # Add feature and credit_wallet to request for use in the view if needed
#             request.feature = feature
#             request.credit_wallet = credit_wallet
#             
#             # Proceed to the view if all checks pass
#             return view_func(self, request, *args, **kwargs)
#         return wrapper
#     return decorator
def check_feature_access(company_id, feature_code):
    """
    Checks if a company has access to a feature and has enough credits.
    Returns (has_access, message, features, valid_credit_wallets)
    """
    subscription = Subscription.objects.filter(
        company_id=company_id,
        is_active=True
    ).first()

    if not subscription:
        return False, 'No active subscription found for this company.', None, None

    feature_codes = feature_code.split(",") if isinstance(feature_code, str) else [feature_code]
    feature_codes = [code.strip() for code in feature_codes if code.strip()]
    
    features = Feature.objects.filter(code__in=feature_codes)
    found_features = {f.code: f for f in features}
    
    missing_features = [code for code in feature_codes if code not in found_features]
    if missing_features:
        return False, f'Feature(s) not found: {", ".join(missing_features)}', None, None

    plan_features = PlanFeatureCredit.objects.filter(
        plan=subscription.plan_pricing.plan,
        feature__in=features
    )
    valid_plan_feature_ids = plan_features.values_list('feature_id', flat=True)
    
    features_not_in_plan = [f.name for f in features if f.id not in valid_plan_feature_ids]
    if features_not_in_plan:
        return False, f'{", ".join(features_not_in_plan)} feature(s) are not available for this plan.', None, None

    credit_wallets = CreditWallet.objects.filter(
        company_id=company_id,
        feature_id__in=valid_plan_feature_ids
    )
    cw_dict = {cw.feature_id: cw for cw in credit_wallets}
    
    features_no_wallet = [f.name for f in features if f.id not in cw_dict]
    if features_no_wallet:
        return False, f'{", ".join(features_no_wallet)} feature(s) are not available for this plan.', None, None

    unavailable_features = []
    valid_credit_wallets = []
    
    for f in features:
        cw = cw_dict[f.id]
        if cw.iswithoutcredit is True:
            valid_credit_wallets.append(cw)
        else:
            available = cw.total_credit - cw.used_credit
            if available > 0:
                valid_credit_wallets.append(cw)
            else:
                unavailable_features.append(f.name)

    if unavailable_features:
        return False, f'{", ".join(unavailable_features)} feature(s) have no credits available.', None, None

    return True, "Feature(s) available.", features, valid_credit_wallets


def check_feature_availability(feature_code_param=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):

            # Resolve feature code
            if feature_code_param is None:
                feature_code = request.data.get('feature_code') or kwargs.get('feature_code')
            else:
                feature_code = (
                    request.data.get(feature_code_param)
                    or kwargs.get(feature_code_param)
                    or feature_code_param
                )

            if not feature_code:
                raise ValidationError({
                    'message': 'Feature code is required.',
                    'isAvailable': False
                })

            company_id = request.user.company_id
            
            has_access, message, features, valid_credit_wallets = check_feature_access(company_id, feature_code)
            
            if not has_access:
                if 'not found' in message or 'Subscription' in message:
                    raise NotFound({'message': message, 'isAvailable': False})
                else:
                    raise DRF_PermissionDenied({'message': message, 'isAvailable': False})

            # Attach for downstream use
            request.feature = features[0] if len(features) == 1 else features
            request.credit_wallet = valid_credit_wallets[0] if len(valid_credit_wallets) == 1 else valid_credit_wallets

            if len(valid_credit_wallets) == 1:
                cw = valid_credit_wallets[0]
                if cw.iscredit or cw.isdayli:
                    request.total_credit = cw.total_credit
                    request.available_credit = cw.total_credit - cw.used_credit

            response = view_func(self, request, *args, **kwargs)
            
            if len(valid_credit_wallets) == 1:
                cw = valid_credit_wallets[0]
                if cw.iscredit or cw.isdayli:
                    if hasattr(response, 'data') and isinstance(response.data, dict):
                        try:
                            response.data['total_credit'] = cw.total_credit
                            response.data['available_credit'] = cw.total_credit - cw.used_credit
                        except Exception:
                            pass
            else:
                if hasattr(response, 'data') and isinstance(response.data, dict):
                    try:
                        credits_info = {}
                        for cw in valid_credit_wallets:
                            if cw.iscredit or cw.isdayli:
                                credits_info[cw.feature.code] = {
                                    'total_credit': cw.total_credit,
                                    'available_credit': cw.total_credit - cw.used_credit
                                }
                        if credits_info:
                            response.data['credits_info'] = credits_info
                    except Exception:
                        pass
                        
            return response

        return wrapper
    return decorator




def check_subscription_and_credits_for_ai(feature_code, usage_code):
    """
    Decorator to check if user has an active subscription and enough credits for AI features.
    
    Args:
        feature_code (str): The feature code to check credits for (e.g., 'AI_CREDITS')
        usage_code (str): The feature usage code to get credit cost (e.g., 'Generate_Job_Description')
    
    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # Check for active subscription
            subscription = Subscription.objects.filter(
                company=request.user.company_id, 
                is_active=True
            ).first()
            
            if not subscription:
                return Response({
                    'success': False,
                    'message': 'Subscription is not active',
                    'issubscription': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get credit wallet for the feature
            try:
                credit_wallet = CreditWallet.objects.get(
                    company=request.user.company_id, 
                    feature__code=feature_code
                )
                feature_usage = FeatureUsage.objects.get(code=usage_code)
                
                # Check available credits
                available_credit = credit_wallet.total_credit - credit_wallet.used_credit
                if available_credit < feature_usage.used_credit:
                    return Response({
                        'success': False,
                        'message': 'Not enough credits',
                        'istopup': True
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except CreditWallet.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'No credit wallet found for {feature_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except FeatureUsage.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Invalid feature usage code: {usage_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If all checks pass, proceed with the view function
            return view_func(self, request, *args, **kwargs)
            
        return _wrapped_view
    return decorator


def deduct_credits_after(feature_code, usage_code):
    """
    Decorator to deduct credits after a successful API call.
    
    Args:
        feature_code (str): The feature code to deduct credits from
        usage_code (str): The feature usage code to determine credit cost
    
    Returns:
        function: Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            response = view_func(self, request, *args, **kwargs)
            
            # Only deduct credits if the request was successful (2xx status code)
            if 200 <= response.status_code < 300:
                try:
                    credit_wallet = CreditWallet.objects.get(
                        company=request.user.company_id,
                        feature__code=feature_code
                    )
                    feature_usage = FeatureUsage.objects.get(code=usage_code)
                    
                    # Update used credits
                    credit_wallet.used_credit += feature_usage.used_credit
                    credit_wallet.save()
                    
                    # Log to credit history
                    CreditHistory.objects.create(
                        credit_wallet=credit_wallet,
                        feature=credit_wallet.feature,
                        feature_usage=feature_usage,
                        credit=feature_usage.used_credit
                    )
                    
                except (CreditWallet.DoesNotExist, FeatureUsage.DoesNotExist):
                    # Log the error but don't fail the request since the main operation succeeded
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(
                        f"Failed to deduct credits for {feature_code} with usage {usage_code}"
                    )
            
            return response
            
        return _wrapped_view
    return decorator

def handle_ai_credits(feature_code, usage_code):
    """
    Decorator to handle AI credit usage including validation and deduction.
    
    Args:
        feature_code (str): The feature code to check credits for (e.g., 'AI_CREDITS')
        usage_code (str): The feature usage code to get credit cost (e.g., 'Generate_Job_Description')
    
    Returns:
        function: Decorated view function that handles credit validation and deduction
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            from settings.models import CreditWallet, FeatureUsage, CreditHistory


            company = None
            # Check if user is authenticated and has a company or job is provided
            if not hasattr(request.user, 'company_id'):
                # Check if job_id is in request data
                job_id = request.data.get('job')
                if job_id:
                    from job.models import Job
                    try:
                        job = Job.objects.get(id=job_id)
                        request.user.company_id = job.company_id
                        company = job.company
                    except (Job.DoesNotExist, ValueError):
                        return Response(
                            {'success': False, 'message': 'Invalid job ID provided'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    return Response(
                        {'success': False, 'message': 'User is not associated with any company'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                company = Company.objects.get(id=request.user.company_id)

            try:
                # Get credit wallet and feature usage in a single transaction
                with transaction.atomic():
                    feature = Feature.objects.get(code=feature_code)
                    credit_wallet = CreditWallet.objects.select_for_update().get(
                        company=company, 
                        feature=feature
                    )
                    feature_usage = FeatureUsage.objects.get(code=usage_code)
                    
                    # Check available credits
                    available_credit = credit_wallet.total_credit - credit_wallet.used_credit
                    if available_credit < feature_usage.used_credit:
                        return Response({
                            'success': False,
                            'message': 'Not enough credits available',
                            'required_credits': feature_usage.used_credit,
                            'available_credits': available_credit
                        }, status=status.HTTP_402_PAYMENT_REQUIRED)
                    
                    # Call the view function
                    response = view_func(self, request, *args, **kwargs)
                    
                    # Only deduct credits if the request was successful
                    if response.status_code == 200:
                        # Update used credits
                        credit_wallet.used_credit += feature_usage.used_credit
                        credit_wallet.save()
                        
                        # Log to credit history
                        CreditHistory.objects.create(
                            company=credit_wallet.company,
                            credit_wallet=credit_wallet,
                            feature=credit_wallet.feature,
                            feature_usage=feature_usage,
                            credit=feature_usage.used_credit
                        )
                    
                    return response

            except Feature.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Feature not found: {feature_code}'
                }, status=status.HTTP_400_BAD_REQUEST)

            except CreditWallet.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'No credit wallet found for feature: {feature_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except FeatureUsage.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Invalid feature usage code: {usage_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in handle_ai_credits: {str(e)}", exc_info=True)
                return Response({
                    'success': False,
                    'message': f'Error processing request: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return _wrapped_view
    return decorator


def handle_career_site_ai_credits(usage_codes):
    """
    Consolidated decorator for career site AI credit usage.
    Supports both API views and background functions.
    Allows balancing even into negative 'minus' values.
    
    Args:
        usage_codes (list): List of feature usage codes to deduct credits for
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            from settings.models import CreditWallet, FeatureUsage, CreditHistory, Feature, Company
            from rest_framework.response import Response
            from django.db import transaction
            import logging
            logger = logging.getLogger(__name__)

            company = None
            request = None
            job_id = None
            
            # 1. Identify Context and Extract Company
            # Try to find a Request object in args
            for arg in args:
                if hasattr(arg, 'user') and hasattr(arg, 'data'):
                    request = arg
                    break
            
            if request:
                # Context: Django REST Framework View
                if hasattr(request.user, 'company_id') and request.user.company_id:
                    try:
                        company = Company.objects.get(id=request.user.company_id)
                    except (Company.DoesNotExist, Exception):
                        pass
                
                if not company:
                    job_id = request.data.get('job')
                    if job_id:
                        from job.models import Job
                        try:
                            job = Job.objects.get(id=job_id)
                            company = job.company
                        except (Job.DoesNotExist, ValueError):
                            pass
            else:
                # Context: Background function / method / direct call
                # Check if it's a method calling 'self' (args[0])
                if len(args) > 0:
                    instance = args[0]
                    if hasattr(instance, 'company') and instance.company:
                        if isinstance(instance.company, Company):
                            company = instance.company
                        else:
                            # Might be an ID or name
                            try:
                                if str(instance.company).isdigit():
                                    company = Company.objects.get(id=instance.company)
                                else:
                                    company = Company.objects.get(name=instance.company)
                            except (Company.DoesNotExist, Exception):
                                pass
                    
                    if not company and hasattr(instance, 'job_id') and instance.job_id:
                        job_id = instance.job_id

                if not company and not job_id:
                    # Try to find job_id in kwargs or positional args
                    job_id = kwargs.get('job_id') or kwargs.get('job')
                    
                    if not job_id:
                        # Look for likely job_id positions based on common function signatures
                        if len(args) >= 2 and 'rjms' in view_func.__name__:
                            if isinstance(args[1], int): job_id = args[1]
                            elif len(args) >= 3 and isinstance(args[2], int): job_id = args[2]
                        elif len(args) >= 3 and 'assessment' in view_func.__name__:
                            if isinstance(args[2], int): job_id = args[2]

                if job_id and not company:
                    from job.models import Job
                    try:
                        job = Job.objects.get(id=job_id)
                        company = job.company
                    except (Job.DoesNotExist, ValueError, Exception):
                        pass

            # Fallback: Check if company was passed directly
            if not company:
                comp_val = kwargs.get('company')
                if isinstance(comp_val, Company):
                    company = comp_val
                elif comp_val:
                    try:
                        if str(comp_val).isdigit():
                            company = Company.objects.get(id=comp_val)
                        else:
                            company = Company.objects.get(name=comp_val)
                    except (Company.DoesNotExist, Exception):
                        pass

            # 2. Call the original function
            # Note: We don't catch exceptions here to let the caller handle errors,
            # but we only deduct credits if it succeeds.
            response = view_func(*args, **kwargs)
            
            # 3. Determine Success and Deduct Credits
            is_success = True
            if hasattr(response, 'status_code'):
                # It's a Response object (View context)
                is_success = 200 <= response.status_code < 300
            elif response is None and 'background' in view_func.__name__:
                # Background tasks often return None on success
                is_success = True
            elif isinstance(response, (dict, list)):
                # Logic functions often return data; check if it's an error dict
                if isinstance(response, dict) and 'error' in response:
                    is_success = False
            
            # Even if AI score is 0, if is_success is true, we deduct credits.
            if is_success and company:
                try:
                    feature = Feature.objects.get(code="AI_CREDITS")
                    usages = FeatureUsage.objects.filter(code__in=usage_codes)
                    
                    if usages.exists():
                        with transaction.atomic():
                            # Fetch or create the wallet (allows negative balance)
                            credit_wallet, created = CreditWallet.objects.select_for_update().get_or_create(
                                company=company, 
                                feature=feature,
                                defaults={'total_credit': 0, 'used_credit': 0}
                            )
                            
                            total_deduction = 0
                            for usage in usages:
                                total_deduction += usage.used_credit
                                
                                # Log history
                                CreditHistory.objects.create(
                                    company=credit_wallet.company,
                                    credit_wallet=credit_wallet,
                                    feature=credit_wallet.feature,
                                    feature_usage=usage,
                                    credit=usage.used_credit
                                )
                            
                            credit_wallet.used_credit += total_deduction
                            credit_wallet.save()
                except Exception as e:
                    logger.error(f"Error deducting AI credits in handle_career_site_ai_credits: {str(e)}")
            
            return response

        return _wrapped_view
    return decorator