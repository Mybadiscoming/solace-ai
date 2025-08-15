from llama_cpp import Llama
from brain.sentiment import detect_emotion
import os

# Load Zephyr model
llm = Llama(
    model_path="C:/Programming/Solace/Models/Zephyr/zephyr-3b-beta.Q3_K_M.gguf",
    n_ctx=1024,
    n_batch=12,
    n_gpu_layers=0,  # CPU only
    use_mlock=False
)

def zephyr_generate(user_input, history=None, emotion=None, confidence=None, max_tokens=80):
    prompt = ""
    if history:
        prompt += "\n".join(history[-5:]) + "\n"

    base_prompt = (
        "You are Solace, a kind, emotionally intelligent AI best friend. "
        "Understand the user's emotion and respond supportively. "
        "Talk casually like a close friend or teen, with emojis and slang.\n"
    )

    # Handle None values for emotion and confidence
    emotion_str = emotion.lower() if emotion else "neutral"
    confidence_str = f"{confidence:.2f}" if confidence is not None else "1.00"

    prompt += (
        f"{base_prompt}"
        f"User seems to be feeling: {emotion_str} ({confidence_str})\n"
        f"User: {user_input}\nSolace:"
    )

    

    try:
    
        output = llm(
            prompt,
            max_tokens=max_tokens,
            stop=["\nUser:", "\nSolace:", "</s>"]
        )
        

        final_output = output["choices"][0]["text"]

        return final_output.strip()

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Oops, something went wrong: {e}"# Main entry point
def generate_response(user_input: str, history: list[str] = None, emotion=None, confidence=None) -> str:
    return zephyr_generate(
        user_input=user_input,
        history=history,
        emotion=emotion,
        confidence=confidence
    )