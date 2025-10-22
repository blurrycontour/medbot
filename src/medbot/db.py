import os
import logging
from typing import Iterator, Dict, Any
import pymongo
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

class Database:
    """
    Class serving as the main interface to the application.
    """
    instance = None

    def __init__(self):
        if not Database.instance:
            self.connect()
            Database.instance = self

    def connect(self):
        """ Connect to database """
        db_name = f"{os.getenv('ENVIRONMENT').lower()}"
        mongodb_string = os.getenv('MONGODB_STRING')
        logger.info("Connecting to MongoDB")
        client = pymongo.MongoClient(
            mongodb_string
        )
        self.db = client[db_name]

        # collections
        self.users: Collection = self.db["users"]
        self.reminders: Collection = self.db["reminders"]

        try:
            client.server_info()
            logger.info("Connected to MongoDB")
        except pymongo.errors.ServerSelectionTimeoutError:
            logger.error("Failed to connect to MongoDB")

    # Convenience helper methods
    def get_user(self, user_id: int) -> Dict[str, Any]:
        return self.users.find_one({'user_id': user_id}) or {}

    def get_users(self) -> Iterator[Dict[str, Any]]:
        return self.users.find()

    def add_reminder(self, reminder_data: Dict[str, Any]) -> Any:
        result = self.reminders.insert_one(reminder_data)
        return result.inserted_id

    def get_reminders(self, user_id: int) -> Iterator[Dict[str, Any]]:
        return self.reminders.find({'user_id': user_id})


db = Database()
