# Plan: FastAPI hello/goodbye API with Poetry

## Context
`hello_api` is an empty Git repo (only `CLAUDE.md`, on `main`). The user wants a small FastAPI app with
`GET /hello` and `GET /goodbye` returning casual JSON messages. It will later deploy to Cloud Run from GitHub,
so it must read `PORT` (default 8080) and ship a `requirements.txt` exported from Poetry.
Tooling checked: Poetry 2.5.1 with `poetry-plugin-export` installed, Python 3.14.

## Steps (in order, following CLAUDE.md)
1. **Prompt log**: create `PROMPTS.md` and add a time-stamped entry with this prompt.
2. **Plan copy**: save this plan as `plans/01_hello_goodbye.md`.
3. **Branch**: `git checkout -b hello_goodbye_api` (never work on `main`).
4. **Poetry project**: `poetry init` non-interactively, `package-mode = false` (app, not a library),
   `requires-python = ">=3.12"`. Add only `fastapi` and `uvicorn` (`poetry add fastapi uvicorn`).
5. **`main.py`** (root):
   - `app = FastAPI()`
   - `GET /hello` → `{"message": "Hey there! 👋 Hope your day's going great."}`
   - `GET /goodbye` → `{"message": "Catch you later! Take it easy. ✌️"}`
   - `if __name__ == "__main__":` run `uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))`
6. **`Procfile`**: `web: python main.py`. Cloud Run's source deploy uses buildpacks; without this they
   guess the start command (older ones guess gunicorn, which can't serve FastAPI as-is). Confirmed with user.
7. **`requirements.txt`**: `poetry export -f requirements.txt --output requirements.txt --without-hashes`.
8. **`.gitignore`**: Python basics (`__pycache__/`, `.venv/`, `.env`) so no secrets/venv get committed.
9. **`README.md`**: install (`poetry install`), run (`poetry run python main.py`, `PORT=9000 ...`),
   endpoints, and how to regenerate `requirements.txt` after dependency changes.
10. No commits/pushes — leave changes for the user.

## Verification
- `poetry run python main.py &` then `curl localhost:8080/hello` and `curl localhost:8080/goodbye` → JSON messages.
- `PORT=9000 poetry run python main.py &` then `curl localhost:9000/hello` → confirms PORT is honored.
- Check `requirements.txt` contains fastapi and uvicorn; `git status` shows we're on `hello_goodbye_api`.
