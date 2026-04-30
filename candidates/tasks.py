from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from account.models import Account
from .models import Tasks, Events, Call, Notification, EmailSettings
from django.core.mail import send_mail, get_connection
from django.conf import settings

@shared_task
def check_reminders_task():
    now = timezone.localtime(timezone.now())
    current_date = now.date()
    current_hour = now.hour
    current_minute = now.minute

    # 1. Process Tasks
    tasks = Tasks.objects.filter(
        completed=False,
        task_alert__isnull=False,
        when_date=current_date,
        when_time__hour=current_hour,
        when_time__minute=current_minute
    )
    for task in tasks:
        send_reminder(task, task.owner, "Task Reminder", f"Reminder for task: {task.subject}", task.task_alert)

    # 2. Process Events
    # Events from_date is a DateTimeField
    events = Events.objects.filter(
        completed=False,
        reminder_alert_type__isnull=False,
        from_date__year=now.year,
        from_date__month=now.month,
        from_date__day=now.day,
        from_date__hour=now.hour,
        from_date__minute=now.minute
    )
    for event in events:
        send_reminder(event, event.host, "Event Reminder", f"Reminder for event: {event.event_name}", event.reminder_alert_type)

    # 3. Process Calls
    calls = Call.objects.filter(
        completed=False,
        reminder_alert_type__isnull=False,
        call_start_time__isnull=False
    )
    for call in calls:
        offset = get_call_offset(call.reminders)
        if offset:
            reminder_time = call.call_start_time - timedelta(minutes=offset)
            if (reminder_time.year == now.year and 
                reminder_time.month == now.month and 
                reminder_time.day == now.day and 
                reminder_time.hour == now.hour and 
                reminder_time.minute == now.minute):
                send_reminder(call, call.owner, "Call Reminder", f"Reminder for call: {call.subject}", call.reminder_alert_type)
        else:
            # If no offset, remind at start time
            if (call.call_start_time.year == now.year and 
                call.call_start_time.month == now.month and 
                call.call_start_time.day == now.day and 
                call.call_start_time.hour == now.hour and 
                call.call_start_time.minute == now.minute):
                send_reminder(call, call.owner, "Call Reminder", f"Reminder for call: {call.subject}", call.reminder_alert_type)

def get_call_offset(reminder_choice):
    mapping = {
        '5_MIN': 5,
        '10_MIN': 10,
        '15_MIN': 15,
        '30_MIN': 30,
        '1_HOUR': 60,
        '2_HOURS': 120,
        '1_Day': 1440,
        '2_Days': 2880,
    }
    return mapping.get(reminder_choice)

def send_reminder(obj, user, title, message, alert_type):
    if not user:
        return
    
    company_id = getattr(user, 'company_id', None)
    if not company_id:
        return
        
    from account.models import Company
    company = Company.objects.filter(id=company_id).first()
    if not company:
        return
    
    if alert_type == 'POP-UP':
        # Avoid creating duplicate notifications for the same object in the same minute
        if not Notification.objects.filter(
            company=company, 
            todo_type=obj.todo_type, 
            related_id=obj.id,
            created_at__gte=timezone.now() - timedelta(seconds=59)
        ).exists():
            Notification.objects.create(
                company=company,
                title=title,
                message=message,
                todo_type=obj.todo_type,
                related_id=obj.id
            )
            
    # Send email if alert_type is explicitly EMAIL, or if the email_notification flag is true
    force_email = getattr(obj, 'email_notification', False)
    if alert_type == 'EMAIL' or force_email:
        send_reminder_email(user, title, message, company)

def send_reminder_email(user, title, message, company=None):
    if not user.email:
        return
    
    email_settings = EmailSettings.objects.filter(company_id=user.company_id).order_by('-created_at').first()
    
    if not email_settings:
        email_settings = EmailSettings.objects.filter(user_id=user).order_by('-created_at').first()
    
    try:
        if email_settings:
            connection = get_connection(
                backend=email_settings.email_backend,
                host=email_settings.email_host,
                port=email_settings.email_port,
                username=email_settings.sender_mail,
                password=email_settings.auth_password,
                use_ssl=email_settings.email_ssl,
                use_tls=email_settings.email_tls
            )
            send_mail(
                title,
                message,
                email_settings.sender_mail,
                [user.email],
                connection=connection,
                fail_silently=False
            )
        else:
            if not company and user.company_id:
                from account.models import Company
                company = Company.objects.filter(id=user.company_id).first()
                
            from_email = company.email if company and company.email else getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)
            send_mail(
                title,
                message,
                from_email,
                [user.email],
                fail_silently=False
            )
    except Exception as e:
        print(f"Error sending reminder email for user {user.id if hasattr(user, 'id') else getattr(user, 'account_id', 'unknown')}: {e}")
