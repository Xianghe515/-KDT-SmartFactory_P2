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
        self.connected = True  # 추가
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        fail_count = 0
        max_fails = 10
        while self.running:
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.stream_url)
                self.connected = False  # 카메라 끊김 표시
                time.sleep(1)
                continue

            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.frame = frame
                fail_count = 0
                self.connected = True
            else:
                fail_count += 1
                if fail_count >= max_fails:
                    self.cap.release()
                    self.cap = None
                    self.connected = False
                time.sleep(0.1)

    def get_frame(self):
        return self.frame

    def is_connected(self):
        return self.connected

    def stop(self):
        self.running = False
        self.thread.join()
        if self.cap:
            self.cap.release()