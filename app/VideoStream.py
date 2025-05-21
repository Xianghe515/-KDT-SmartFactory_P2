from threading import Thread
import cv2 as cv


class VideoStream:
    def __init__(self, stream_url):
        self.cap = cv.VideoCapture(stream_url, cv.CAP_DSHOW)  # Windows 환경 오류 줄이기
        if not self.cap.isOpened():
            raise ValueError(f"[오류] 스트림 {stream_url} 열기 실패")
        self.frame = None
        self.running = True
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        """ 스트림에서 계속 프레임을 읽어 최신 상태 유지 """
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
            else:
                print(f"[경고] 스트림 {self.cap}에서 프레임을 읽을 수 없습니다.")

    def get_frame(self):
        """ 최신 프레임 반환 """
        return self.frame

    def stop(self):
        """ 스트림 중지 """
        self.running = False
        self.thread.join()
        self.cap.release()