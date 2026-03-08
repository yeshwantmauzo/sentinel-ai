from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "sentinel-api"}

def test_submit_transaction():
    # 1. Create a fake transaction payload to send to our API
    payload = {
        "transaction_id": "txn_123",
        "user_id": "user_456",
        "amount": 5000.00,
        "timestamp": "2026-03-08T12:00:00Z"
    }
    
    # 2. Simulate a POST request to the /transactions endpoint
    response = client.post("/transactions", json=payload)
    
    # 3. Assert that the API accepted the request (202 means Accepted for background processing)
    assert response.status_code == 202
    
    # 4. Assert that the API returned the correct success message
    assert response.json()["message"] == "Transaction queued for review"