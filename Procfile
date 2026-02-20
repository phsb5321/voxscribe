web: /opt/venv/bin/uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT
worker: /opt/venv/bin/rq worker --url $REDIS_URL
