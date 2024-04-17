from datetime import date
from datetime import datetime

class Location:
    def __init__(self, location = None, time=datetime.now()):
        location: str = location
        time: datetime = time