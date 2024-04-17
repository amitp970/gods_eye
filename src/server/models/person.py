from typing import List
from cv2.typing import MatLike
from uuid import UUID

from location import Location

class Person:
    def __init(self, ids = [], location = None, img_vct = None):
        self.ids: List[UUID] = []
        self.location: List[Location] = Location
        self.img_vct: MatLike = img_vct

