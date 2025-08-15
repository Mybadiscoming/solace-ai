🌸 Solace — AI Chat Assistant

Solace is an emotion-aware AI assistant built with FastAPI (backend) and Vite + React (frontend).
It can detect user emotions, remember conversation history, and respond with empathy.


---

🚀 Running Locally

1️⃣ Backend (FastAPI)

# Make sure you are in the project root
# (where main.py and requirements.txt are located)

# Install Python dependencies
pip install -r requirements.txt

# Run the backend server
python main.py web

Backend will start at http://localhost:8000.


---

2️⃣ Frontend (Vite + React)

# Navigate to frontend folder
cd frontend   # or the folder containing package.json

# Install dependencies
npm install

# Run the development server
npm run dev

Frontend will start at http://localhost:5173.


---

🌐 Deployment on Hugging Face Spaces

Project structure example:

.
├── main.py
├── requirements.txt
├── brain/
│   ├── memory.py
│   ├── responder.py
│   ├── sentiment.py
│   └── ...
├── interface/
│   └── terminal_chat.py
├── frontend/
│   ├── dist/          # Built frontend files
│   └── ...
├── README.md

Hugging Face Settings

SDK: Docker

App File: Dockerfile

Hardware: CPU Basic (free)


Push your code and Spaces will build & deploy automatically.


---

📂 API Endpoints

GET /

Returns:

{ "message": "Solace backend is running ✨" }

POST /api/chat

Request:

{
  "user_id": "123",
  "text": "Hey, how are you?"
}

Response:

{
  "response": "I'm feeling good today, thanks for asking!",
  "emotion": "happy",
  "confidence": 0.92
}


---

⚡ Features

Emotion detection with scikit-learn

Memory of past chats

Friendly, empathetic responses

Frontend + backend fully integrated



---

📜 License

MIT License