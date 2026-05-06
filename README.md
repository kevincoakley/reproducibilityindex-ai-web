# reproducibilityindex-ai-web

Flask website for `reproducibilityindex.ai`, backed by a read-only SQLite datastore.

## Setup

```bash
uv sync --group test
```

## Run (development)

```bash
uv run flask --app run.py --debug run
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

Key pages:
- `/` home
- `/countries/` country-level reproducibility chart and table
- `/institutions/` institution-level reproducibility chart and table, defaulting to institutions with 100+ contributing papers
- `/institutions/contributing_papers/100` institution chart and table filtered to 100+ contributing papers
- `/data/` stacked area chart of paper counts by venue and year

## Run (production-style)

```bash
uv run gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 60 run:app
```

## Run with Docker

Build image:

```bash
docker build -t reproducibilityindex-ai-web .
```

Run container (mount local SQLite database as read-only volume):

```bash
docker run --rm -p 5000:5000 \
  -e SQLITE_DB_PATH=/data/results.sqlite \
  -e GUNICORN_WORKERS=4 \
  -e GUNICORN_THREADS=2 \
  -e GUNICORN_TIMEOUT=60 \
  -v "$(pwd)/results.sqlite:/data/results.sqlite:ro" \
  reproducibilityindex-ai-web
```

The container runs Gunicorn bound to `0.0.0.0:5000` by default.

## Test

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=.
```

Coverage checks enforce a minimum of 90%.

## Format

```bash
uv run black .
```

## Configuration

- `SITE_TITLE` (default: `reproducibilityindex.ai`)
- `DB_BACKEND` (default: `sqlite`)
- `SQLITE_DB_PATH` (default: `results.sqlite` in repo root)
- `GUNICORN_BIND` (default: `0.0.0.0:5000`)
- `GUNICORN_WORKERS` (default: `4`)
- `GUNICORN_THREADS` (default: `2`)
- `GUNICORN_TIMEOUT` (default: `60`)
