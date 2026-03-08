from fastapi import FastAPI, status
from pydantic import BaseModel
from redis import Redis
from rq import Queue
import os
from database import transactions_collection
from ai_agent import evaluate_transaction

app = FastAPI(title="Sentinel AI API")

# Set up the connection to our Redis container (defaults to 'redis:6379' inside Docker)
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
redis_conn = Redis.from_url(redis_url)

# Create a 'Waiting Room' queue called 'fraud_queue' inside Redis
task_queue = Queue('fraud_queue', connection=redis_conn)

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

    # 2. Hand the data to Gemini and wait for its verdict!
    ai_decision = evaluate_transaction(transaction_data)
    
    # 3. Update the transaction dictionary with the AI's exact findings
    transaction_data["status"] = ai_decision.get("status", "flagged")
    transaction_data["fraud_score"] = ai_decision.get("fraud_score", 0.99)
    
    # 4. Permanently save the updated dictionary into the MongoDB vault
    # PyMongo automatically converts the Python dictionary into a BSON document
    transactions_collection.insert_one(transaction_data)
    
    # 5. Print the AI's verdict to the console so we can watch it work
    print(f"AI Verdict: {transaction_data['status'].upper()} (Score: {transaction_data['fraud_score']}) | Saved to Vault")
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