import logging
import os

from groq import APIConnectionError, APIError, APIStatusError, Groq, RateLimitError

from app.config import get_settings

logger = logging.getLogger("pymate.groq")

REQUEST_TIMEOUT_SECONDS = 30.0
SDK_MAX_RETRIES = 1
DEFAULT_MAX_COMPLETION_TOKENS = 1024

CHAT_SYSTEM_PROMPT = (
    "You are PyMate AI, a careful assistant focused on Python programming. "
    "Explain things in simple English. Put code in fenced code blocks labeled python. "
    "If a question is not about Python, say briefly that PyMate AI focuses on Python."
)

PING_MESSAGES = [
    {
        "role": "system",
        "content": "You are a connection test. Reply with exactly: PyMate AI connected",
    },
    {"role": "user", "content": "Send the connection message now."},
]


class GroqServiceError(Exception):
    """An error with an HTTP status code and a message that is safe to show in the UI."""

    def __init__(self, status_code: int, user_message: str):
        super().__init__(user_message)
        self.status_code = status_code
        self.user_message = user_message


def _read_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise GroqServiceError(
            500,
            "The server is missing its Groq API key. Add GROQ_API_KEY to backend/.env and restart the server.",
        )
    return api_key


def get_client() -> Groq:
    return Groq(
        api_key=_read_api_key(),
        timeout=REQUEST_TIMEOUT_SECONDS,
        max_retries=SDK_MAX_RETRIES,
    )


def _status_error(status_code: int | None) -> GroqServiceError:
    logger.warning("Groq API returned HTTP status %s", status_code)
    if status_code in (401, 403):
        return GroqServiceError(
            401,
            "Groq rejected the API key. Check GROQ_API_KEY in backend/.env and restart the server.",
        )
    if status_code == 404:
        return GroqServiceError(
            502,
            "Groq could not find the configured model. Check GROQ_MODEL in backend/.env.",
        )
    if status_code == 400:
        return GroqServiceError(
            400,
            "Groq rejected the request. Check GROQ_MODEL in backend/.env, or try a shorter message.",
        )
    if status_code is not None and status_code >= 500:
        return GroqServiceError(
            503,
            "Groq is temporarily unavailable. Please wait a moment and try again.",
        )
    return GroqServiceError(502, "Groq returned an unexpected error. Please try again.")


def create_chat_completion(
    messages: list[dict[str, str]],
    max_completion_tokens: int = DEFAULT_MAX_COMPLETION_TOKENS,
) -> str:
    model = get_settings().groq_model
    client = get_client()

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=max_completion_tokens,
            temperature=0.2,
        )
    except RateLimitError as exc:
        logger.warning("Groq rate limit reached")
        raise GroqServiceError(
            429,
            "The Groq usage limit was reached. Wait a little, then try again.",
        ) from exc
    except APIConnectionError as exc:
        logger.warning("Could not connect to Groq: %s", type(exc).__name__)
        raise GroqServiceError(
            502,
            "Could not reach Groq. Check your internet connection, then try again.",
        ) from exc
    except APIStatusError as exc:
        raise _status_error(exc.status_code) from exc
    except APIError as exc:
        logger.warning("Unexpected Groq SDK error: %s", type(exc).__name__)
        raise GroqServiceError(502, "Groq returned an unexpected error. Please try again.") from exc

    try:
        content = completion.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as exc:
        logger.error("Malformed Groq response shape")
        raise GroqServiceError(
            502,
            "The AI returned an unexpected response. Please try again.",
        ) from exc

    text = (content or "").strip()
    if not text:
        raise GroqServiceError(
            502,
            "The AI returned an empty answer. Please try again, or ask a shorter question.",
        )
    return text


def ping_model() -> str:
    return create_chat_completion(PING_MESSAGES, max_completion_tokens=256)