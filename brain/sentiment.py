from transformers import pipeline

# Load emotion classification pipeline (only loads once)
emotion_classifier = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
    return_all_scores=True 
)

GREETINGS = ["hi", "hello", "hey", "hii", "heyy", "yo", "sup"]

def detect_emotion(text):
    if text.lower().strip() in GREETINGS:
        return "joy", 0.99  # override with a positive emotion

    results = emotion_classifier(text)
    sorted_emotions = sorted(results[0], key=lambda x: x['score'], reverse=True)
    top_emotion = sorted_emotions[0]
    return top_emotion['label'], top_emotion['score']