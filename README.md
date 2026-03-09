# 🛡️ Sentinel AI: Real-Time Fraud Detection Pipeline

A full-stack, event-driven microservices architecture designed to simulate, stream, and evaluate financial transactions in real-time. Sentinel AI uses a Retrieval-Augmented Generation (RAG) pipeline powered by Google's Gemini 3 to enforce compliance rules and detect fraudulent activity on the fly.

## 🚀 The Tech Stack
* **Frontend:** React, Vite, Tailwind CSS, Lucide Icons
* **Backend:** FastAPI (Python), WebSockets
* **Message Queue:** Redis + RQ (Redis Queue)
* **Database:** MongoDB
* **AI Engine:** LangChain, Google Gemini 3 Flash, FAISS Vector Database
* **Infrastructure:** Docker & Docker Compose

## 🧠 System Architecture

1. **The Firehose:** A Python generator that blasts synthetic financial transactions.
2. **The Waiting Room:** A Redis queue that catches the massive influx of data so the API doesn't crash.
3. **The Worker:** A background process that pulls jobs from the queue and evaluates them against a set of compliance rules (using Gemini AI or local mock rules).
4. **The Vault:** MongoDB permanently stores the transaction and the AI's verdict.
5. **The Broadcaster:** FastAPI opens a WebSocket to push the verdict to the frontend instantly.
6. **The Command Center:** A real-time React dashboard that visually flags fraudulent transactions.

---

## 🛠️ Quick Start Guide

### Prerequisites
Make sure you have [Docker](https://www.docker.com/) and [Node.js](https://nodejs.org/) installed on your machine.

### 1. Environment Setup
Create a `.env` file inside the `backend/` directory and add your Google API Key:
```text
GOOGLE_API_KEY=your_gemini_api_key_here

### 2. Boot the Infrastructure
Start the backend microservices (FastAPI, Redis, MongoDB, and the background worker) using Docker:
docker compose up -d --build

### 3. Start the Command Center (Frontend)
Open a new terminal, navigate to the frontend folder, and start the React app:
cd frontend
npm install
npm run dev

The dashboard will be available at http://localhost:5173.

### 4. Turn on the Firehose
Open one final terminal and run the synthetic traffic generator to watch the system process transactions in real-time:
python backend/traffic_generator.py

🛑 Note on AI Rate Limits
If you are using the free tier of the Gemini API, the firehose will quickly exhaust your quota (Error 429). To bypass this for UI testing,
a local "Mock Bypass" rule has been implemented in the worker logic to simulate the AI's decision-making process.
