from pymongo import MongoClient
from uuid import uuid4
import numpy as np
import faiss
import os

from .modals.person import Person
from .deepface_encapsulator import FeatureExtractor

class DataManager:
    """
    A class to manage data storage and retrieval operations, including interfacing
    with MongoDB for person data and FAISS for feature vector indexing and search.
    
    Attributes:
        db (MongoClient): A client connected to the MongoDB database.
        index (faiss.Index): A FAISS index for efficient similarity search of feature vectors.
    
    Args:
        index_path (str): The file path to the FAISS index.
        db_path (str): The path/url to the database
    """
    
    def __init__(self, mongodb_url, index_path) -> None:
        client = MongoClient(mongodb_url)

        self.db = client['gods_eye']
        self.collection = self.db['persons']

        self.collection.create_index([('embeddings_ids', 1)])

        os.environ['KMP_DUPLICATE_LIB_OK'] = "True"
        self.index_path = index_path
        self.index = self.read_faiss_index()

    def read_faiss_index(self):
            try:
                index = faiss.read_index(self.index_path)
            except Exception as e:
                print(e)
                index = faiss.IndexIDMap(faiss.IndexFlatL2(128))
            return index
    
    def save_faiss(self):
        faiss.write_index(self.index, self.index_path)

    def add_embedding_to_faiss(self, embedding, ids):
        """
        Adds a given vector to the FAISS index with a specified ID.
        
        Args:
            vector (np.array): The feature vector to be added.
            ids (np.array.int64): The unique identifier for the vector.
        """

        if len(embedding.shape) == 1:
            embedding = np.expand_dims(embedding, axis=0)

        self.index.add_with_ids(embedding, ids)

    def insert_new_person(self, embedding, embedding_id, location, time):
        """
        Inserts a new person into the database with a unique ID and location.
        
        Args:
            id (UUID): The unique identifier for the new person.
            location (tuple): The location of the new person sighting.
        """
        return Person.create_person(self.db, embedding=embedding, embedding_id=embedding_id,  location=location, time=time)
    
    def insert_new_sighting(self, embedding_id, new_embedding_id, location, time):
        """
        Inserts a new sighting of an existing person identified by ID with a new location.
        
        Args:
            id (UUID): The unique identifier of the existing person.
            new_id (UUID): The unique identifier for the new sighting.
            location (tuple): The location of the new sighting.
        """
        return Person.add_sighting(self.db, embedding_id=embedding_id, new_embedding_id=new_embedding_id, location=location, time=time)

    # def get_closest_embedding(self, embedding):
    #     query_resp = self.db['person'].aggregate([
    #         {"$addFields": { 
    #             "target_embedding": embedding  # Ensure 'embedding' is defined and an array
    #         }},
    #         {"$unwind": { "path": "$embedding", "includeArrayIndex": "embedding_index" }},
    #         {"$unwind": { "path": "$target_embedding", "includeArrayIndex": "target_index" }},
    #         {"$project": {
    #             "id": 1,
    #             "embedding": 1,
    #             "target_embedding": 1,
    #             "compare": {"$cmp": ['$embedding_index', '$target_index']}
    #         }},
    #         {"$match": {"compare": 0}},  # Ensure comparison is 0 (matching indexes)
    #         {"$group": {
    #             "_id": "$id",
    #             "distance": {"$sum": {"$pow": [{"$subtract": ['$embedding', '$target_embedding']}, 2]}}
    #         }},
    #         {"$project": {
    #             "_id": 1,
    #             "distance": {"$sqrt": "$distance"}
    #         }},
    #         {"$match": {"distance": {"$lte": 20}}},
    #         {"$sort": {"distance": 1}},
    #         {"$limit": 1}
    #     ])

    #     print(query_resp)


    #     results = list(query_resp)
        
    #     if results:
    #         return results[0]

    #     print("NO MATCHING DOCUMENTS!")
    #     return None 

    def insert(self, embedding, location, time):
        """
        Inserts a feature vector and location into the database, updating existing person records or creating new ones as necessary.
        
        Args:
            vector (np.array): The feature vector of the person to insert.
            location (tuple): The location of the person to insert.

        """

        distances, ids = self.index.search(np.expand_dims(embedding, axis=0), 1)
        print(f'distances: {distances}, ids: {ids}' )

        new_embedding_ids = DataManager.generate_ids(1)

        new_embedding_id = new_embedding_ids[0]
        
        if distances.size > 0 and distances[0][0] <= FeatureExtractor.FACENET_THRESHOLD_EUCLIDEAN:
            # print(f"response: {response}")
            db_resp = self.insert_new_sighting(embedding_id=ids[0][0], new_embedding_id=new_embedding_id, location=location, time=time)
            print('added sighting of an existing person')
        else:
            db_resp = self.insert_new_person(embedding, new_embedding_id, location, time=time)
            print('added a new person')
        if db_resp.acknowledged:
            self.add_embedding_to_faiss(embedding=np.array(embedding), ids=new_embedding_ids)

    @staticmethod
    def generate_ids(n: int):
        return np.array([(uuid4().int & ((1 << 64) - 1)) for _ in range(n)]).astype('int64')