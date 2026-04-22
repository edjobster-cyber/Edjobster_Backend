from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import ToolRequest

User = get_user_model()


@receiver(post_save, sender=ToolRequest)
def send_tool_request_email_to_superuser(sender, instance, created, **kwargs):
    """
    Send email notification to superuser when a new tool request is created
    """
    if created:
        try:
            # Get all superusers
            superusers = User.objects.filter(is_superuser=True, is_active=True)
            
            if not superusers.exists():
                print("No active superusers found to send notification")
                return
            
            # Prepare email content
            subject = f"New Tool Request: {instance.tool_name}"
            
            message = f"""
A new tool request has been submitted:

Tool Name: {instance.tool_name}
Category: {instance.category}
Description: {instance.description}
Use Case: {instance.use_case or 'Not specified'}
Requested By: {instance.requested_by.username} ({instance.requested_by.email})
Requested At: {instance.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Please review this request in the admin panel.
"""
            
            # Send email to all superusers
            recipient_list = [superuser.email for superuser in superusers if superuser.email]
            
            if recipient_list:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'EMAIL_HOST_USER', None),
                    recipient_list=recipient_list,
                    fail_silently=False,
                )
                print(f"Tool request email sent to superusers: {recipient_list}")
            else:
                print("No superuser email addresses found")
                
        except Exception as e:
            print(f"Error sending tool request email: {e}")
