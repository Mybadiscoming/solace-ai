# -----------------------
# OpenBLAS / PyTorch check
# -----------------------
import numpy as np
import torch
import time
from numpy import show_config

print("=== OpenBLAS / NumPy / PyTorch Info ===")
show_config()  # Shows which BLAS library is linked
print("PyTorch MKL enabled:", torch.backends.mkl.is_available())
print("PyTorch OpenMP threads:", torch.get_num_threads())

# Quick performance test
size = 1000
a = np.random.rand(size, size)
b = np.random.rand(size, size)
start = time.time()
c = a @ b
end = time.time()
print(f"[OpenBLAS Test] {size}x{size} matrix multiplication took {end-start:.2f} seconds")
print("======================================\n")

# -----------------------
# Existing imports
# -----------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import uvicorn
import sys

# Your local imports
from interface.terminal_chat import start_chat
from brain.sentiment import detect_emotion
from brain.responder import generate_response
from brain.memory import add_to_history, get_history, chat_history, reset_history

# Reset chat history at startup
reset_history()
chat_history.clear()
print("Solace memory has been cleared on startup.")

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
# Frontend serving
# -----------------------
frontend_path = Path(__file__).parent / "dist"  # HF Spaces will have dist in root
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
# API Endpoints
# -----------------------
@app.post("/api/chat", response_model=Reply)
def chat_with_solace(message: Message):
    # Detect emotion once
    emotion, confidence = detect_emotion(message.text)
    print(f"[Emotion] {emotion} ({confidence:.2f})")

    # Retrieve chat history
    history = get_history(message.user_id)

    # Generate reply
    reply = generate_response(
        user_input=message.text,
        history=history,
        emotion=emotion,
        confidence=confidence
    )

    # Save this exchange
    add_to_history(message.user_id, message.text, reply)

    return Reply(
        response=reply,
        emotion=emotion,
        confidence=round(confidence, 2)
    )

@app.get("/api/memory")
def debug_memory():
    return chat_history

# -----------------------
# Run server or terminal
# -----------------------
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        start_chat()