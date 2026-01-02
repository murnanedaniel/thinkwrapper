web: gunicorn "app:create_app()"
worker: python celery_worker.py worker --loglevel=info --concurrency=4
beat: python celery_worker.py beat --loglevel=info 