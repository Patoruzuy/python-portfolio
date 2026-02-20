"""
Celery configuration for async task processing.
Requires Redis server running on localhost:6379

To start worker:
    celery -A celery_config.celery worker --loglevel=info --pool=solo
"""
from celery import Celery
import os

# Create Celery instance
celery = Celery(
    'portfolio',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['tasks.email_tasks']  # Auto-discover tasks
)

# Configure Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_send_sent_event=True,
    task_track_started=True,
    task_time_limit=15 * 60,  # 15 minutes hard limit
    task_soft_time_limit=10 * 60,  # 10 minutes soft limit
    broker_connection_retry_on_startup=True  # Fix Celery 6.0 deprecation warning
)


def make_celery(app):
    """
    Factory function to integrate Celery with Flask app context.
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Celery instance
    """
    # Update Celery broker/backend from Flask config if available
    if app.config.get('CELERY_BROKER_URL'):
        celery.conf.broker_url = app.config['CELERY_BROKER_URL']
    if app.config.get('CELERY_RESULT_BACKEND'):
        celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
    
    # Create a task context that wraps tasks with Flask app context
    class ContextTask(celery.Task):  # type: ignore[name-defined]
        """Custom task class that ensures Flask app context is available."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery
