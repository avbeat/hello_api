# hello_api

A tiny FastAPI app with two casual endpoints.

## Endpoints

| Method | Path       | Response                                                   |
|--------|------------|------------------------------------------------------------|
| GET    | `/hello`   | `{"message": "Hey there! 👋 Hope your day's going great."}` |
| GET    | `/goodbye` | `{"message": "Catch you later! Take it easy. ✌️"}`          |

Interactive docs are available at `/docs` while the app is running.

## Install

Requires Python 3.12+ and [Poetry](https://python-poetry.org/).

```bash
poetry install
```

## Run

```bash
poetry run uvicorn main:app --reload --port 8080
```

`--reload` restarts the server whenever you save a file (use it for local development only). Change `--port` to run on a different port.

Try it:

```bash
curl localhost:8080/hello
curl localhost:8080/goodbye
```

## Deployment (Google Cloud Run)

- `requirements.txt` is exported from Poetry for Cloud Run's build. Regenerate it whenever dependencies change:

  ```bash
  poetry export -f requirements.txt --output requirements.txt --without-hashes
  ```

  (Needs the `poetry-plugin-export` plugin: `poetry self add poetry-plugin-export`.)
- `Procfile` tells Cloud Run's buildpacks to start the app with
  `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}`, so it listens on the port in the `PORT` environment variable (default `8080`).
