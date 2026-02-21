web: uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT
worker: uv run rq worker --url $REDIS_URL
