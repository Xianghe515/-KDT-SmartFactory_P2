import cv2
import threading
import time
import logging
import wmi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoStream:
    def __init__(self, camera_id, socketio):  # socketio 객체 추가
        self.camera_id = camera_id
        self.socketio = socketio
        self.stream = None
        self.running = False
        self.thread = None
        self.frame = None
        self.lock = threading.Lock()

    def start(self):
        if not self.running:
            logger.info(f"[{self.camera_id}] Starting video stream")
            time.sleep(1)  # OS에서 디바이스 해제할 시간 확보
            self.stream = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
            if self.stream is None or not self.stream.isOpened():
                logger.error(f"[{self.camera_id}] cv2.VideoCapture 초기화 실패 (camera_id: {self.camera_id})")
                self.socketio.emit('camera_status_update', {self.camera_id: False})
                return # 초기화 실패 시 더 이상 진행하지 않음
            self.running = True
            self.thread = threading.Thread(target=self.update, daemon=True)
            self.thread.start()

    def update(self):
        while self.running:
            if self.stream is None or not self.stream.isOpened():
                logger.warning(f"[{self.camera_id}] Stream not opened, retrying...")
                self.socketio.emit('camera_status_update', {self.camera_id: False})  # 🔴 연결 안됨 상태 전송
                self.stream = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
                time.sleep(1)
                continue

            ret, frame = self.stream.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                logger.warning(f"[{self.camera_id}] Frame read failed")
                self.socketio.emit('camera_status_update', {self.camera_id: False})  # 🔴 프레임 읽기 실패 시 연결 안됨 상태 전송
                time.sleep(0.1)

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        logger.info(f"[{self.camera_id}] Stopping video stream")
        self.running = False
        if self.stream is not None:
            self.stream.release()
            logger.info(f"[{self.camera_id}] 스트림 release 완료")
            self.stream = None
            try:
                cv2.destroyAllWindows()
                logger.info(f"[{self.camera_id}] 모든 OpenCV 윈도우 닫기 시도")
            except Exception as e:
                logger.warning(f"[{self.camera_id}] OpenCV 윈도우 닫기 중 오류 발생: {e}")
        if self.thread and self.thread.is_alive():
            logger.info(f"[{self.camera_id}] 업데이트 쓰레드 join 시도 (timeout=1)")
            self.thread.join(timeout=1)
            if self.thread.is_alive():
                logger.warning(f"[{self.camera_id}] 업데이트 쓰레드가 timeout 내에 종료되지 않음")
        with self.lock:
            self.frame = None  # 🔥 중요: 프레임 초기화
        self.socketio.emit('camera_status_update', {self.camera_id: False}) # 🔴 명시적인 stop 시 연결 안됨 상태 전송

    def is_running(self):
        return self.running and self.stream is not None and self.stream.isOpened()


class CameraManager:
    def __init__(self, socketio, camera_names):
        self.socketio = socketio
        self.camera_names = camera_names
        self.cameras = {}
        self.lock = threading.Lock()

        # 초기 카메라 시작
        for camera_id in self.camera_names:
            self.start_camera(camera_id)

        # WMI 이벤트 쓰레드 시작 (USB 연결 감지)
        self.wmi_thread = threading.Thread(target=self._watch_camera_events, daemon=True)
        self.wmi_thread.start()

    def start_camera(self, camera_id):
        with self.lock:
            if camera_id in self.cameras:
                self.cameras[camera_id].stop()
                del self.cameras[camera_id]
            stream = VideoStream(camera_id, self.socketio)  # socketio 객체 전달
            stream.start()
            self.cameras[camera_id] = stream
            logger.info(f"Camera {camera_id} started")
            self.socketio.emit('camera_status_update', {camera_id: True}) # 🟢 연결됨 알림

    def stop_camera(self, camera_id):
        with self.lock:
            if camera_id in self.cameras:
                self.cameras[camera_id].stop()
                del self.cameras[camera_id]
                logger.info(f"Camera {camera_id} stopped")
                self.socketio.emit('camera_status_update', {camera_id: False}) # 🔴 연결 안됨 알림

    def reconnect_camera(self, camera_id):
        logger.info(f"[{camera_id}] reconnect_camera 호출됨")
        if camera_id in self.cameras:
            logger.info(f"[{camera_id}] 이전 카메라 스트림 중지 시도")
            try:
                self.cameras[camera_id].stop()
                logger.info(f"[{camera_id}] 이전 카메라 스트림 중지 완료")
            except Exception as e:
                logger.error(f"[{camera_id}] 이전 카메라 스트림 중지 중 오류 발생: {e}")
            time.sleep(0.5)  # 잠시 대기
        logger.info(f"[{camera_id}] 새로운 VideoStream 객체 생성 시도")
        stream = VideoStream(camera_id, self.socketio) # socketio 객체 전달
        logger.info(f"[{camera_id}] 새로운 VideoStream 객체 시작 시도")
        stream.start()
        self.cameras[camera_id] = stream
        logger.info(f"[{camera_id}] 카메라 재연결 완료")
        self.socketio.emit('camera_status_update', {camera_id: True}) # 🟢 재연결됨 알림


    def get_frame(self, camera_id):
        with self.lock:
            stream = self.cameras.get(camera_id)
            if stream and stream.is_running():
                return stream.read()
        return None

    def is_connected(self, camera_id):
        with self.lock:
            stream = self.cameras.get(camera_id)
            return stream.is_running() if stream else False

    def get_camera_ids(self):
        return list(self.camera_names.keys())

    def _unwatch_camera_events(self):
        if hasattr(self, 'watcher'):
            self.watcher.Cancel()
            logger.info("WMI event watcher cancelled.")
        self.wmi_thread_running = False
        if hasattr(self, 'wmi_thread') and self.wmi_thread.is_alive():
            self.wmi_thread.join(timeout=5)
            logger.info("WMI thread joined.")

    def _watch_camera_events(self):
        c = wmi.WMI()
        watcher = c.watch_for(notification_type="Creation", wmi_class="Win32_USBControllerDevice")
        while True:
            try:
                watcher()  # blocking until USB device inserted
                logger.info("WMI: USB device connected")
                time.sleep(2)  # 잠시 대기

                # 연결된 USB 장치 리스트 얻기
                usb_devices = c.query("SELECT * FROM Win32_PnPEntity WHERE DeviceID LIKE '%USB%'")
                connected_camera_names = set()

                for dev in usb_devices:
                    dev_name = dev.Name.lower() if dev.Name else ""
                    connected_camera_names.add(dev_name)

                # camera_names 안의 이름과 비교해서 일치하는 것만 start_camera 호출
                for camera_id, camera_name in self.camera_names.items():
                    if camera_name.lower() in connected_camera_names:
                        # 만약 카메라가 없거나 현재 실행중이지 않으면 시작
                        if camera_id not in self.cameras or not self.cameras[camera_id].is_running():
                            logger.info(f"[{camera_id}] USB 연결 감지, 카메라 시작 시도: {camera_name}")
                            self.start_camera(camera_id)
                            time.sleep(1)

            except Exception as e:
                logger.error(f"WMI monitoring error: {e}")
                time.sleep(5)
