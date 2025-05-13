from flask import Blueprint, Response, jsonify, redirect, url_for
from . import bp
from .VideoStream import VideoStream  # VideoStream 클래스 임포트
import cv2
import time
from ultralytics import YOLO
import numpy as np
import os
import requests
from PIL import ImageFont, ImageDraw, Image
from datetime import datetime

import logging

logging.getLogger('ultralytics').setLevel(logging.WARNING)

# 설정
MODEL_PATH = "./runs/detect/train4_custom/weights/best.pt"
trigger_flag = False
trigger_counter = 0

# 모델 로드
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    print("모델이 성공적으로 로드되었습니다.")
except Exception as e:
    print(f"모델 로드 중 오류 발생: {e}")
    exit(1)

# 활성화된 비디오 스트림 객체 저장
video_streams = {}

# 카메라 자동 탐색 및 VideoStream 객체 생성
camera_indexes = []
max_cameras = 3  # 최대 연결 가능한 카메라 수

for i in range(max_cameras):
    cap_test = cv2.VideoCapture(i)
    if cap_test.isOpened():
        print(f"카메라 {i}번 감지됨 (VideoStream 생성)")
        camera_indexes.append(i)
        video_streams[i] = VideoStream(i)  # VideoStream 객체 생성
    cap_test.release()


def classify_panel_type(width_px, height_px):
    aspect_ratio = width_px / height_px if height_px != 0 else 0

    if 0.9 <= aspect_ratio <= 1.1:
        return "square"
    elif aspect_ratio >= 2.5:
        return "long"
    else:
        return "unknown"


def generate_frames(camera_id):
    global trigger_flag

    video_stream = video_streams.get(camera_id)
    if not video_stream or not video_stream.is_connected():
        print(f"경고: 카메라 {camera_id}가 연결되지 않았습니다.")
        yield (b'--frame\r\n'
               b'Content-Type:image/jpeg\r\n'
               b'Content-Length: 0\r\n'
               b'\r\n')  # 연결 실패 시 빈 프레임 반환
        return

    model_local = model
    target_class_indices = [0]
    colors = np.random.uniform(0, 255, size=(len(model_local.names), 3))
    trigger_counter_local = 0
    last_saved_time = 0

    while True:
        if trigger_flag:
            trigger_counter_local = 40
            trigger_flag = False

        frame = video_stream.get_frame()
        if frame is None:
            time.sleep(0.1)
            continue

        img = frame.copy()

        if trigger_counter_local > 0:
            try:
                results = model_local(img)

                now = datetime.now()
                current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(img, current_time_str, (img.shape[1] - 630, img.shape[0] - 20),
                            cv2.FONT_HERSHEY_DUPLEX, 0.7, (83, 115, 219), 2)

                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].item()
                        cls = box.cls[0].item()
                        class_index = int(cls)

                        if class_index in target_class_indices and conf >= 0.6:
                            color = colors[class_index]

                            width_px = x2 - x1
                            height_px = y2 - y1
                            aspect_ratio = width_px / height_px
                            panel_type = classify_panel_type(width_px, height_px)

                            label = f"{model_local.names[class_index]} {conf:.2f}"
                            size_info = f"W: {width_px:.0f}px H: {height_px:.0f}px R: {aspect_ratio:.2f}"
                            type_info = f"Type: {panel_type}"

                            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
                            cv2.putText(img, label, (int(x1), int(y1) - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                            cv2.putText(img, size_info, (int(x1), int(y2) + 20),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                            cv2.putText(img, type_info, (int(x1), int(y2) + 40),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                            current_timestamp = int(time.time() * 1000)
                            if current_timestamp - last_saved_time >= 5000:
                                save_dir = f"static/detected/camera_{camera_id}"
                                os.makedirs(save_dir, exist_ok=True)
                                filename = f"defect_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                                save_path = os.path.join(save_dir, filename)
                                cv2.imwrite(save_path, img)
                                print(f"[저장됨] {save_path}")
                                last_saved_time = current_timestamp
                                try:
                                    requests.post("http://192.168.0.133:8000/upload_and_create_task")
                                except requests.exceptions.RequestException as e:
                                    print(f"POST 요청 실패: {e}")

                trigger_counter_local -= 1
            except Exception as e:
                print(f"YOLO 처리 오류 (카메라 {camera_id}): {e}")
                time.sleep(1)
                continue

        try:
            _, buffer = cv2.imencode('.jpg', img)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type:image/jpeg\r\n'
                   b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
                   b'\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)
        except Exception as e:
            print(f"프레임 인코딩 오류 (카메라 {camera_id}): {e}")
            yield (b'--frame\r\n'
                   b'Content-Type:image/jpeg\r\n'
                   b'Content-Length: 0\r\n'
                   b'\r\n')  # 인코딩 실패 시 빈 프레임 반환
            time.sleep(1)


@bp.route('/stream')
def video_feed_default():
    return redirect(url_for('.video_feed_0'))


for i in camera_indexes:
    def make_view_func(camera_id):
        def view_func():
            if camera_id in video_streams and video_streams[camera_id].is_connected():
                return Response(generate_frames(camera_id),
                                mimetype='multipart/x-mixed-replace; boundary=frame')
            else:
                return "카메라 연결 실패", 500
        return view_func

    view_func = make_view_func(i)
    endpoint_name = f'video_feed_{i}'
    route_path = f'/stream/{i}'
    bp.add_url_rule(route_path, endpoint=endpoint_name, view_func=view_func)


@bp.route('/api/camera_status')
def api_camera_status():
    camera_status = {}
    for index, stream in video_streams.items():
        # camera_id는 실제로 0, 1, 2인데 JS에서는 1, 2, 3으로 씀
        camera_status[str(index)] = stream.is_connected()
    return jsonify(camera_status)


@bp.route("/trigger")
def trigger_detection():
    global trigger_flag
    trigger_flag = True
    return "YOLO 분석 트리거됨"


# 추가된 save_label 함수
@bp.route("/save_label", methods=["POST"])
def save_label():
    from flask import request
    data = request.get_json()
    print("라벨 데이터 수신:", data)
    # 여기에 라벨 데이터를 저장하는 실제 로직을 구현해야 합니다.
    # 예: 파일에 저장, 데이터베이스에 저장 등
    return jsonify({"message": "라벨 데이터 저장됨"})