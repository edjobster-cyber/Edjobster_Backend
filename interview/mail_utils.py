from django.core.mail import send_mail
from django.template.loader import render_to_string
import threading
import string
from candidates.models import Mail
from django.core.mail import get_connection


class InterviewMailer(threading.Thread):
    def __init__(self, account, interview, email_data, candidate, placeholders):
        threading.Thread.__init__(self)
        self.account = account
        self.interview = interview
        self.email_data = email_data
        self.candidate = candidate
        self.placeholders = placeholders
        self.subject = interview.email_sub
        self.body = interview.email_msg
        self.emails = [candidate.email]
        self.sender_mail = email_data.sender_mail
        self.auth_password = email_data.auth_password
        self.email_backend = email_data.email_backend
        self.email_host = email_data.email_host
        self.email_port = email_data.email_port
        self.email_tls = email_data.email_tls
        self.email_ssl = email_data.email_ssl

    def run(self):
        print("===========send mail=========")
        subject_template = string.Template(self.subject)
        formatted_subject = subject_template.safe_substitute(self.placeholders)
        
        template = string.Template(self.body)
        formatted_body = template.safe_substitute(self.placeholders)
        msg_html = render_to_string("interview-mail.html", {"formatted_body": formatted_body})
        
        mail_instance = Mail()
        mail_instance.sender = self.account
        mail_instance.receiver = self.emails
        mail_instance.subject = formatted_subject
        mail_instance.body = formatted_body
        mail_instance.save()
        
        self.interview.email_msg = formatted_body
        self.interview.email_sub = formatted_subject
        self.interview.save()
        
        
        connection = get_connection(
            backend=self.email_backend,
            host=self.email_host,
            port=self.email_port,
            username=self.sender_mail,
            password=self.auth_password,
            use_ssl=self.email_ssl,
            use_tls=self.email_tls
        )

        send_mail(
            subject=formatted_subject,
            message="Interview Mail",
            from_email=self.sender_mail,
            recipient_list=self.emails,
            html_message=msg_html,
            fail_silently=False,
            connection=connection,
        )