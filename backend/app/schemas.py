from pydantic import BaseModel, Field, field_validator

MAX_CODE_CHARS = 50_000
MAX_TRACEBACK_CHARS = 20_000
MAX_CHAT_CHARS = 8_000


class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=MAX_CODE_CHARS)

    @field_validator("code")
    @classmethod
    def code_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Code cannot be empty or only spaces.")
        return value


class TracebackRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TRACEBACK_CHARS)

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Traceback text cannot be empty or only spaces.")
        return value


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_CHAT_CHARS)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be empty or only spaces.")
        return value


class ChatResponse(BaseModel):
    reply: str
    model: str