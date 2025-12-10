import os
import re
from typing import Optional

# Try importing llama_cpp; if unavailable we still keep server running
try:
    from llama_cpp import Llama
except Exception:
    Llama = None

# Holds lazy-loaded Llama instance
_llm_instance = None


def sanitize_response(text: str) -> str:
    """Sanitize placeholder phone numbers."""
    return re.sub(r"\(?123\)?[-\s.]?456[-\s.]?7890", "[number unavailable]", text)


def get_model_path() -> Optional[str]:
    """Checks MODEL_PATH env var; otherwise returns default path."""
    env_path = os.environ.get("MODEL_PATH")
    if env_path:
        return env_path

    # Default path — safe to change
    return r"C:/Programming/Solace/Models/Zephyr/zephyr-3b-beta.Q3_K_M.gguf"


def get_llm():
    """Lazy-loads the model only when needed. Never crashes server."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    model_path = get_model_path()

    # If model missing → reduced mode
    if not model_path or not os.path.exists(model_path):
        print(f"[responder] WARNING: model path not found: {model_path!r}. Running in reduced mode.")
        _llm_instance = None
        return None

    # If llama_cpp not installed
    if Llama is None:
        print("[responder] WARNING: llama_cpp not installed; cannot load model.")
        _llm_instance = None
        return None

    # Try loading model
    try:
        print(f"[responder] Loading model from: {model_path}")
        _llm_instance = Llama(
            model_path=model_path,
            n_ctx=512,
            n_batch=32,
            n_gpu_layers=0,
            use_mlock=False,
        )
        print("[responder] Model loaded successfully.")
    except Exception as e:
        print(f"[responder] ERROR loading Llama model: {e}")
        _llm_instance = None

    return _llm_instance


def zephyr_generate(user_input: str, history=None, emotion=None, confidence=None, max_tokens=80) -> str:
    """
    Generates response using local model if available.
    Otherwise returns fallback friendly responses.
    """
    llm = get_llm()

    base_prompt = (
        "You are Solace 🌸 — the user's hype bestie and emotional BFF. "
        "Talk casually, warm, friendly, supportive. Keep replies short.\n"
    )

    if emotion:
        base_prompt += f"<|emotion|>{emotion}</|emotion|>\n"

    prompt = base_prompt

    if history:
        prompt += "\n".join(history[-5:]) + "\n"

    prompt += f"User: {user_input}\nSolace:"

    # FALLBACK MODE — no model loaded
    if llm is None:
        return (
            "Heyyy, I’m running in reduced mode rn (model not loaded) but I’m still here 💛 "
            "Tell me what’s going on."
        )

    # NORMAL MODE — generate with model
    try:
        output = llm(prompt, max_tokens=max_tokens, stop=["\nUser:", "\nSolace:", "</s>"])
        text = output.get("choices", [{}])[0].get("text", "").strip()
        return sanitize_response(text)
    except Exception as e:
        print(f"[responder] Generation error: {e}")
        return "Oops—something glitched while replying. Can you try again?"


def generate_response(user_input: str, history=None, emotion=None, confidence=None, session_id=None, check_in=False):
    """Public API used by backend."""
    return zephyr_generate(
        user_input=user_input,
        history=history,
        emotion=emotion,
        confidence=confidence,
    )