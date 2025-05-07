import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('peersight', broker=os.environ.get("CELERY_BROKER_URL"), backend=os.environ.get("CELERY_RESULT_BACKEND"))

app.config_from_object('django.conf:settings', namespace='CELERY')
# Apply SSL cert option if using rediss://
if app.conf.result_backend and app.conf.result_backend.startswith("rediss://"):
    app.conf.update(
        redis_backend_transport_options={'ssl_cert_reqs': 'CERT_NONE'}
    )
app.autodiscover_tasks()
