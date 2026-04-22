from django.apps import AppConfig
import json

class InterviewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interview'

    def ready(self):
        # -----------------------------------------
        # 1️⃣  Import signals
        # -----------------------------------------
        import interview.signals  # 👈 ensures signal handlers are registered
        
        # Create Celery Beat schedules using a safer approach
        self._create_celery_beat_schedules()
    
    def _create_celery_beat_schedules(self):
        """Create Celery Beat schedules safely"""
        try:
            from django_celery_beat.models import IntervalSchedule, PeriodicTask
            
            # Create 1-minute schedule for interview reminders
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=1, 
                period=IntervalSchedule.MINUTES,
                defaults={'every': 1, 'period': IntervalSchedule.MINUTES}
            )
            PeriodicTask.objects.get_or_create(
                interval=schedule,
                name='Send Interview Reminders',
                task='interview.tasks.send_interview_reminders',
                defaults={'args': json.dumps([])},
            )
            
            # Create 5-minute schedule for auto-accept task
            # auto_accept_schedule, created = IntervalSchedule.objects.get_or_create(
            #     every=5, 
            #     period=IntervalSchedule.MINUTES,
            #     defaults={'every': 5, 'period': IntervalSchedule.MINUTES}
            # )
            # PeriodicTask.objects.get_or_create(
            #     interval=auto_accept_schedule,
            #     name='Auto Accept Interviews One Hour Before',
            #     task='interview.tasks.auto_accept_interviews_one_hour_before',
            #     defaults={'args': json.dumps([])},
            # )
            
        except Exception as e:
            print(f"Warning: Could not create Celery Beat schedules: {e}")
            # Don't raise the exception to avoid breaking app startup

