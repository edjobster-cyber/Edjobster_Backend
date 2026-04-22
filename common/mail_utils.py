from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import os
from django.template.loader import render_to_string
import threading
from common.encoder import encode
from django.core.mail import get_connection
import string
from candidates.models import Mail, EmailSettings
from settings.decorators import check_feature_availability, check_feature_access

from .format_email_body import format_email_body, format_email_body_bulke_mailSend, format_unsubscribe_link
from settings.models import UnsubscribeEmailToken
import mimetypes

# APP_URL from settings (env-driven)
BASE_URL_FRONTEND = settings.APP_URL
BASE_URL_JOB_FRONTEND = settings.JOB_URL

URL_RESET_PSWD = f"{BASE_URL_FRONTEND}/login?resetpassword=true&token="
URL_JOB_PSWS = f"{BASE_URL_JOB_FRONTEND}/reset-password?token="
URL_EMAIL_VERIFY = f"{BASE_URL_FRONTEND}/auth/activate/"
URL_EMAIL_ACTIVATE = f"{BASE_URL_FRONTEND}/auth/verify/"

class ResetPasswordMailer(threading.Thread):
    def __init__(self, token,role):
        threading.Thread.__init__(self)
        self.token = token
        self.role = role

    def run(self):
        print("===========send mail=========")
        token = self.token
        name = token.user.first_name + " " + token.user.last_name
        if self.role == "C":
            link = URL_JOB_PSWS + str(encode(token.id))
        else:
            link = URL_RESET_PSWD + str(encode(token.id))
        data = {"name": name, "link": link}
        msg_html = render_to_string("password-reset-mail.html", {"data": data})

        send_mail(
            "Edjobster| Password Reset",
            "Rest your password",
            "faimsoft@gmail.com",
            [self.token.user.email],
            html_message=msg_html,
            fail_silently=False,
        )


class EmailVerificationMailer(threading.Thread):
    def __init__(self, token, email_data, user_email, user_password):
        threading.Thread.__init__(self)
        self.token = token
        self.email_data = email_data
        self.user_password = user_password

    def run(self):
        print("===========send mail=========")
        token = self.token
        user = token.user
        name = user.first_name + " " + user.last_name
        link = URL_EMAIL_VERIFY + str(token.id)
        # data = {"name": name, "link": link}
        user_email = user.email
        user_role = user.role
        
        data = {
            "name": name,
            "link": link,
            "user_email": user_email,
            "user_role": user_role,
            "user_password": self.user_password
        }
        msg_html = render_to_string("email-verification.html", {"data": data})
        # If per-user email settings are provided, use them; otherwise fall back to Django defaults
        if getattr(self, 'email_data', None):
            connection = get_connection(
                backend=self.email_data.email_backend,
                host=self.email_data.email_host,
                port=self.email_data.email_port,
                username=self.email_data.sender_mail,
                password=self.email_data.auth_password,
                use_ssl=self.email_data.email_ssl,
                use_tls=self.email_data.email_tls
            )

            send_mail(
                "Edjobster| Verify Account",
                "Verify Account",
                from_email=self.email_data.sender_mail,
                recipient_list=[user.email],
                html_message=msg_html,
                fail_silently=False,
                connection=connection,
            )
        else:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)
            send_mail(
                "Edjobster| Verify Account",
                "Verify Account",
                from_email=from_email,
                recipient_list=[user.email],
                html_message=msg_html,
                fail_silently=False,
            )


class EmailActivationMailer(threading.Thread):
    def __init__(self, token):
        threading.Thread.__init__(self)
        self.token = token

    def run(self):
        print("===========send mail=========")
        token = self.token
        name = token.user.first_name + " " + token.user.last_name
        link = URL_EMAIL_ACTIVATE + encode(token.id)
        data = {"name": name, "link": link}

        msg_html = render_to_string("account-activate.html", {"data": data})

        send_mail(
            "Edjobster| Activate Account",
            "Activate Account",
            "faimsoft@gmail.com",
            [self.token.user.email],
            html_message=msg_html,
            fail_silently=False,
        )

