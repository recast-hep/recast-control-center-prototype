web: PYTHONUNBUFFERED=true gunicorn --worker-class socketio.sgunicorn.GeventSocketIOWorker server:app --limit-request-field_size 32000 --bind 127.0.0.1:8000
redis: redis-server
