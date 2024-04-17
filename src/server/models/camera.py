from .location import Location
from uuid import UUID, uuid4

class Camera:
    def  __init__(self, id = uuid4(), location = None):  
        self.id: UUID = id
        self.location: Location = location
    