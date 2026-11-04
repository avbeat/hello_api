import logging
import os
from functools import cache

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from google import genai
from google.auth.exceptions import GoogleAuthError
from google.genai import errors, types

logger = logging.getLogger(__name__)

GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

HAIKU_PROMPT = (
    "Write a short haiku (three lines, 5-7-5 syllables) about DevOps. "
    "Reply with only the haiku, no title or commentary."
)
FORTUNE_PROMPT = (
    "Write a one-sentence, software-themed fortune-cookie message. "
    "Reply with only the fortune, no quotes or commentary."
)

# Thinking tokens count toward max_output_tokens, so keep thinking minimal.
MINIMAL_THINKING = types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL)

GENERATE_CONFIG = types.GenerateContentConfig(
    max_output_tokens=100,
    thinking_config=MINIMAL_THINKING,
)

ASK_MAX_CHARS = 200
ASK_CONFIG = types.GenerateContentConfig(
    system_instruction=(
        "You are a concise assistant. Answer the user's question in three sentences or fewer."
    ),
    max_output_tokens=200,
    thinking_config=MINIMAL_THINKING,
)

app = FastAPI()


class ApiError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@cache
def get_client() -> genai.Client:
    # Authenticates with Application Default Credentials; no API keys.
    return genai.Client(
        vertexai=True, project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION
    )


def generate(prompt: str, config: types.GenerateContentConfig = GENERATE_CONFIG) -> str:
    if not GOOGLE_CLOUD_PROJECT:
        raise ApiError("Server is not configured: GOOGLE_CLOUD_PROJECT is not set.", 500)
    try:
        response = get_client().models.generate_content(
            model=GEMINI_MODEL, contents=prompt, config=config
        )
    except GoogleAuthError:
        logger.exception("Google Cloud authentication failed")
        raise ApiError("Server could not authenticate with Google Cloud.", 500)
    except errors.APIError as e:
        logger.exception("Gemini API call failed")
        if e.code == 429:
            raise ApiError("Gemini is busy or over quota. Try again later.", 503)
        raise ApiError("Gemini request failed.", 502)

    text = (response.text or "").strip()
    if not text:
        logger.error("Gemini returned an empty response: %s", response)
        raise ApiError("Gemini returned an empty response.", 502)
    return text


@app.exception_handler(ApiError)
def api_error_handler(request, exc: ApiError):
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)


@app.get("/hello")
def hello():
    return {"message": "Hey there! 👋 Hope your day's going great."}


@app.get("/goodbye")
def goodbye():
    return {"message": "Catch you later! Take it easy. ✌️"}


@app.get("/haiku")
def haiku():
    return {"haiku": generate(HAIKU_PROMPT)}


@app.get("/fortune")
def fortune():
    return {"fortune": generate(FORTUNE_PROMPT)}


@app.get("/ask")
def ask(q: str | None = None):
    # Validate before calling Gemini so rejected requests cost nothing.
    if q is None or not q.strip():
        raise ApiError("Query parameter 'q' is required and cannot be empty.", 400)
    if len(q) > ASK_MAX_CHARS:
        raise ApiError(f"Query parameter 'q' must be {ASK_MAX_CHARS} characters or fewer.", 400)
    return {"answer": generate(q, ASK_CONFIG)}
