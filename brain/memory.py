# memory.py
from collections import defaultdict, deque

# In-memory message store: user_id -> list of messages
chat_history = defaultdict(lambda: deque(maxlen=10))  # Store up to last 10 lines per user

def add_to_history(user_id: str, user_input: str, bot_reply: str):
    chat_history[user_id].append(f"User: {user_input}")
    chat_history[user_id].append(f"Solace: {bot_reply}")

def get_history(user_id: str):
    return list(chat_history[user_id])
def reset_history():
    global chat_history
    chat_history = defaultdict(lambda: deque(maxlen=10))