import cv2
from threading import Thread
import time


class VideoStream:
    def __init__(self, stream_url):
        self.stream_url = stream_url
        self.cap = cv2.VideoCapture(self.stream_url)
        if not self.cap.isOpened():
            raise ValueError(f"[SYSTEM] 스트림 {stream_url} 열기 실패")
        self.frame = None
        self.running = True
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        fail_count = 0
        max_fails = 10
        while self.running:
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.stream_url)
                time.sleep(1)
                continue

            start = time.time()
            ret, frame = self.cap.read()
            elapsed = time.time() - start
            
            if ret and frame is not None:
                self.frame = frame
                fail_count = 0
            else:
                fail_count += 1
                if fail_count >= max_fails or elapsed > 1.0:
                    self.cap.release()
                    self.cap = None
                time.sleep(0.1)

    def get_frame(self):
        return self.frame

    def stop(self):
        self.running = False
        self.thread.join()
        if self.cap:
            self.cap.release()
