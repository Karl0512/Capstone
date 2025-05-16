# face_services.py
from insightface.app import FaceAnalysis
import cv2
import numpy as np

class FaceDetectionService:
    _instance = None

    def __init__(self):
        self.model = FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider'])
        self.model.prepare(ctx_id=-1)  # -1 = CPU

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = FaceDetectionService()
        return cls._instance

    def detect_faces(self, image):
        """
        Detects faces and returns a list of Face objects with .bbox and .embedding
        """
        return self.model.get(image)

    def get_embedding(self, face):
        """
        Gets embedding vector from a Face object.
        """
        return face.embedding
