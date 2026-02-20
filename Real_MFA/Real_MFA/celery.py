"""
Celery Configuration - Async task queue setup with Redis broker
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Real_MFA.settings')

# Create Celery app
app = Celery('Real_MFA')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Broker and Result Backend
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    
    # Serialization
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    
    # Task Configuration
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Retry Configuration
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_acks_late=True,
    
    # Worker Configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Result Backend Configuration
    result_expires=3600,  # 1 hour
    
    # Beat Scheduler Configuration
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
    
    # Periodic Tasks
    beat_schedule={
        'cleanup-old-otp-codes': {
            'task': 'accounts.tasks.cleanup_old_otp_codes',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        'cleanup-expired-sessions': {
            'task': 'accounts.tasks.cleanup_expired_sessions',
            'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        'send-pending-notifications': {
            'task': 'notification.tasks.send_pending_notifications',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
    },
)

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
