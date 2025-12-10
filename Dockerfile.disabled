##########################
# FRONTEND STAGE
##########################
FROM node:18-bullseye AS frontend
WORKDIR /app/solace-frontend

COPY solace-frontend/package*.json ./
RUN npm install --include=dev
RUN npm install -g vite
COPY solace-frontend/ ./
RUN vite build

##########################
# BACKEND STAGE
##########################
FROM python:3.10-slim AS backend
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake curl socat \
    libopenblas-dev libomp-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.2.2+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu
RUN grep -v '^torch' requirements.txt > requirements-cpu.txt && \
    pip install --no-cache-dir -r requirements-cpu.txt

COPY . .
RUN mkdir -p frontend/dist
COPY --from=frontend /app/solace-frontend/dist ./frontend/dist

EXPOSE 7860

# Run app on 8000 and forward Hugging Face's 7860 → 8000
CMD python main.py web & socat TCP-LISTEN:7860,fork TCP:localhost:8000