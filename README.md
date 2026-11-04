# hello_api

A tiny FastAPI app with two casual endpoints and three that use Google's Gemini (via Vertex AI).

## Endpoints

| Method | Path       | Response                                                   |
|--------|------------|------------------------------------------------------------|
| GET    | `/hello`   | `{"message": "Hey there! 👋 Hope your day's going great."}` |
| GET    | `/goodbye` | `{"message": "Catch you later! Take it easy. ✌️"}`          |
| GET    | `/haiku`   | `{"haiku": "..."}`: a short DevOps haiku written by Gemini   |
| GET    | `/fortune` | `{"fortune": "..."}`: a one-sentence software fortune by Gemini |
| GET    | `/ask?q=…` | `{"answer": "..."}`: Gemini's short answer to your question  |

`/haiku` and `/fortune` use fixed prompts, take no input, and cap Gemini's reply at about 100 output tokens.

### `/ask`

`/ask` sends the `q` query parameter to Gemini and returns its answer. Because it's public and every call costs money, it's capped:

- `q` is required and must be 1–200 characters. A missing, empty (or whitespace-only), or too-long `q` gets a `400` before Gemini is called, so it costs nothing.
- A system instruction tells Gemini to answer in three sentences or fewer, and the reply is limited to about 200 output tokens.

```bash
curl -G --data-urlencode "q=What is CI/CD?" localhost:8080/ask
```

```json
{"error": "Query parameter 'q' must be 200 characters or fewer."}
```

`/ask` has no authentication or rate limiting. To cap spending on Cloud Run, limit instances (`gcloud run deploy ... --max-instances 2`) and set a budget alert or a lower Vertex AI quota for the project.

### Errors

Errors come back as JSON instead of a crash:

| Status | When                                                                 |
|--------|----------------------------------------------------------------------|
| 400    | `/ask` only: `q` is missing, empty, or longer than 200 characters    |
| 500    | `GOOGLE_CLOUD_PROJECT` isn't set, or Google Cloud credentials are missing/invalid |
| 502    | Vertex AI returned an error or an empty (e.g. blocked) response      |
| 503    | Gemini is rate-limited or over quota (HTTP 429)                      |

```json
{"error": "Gemini is busy or over quota. Try again later."}
```

Details are written to the server log.

Interactive docs are available at `/docs` while the app is running.

## Install

Requires Python 3.12+ and [Poetry](https://python-poetry.org/).

```bash
poetry install
```

## Gemini / Vertex AI setup

The Gemini endpoints authenticate with [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) (ADC) only: no API keys, no key files.

Settings (environment variables):

| Variable                | Required | Default                 |
|-------------------------|----------|-------------------------|
| `GOOGLE_CLOUD_PROJECT`  | yes      | (none)                  |
| `GOOGLE_CLOUD_LOCATION` | no       | `global`                |
| `GEMINI_MODEL`          | no       | `gemini-3.1-flash-lite` |

One-time setup for your project:

```bash
gcloud services enable aiplatform.googleapis.com
```

Local development: log in once so ADC can find your user credentials, then set the project:

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-project-id
```

The app starts without `GOOGLE_CLOUD_PROJECT`. `/hello` and `/goodbye` still work, and the Gemini endpoints return a 500 error that says it's missing.

## Run

```bash
poetry run uvicorn main:app --reload --port 8080
```

`--reload` restarts the server whenever you save a file (use it for local development only). Change `--port` to run on a different port.

Try it:

```bash
curl localhost:8080/hello
curl localhost:8080/goodbye
curl localhost:8080/haiku
curl localhost:8080/fortune
curl -G --data-urlencode "q=What is Kubernetes?" localhost:8080/ask
```

## Deployment (Google Cloud Run)

- `requirements.txt` is exported from Poetry for Cloud Run's build. Regenerate it whenever dependencies change:

  ```bash
  poetry export -f requirements.txt --output requirements.txt --without-hashes
  ```

  (Needs the `poetry-plugin-export` plugin: `poetry self add poetry-plugin-export`.)
- `Procfile` tells Cloud Run's buildpacks to start the app with
  `uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}`, so it listens on the port in the `PORT` environment variable (default `8080`).
- Set the Gemini settings on the service, e.g.
  `gcloud run deploy ... --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_CLOUD_LOCATION=global`.
- On Cloud Run, ADC uses the service's runtime service account automatically, so no keys are needed. Grant that account the Vertex AI User role:

  ```bash
  gcloud projects add-iam-policy-binding your-project-id \
    --member=serviceAccount:SERVICE_ACCOUNT_EMAIL --role=roles/aiplatform.user
  ```
