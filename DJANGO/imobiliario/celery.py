import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'imobiliario.settings')

app = Celery('imobiliario')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Schedule tasks
app.conf.beat_schedule = {
    'expire-properties': {
        'task': 'listings.tasks.expire_properties',
        'schedule': 3600.0,  # Run every hour
    },
    'update-contract-statuses': {
        'task': 'contracts.tasks.update_contract_statuses',
        'schedule': 1800.0,  # Run every 30 minutes
    },
    'expire-sponsorships': {
        'task': 'ads.tasks.expire_sponsorships',
        'schedule': 1800.0,  # Run every 30 minutes
    },
    'calculate-overdue-payments': {
        'task': 'contracts.tasks.calculate_overdue_payments',
        'schedule': 3600.0,  # Run every hour
    },
    'cleanup-old-notifications': {
        'task': 'chat.tasks.cleanup_old_notifications',
        'schedule': 86400.0,  # Run daily
    },
    'update-property-statistics': {
        'task': 'listings.tasks.update_property_statistics',
        'schedule': 3600.0,  # Run every hour
    },
}

app.conf.timezone = settings.TIME_ZONE
