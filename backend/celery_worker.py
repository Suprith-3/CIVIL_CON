from app import create_app
from celery import Celery
import os

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
        broker=app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

flask_app = create_app()
celery = make_celery(flask_app)

@celery.task
def send_async_email(data):
    """Background task for sending emails"""
    print(f"DEBUG: Processing async email for {data}")
    return True
