from pymongo import MongoClient
from uuid import uuid4
import numpy as np
import faiss
import os
import threading

from .models.person import Person
from .deepface_encapsulator import FeatureExtractor

class ThreadSafeFaissIndex:
    def __init__(self, index_path) -> None:
        os.environ['KMP_DUPLICATE_LIB_OK'] = "True"
        self.index_path = index_path
        self.index = self.read_faiss_index()
        self.lock = threading.Lock()
       
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

        with self.lock:
            self.index.add_with_ids(embedding, ids)
    
    def search(self, embedding, k):
        """
        Adds a given vector to the FAISS index with a specified ID.
        
        Args:
            vector (np.array): The feature vector to be added.
            ids (np.array.int64): The unique identifier for the vector.
        """

        with self.lock:
            return self.index.search(embedding, k)
    

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

        self.index = ThreadSafeFaissIndex(index_path=index_path)

    def insert_new_person(self, embedding_id, location, time):
        """
        Inserts a new person into the database with a unique ID and location.
        
        Args:
            id (UUID): The unique identifier for the new person.
            location (tuple): The location of the new person sighting.
        """
        return Person.create_person(self.db, embedding_id=embedding_id,  location=location, time=time)
    
    def insert_new_sighting(self, embedding_id, new_embedding_id, location, time):
        """
        Inserts a new sighting of an existing person identified by ID with a new location.
        
        Args:
            id (UUID): The unique identifier of the existing person.
            new_id (UUID): The unique identifier for the new sighting.
            location (tuple): The location of the new sighting.
        """
        return Person.add_sighting(self.db, embedding_id=embedding_id, new_embedding_id=new_embedding_id, location=location, time=time)

    def search_person_by_id(self, id):
        return self.db['persons'].find_one({'embeddings_ids': int(id)})
    
    def insert_name(self, _id, name):
        return self.db['persons'].update_one({'_id': _id}, {'$set': {'name': name}})
    
    def insert(self, embedding, location, time):
        """
        Inserts a feature vector and location into the database, updating existing person records or creating new ones as necessary.
        
        Args:
            vector (np.array): The feature vector of the person to insert.
            location (tuple): The location of the person to insert.

        """

        distances, ids = self.index.search(np.expand_dims(embedding, axis=0), 1)

        new_embedding_ids = DataManager.generate_ids(1)

        new_embedding_id = new_embedding_ids[0]
        
        if distances.size > 0 and distances[0][0] <= FeatureExtractor.FACENET_THRESHOLD_EUCLIDEAN:

            db_resp = self.insert_new_sighting(embedding_id=ids[0][0], new_embedding_id=new_embedding_id, location=location, time=time)
        else:
            db_resp = self.insert_new_person(new_embedding_id, location, time=time)
        if db_resp.acknowledged:
            self.index.add_embedding_to_faiss(embedding=np.array(embedding), ids=new_embedding_ids)

    @staticmethod
    def generate_ids(n: int):
        return np.array([(uuid4().int & ((1 << 64) - 1)) for _ in range(n)]).astype('int64')