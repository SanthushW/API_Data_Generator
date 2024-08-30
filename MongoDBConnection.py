from pymongo import MongoClient
import json

def insert_to_mongodb(file_path, db_name, collection_name):
    """Insert the JSON data from a file into a MongoDB collection."""
    # Load the JSON data from the file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://wsanthush2002:a8TsMPnIvtBvl6Cd@clustertraindatagenerat.x9d1i.mongodb.net/?retryWrites=true&w=majority&appName=ClusterTrainDataGenerator')  # Adjust the connection string as needed
    db = client[db_name]
    collection = db[collection_name]
    
    # Insert the data into the collection
    if isinstance(data, list):
        # If the JSON file contains a list of documents
        result = collection.insert_many(data)
        print(f"Inserted {len(result.inserted_ids)} documents into the collection '{collection_name}' in database '{db_name}'.")
    else:
        # If the JSON file contains a single document
        result = collection.insert_one(data)
        print(f"Inserted 1 document into the collection '{collection_name}' in database '{db_name}'.")

# Configuration
FILE_PATH = 'train_tracking_data.json'  # Path to your JSON file
DB_NAME = 'train_database'
COLLECTION_NAME = 'train_tracking_data'

# Insert the JSON data into MongoDB
insert_to_mongodb(FILE_PATH, DB_NAME, COLLECTION_NAME)
