import cv2
import time
import platform
from threading import Thread, Lock

class VideoStream:
    def __init__(self, stream_id):
        self.stream_id = stream_id
        self.frame = None
        self.lock = Lock()
        self.running = True
        self.connected = False  # 초기 연결 상태는 False로 시작
        
        # OS별 VideoCapture 설정
        self.cap = self.create_capture(self.stream_id)
        self.connected = self.cap.isOpened()  # 초기 연결 상태 확인
        print(f"카메라 {self.stream_id} 초기 연결 상태: {self.connected}")

        # 프레임 수집 쓰레드 시작
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()

    def create_capture(self, stream_id):
        if platform.system() == 'Windows':
            return cv2.VideoCapture(stream_id, cv2.CAP_DSHOW)
        else:
            return cv2.VideoCapture(stream_id)

    def update(self):
        consecutive_failures = 0
        last_connected_status = self.connected

        while self.running:
            if not self.cap.isOpened():  # 연결 끊김 감지
                self.connected = False
                if self.connected != last_connected_status:
                    print(f"카메라 {self.stream_id} 연결 끊김 (캡처 열기 실패)")
                    last_connected_status = self.connected
                self.reconnect()  # 재연결 시도
                time.sleep(5)  # 재시도 간격
                continue

            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
                if not self.connected:
                    self.connected = True  # 연결 상태 갱신
                    print(f"카메라 {self.stream_id} 연결됨")
                    last_connected_status = self.connected
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if self.connected and consecutive_failures >= 3:  # 프레임 읽기 실패 3회 연속
                    self.connected = False
                    print(f"카메라 {self.stream_id} 연결 끊김 (프레임 읽기 실패)")
                    last_connected_status = self.connected
                    self.reconnect()  # 재연결 시도
                time.sleep(1)

    def reconnect(self):
        print(f"카메라 {self.stream_id} 재연결 시도 중...")
        self.cap.release()
        time.sleep(1)

        for attempt in range(5):
            self.cap = self.create_capture(self.stream_id)  # 카메라 다시 열기
            if self.cap.isOpened():
                ret, frame = self.cap.read()  # 프레임 읽기 시도
                if ret:
                    with self.lock:
                        self.frame = frame
                    self.connected = True  # 재연결 성공
                    print(f"카메라 {self.stream_id} 재연결 성공 (시도 {attempt + 1}회)")
                    return
                else:
                    print(f"카메라 {self.stream_id} 프레임 읽기 실패 (시도 {attempt + 1}회)")
            else:
                print(f"카메라 {self.stream_id} 열기 실패 (시도 {attempt + 1}회)")
            time.sleep(2)  # 2초 대기 후 재시도

        self.connected = False  # 재연결 최종 실패
        print(f"카메라 {self.stream_id} 재연결 최종 실패")

    def get_frame(self):
        with self.lock:
            return self.frame

    def is_connected(self):
        return self.connected

    def stop(self):
        self.running = False
        self.thread.join()
        self.cap.release()
