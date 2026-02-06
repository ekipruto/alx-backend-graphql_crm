"""
Celery Configuration for CRM Application
Configures Celery for asynchronous task processing with Redis broker.
"""

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')

# Create Celery app
app = Celery('crm')

# Configure Celery using settings from Django settings.py
# Namespace='CELERY' means all celery-related config keys should be uppercase
# and prefixed with CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working"""
    print(f'Request: {self.request!r}')


# Optional: Configure Celery Beat schedule here
# (Can also be configured in settings.py)
app.conf.beat_schedule = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}

app.conf.timezone = 'UTC'
