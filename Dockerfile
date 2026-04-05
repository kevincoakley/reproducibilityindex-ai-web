FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY run.py ./

ENV DB_BACKEND=sqlite
ENV SQLITE_DB_PATH=/data/results.sqlite
ENV GUNICORN_BIND=0.0.0.0:5000
ENV GUNICORN_WORKERS=4
ENV GUNICORN_THREADS=2
ENV GUNICORN_TIMEOUT=60

EXPOSE 5000

CMD ["sh", "-c", "exec uv run gunicorn --bind \"$GUNICORN_BIND\" --workers \"$GUNICORN_WORKERS\" --threads \"$GUNICORN_THREADS\" --timeout \"$GUNICORN_TIMEOUT\" run:app"]
