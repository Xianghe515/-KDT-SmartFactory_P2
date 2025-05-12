import cv2
import time
from threading import Thread, Lock
import json
from flask_socketio import SocketIO, emit  # 필요한 임포트 추가

class VideoStream:
    def __init__(self, stream_id, socketio):  # socketio 인자 추가
        self.stream_id = stream_id
        self.cap = cv2.VideoCapture(stream_id)
        self.frame = None
        self.connected = self.cap.isOpened()
        self.running = True
        self.lock = Lock()
        self.thread = Thread(target=self.update, daemon=True)
        self.thread.start()
        self.socketio = socketio  # socketio 객체 저장

    def update(self):
        """스트림에서 프레임을 읽어 최신 상태 유지 및 연결 상태 변경 시 알림"""
        last_connected_status = self.connected
        while self.running:
            if not self.cap.isOpened():
                self.connected = False
                if self.connected != last_connected_status:
                    if self.socketio:
                        self.socketio.emit('camera_status', json.dumps({"id": self.stream_id, "connected": False}))
                    last_connected_status = self.connected
                self.reconnect()
                time.sleep(2)
                continue

            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
                if not self.connected:
                    self.connected = True
                    if self.socketio:
                        self.socketio.emit('camera_status', json.dumps({"id": self.stream_id, "connected": True}))
                    last_connected_status = self.connected
            else:
                if self.connected:
                    self.connected = False
                    if self.socketio:
                        self.socketio.emit('camera_status', json.dumps({"id": self.stream_id, "connected": False}))
                    last_connected_status = self.connected
                time.sleep(1)

    def reconnect(self):
        """카메라가 끊긴 경우 재연결 시도"""
        self.cap.release()
        self.cap = cv2.VideoCapture(self.stream_id)
        time.sleep(1) # 재연결 시도 후 잠시 대기

    def get_frame(self):
        """현재 프레임 반환"""
        with self.lock:
            return self.frame

    def is_connected(self):
        """카메라 연결 상태 확인"""
        return self.connected

    def stop(self):
        """스트림 종료"""
        self.running = False
        self.thread.join()
        self.cap.release()