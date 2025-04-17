web: gunicorn runserver:app --log-file=-
worker: celery -A app.tasks worker -c 3 -B