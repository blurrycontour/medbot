import os
import logging
from typing import Optional, Iterator, Dict, Any
import pymongo
from pymongo.collection import Collection

logger = logging.getLogger(__name__)

class DataBase:
    """
    Class serving as the main interface to the application.
    """
    instance = None
    # class-level annotations for static analysis
    users: Collection
    reminders: Collection

    def __init__(self):
        if not DataBase.instance:
            self.connect()
            DataBase.instance = self

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
        # annotate collections for static analysis
        self.users: Collection = self.db["users"]
        self.reminders: Collection = self.db["reminders"]

        try:
            client.server_info()
            logger.info("Connected to MongoDB")
        except pymongo.errors.ServerSelectionTimeoutError:
            logger.error("Failed to connect to MongoDB")

    # Convenience helper methods
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.users.find_one({'user_id': user_id})

    def add_reminder(self, user_id: int, time_hhmm: str) -> str:
        res = self.reminders.insert_one({'user_id': user_id, 'time': time_hhmm, 'confirmed': 0, 'last_sent_date': None})
        return str(res.inserted_id)

    def update_reminder(self, reminder_obj_id, fields: Dict[str, Any]):
        self.reminders.update_one({'_id': reminder_obj_id}, {'$set': fields})

    def find_reminders_for_user(self, user_id: int) -> Iterator[Dict[str, Any]]:
        return self.reminders.find({'user_id': user_id})


db = DataBase()
