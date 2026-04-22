from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from settings.models import Subscription, CreditWallet, CreditHistory
from django.db.models import F
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def check_subscription_and_credits(feature_code):
    """
    Decorator factory to check if user has an active subscription and enough credits.
    
    Args:
        feature_code (str): The feature code to check credits for (e.g., 'JOB_POST')
        
    Returns:
        function: Decorator function
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            # For class-based views, self is the first argument
            # For function-based views, request is the first argument
            if len(args) > 0 and hasattr(args[0], 'request'):
                # Class-based view
                self = args[0]
                request = args[0].request
                args = args[1:]
            else:
                # Function-based view
                self = None
                request = args[0]
            # Check for active subscription
            subscription = Subscription.objects.filter(
                company=request.user.company_id, 
                is_active=True
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'message': 'Subscription is not active',
                    'issubscription': True
                }, status.HTTP_400_BAD_REQUEST
                
            # Check credits
            try:
                credit_wallet = CreditWallet.objects.get(
                    company=request.user.company_id, 
                    feature__code=feature_code
                )
                available_credit = credit_wallet.total_credit - credit_wallet.used_credit
                if available_credit <= 0:  # Changed from >= 1000 to <= 0
                    print("................")
                    return {
                        'success': False,
                        'message': 'Not enough credits',
                        'istopup': True
                    }, status.HTTP_400_BAD_REQUEST
                print("123")
            except CreditWallet.DoesNotExist:
                return {
                    'success': False,
                    'message': 'No credit wallet found for this feature',
                    'istopup': True
                }, status.HTTP_400_BAD_REQUEST
            
            # If all checks pass, proceed with the view function
            # Check if the view function is a bound method (class-based view)
            if hasattr(view_func, '__self__') and view_func.__self__ is not None:
                return view_func(request, *args, **kwargs)
            # For function-based views or unbound methods
            elif self is not None and hasattr(self, 'get'):
                return view_func(self, request, *args, **kwargs)
            else:
                return view_func(request, *args, **kwargs)
            
        return _wrapped_view
    return decorator


def deduct_credit(company, feature_code):
    """
    Deducts a job posting credit from the company's wallet.
    
    Args:
        company: The company object to deduct credits from
        feature_code: The feature code to deduct credits for
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        print(f"Debug - Looking for credit wallet. Company: {company if company else 'None'}, Feature: {feature_code}")
        credit_wallet = CreditWallet.objects.get(
            company=company, 
            feature__code=feature_code
        )
        print(f"Debug - Found wallet. Current used_credit: {credit_wallet.used_credit}")
        
        credit_wallet.used_credit = F('used_credit') + 1
        credit_wallet.save()
        
        # print(f"Debug - After update. New used_credit: {credit_wallet.used_credit}")
        
        # Fixed code
        CreditHistory.objects.create(
            company=credit_wallet.company,  # Use the company from the credit wallet
            credit_wallet=credit_wallet,
            feature=credit_wallet.feature,
            credit=1
        )
        print("Debug - Credit history created")
        return True, "Credit deducted successfully"
    except CreditWallet.DoesNotExist:
        print(f"Debug - CreditWallet not found for company {company if company else 'None'} and feature {feature_code}")
        return False, "Credit wallet not found for this feature"
    except Exception as e:
        print(f"Debug - Error in deduct_job_credit: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Error deducting credit: {str(e)}"


def deduct_credit_decorator(feature_code):
    """
    Decorator factory to handle credit deduction for different features.
    
    Args:
        feature_code (str): The feature code to check credits for (e.g., 'JOB_POST')
        
    Returns:
        function: Decorator function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            # Get company before calling the view function
            request = self_or_request if hasattr(self_or_request, 'user') else args[0] if args and hasattr(args[0], 'user') else None
            company = None
            
            # if request and hasattr(request, 'user') and hasattr(request.user, 'company_id'):
            #     company = request.user.company_id
            # elif 'company' in kwargs:
            #     company = kwargs['company']
            # elif args and hasattr(args[0], 'company_id'):
            #     company = args[0].company_id
            
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
                company = request.user.company_id


            print(f"Debug - Before view function - Company: {company if company else 'None'}, Feature: {feature_code}")
            
            # Call the original function
            response = view_func(self_or_request, *args, **kwargs)
            
            # Only proceed with deduction if we have a company and the view was successful
            is_success = False
            if company:
                if isinstance(response, dict) and response.get('code') == 200:
                    is_success = True
                elif isinstance(response, tuple) and response[1] == 200:
                    is_success = True
                elif hasattr(response, 'status_code') and response.status_code == 200:
                    is_success = True
            
            if is_success:
                print("Debug - Before deduct_credit")
                success, message = deduct_credit(company, feature_code)
                print(f"Debug - After deduct_credit. Success: {success}, Message: {message}")
                if not success:
                    print(f"Warning: {message}")
            
            return response
        return wrapper
    return decorator


def send_credit_limit_email(company, feature):
    """
    Send email notifications for credit limit warnings
    """
    try:
        # Get company admin users
        from account.models import Account
        admin_users = Account.objects.filter(company=company, role='A')
        credit_wallet = CreditWallet.objects.get(company=company, feature__code=feature)
        
        if not admin_users.exists():
            print(f"No admin users found for company {company.name}")
            return

        # Prepare email context
        context = {
            'company_name': company.name,
            'feature_name': feature.name,
            'available_credit': credit_wallet.total_credit - credit_wallet.used_credit,
            'total_credit': credit_wallet.total_credit,
            'usage_percentage': round((credit_wallet.total_credit - credit_wallet.used_credit) / credit_wallet.total_credit * 100, 2) if credit_wallet.total_credit > 0 else 0,
        }

        # Choose email template based on notification type
        if credit_wallet.total_credit - credit_wallet.used_credit <= 0:
            subject = f"Credit Limit Reached - {feature.name}"
            template_name = 'credit_limit_reached.html'
        # else:  # low_credit
        #     subject = f"Low Credit Warning - {feature.name}"
        #     template_name = 'low_credit_warning.html'

        # Render HTML email
        html_message = render_to_string(template_name, context)

        # Send email to all admin users
        recipient_list = [admin.email for admin in admin_users if admin.email]
        
        if recipient_list:
            send_mail(
                subject=subject,
                message=f"Credit notification for {feature.name}",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@edjobster.com'),
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            print(f"Credit limit email sent to {recipient_list} for {company.name} - {feature.name}")
        else:
            print(f"No email addresses found for admin users of {company.name}")

    except Exception as e:
        print(f"Error sending credit limit email: {str(e)}")
        import traceback
        traceback.print_exc()


def credit_limit_email_notifier(feature_code):
    """
    Decorator factory to send email notifications when credit limit is reached or credits are below 10%.
    
    This decorator checks credit usage after the view function executes successfully and sends
    email notifications to company admins if:
    1. Credits are completely exhausted (0 available)
    2. Available credits are 10% or less of total credits
    
    Args:
        feature_code (str): The feature code to monitor credits for (e.g., 'JOB_POST')
        
    Returns:
        function: Decorator function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self_or_request, *args, **kwargs):
            # Execute the original view function first
            response = view_func(self_or_request, *args, **kwargs)
            
            # Extract request object - for DRF views, it's the first arg after self
            if hasattr(self_or_request, 'user'):  # Function-based view
                request = self_or_request
            else:  # Class-based view method
                request = args[0] if args else None
            
            if not request:
                return response

            # Only proceed with credit check if the view was successful
            # is_success = False
            # if isinstance(response, dict) and response.get('code') == 200:
            #     is_success = True
            # elif isinstance(response, tuple) and response[1] == 200:
            #     is_success = True
            # elif hasattr(response, 'status_code') and response.status_code == 200:
            #     is_success = True
            
            # if not is_success:
            #     return response

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
                        None
                        # return Response(
                        #     {'success': False, 'message': 'Invalid job ID provided'},
                        #     status=status.HTTP_400_BAD_REQUEST
                        # )
                # else:
                    # return Response(
                    #     {'success': False, 'message': 'User is not associated with any company'},
                    #     status=status.HTTP_400_BAD_REQUEST
                    # )
            else:
                company = request.user.company_id

            try:
                # Get credit wallet for the feature
                credit_wallet = CreditWallet.objects.select_related('feature', 'company').get(
                    company=company,
                    feature__code=feature_code
                )

                available_credit = credit_wallet.total_credit - credit_wallet.used_credit
                total_credit = credit_wallet.total_credit

                # Skip if total_credit is 0 or negative
                if total_credit <= 0:
                    return response

                # Calculate credit usage percentage
                usage_percentage = (total_credit - available_credit) / total_credit * 100

                # Check if credits are exhausted (0 available)
                if available_credit <= 0:
                    # Send credit limit reached email
                    send_credit_limit_email(
                        company=credit_wallet.company,
                        feature=credit_wallet.feature
                    )

                # Check if credits are 10% or less remaining
                elif available_credit <= total_credit * 0.1:
                    # Send low credit warning email
                    send_credit_limit_email(
                        company=credit_wallet.company,
                        feature=credit_wallet.feature
                    )

            except CreditWallet.DoesNotExist:
                # No credit wallet found for this feature, skip notification
                pass
            except Exception as e:
                print(f"Error in credit_limit_email_notifier: {str(e)}")
                import traceback
                traceback.print_exc()

            return response
        return wrapper
    return decorator


# Usage Example:
# 
# from job.decorators import credit_limit_email_notifier
#
# @credit_limit_email_notifier('JOB_POST')
# def post_job_view(request):
#     # Your view logic here
#     # After successful execution, credit limit will be checked
#     # and email will be sent if credits are <= 0 or <= 10% remaining
#     pass
#
# @credit_limit_email_notifier('candidate_apply')
# class CandidateApplicationView(APIView):
#     def post(self, request):
#         # Your view logic here
#         # Credit limit check happens after successful post
#         pass