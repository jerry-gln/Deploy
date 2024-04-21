# celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InventoryProject.settings')

app = Celery('InventoryProject')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Define a periodic task to call check_low_stock_and_generate_orders() every day at 1 AM
app.conf.beat_schedule = {
    'check-low-stock': {
        'task': 'dashboard.tasks.check_low_stock_and_generate_orders',
        
    },
}
