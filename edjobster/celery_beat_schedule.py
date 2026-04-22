from celery.schedules import crontab

# Define your periodic tasks here
CELERY_BEAT_SCHEDULE = {
    'send-interview-reminders-every-minute': {
        'task': 'interview.tasks.send_interview_reminders',
        'schedule': crontab(minute='*'),  # Run at the start of every minute
        'options': {
            'expires': 30.0,  # Task expires after 30 seconds if not executed
        },
    },
    # 'auto-accept-interviews-every-5-minutes': {
    #     'task': 'interview.tasks.auto_accept_interviews_one_hour_before',
    #     'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    #     'options': {
    #         'expires': 60.0,  # Task expires after 60 seconds if not executed
    #     },
    # },
    'send-feedback-reminders-post-interview-every-minute': {
        'task': 'interview.tasks.send_feedback_reminders_post_interview',
        'schedule': crontab(minute='*'),  # Run every minute
        'options': {
            'expires': 30.0,  # Small window to avoid duplicate sends
        },
    },
    'deactivate-expired-subscriptions-daily': {
        'task': 'settings.tasks.deactivate_expired_subscriptions',
        'schedule': crontab(minute=0, hour=0),  # Run daily at midnight
        'options': {
            'expires': 60 * 30,  # Task expires after 30 minutes if not executed
        },
    },
    'reset-daily-credits': {
        'task': 'settings.tasks.reset_daily_credits',
        'schedule': crontab(minute=5, hour=0),  # Run daily at 00:05 AM
        'options': {
            'expires': 60 * 30,  # Task expires after 30 minutes if not executed
        },
    },
}
