import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, groq_api_key_configured
from app.schemas import AnalyzeRequest, ChatRequest, ChatResponse, TracebackRequest
from app.services.groq_service import (
    CHAT_SYSTEM_PROMPT,
    GroqServiceError,
    create_chat_completion,
    ping_model,
)
from app.tools.python_analyzer import analyze_python_source, explain_traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("pymate")

settings = get_settings()

app = FastAPI(title="PyMate AI Backend", version="0.3.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "https://ai-agent-226h9vajl-manomanovk-6865s-projects.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(GroqServiceError)
async def groq_error_handler(request: Request, exc: GroqServiceError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.user_message})


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "PyMate AI",
        "groq_api_key_configured": groq_api_key_configured(),
        "groq_model": get_settings().groq_model,
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    logger.info("Analyzing Python code with %d characters", len(request.code))
    return analyze_python_source(request.code)


@app.post("/api/traceback/explain")
def explain(request: TracebackRequest):
    return explain_traceback(request.text)


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": request.message},
    ]
    reply = create_chat_completion(messages)
    return ChatResponse(reply=reply, model=get_settings().groq_model)


@app.post("/api/ai/ping")
def ai_ping():
    reply = ping_model()
    return {"ok": True, "model": get_settings().groq_model, "reply": reply}