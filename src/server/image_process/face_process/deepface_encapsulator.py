# built-in dependencies
from typing import Any, Dict, List, Union

# 3rd party dependencies
import numpy as np
import cv2

# project dependencies
from deepface.modules import modeling, detection, preprocessing
from deepface.models.FacialRecognition import FacialRecognition
from deepface import DeepFace

class FeatureExtractor:
    FACENET_THRESHOLD_EUCLIDEAN = 60

    def __init__(self, model_name = "Facenet") -> None:
        self.model: FacialRecognition  = DeepFace.build_model(model_name)
    
    def represent(self,
        img_path: Union[str, np.ndarray],
        enforce_detection: bool = False,
        detector_backend: str = "skip",
        align: bool = False,
        expand_percentage: int = 0,
        normalization: str = "base",
        ) -> List[Dict[str, Any]]:
        """
        Represent facial images as multi-dimensional vector embeddings.

        Args:
            img_path (str or np.ndarray): The exact path to the image, a numpy array in BGR format,
                or a base64 encoded image. If the source image contains multiple faces, the result will
                include information for each detected face.

            enforce_detection (boolean): If no face is detected in an image, raise an exception.
                Default is True. Set to False to avoid the exception for low-resolution images.

            detector_backend (string): face detector backend. Options: 'opencv', 'retinaface',
                'mtcnn', 'ssd', 'dlib', 'mediapipe', 'yolov8'.

            align (boolean): Perform alignment based on the eye positions.

            expand_percentage (int): expand detected facial area with a percentage (default is 0).

            normalization (string): Normalize the input image before feeding it to the model.
                Default is base. Options: base, raw, Facenet, Facenet2018, VGGFace, VGGFace2, ArcFace

        Returns:
            results (List[Dict[str, Any]]): A list of dictionaries, each containing the
                following fields:

            - embedding (np.array): Multidimensional vector representing facial features.
                The number of dimensions varies based on the reference model
                (e.g., FaceNet returns 128 dimensions, VGG-Face returns 4096 dimensions).
            - facial_area (dict): Detected facial area by face detection in dictionary format.
                Contains 'x' and 'y' as the left-corner point, and 'w' and 'h'
                as the width and height. If `detector_backend` is set to 'skip', it represents
                the full image area and is nonsensical.
            - face_confidence (float): Confidence score of face detection. If `detector_backend` is set
                to 'skip', the confidence will be 0 and is nonsensical.
        """
        resp_objs = []

        # ---------------------------------
        # we have run pre-process in verification. so, this can be skipped if it is coming from verify.
        target_size = self.model.input_shape
        if detector_backend != "skip":
            img_objs = detection.extract_faces(
                img_path=img_path,
                target_size=(target_size[1], target_size[0]),
                detector_backend=detector_backend,
                grayscale=False,
                enforce_detection=enforce_detection,
                align=align,
                expand_percentage=expand_percentage,
            )
        else:  # skip
            # Try load. If load error, will raise exception internal
            img, _ = preprocessing.load_image(img_path)
            # --------------------------------
            if len(img.shape) == 4:
                img = img[0]  # e.g. (1, 224, 224, 3) to (224, 224, 3)
            if len(img.shape) == 3:
                img = cv2.resize(img, target_size)
                img = np.expand_dims(img, axis=0)
                # when called from verify, this is already normalized. But needed when user given.
                if img.max() > 1:
                    img = (img.astype(np.float32) / 255.0).astype(np.float32)
            # --------------------------------
            # make dummy region and confidence to keep compatibility with `extract_faces`
            img_objs = [
                {
                    "face": img,
                    "facial_area": {"x": 0, "y": 0, "w": img.shape[1], "h": img.shape[2]},
                    "confidence": 0,
                }
            ]
        # ---------------------------------

        for img_obj in img_objs:
            img = img_obj["face"]
            region = img_obj["facial_area"]
            confidence = img_obj["confidence"]
            # custom normalization
            img = preprocessing.normalize_input(img=img, normalization=normalization)

            embedding = self.model.find_embeddings(img)

            resp_obj = {}
            resp_obj["embedding"] = embedding
            resp_obj["facial_area"] = region
            resp_obj["face_confidence"] = confidence
            resp_objs.append(resp_obj)

        return resp_objs
    
    def get_embedding(self, image):
        return self.represent(image)[0]['embedding']
    
    @staticmethod
    def find_threshold(model_name: str = 'Facenet', distance_metric: str = 'euclidean') -> float:
        """
        Retrieve pre-tuned threshold values for a model and distance metric pair
        Args:
            model_name (str): facial recognition model name
            distance_metric (str): distance metric name. Options are cosine, euclidean
                and euclidean_l2.
        Returns:
            threshold (float): threshold value for that model name and distance metric
                pair. Distances less than this threshold will be classified same person.
        """

        base_threshold = {"cosine": 0.40, "euclidean": 0.55, "euclidean_l2": 0.75}

        thresholds = {
            # "VGG-Face": {"cosine": 0.40, "euclidean": 0.60, "euclidean_l2": 0.86}, # 2622d
            "VGG-Face": {
                "cosine": 0.68,
                "euclidean": 1.17,
                "euclidean_l2": 1.17,
            },  # 4096d - tuned with LFW
            "Facenet": {"cosine": 0.40, "euclidean": 15, "euclidean_l2": 0.80},
            "Facenet512": {"cosine": 0.30, "euclidean": 23.56, "euclidean_l2": 1.04},
            "ArcFace": {"cosine": 0.68, "euclidean": 4.15, "euclidean_l2": 1.13},
            "Dlib": {"cosine": 0.07, "euclidean": 0.6, "euclidean_l2": 0.4},
            "SFace": {"cosine": 0.593, "euclidean": 10.734, "euclidean_l2": 1.055},
            "OpenFace": {"cosine": 0.10, "euclidean": 0.55, "euclidean_l2": 0.55},
            "DeepFace": {"cosine": 0.23, "euclidean": 64, "euclidean_l2": 0.64},
            "DeepID": {"cosine": 0.015, "euclidean": 45, "euclidean_l2": 0.17},
        }

        threshold = thresholds.get(model_name, base_threshold).get(distance_metric, 0.4)

        return threshold

                
