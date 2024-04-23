class Camera:
    def __init__(self, location):
        self.location = location

    async def save(self, db):
        # This method inserts the object into the MongoDB collection.
        await db.cameras.insert_one(self.to_dict())

    def to_dict(self):
        # Convert the object to a dictionary, suitable for MongoDB.
        return {
            "location" : self.location
        }