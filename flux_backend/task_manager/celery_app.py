# celery_app.py

from celery import Celery

from . import config

celery_app = Celery("my_spider_scheduler")
celery_app.config_from_object(config)
celery_app.autodiscover_tasks(['flux_backend.task_manager'])

celery_app.conf.update(
    broker_url=config.broker_url,
    result_backend=config.result_backend,
    beat_schedule=config.CELERY_BEAT_SCHEDULE,
    timezone=config.timezone
)
