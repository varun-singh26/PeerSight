import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('peersight', broker=os.environ.get("CELERY_BROKER_URL"))

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
