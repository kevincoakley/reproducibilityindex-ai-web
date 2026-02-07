FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY run.py ./

ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV DB_BACKEND=sqlite
ENV SQLITE_DB_PATH=/data/results.sqlite

EXPOSE 5000

CMD ["uv", "run", "flask", "run"]
