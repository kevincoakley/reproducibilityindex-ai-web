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

## Test

```bash
uv run pytest
```

With coverage:

```bash
uv run pytest --cov=.
```

## Configuration

- `SITE_TITLE` (default: `reproducibilityindex.ai`)
- `DB_BACKEND` (default: `sqlite`)
- `SQLITE_DB_PATH` (default: `results.sqlite` in repo root)
