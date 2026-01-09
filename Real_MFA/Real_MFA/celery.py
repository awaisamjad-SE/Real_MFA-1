"""
Celery Configuration - Async task queue setup with Redis broker
"""

import os
from celery import Celery

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Real_MFA.settings')

# Create Celery app
app = Celery('Real_MFA')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery defaults (can be overridden via Django settings / env)
app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),

    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,

    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,

    default_rate_limit='2/s',
    task_autoretry_for=(Exception,),
    task_max_retries=3,
)

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
