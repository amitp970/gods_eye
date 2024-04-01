import asyncio
import aiofiles
import os
from typing import List
from pymongo import MongoClient
import faiss
from deepface_encapsulator import FeatureExtractor
from data_manager import DataManager
import numpy as np 
import cv2

class FaceProcessor:
    """
    A class to encapsulate functionalities for processing images for facial recognition.
    This includes monitoring a specified folder for new images, processing those images
    using DeepFace for facial recognition, and performing FAISS searches for similarity matching.

    Attributes:
        folder_path (str): The path to the folder to monitor for new images.
        db_conn: The database connection object.
        model: The DeepFace model for facial recognition.
        index: The loaded FAISS index for similarity searches.
    """
    def __init__(self, folder_path: str, index_path, db_path):
        """
        Initializes the FaceProcessor with the specified folder path, database connection,
        DeepFace model, and FAISS index URL.

        Args:
            folder_path (str): The path to the folder to monitor for new images.
            db_conn: The database connection object.
            model: The DeepFace model for facial recognition.
            index_url (str): The URL to the FAISS index file.
        """
        self.folder_path = folder_path
        self.model = FeatureExtractor('Facenet')
        self.data_manager = DataManager(index_path, db_path)


    async def find_files(self) -> List[str]:
        """
        Asynchronously finds and lists all files in the specified folder path.

        Returns:
            List[str]: A list of file paths to the found files.
        """
        locations = dict()
        for entry in os.listdir(self.folder_path):
            path = os.path.join(self.folder_path, entry)
            if os.path.isdir(path):
                locations[str(entry)] = []
                for file_path in os.listdir(path):
                    if os.path.isfile(os.path.join(path, file_path)):
                        locations[str(entry)].append(os.path.join(path, file_path))

        return locations

    async def process_file(self, file_path: str):
        """
        Asynchronously processes a given file, potentially involving facial recognition tasks.

        Args:
            file_path (str): The path to the file to be processed.
        """
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()

            print(f"Processed content of {file_path}")
        os.remove(file_path)
        print(f"Deleted {file_path}")
    
    
    async def process_files(self, location: str, file_paths: str):
        """
        Asynchronously processes files, potentially involving facial recognition tasks.

        Args:
            file_path (str): The path to the file to be processed.
        """
        for file_path in file_paths:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
                image_data = np.frombuffer(content, dtype=np.uint8)
                image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

            embedding = self.model.get_embedding(image)
            await self.data_manager.insert(np.array(embedding).astype("float32"), location)
            print(f"Processed content of {file_path}")
            os.remove(file_path)
            print(f"Deleted {file_path}")

    async def monitor_folder(self, interval: int = 5):
        """
        Continuously monitors the specified folder for new files and processes them accordingly.

        Args:
            interval (int): The interval (in seconds) at which to check the folder for new files.
        """
        while True:
            locations = await self.find_files()
            if locations:
                await asyncio.gather(*(self.process_files(location, locations[location]) for location in locations))
            await asyncio.sleep(interval)

async def main():
    """
    Main function to create an instance of FaceProcessor and start the folder monitoring process.
    """
    folder_path = "./data/faces"
    index_path = "./data/faiss/faces_index.index"
    db_path = r"mongodb://localhost:27017/"

    print(os.getcwd())

    try:
        face_processor = FaceProcessor(folder_path, index_path, db_path)
        await face_processor.monitor_folder()
    except Exception as e:
        import traceback
        print(traceback.print_exc())
    finally:
        face_processor.data_manager.save_faiss()

if __name__ == "__main__":
    asyncio.run(main())
