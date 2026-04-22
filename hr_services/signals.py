from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactDetails, ScheduleCall


@receiver(post_save, sender=ContactDetails)
def send_contact_email(sender, instance, created, **kwargs):
    if created:
        # Send notification email to admin
        try:
            subject = "New Contact Request"
            message = (
                f"Name: {instance.full_name}\n"
                f"Email: {instance.email}\n"
                f"Mobile: {instance.mobile_number}\n"
                f"Company: {instance.company_name}\n"
                f"Platform: {instance.platform}\n\n"
                f"Message:\n{instance.message}"
            )
            admin_recipient = getattr(settings, 'EMAIL_HOST_USER', None)
            if admin_recipient:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[admin_recipient],
                    fail_silently=False,
                )
        except Exception as e:
            print(e, "error sending admin email")

        # Send acknowledgment email to user
        try:
            ack_subject = "Thanks for contacting Edjobster"
            ack_message = (
                f"Hi {instance.full_name},\n\n"
                "Thanks for reaching out. Our team will get back to you soon.\n\n"
                "Regards,\nEdjobster Team"
            )
            if instance.email:
                send_mail(
                    subject=ack_subject,
                    message=ack_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[instance.email],
                    fail_silently=False,
                )
        except Exception as e:
            print(e, "error sending acknowledgment email")


@receiver(post_save, sender=ScheduleCall)
def send_contact_email(sender, instance, created, **kwargs):
    if created:
        # Send notification email to admin
        try:
            subject = "New Schedule Call Request"
            message = (
                f"Name: {instance.name}\n"
                f"Email: {instance.email}\n"
                f"Mobile: {instance.mobile_number}\n"
                f"Company: {instance.company}\n"
                f"Platform: {instance.platform}\n\n"
                f"Date: {instance.date}\n"
                f"Time: {instance.time}\n\n"
            )
            admin_recipient = getattr(settings, 'EMAIL_HOST_USER', None)
            if admin_recipient:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[admin_recipient],
                    fail_silently=False,
                )
        except Exception as e:
            print(e, "error sending admin email")

    try:
            ack_subject = "Thanks for contacting Edjobster"
            ack_message = (
                f"Hi {instance.name},\n\n"
                "Thanks for reaching out. Our team will get back to you soon.\n\n"
                "Regards,\nEdjobster Team"
            )
            if instance.email:
                send_mail(
                    subject=ack_subject,
                    message=ack_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[instance.email],
                    fail_silently=False,
                )
    except Exception as e:
        print(e, "error sending acknowledgment email")