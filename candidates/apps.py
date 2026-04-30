from django.apps import AppConfig
from django.core.mail import EmailMessage

original_send = EmailMessage.send

def logged_email_send(self, fail_silently=False):
    # Call the original send method
    result = original_send(self, fail_silently=fail_silently)
    
    # If the email was successfully sent, log it to the database
    if result:
        try:
            from candidates.models import Mail
            from account.models import Account
            
            # Try to match the from_email to an existing account
            sender_account = Account.objects.filter(email=self.from_email).first()
            
            Mail.objects.create(
                sender=sender_account,
                from_email=self.from_email,
                receiver=list(self.to) if self.to else [],
                subject=self.subject,
                body=self.body
            )
        except Exception as e:
            print(f"Failed to log email to DB: {e}")
            
    return result

class CandidatesConfig(AppConfig):
    name = 'candidates'

    def ready(self):
        # Import signals to register handlers
        from . import signals  # noqa: F401
        
        # Monkey patch EmailMessage.send to log all emails to the DB globally
        if EmailMessage.send != logged_email_send:
            EmailMessage.send = logged_email_send