class CandidateMailer(threading.Thread):
    def __init__(self, account, data, emails, email_data, candidate, placeholders, job, interview=None, assessment=None):
        threading.Thread.__init__(self)
        self.account = account
        self.body = data.get('body',None)
        self.subject = data.get('subject',None)
        self.auth_password = email_data.auth_password
        self.emails = emails
        self.sender_mail = email_data.sender_mail
        self.email_backend = email_data.email_backend
        self.email_host = email_data.email_host
        self.email_port = email_data.email_port
        self.email_ssl = email_data.email_ssl
        self.email_tls = email_data.email_tls
        self.candidate = candidate
        self.placeholders = placeholders
        self.job = job
        self.interview = interview
        self.assessment = assessment

    def run(self):
        print("===========send mail=========")
        emails = self.emails
        sender_mail = self.sender_mail
        auth_password = self.auth_password
        print("self.body",self.body)
        print("self.subject",self.subject)
        print("self.candidate",self.candidate)
        print("self.job",self.job)
        print("self.account",self.account)
        # Format body using format_email_body_bulke_mailSend (handles ${...} placeholders)
        formatted_body = format_email_body_bulke_mailSend(
            body=self.body if self.body is not None else "",
            candidate=self.candidate,
            job=self.job,
            account=self.account,
            interview=self.interview,
            assessment=self.assessment,
            placeholders=self.placeholders,
        )

        formatted_subject = format_email_body_bulke_mailSend(
            body=self.subject if self.subject is not None else "",
            candidate=self.candidate,
            job=self.job,
            account=self.account,
            interview=self.interview,
            assessment=self.assessment,
            placeholders=self.placeholders,
        )

        # Format subject the same way
        # formatted_subject = format_email_body_bulke_mailSend(
        #     body=self.subject if self.subject is not None else "",
        #     candidate=self.candidate,
        #     job=self.job,
        #     account=self.account,
        # )

        msg_html = render_to_string("candidate-mail.html", {"formatted_body": formatted_body})
        
        mail_instance = Mail()
        mail_instance.sender = self.account
        mail_instance.receiver = emails
        mail_instance.subject = formatted_subject
        mail_instance.body = formatted_body
        mail_instance.save()
        
        connection = get_connection(
            backend=self.email_backend,
            host=self.email_host,
            port=self.email_port,
            username=sender_mail,
            password=auth_password,
            use_ssl=self.email_ssl,
            use_tls=self.email_tls
        )
        print("connection",connection)  
        print("formatted_subject",formatted_subject)
        print("sender_mail",sender_mail)
        print("emails",emails)
        print("msg_html",msg_html)

        send_mail(
            subject=formatted_subject,
            message="Candidate Mail",
            from_email=sender_mail,
            recipient_list=emails,
            html_message=msg_html,
            fail_silently=False,
            connection=connection,
        )
        
