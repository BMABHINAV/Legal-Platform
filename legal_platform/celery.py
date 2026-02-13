"""
Celery configuration for legal_platform project.
Handles background tasks like document analysis, notifications, etc.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_platform.settings')

app = Celery('legal_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery Beat Schedule (Periodic Tasks)
app.conf.beat_schedule = {
    # Auto-release escrow payments after dispute window
    'auto-release-escrow': {
        'task': 'core.tasks.auto_release_escrow_payments',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    # Send reminder notifications for upcoming consultations
    'consultation-reminders': {
        'task': 'core.tasks.send_consultation_reminders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    # Clean up old emergency alerts
    'cleanup-emergencies': {
        'task': 'core.tasks.cleanup_old_emergencies',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Update leaderboard rankings
    'update-leaderboard': {
        'task': 'core.tasks.update_leaderboard_rankings',
        'schedule': crontab(minute=0),  # Every hour
    },
}

app.conf.timezone = 'Asia/Kolkata'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
