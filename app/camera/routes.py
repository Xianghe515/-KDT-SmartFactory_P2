from flask import Blueprint, Response, stream_with_context
from PIL import ImageFont, ImageDraw, Image
from datetime import datetime
from ultralytics import YOLO
from . import bp
import cv2
import time
import numpy as np
import os
import requests
from app.models import DetectionLog
from app import socketio
from app import Log_Utils
from app import db

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

# 카메라 자동 탐색
camera_indexes = []
max_cameras = 3  # 최대 연결 가능한 카메라 수

for i in range(max_cameras):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"카메라 {i}번 감지됨")
        camera_indexes.append(i)
    cap.release()

caps = [cv2.VideoCapture(index) for index in camera_indexes]  # 감지된 카메라 리스트 생성

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
    detected_classes = set()

    target_class_indices = [0]
    colors = np.random.uniform(0, 255, size=(len(model.names), 3))

    trigger_counter = 0
    last_saved_time = 0

    cap = caps[camera_id]  # 해당 카메라 인덱스를 사용

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        img = frame.copy()

        if trigger_flag:
            trigger_counter = 40
            trigger_flag = False

        if trigger_counter > 0:
            results = model(img)

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
                        detected_classes.add(model.names[class_index])
                        color = colors[class_index]
                        width_px = x2 - x1
                        height_px = y2 - y1
                        aspect_ratio = width_px / height_px
                        panel_type = classify_panel_type(width_px, height_px)

                        label = f"{model.names[class_index]} {conf:.2f}"
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
                        if current_timestamp - last_saved_time >= 5000 and detected_classes:
                            save_dir = f"app/static/detected"
                            os.makedirs(save_dir, exist_ok=True)

                            class_str = '_'.join(sorted(detected_classes))
                            filename = f"Camera {camera_id}_{class_str}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                            save_path = os.path.join(save_dir, filename)

                            # 이미지 저장
                            cv2.imwrite(save_path, img)
                            print(f"[저장됨] {save_path}")
                            last_saved_time = current_timestamp

                            # 웹에서 접근 가능한 경로 생성 (예: static/detected/xxx.jpg)
                            image_path_for_web = f"static/detected/{filename}"

                            # 로그 저장
                            for result in results:
                                for box in result.boxes:
                                    conf = box.conf[0].item()
                                    cls = int(box.cls[0].item())
                                    if cls in target_class_indices and conf >= 0.6:
                                        log = DetectionLog(
                                            timestamp=now,
                                            camera_id=camera_id,
                                            defect_type=model.names[cls],
                                            confidence=conf,
                                            image_path=image_path_for_web  # 웹 경로 저장
                                        )
                                        db.session.add(log)
                            
                            # WebSocket - 실시간 로그 출력
                            issue_type = Log_Utils.extract_issue_type(filename)
                            severity, severity_color = Log_Utils.map_severity(issue_type)
                            camera_name = filename.split('_')[0]
                            created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            log = {
                                'filename': filename,
                                'timestamp': created_time,
                                'imageUrl': f'/static/detected/{filename}',
                                'issueType': issue_type,
                                'severity': severity,
                                'severityColor': severity_color,
                                'cameraName': camera_name
                            }

                            socketio.emit('new_log', log)
                            db.session.commit()
                            detected_classes.clear()


            trigger_counter -= 1

        _, buffer = cv2.imencode('.jpg', img)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type:image/jpeg\r\n'
               b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
               b'\r\n' + frame_bytes + b'\r\n')

# 동적으로 엔드포인트 생성
# 동적으로 카메라 스트림 뷰 생성
for i in range(len(camera_indexes)):
    def make_view_func(camera_id):
        def view_func():
            return Response(stream_with_context(generate_frames(camera_id)),
                            mimetype='multipart/x-mixed-replace; boundary=frame')
        return view_func

    view_func = make_view_func(i)
    endpoint_name = f'video_feed_{i}'
    route_path = f'/stream/{i}'

    bp.add_url_rule(route_path, endpoint=endpoint_name, view_func=view_func)

@bp.route("/trigger")
def trigger_detection():
    global trigger_flag
    trigger_flag = True
    return "YOLO 분석 트리거됨"