class CandidateCreateMailer(threading.Thread):
    def __init__(self, emails, email_Settings, message, candidate=None, job=None, account=None):
        threading.Thread.__init__(self)
        self.emails = emails
        self.email_Settings = email_Settings
        self.message = message
        self.candidate = candidate
        self.job = job
        self.account = account
    def run(self):
        # Manual check for feature availability
        if self.account and hasattr(self.account, 'company_id'):
            has_access, _, _, _ = check_feature_access(self.account.company_id, "auto_response_rules")
            if not has_access:
                print(f"Feature auto_response_rules not available for company {self.account.company_id}")
                return
        
        try:

            print(f"=========== Sending email to {self.emails} =========")
            
            # Prepare context data for the template
            context = {
                "full_name": f"{self.candidate.webform_candidate_data['Personal Details']['first_name']} {self.candidate.webform_candidate_data['Personal Details']['last_name']}",
                "job_title": f"{self.job.dynamic_job_data['Create Job']['title']}",
                "email": f"{self.candidate.webform_candidate_data['Personal Details']['email']}",
                "mobile": f"{self.candidate.webform_candidate_data['Personal Details']['mobile']}",
                
                'candidate': self.candidate,
                'job': self.job,
                'account': self.account,
                'message': self.message,
                'application_date': getattr(self.candidate, 'created_at', None) if self.candidate else None,
                'application_id': getattr(self.candidate, 'id', '') if self.candidate else ''
            }
            # for i in self.job:
            # Render the HTML template with context
            html_message = render_to_string('edjobster_application_success.html', context)
            
            # Set up email connection
            connection = get_connection(
                backend=self.email_Settings.email_backend,
                host=self.email_Settings.email_host,
                port=self.email_Settings.email_port,
                username=self.email_Settings.sender_mail,
                password=self.email_Settings.auth_password,
                use_ssl=self.email_Settings.email_ssl,
                use_tls=self.email_Settings.email_tls
            )

            # Create email message with HTML content
            email = EmailMessage(
                subject="Application Submitted Successfully - EdJobster",
                body=html_message,
                from_email=self.email_Settings.sender_mail,
                to=[self.emails] if isinstance(self.emails, str) else self.emails,
                connection=connection,
            )
            email.content_subtype = 'html'  # Set content type to HTML
            
            # Send email
            email.send(fail_silently=False)
            print(f"Email sent successfully to {self.emails}")
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            # Consider logging the error to a file or error tracking system
            # logger.error(f"Failed to send email: {str(e)}")
            raise
        
