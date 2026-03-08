import os
from pymongo import MongoClient

# Fetch the MongoDB connection URL from the environment.
# When running inside Docker, the hostname is 'mongodb' (matching our docker-compose service name).
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017")

# Establish a connection to the MongoDB server.
client = MongoClient(MONGO_URL)

# Select (or automatically create) a database named 'sentinel_db'.
db = client.sentinel_db

# Select (or automatically create) a collection (like a table) named 'transactions'.
# This is where we will store all the processed transaction data.
transactions_collection = db.transactions