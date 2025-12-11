# main.py
# -----------------------
# OpenBLAS / PyTorch check (safe when torch is missing)
# -----------------------
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from numpy import show_config

# Try to import torch, but allow missing torch on prod (Render)
try:
    import torch
except Exception:
    torch = None
    # minimal info to stdout during early startup
    print("[INFO] torch not installed or failed to import — running in lightweight mode.")

print("=== OpenBLAS / NumPy Info ===")
try:
    show_config()  # Shows which BLAS library is linked
except Exception as e:
    print("[WARN] numpy.show_config() failed:", e)

if torch is not None:
    try:
        print("PyTorch MKL enabled:", torch.backends.mkl.is_available())
        print("PyTorch OpenMP threads:", torch.get_num_threads())
    except Exception as e:
        print("[WARN] torch exists but querying backends failed:", e)
else:
    print("[INFO] torch: NOT AVAILABLE (skipping torch-specific checks)")

# Quick performance test (numpy only — safe without torch)
try:
    size = 1000
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    start = time.time()
    c = a @ b
    end = time.time()
    print(f"[OpenBLAS Test] {size}x{size} matrix multiplication took {end-start:.2f} seconds")
except Exception as e:
    print("[WARN] numpy performance test failed:", e)

print("======================================\n")

# -----------------------
# Logging config
# -----------------------
LOG_LEVEL = os.environ.get("SNUGSY_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("snugsy.main")

# -----------------------
# Existing imports
# -----------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# -----------------------
# Secret Key (Render will inject SNUGSY variable)
# -----------------------
SECRET_KEY = os.getenv("SNUGSY", "snugsy_local_dev_key")
# mask printing slightly so logs don't leak full secret
masked = SECRET_KEY[:5] + ("*" * max(0, len(SECRET_KEY) - 5))
logger.info("Using SECRET_KEY (masked) = %s", masked)

# -----------------------
# Local imports (resilient)
# -----------------------
# These modules must exist in your repo. If they fail to import, the server still runs
# with safe fallback stubs so Render won't crash the process.
try:
    from interface.terminal_chat import start_chat
except Exception as e:
    logger.warning("interface.terminal_chat.start_chat not available: %s", e)
    def start_chat():
        logger.info("start_chat stub called (no terminal interface available).")

try:
    from brain.sentiment import detect_emotion, classify_emotion
except Exception as e:
    logger.warning("Could not import brain.sentiment: %s", e)
    def detect_emotion(text: str):
        return "neutral", 0.5
    def classify_emotion(text: str, remote_url: Optional[str] = None):
        return {"label": "neutral", "confidence": 0.5, "method": "fallback", "escalate": False, "quality": "low"}

try:
    from brain.responder import generate_response
except Exception as e:
    logger.warning("Could not import brain.responder: %s", e)
    def generate_response(user_input: str, history=None, emotion=None, confidence=None, **_):
        return "Hey — I'm running in reduced mode (responder missing). Try again later."

try:
    from brain.memory import add_to_history, get_history, chat_history, reset_history
except Exception as e:
    logger.warning("Could not import brain.memory: %s", e)
    chat_history = {}
    def reset_history():
        chat_history.clear()
    def add_to_history(user_id: str, user_text: str, reply_text: str):
        chat_history.setdefault(user_id, []).append({"user": user_text, "reply": reply_text})
    def get_history(user_id: str):
        return [turn["user"] + " -> " + turn["reply"] for turn in chat_history.get(user_id, [])]

# Reset chat history at startup (best-effort)
try:
    reset_history()
    if isinstance(chat_history, dict):
        chat_history.clear()
    logger.info("Solace memory has been cleared on startup.")
except Exception as e:
    logger.warning("Memory reset skipped or failed: %s", e)

# -----------------------
# Create FastAPI app
# -----------------------
app = FastAPI(title="Solace API")

# CORS setup (allow from anywhere)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# -----------------------
# Health Check
# -----------------------
@app.get("/health")
def health():
    return {"ok": True}

# -----------------------
# Frontend serving
# -----------------------
frontend_path = Path(__file__).parent / "dist"
index_file = frontend_path / "index.html"

@app.get("/")
def serve_index():
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Frontend not built yet."}

@app.get("/{path:path}")
def serve_static(path: str):
    file_path = frontend_path / path
    if file_path.exists():
        return FileResponse(file_path)
    return FileResponse(index_file) if index_file.exists() else {"error": "Not found"}

# -----------------------
# API Models
# -----------------------
class Message(BaseModel):
    user_id: str
    text: str

class Reply(BaseModel):
    response: str
    emotion: str
    confidence: float

# -----------------------
# Chat Endpoint
# -----------------------
@app.post("/api/chat", response_model=Reply)
def chat_with_solace(message: Message):
    # --- emotion classification (try new hybrid classifier first) ---
    try:
        # classify_emotion should return a dict like:
        # {"label": "joy", "confidence": 0.92, "escalate": False, "quality": "high", "method": "transformer"}
        cls = classify_emotion(message.text)
        emotion = cls.get("label", "neutral")
        confidence = float(cls.get("confidence", 0.0))
        escalate = bool(cls.get("escalate", False))
        quality = cls.get("quality", "unknown")
        method = cls.get("method", "classifier")
    except Exception as e:
        # fallback to the older simple detector
        logger.exception("classify_emotion failed — falling back to detect_emotion: %s", e)
        emotion, confidence = detect_emotion(message.text)
        escalate = False
        quality = "heuristic"
        method = "heuristic"

    logger.info("Emotion: %s (%.2f) — method=%s quality=%s escalate=%s", emotion, confidence, method, quality, escalate)

    # --- history + reply generation (unchanged) ---
    history = get_history(message.user_id)

    try:
        reply = generate_response(
            user_input=message.text,
            history=history,
            emotion=emotion,
            confidence=confidence
        )
    except Exception as e:
        logger.exception("generate_response failed: %s", e)
        reply = "Oops — I'm having trouble generating a reply right now."

    # --- if the classifier flagged escalation, tack on a gentle professional suggestion ---
    if escalate:
        escalation_note = (
            "\n\nIf you're feeling overwhelmed or unsafe, I may be limited in how much I can help. "
            "Please consider reaching out to a trusted person or a professional for immediate support. "
            "If it's an emergency, contact local emergency services right away."
        )
        if escalation_note.strip() not in reply:
            reply = reply.rstrip() + escalation_note

    # save to memory/history
    try:
        add_to_history(message.user_id, message.text, reply)
    except Exception:
        logger.warning("add_to_history failed (memory backend missing)")

    return Reply(
        response=reply,
        emotion=emotion,
        confidence=round(confidence, 2)
    )

# -----------------------
# Debug Memory Endpoint
# -----------------------
@app.get("/api/memory")
def debug_memory():
    return chat_history

# -----------------------
# Run server or terminal mode
# -----------------------
if __name__ == "__main__":
    # only import uvicorn in _main_ to avoid requiring it during import-time
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        start_chat()