class CandidateBulkMailer(threading.Thread):
    def __init__(self,emails, email_tamplate, email_Settings,message, candidate=None,job=None,account=None,interview=None,assessment=None,contact=None,unsubscribe_link=None, attachment_content=None, attachment_name=None, attachment_category=None, attachment_subcategory=None):
        threading.Thread.__init__(self)
        self.emails = emails
        self.email_tamplate = email_tamplate
        self.email_Settings = email_Settings
        self.candidate = candidate
        self.job = job
        self.account = account
        self.interview = interview
        self.assessment = assessment
        self.contact = contact
        self.message = message
        self.unsubscribe_link = unsubscribe_link
        self.attachment_content = attachment_content
        self.attachment_name = attachment_name
        self.attachment_category = attachment_category
        self.attachment_subcategory = attachment_subcategory
        
    def run(self):
        print("===========send mail=========")
       

        formatted_body = format_email_body_bulke_mailSend(
            body=self.email_tamplate['message'],
            interview=self.interview,
            candidate=self.candidate,
            job=self.job,
            account=self.account,
            assessment=self.assessment,
            contact=self.contact,
            placeholders=self.message if isinstance(self.message, dict) else None
        )
        formatted_subject = format_email_body_bulke_mailSend(
            body=self.email_tamplate['subject'],
            interview=self.interview,
            candidate=self.candidate,
            job=self.job,
            account=self.account,
            assessment=self.assessment,
            contact=self.contact,
            placeholders=self.message if isinstance(self.message, dict) else None
        )
        if self.unsubscribe_link:
            token = UnsubscribeEmailToken.objects.create(candidate=self.candidate)
            unsubscribe_link = format_unsubscribe_link(unsubscribe_link=self.unsubscribe_link, token=token.token)
        else:
            unsubscribe_link=None
        msg_html = render_to_string("candidate-mail.html", {"formatted_body": formatted_body,"unsubscribe_link":unsubscribe_link})  


        connection = get_connection(
            backend=self.email_Settings.email_backend,
            host=self.email_Settings.email_host,
            port=self.email_Settings.email_port,
            username=self.email_Settings.sender_mail,
            password=self.email_Settings.auth_password,
            use_ssl=self.email_Settings.email_ssl,
            use_tls=self.email_Settings.email_tls
        )

        # Prepare recipient list
        recipient_list = [self.emails] if isinstance(self.emails, str) else self.emails

        # Create EmailMessage for attachment support
        email = EmailMessage(
            subject=formatted_subject,
            body=msg_html,
            from_email=self.email_Settings.sender_mail,
            to=recipient_list,
            connection=connection,
        )
        
        # Set content type to HTML
        email.content_subtype = "html"

        # Add attachment if provided
        if self.attachment_content and self.attachment_name:
            try:
                print(f"Attachment details:")
                print(f"- Name: {self.attachment_name}")
                print(f"- Size: {len(self.attachment_content)} bytes")
                print(f"- Category: {self.attachment_category}")
                print(f"- Subcategory: {self.attachment_subcategory}")
                
                # Ensure we have content
                if len(self.attachment_content) == 0:
                    print("Warning: Attachment content is empty")
                else:
                    # Get mime type based on file extension
                    mime_type, _ = mimetypes.guess_type(self.attachment_name)
                    if mime_type is None:
                        # Try to determine mime type based on file extension
                        file_ext = os.path.splitext(self.attachment_name)[1].lower()
                        mime_map = {
                            '.pdf': 'application/pdf',
                            '.doc': 'application/msword',
                            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            '.txt': 'text/plain',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.png': 'image/png',
                            '.gif': 'image/gif',
                            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            '.xls': 'application/vnd.ms-excel',
                            '.ppt': 'application/vnd.ms-powerpoint',
                            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                        }
                        mime_type = mime_map.get(file_ext, 'application/octet-stream')
                    
                    print(f"- MIME type: {mime_type}")
                    
                    # Add attachment to email
                    email.attach(self.attachment_name, self.attachment_content, mime_type)
                    print(f"Attachment successfully added to email")
                
            except Exception as e:
                print(f"Error adding attachment: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print("No attachment provided")
        
        # Send the email
        try:
            email.send(fail_silently=False)
            print("Email sent successfully")
            if self.attachment_content:
                print("Email sent with attachment")
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            import traceback
            traceback.print_exc()


class ApiIntegrationRequestMailer(threading.Thread):
    """Email notification for new API integration request to superuser"""
    
    def __init__(self, api_request, superuser_emails):
        threading.Thread.__init__(self)
        self.api_request = api_request
        self.superuser_emails = superuser_emails
    
    def run(self):
        print("=========== Sending API Integration Request Email =========")
        
        try:
            platform = self.api_request.platform or "Not specified"
            
            # Handle ai_tools as array
            ai_tools = self.api_request.ai_tools
            if isinstance(ai_tools, list) and ai_tools:
                ai_tools_str = ", ".join(ai_tools)
            elif ai_tools:
                ai_tools_str = str(ai_tools)
            else:
                ai_tools_str = "Not specified"
            
            note = self.api_request.note or "No notes provided"
            created_at = self.api_request.created.strftime('%Y-%m-%d %H:%M:%S')
            
            subject = "New API Integration Request - Edjobster"
            
            message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2c3e50;">New API Integration Request</h2>
                <p>A new API integration request has been submitted with the following details:</p>
                
                <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Platform:</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{platform}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">AI Tools:</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{ai_tools_str}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Note:</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{note}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Request Time:</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{created_at}</td>
                    </tr>
                </table>
                
                <p style="margin-top: 20px;">Please review this request in the admin panel.</p>
                
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #dee2e6;">
                <p style="font-size: 12px; color: #6c757d;">
                    This is an automated message from Edjobster.<br>
                    Request ID: {self.api_request.id}
                </p>
            </body>
            </html>
            """
            
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', 'noreply@edjobster.com')
            
            send_mail(
                subject=subject,
                message="New API Integration Request",
                from_email=from_email,
                recipient_list=self.superuser_emails,
                html_message=message,
                fail_silently=False,
            )
            print(f"API Integration Request email sent successfully to superusers: {self.superuser_emails}")
            
        except Exception as e:
            print(f"Error sending API Integration Request email: {str(e)}")
            import traceback
            traceback.print_exc()