import time
import random
import requests
from faker import Faker

# Initialize the Faker library to generate realistic synthetic data
fake = Faker()

# Define the endpoint URL for our local FastAPI container
# We use localhost because we are running this script outside of Docker
API_URL = "http://localhost:8000/transactions"

def generate_transaction():
    # Create a dictionary representing a single fake financial transaction
    return {
        # Generate a random unique identifier for the transaction
        "transaction_id": fake.uuid4(),
        
        # Generate a realistic-looking fake username
        "user_id": fake.user_name(),
        
        # Generate a random transaction amount between $5 and $10,000, rounded to 2 decimals
        "amount": round(random.uniform(5.00, 10000.00), 2),
        
        # Generate a current timestamp in standard ISO 8601 format
        "timestamp": fake.iso8601()
    }

def run_firehose():
    # Print a startup message to the console
    print("Starting the Sentinel AI Firehose... Press Ctrl+C to stop.")
    
    # Start an infinite loop to continuously send data
    while True:
        # Generate a new random transaction payload
        payload = generate_transaction()
        
        try:
            # Send the payload as a POST request to our FastAPI endpoint
            response = requests.post(API_URL, json=payload)
            
            # Print the successfully sent transaction details to the console
            print(f"Sent: ${payload['amount']} by {payload['user_id']} | Status: {response.status_code}")
            
        except requests.exceptions.ConnectionError:
            # Catch and print an error if the FastAPI server is not running
            print("Connection failed. Is the Docker container running?")
        
        # Pause the script for a random duration between 0.1 and 1.5 seconds
        # This simulates realistic, variable user traffic and prevents overloading your laptop
        time.sleep(random.uniform(0.1, 1.5))

# Ensure the script only runs when executed directly from the terminal
if __name__ == "__main__":
    run_firehose()