from datetime import datetime
from uuid import uuid4

class Person:
    def __init__(self):
        self.id = str(uuid4())
        # self.embedding = None
        self.embeddings_ids = []
        self.locations_time = []

    def to_dict(self):
        # Convert the object to a dictionary, suitable for MongoDB.
        return {
            "id": self.id,
            "embeddings_ids": self.embeddings_ids,
            "locations" : self.locations_time
        }
    
    def save(self, db):
        # This method inserts the object into the MongoDB collection.
        return db.persons.insert_one(self.to_dict())


    @classmethod
    def create_person(cls, db, embedding_id, location, time=datetime.now()):
        # This class method creates a person and inserts it's embedding and location_time to the db.
        p = Person()
        location_time = {
            'coordinates' : location,
            'date': time
        }
        p.embeddings_ids.append(int(embedding_id))
        p.locations_time.append(location_time)

        response = p.save(db)

        return response

    @classmethod
    def add_sighting(cls, db, embedding_id, new_embedding_id, location, time=datetime.now()):
        # This class method appends a embedding and location to the person.
        response = db['persons'].update_one(
            {"embeddings_ids": int(embedding_id)},
            {"$push": {"locations" : {'coordinates' : location, 'date': time}, "embeddings_ids" : int(new_embedding_id)}}
        )
        return response