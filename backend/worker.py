import os
from redis import Redis
from rq import Worker, Queue, Connection

# Connect to the exact same Redis database as the API
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
redis_conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    # Establish the connection context
    with Connection(redis_conn):
        # Create a worker that specifically listens to the 'fraud_queue'
        worker = Worker(['fraud_queue'])
        
        print("Worker is awake and listening to 'fraud_queue'...")
        
        # Start the infinite loop where the worker waits for new tasks
        worker.work()