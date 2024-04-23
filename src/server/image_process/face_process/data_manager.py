import faiss
import asyncio
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from uuid import uuid4
import numpy as np
from modals.person import Person
from deepface_encapsulator import FeatureExtractor

class DataManager:
    """
    A class to manage data storage and retrieval operations, including interfacing
    with MongoDB for person data and FAISS for feature vector indexing and search.
    
    Attributes:
        db (AsyncIOMotorClient): An asynchronous client connected to the MongoDB database.
        index (faiss.Index): A FAISS index for efficient similarity search of feature vectors.
    
    Args:
        index_path (str): The file path to the FAISS index.
        db_path (str): The path/url to the database
    """
    
    def __init__(self, index_path, db_path) -> None:
        client = AsyncIOMotorClient(db_path)
        self.db = client['gods_eye']

        # NOTE: figure out how to take care of the faiss loading
        self.index = DataManager.read_faiss_index(index_path)
    
    def read_faiss_index(index_path):
        try:
            index = faiss.read_index(index_path)
        except Exception as e:
            print(e)
            index = faiss.IndexIDMap(faiss.IndexFlatL2(128))
        return index
    
    def save_faiss(self):
        faiss.write_index(self.index, r".\data\faiss\faces_index.index")

    async def async_faiss_search(self, query_vectors, k=1):
        """
        Performs an asynchronous FAISS search on the given query vectors to find the top k nearest neighbors.
        
        Args:
            query_vectors (np.array): The query vectors for the FAISS search.
            k (int, optional): The number of nearest neighbors to find. Defaults to 1.
        
        Returns:
            tuple: A tuple of two elements (distances, ids) where distances is a 2D numpy array of shape
                   (n, k) containing the distances of the nearest neighbors, and ids is a 2D numpy array of shape
                   (n, k) containing the ids of the nearest neighbors.
        """
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.index.search, query_vectors, k)
        return result

    async def async_add_embedding_to_faiss(self, embedding, ids):
        """
        Asynchronously adds a given vector to the FAISS index with a specified ID.
        
        Args:
            vector (np.array): The feature vector to be added.
            ids (np.array.int64): The unique identifier for the vector.
        """
        # loop = asyncio.get_running_loop()

        # def add_embedding_sync(embedding):
        #     if len(embedding.shape) == 1:
        #         embedding = np.expand_dims(embedding, axis=0)
        #     self.index.add_with_ids(embedding, ids)

        # await loop.run_in_executor(None, add_embedding_sync, embedding)

        if len(embedding.shape) == 1:
            embedding = np.expand_dims(embedding, axis=0)

        self.index.add_with_ids(embedding, ids)

    async def insert_new_person(self, id, location):
        """
        Inserts a new person into the database with a unique ID and location.
        
        Args:
            id (UUID): The unique identifier for the new person.
            location (tuple): The location of the new person sighting.
        """
        person = Person(ids=[str(id),], locations=[location,])
        await person.save(self.db)
    
    async def insert_new_sighting(self, id, new_id, location):
        """
        Inserts a new sighting of an existing person identified by ID with a new location.
        
        Args:
            id (UUID): The unique identifier of the existing person.
            new_id (UUID): The unique identifier for the new sighting.
            location (tuple): The location of the new sighting.
        """
        await Person.add_sighting(self.db, str(id), str(new_id), location)

    async def insert(self, embedding, location):
        """
        Inserts a feature vector and location into the database, updating existing person records or creating new ones as necessary.
        
        Args:
            vector (np.array): The feature vector of the person to insert.
            location (tuple): The location of the person to insert.
        """
        distances, ids = await self.async_faiss_search(np.expand_dims(embedding, axis=0))

        new_ids = DataManager.generate_ids(1)
        new_id = new_ids[0]

        if distances.size > 0 and distances[0][0] <= FeatureExtractor.find_threshold():
            await self.insert_new_sighting(ids[0][0], new_id, location)
            print('added sighting of an existing person')
        else:
            await self.insert_new_person(new_id, location)
            print('added a new person')
        
        await self.async_add_embedding_to_faiss(embedding=embedding, ids=new_ids)

    def generate_ids(n: int):
        return np.array([(uuid4().int & ((1 << 64) - 1)) for _ in range(n)]).astype('int64')
