FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1

RUN pip install --no-cache-dir poetry==$POETRY_VERSION

WORKDIR /app

COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-interaction --no-ansi

COPY . /app

EXPOSE 5000

# Build arg to determine entrypoint
ARG APP_TARGET=flask

CMD if [ "$APP_TARGET" = "fastapi" ]; then \
      poetry run uvicorn demo.fastapi.app:app --host 0.0.0.0 --port 5000; \
    else \
      poetry run python demo/flaskapp/app.py --use-redis; \
    fi