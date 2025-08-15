import time
from brain.responder import generate_response

def type_print(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.01)
    print()

def start_chat():
    print("🌸 Solace: Your emotional companion 🌸")
    print("Type 'exit' to end the conversation.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            type_print("Solace: I'm here whenever you're ready to talk.\n")
            continue

        if user_input.lower() in ['exit', 'quit', 'bye']:
            type_print("Solace: Take care. You're not alone 💗")
            break

        print("Solace: ", end='', flush=True)
        generate_response(user_input)  # Streaming happens inside