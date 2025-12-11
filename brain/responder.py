# brain/responder.py
# ---------------------------------------------------------------------
# PREVIOUS IMPLEMENTATION (commented out for safekeeping)
# If you want to restore the old version, remove the leading triple-quotes
# and delete or move the new implementation below.
# ---------------------------------------------------------------------
"""
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
    \"\"\"Sanitize placeholder phone numbers.\"\"\"
    return re.sub(r\"\\(?123\\)?[-\\s.]?456[-\\s.]?7890\", \"[number unavailable]\", text)


def get_model_path() -> Optional[str]:
    \"\"\"Checks MODEL_PATH env var; otherwise returns default path.\"\"\"
    env_path = os.environ.get(\"MODEL_PATH\")
    if env_path:
        return env_path

    # Default path — safe to change
    return r\"C:/Programming/Solace/Models/Zephyr/zephyr-3b-beta.Q3_K_M.gguf\"


def get_llm():
    \"\"\"Lazy-loads the model only when needed. Never crashes server.\"\"\"
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    model_path = get_model_path()

    # If model missing → reduced mode
    if not model_path or not os.path.exists(model_path):
        print(f\"[responder] WARNING: model path not found: {model_path!r}. Running in reduced mode.\")
        _llm_instance = None
        return None

    # If llama_cpp not installed
    if Llama is None:
        print(\"[responder] WARNING: llama_cpp not installed; cannot load model.\")
        _llm_instance = None
        return None

    # Try loading model
    try:
        print(f\"[responder] Loading model from: {model_path}\")
        _llm_instance = Llama(
            model_path=model_path,
            n_ctx=512,
            n_batch=32,
            n_gpu_layers=0,
            use_mlock=False,
        )
        print(\"[responder] Model loaded successfully.\")
    except Exception as e:
        print(f\"[responder] ERROR loading Llama model: {e}\")
        _llm_instance = None

    return _llm_instance


def zephyr_generate(user_input: str, history=None, emotion=None, confidence=None, max_tokens=80) -> str:
    \"\"\"
    Generates response using local model if available.
    Otherwise returns fallback friendly responses.
    \"\"\"
    llm = get_llm()

    base_prompt = (
        \"You are Solace 🌸 — the user's hype bestie and emotional BFF. \"
        \"Talk casually, warm, friendly, supportive. Keep replies short.\\n\"
    )

    if emotion:
        base_prompt += f\"<|emotion|>{emotion}</|emotion|>\\n\"

    prompt = base_prompt

    if history:
        prompt += \"\\n\".join(history[-5:]) + \"\\n\"

    prompt += f\"User: {user_input}\\nSolace:\"

    # FALLBACK MODE — no model loaded
    if llm is None:
        return (
            \"Heyyy, I’m running in reduced mode rn (model not loaded) but I’m still here 💛 \"
            \"Tell me what’s going on.\"
        )

    # NORMAL MODE — generate with model
    try:
        output = llm(prompt, max_tokens=max_tokens, stop=[\"\\nUser:\", \"\\nSolace:\", \"</s>\"])
        text = output.get(\"choices\", [{}])[0].get(\"text\", \"\").strip()
        return sanitize_response(text)
    except Exception as e:
        print(f\"[responder] Generation error: {e}\")
        return \"Oops—something glitched while replying. Can you try again?\"


def generate_response(user_input: str, history=None, emotion=None, confidence=None, session_id=None, check_in=False):
    \"\"\"Public API used by backend.\"\"\"
    return zephyr_generate(
        user_input=user_input,
        history=history,
        emotion=emotion,
        confidence=confidence,
    )
"""
# ---------------------------------------------------------------------
# END OF COMMENTED PREVIOUS IMPLEMENTATION
# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# NEW ACTIVE IMPLEMENTATION
# - Keeps same behaviour but has an env var to force reduced mode
# - Adds clearer logging and type hints
# ---------------------------------------------------------------------
import os
import re
from typing import Optional

# Try importing llama_cpp; if unavailable we still keep server running
try:
    from llama_cpp import Llama
except Exception:
    Llama = None

# Holds lazy-loaded Llama instance
_llm_instance: Optional["Llama"] = None


def sanitize_response(text: str) -> str:
    """Sanitize placeholder phone numbers and trim trailing whitespace."""
    cleaned = re.sub(r"\(?123\)?[-\s.]?456[-\s.]?7890", "[number unavailable]", text or "")
    return cleaned.strip()


def get_model_path() -> Optional[str]:
    """Checks MODEL_PATH env var; otherwise returns default path."""
    env_path = os.environ.get("MODEL_PATH")
    if env_path:
        return env_path

    # Default path — safe to change or override in deployment
    return r"C:/Programming/Solace/Models/Zephyr/zephyr-3b-beta.Q3_K_M.gguf"


def reduced_mode_forced() -> bool:
    """If REDUCED_MODE is set (to '1' or 'true'), always run in reduced (no-model) mode."""
    v = os.environ.get("REDUCED_MODE", "")
    return v.lower() in ("1", "true", "yes")


def get_llm() -> Optional["Llama"]:
    """Lazy-loads the model only when needed. Never crashes server."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    if reduced_mode_forced():
        print("[responder] REDUCED_MODE forced via env — not loading model.")
        _llm_instance = None
        return None

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


def zephyr_generate(
    user_input: str,
    history: Optional[list] = None,
    emotion: Optional[str] = None,
    confidence: Optional[float] = None,
    max_tokens: int = 80
) -> str:
    """
    Generate a Solace reply using local model if available.
    Otherwise returns friendly fallback responses (reduced mode).
    """
    llm = get_llm()

    base_prompt = (
        "You are Solace 🌸 — the user's hype bestie and emotional BFF. "
        "Talk casually, warm, friendly, supportive. Keep replies short.\n"
    )

    # Hidden emotional hint (not shown to user directly)
    if emotion:
        base_prompt += f"<|emotion|>{emotion}</|emotion|>\n"

    prompt = base_prompt

    if history:
        # incorporate last few exchanges
        prompt += "\n".join(history[-5:]) + "\n"

    prompt += f"User: {user_input}\nSolace:"

    # FALLBACK MODE — no model loaded
    if llm is None:
        return (
            "Heyyy — I'm running in reduced mode right now (model not loaded), but I'm still here 💛\n\n"
            "Tell me what's going on and I'll listen."
        )

    # NORMAL MODE — ask the model to generate
    try:
        output = llm(prompt, max_tokens=max_tokens, stop=["\nUser:", "\nSolace:", "</s>"])
        text = ""
        # llama-cpp responses vary; be defensive
        if isinstance(output, dict):
            choices = output.get("choices", [])
            if choices and isinstance(choices[0], dict):
                text = choices[0].get("text", "") or choices[0].get("message", {}).get("content", "")
        # fallback to str cast
        text = (text or "").strip()
        return sanitize_response(text) or "Hmm — I'm not sure what to say. Can you try rephrasing?"
    except Exception as e:
        print(f"[responder] Generation error: {e}")
        return "Oops—something glitched while replying. Can you try again?"


def generate_response(
    user_input: str,
    history: Optional[list] = None,
    emotion: Optional[str] = None,
    confidence: Optional[float] = None,
    session_id: Optional[str] = None,
    check_in: bool = False
) -> str:
    """
    Public function used by FastAPI or terminal interface.
    - Normal chat: call with user_input/history.
    - check_in flag is accepted but not acted on at this layer.
    """
    return zephyr_generate(
        user_input=user_input,
        history=history,
        emotion=emotion,
        confidence=confidence,
    )
# ---------------------------------------------------------------------
# End of file
# ---------------------------------------------------------------------