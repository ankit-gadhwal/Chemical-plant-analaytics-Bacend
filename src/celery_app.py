from celery import Celery

c_app = Celery("chemical_backend")
c_app.config_from_object("src.config")
# Import tasks so Celery registers them
import src.celery_tasks