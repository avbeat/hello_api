# Plan: `/ask` endpoint (user question → Gemini)

## Context
`main.py` already has `/haiku` and `/fortune`, which send fixed prompts to Gemini through a shared client (`get_client()`) and a shared helper (`generate()`), with errors mapped to `{"error": ...}` JSON by `gemini_error_handler`. We're adding `GET /ask?q=...`, which forwards a user's question to Gemini. The endpoint will be public and every call costs money, so input length, output length and answer style are all capped.

## Steps

0. **Housekeeping (CLAUDE.md)**
   - We're on `main` (clean, PR #1 merged). Create the branch `ask_endpoint` from `main`.
   - Add a time-stamped entry with this prompt to `PROMPTS.md`.
   - Save this plan as `plans/03_ask_endpoint.md`.

1. **`main.py`**
   - Change `generate(prompt)` to `generate(prompt, config=GENERATE_CONFIG)`. `/haiku` and `/fortune` keep their current behavior, and the env vars, client, error mapping and empty-response check are all reused.
   - Add the constants `ASK_MAX_CHARS = 200` and `ASK_CONFIG = types.GenerateContentConfig(system_instruction="Answer in three sentences or fewer. ...", max_output_tokens=200, thinking_config=<same minimal thinking>)`.
   - Endpoint: `def ask(q: str | None = None)`.
     - If `q` is missing, empty or only whitespace, return **400** `{"error": "Query parameter 'q' is required and cannot be empty."}`.
     - If `len(q) > 200`, return **400** `{"error": "Query parameter 'q' must be 200 characters or fewer."}`.
     - Both checks run before any Gemini call, so rejected requests cost nothing. They raise `GeminiError(msg, 400)`, so they go through the existing handler and use the same `{"error": ...}` shape. (FastAPI's built-in `max_length` validation would return a 422 in a different `{"detail": [...]}` format, so I'm not using it.)
     - On success, return `{"answer": "..."}`. Gemini failures map exactly as they do for `/haiku` (500/502/503).
   - Rename `GeminiError` to `ApiError`, since it now also covers input errors. It's a small rename inside `main.py` only.

2. **README.md**
   - Add `/ask?q=...` to the endpoint table.
   - Add a short `/ask` section covering the limits (q: 1–200 chars, about 200 output tokens, three sentences or fewer), the 400 cases, and a curl example (`curl "localhost:8080/ask?q=What%20is%20CI%2FCD%3F"` or `curl -G --data-urlencode "q=What is CI/CD?" localhost:8080/ask`).
   - Add 400 to the error status table.
   - Add a note that `/ask` is public and has no rate limiting or authentication. For Cloud Run, suggest `--max-instances` plus a Vertex AI quota or budget alert to limit spend.

## Critical files
- `main.py`, `README.md`, `PROMPTS.md`, `plans/03_ask_endpoint.md`. No new packages are needed.

## Verification
1. Run a `fastapi.testclient` script with a stubbed `get_client` (like last time). It should cover:
   - no q, `q=`, `q=%20%20`, and a 201-character q → all return 400 with an `{"error"}` body, and the stub records that it was **not** called
   - a 200-character q → the stub is called
   - the config passed to the stub has `max_output_tokens=200` and the system instruction
   - `/haiku` still uses the 100-token config
   - a 429 from the stub → 503
2. Run uvicorn without `GOOGLE_CLOUD_PROJECT`: `/ask` with no q should return 400 (validation runs first), and `/ask?q=hi` should return 500 with the config error.
3. A real Gemini call needs `gcloud auth application-default login` (ADC isn't set up on this machine yet). Once it is, `curl -G --data-urlencode "q=What is Kubernetes?" localhost:8080/ask` should return an answer of three sentences or fewer.

## Out of scope (suggest only)
Rate limiting or auth for `/ask`. Doing it in the app would need a new package or extra state, and you didn't ask for it.
