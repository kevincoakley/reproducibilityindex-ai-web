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

## Run (production-style)

```bash
uv run flask --app run.py run --host 0.0.0.0 --port 5000
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
  -v "$(pwd)/results.sqlite:/data/results.sqlite:ro" \
  reproducibilityindex-ai-web
```

## Test

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=.
```

## Format

```bash
uv run black .
```

## Configuration

- `SITE_TITLE` (default: `reproducibilityindex.ai`)
- `DB_BACKEND` (default: `sqlite`)
- `SQLITE_DB_PATH` (default: `results.sqlite` in repo root)
