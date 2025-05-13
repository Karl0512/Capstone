import cv2

class CameraManager:
    def __init__(self, source=0):
        self.source = source
        self.cap = None

    def start(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.source)
            print("📷 Camera started.")

    def read(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("❌ Failed to read frame from camera.")
            return frame
        else:
            raise Exception("❌ Camera is not initialized or already released.")

    def stop(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            print("🛑 Camera released.")

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()
