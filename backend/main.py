from fastapi import FastAPI, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
import os
import json
import asyncio
import requests
from database import transactions_collection
#  from ai_agent import evaluate_transaction

app = FastAPI(title="Sentinel AI API")

# This tells the API that it is safe to accept connections from your React app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this would be restricted to "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Connection Manager
class ConnectionManager:
    """Manages active WebSocket connections to the dashboard."""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: dict):
        # Loops through every connected browser and sends the JSON data
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # If a connection is dead, we'll clean it up later via disconnect
                pass

manager = ConnectionManager()

# Set up the connection to our Redis container (defaults to 'redis:6379' inside Docker)
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
redis_conn = Redis.from_url(redis_url)

# Create a 'Waiting Room' queue called 'fraud_queue' inside Redis
task_queue = Queue('fraud_queue', connection=redis_conn)

# --- WebSocket Route ---
@app.websocket("/ws/transactions")
async def websocket_endpoint(websocket: WebSocket):
    """The 'Phone Line' the frontend will call to listen for updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- THE INTERNAL WEBHOOK ---
@app.post("/internal/broadcast")
async def internal_broadcast(transaction_data: dict):
    # The Worker container hits this route. 
    # Because this runs IN the API container, it can successfully use the manager!
    await manager.broadcast(transaction_data)
    return {"status": "broadcasted"}

# Pydantic Model: This strictly enforces what a valid transaction must look like
class Transaction(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    timestamp: str

# Our background worker function
def analyze_fraud(transaction_data: dict):
    # 1. Print to the console so we know the worker picked it up
    print(f"Worker analyzing transaction: {transaction_data['transaction_id']}")

    # # 2. Hand the data to Gemini and wait for its verdict!
    # ai_decision = evaluate_transaction(transaction_data)

    is_fraud = transaction_data['amount'] > 8000.00
    
    # # 3. Update the transaction dictionary with the AI's exact findings
    # transaction_data["status"] = ai_decision.get("status", "flagged")
    # transaction_data["fraud_score"] = ai_decision.get("fraud_score", 0.99)

    transaction_data["status"] = "flagged" if is_fraud else "approved"
    transaction_data["fraud_score"] = 0.99 if is_fraud else 0.05
    
    # 4. Permanently save the updated dictionary into the MongoDB vault
    # PyMongo automatically converts the Python dictionary into a BSON document
    transactions_collection.insert_one(transaction_data)
    
    # Broadcast the result to the dashboard immediately!
    # We use a helper to run the async broadcast from our sync worker
    # loop = asyncio.get_event_loop()

    # We remove the MongoDB internal ID before sending to the frontend
    if "_id" in transaction_data:
        transaction_data["_id"] = str(transaction_data["_id"])

    # Have the worker send an HTTP request to the API container using Docker's internal network name ('api')
    try:
        requests.post("http://api:8000/internal/broadcast", json=transaction_data)
    except Exception as e:
        print(f"Failed to bridge to API: {e}")
    
    # # we'll ensure the 'manager' can broadcast from the worker.
    # asyncio.run_coroutine_threadsafe(manager.broadcast(transaction_data), loop)

    # 5. Print the AI's verdict to the console so we can watch it work
    # print(f"AI Verdict: {transaction_data['status'].upper()} (Score: {transaction_data['fraud_score']}) | Saved to Vault")
    print(f"Verdict: {transaction_data['status'].upper()} | Sent to API Broadcaster")
    return True

@app.get("/health")
def health_check():
    # Simple endpoint to verify the API is running
    return {"status": "healthy", "service": "sentinel-api"}

@app.post("/transactions", status_code=status.HTTP_202_ACCEPTED)
def submit_transaction(transaction: Transaction):
    # 1. Take the incoming transaction and convert it to a standard dictionary
    txn_dict = transaction.model_dump()
    
    # 2. Shove the job into the Redis queue to be processed asynchronously
    # We pass the target function (analyze_fraud) and its arguments (txn_dict)
    task_queue.enqueue(analyze_fraud, txn_dict)
    
    # 3. Immediately respond to the user so they aren't kept waiting
    return {
        "message": "Transaction queued for review", 
        "transaction_id": transaction.transaction_id
    }