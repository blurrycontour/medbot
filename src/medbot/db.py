import pymongo
import os
from dotenv import load_dotenv

class DataBase:
    """
    Class serving as the main interface to the application.
    """
    instance = None

    def __init__(self):
        if not DataBase.instance:
            load_dotenv()
            self.connect()
            DataBase.instance = self

    def connect(self):
        """ Connect to database """
        db_name = f"{os.getenv('ENVIRONMENT').lower()}-medbot"
        mongodb_string = os.getenv('MONGODB_STRING')
        print("Connecting to MongoDB")
        client = pymongo.MongoClient(
            mongodb_string
        )
        self.db = client[db_name]
        self.users_collection = self.db["users"]
        self.reminders_collection = self.db["reminders"]
        try:
            client.server_info()
            print("Connected to MongoDB")
        except pymongo.errors.ServerSelectionTimeoutError:
            print("Failed to connect to MongoDB")

db = DataBase()
