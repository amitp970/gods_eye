from datetime import datetime
from datetime import datetime
import asyncio


class Person:
    def __init__(self, ids, locations):
        self.ids = ids
        self.locations_time = [(loc, datetime.now()) for loc in locations]

    async def save(self, db):
        # This method inserts the object into the MongoDB collection.
        await db.persons.insert_one(self.to_dict())

    def to_dict(self):
        # Convert the object to a dictionary, suitable for MongoDB.
        return {
            "ids": self.ids,
            "locations" : self.locations_time
        }

    @classmethod
    async def add_sighting(cls, db, existing_id, new_id, location):
        # This class method appends a new id and location to the person.
        response = await db.persons.update_one(
            {"ids": existing_id},
            {"$push": {"ids" : new_id, "locations" : (location, datetime.now())}}
        )
        print(response)
        print('Added sighting')