from flask import Blueprint, Response, stream_with_context, request, url_for, jsonify
from datetime import datetime
from ultralytics import YOLO
from . import bp
import cv2
import time
import numpy as np
import os
import requests
import threading
from app.models import DetectionLog
from app.VideoStream import VideoStream
from app import socketio
from app import Log_Utils
from app import db

import logging
logging.getLogger('ultralytics').setLevel(logging.WARNING)

# 설정
MODEL_PATH = "./runs/detect/train5_new/weights/best.pt"
trigger_flag = False
trigger_counter = 0
current_sensitivity = 0.6
latest_frames = {}

# 모델 로드
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    print("모델이 성공적으로 로드되었습니다.")
except Exception as e:
    print(f"모델 로드 중 오류 발생: {e}")
    exit(1)

# 고정된 카메라 인덱스 수
max_cameras = 3
streams = {}

# 카메라 감지 및 VideoStream 객체 생성
for i in range(max_cameras):
    try:
        stream = VideoStream(i)
        print(f"카메라 {i}번 감지됨")
        streams[i] = stream
    except ValueError as e:
        print(f"카메라 {i}번 감지 실패: {e}")
        streams[i] = None  # 연결 안 된 카메라도 자리 확보

# 상태 브로드캐스트 함수
def broadcast_camera_status():
    while True:
        status = {}
        for cam_id in range(max_cameras):
            stream = streams.get(cam_id)
            status[str(cam_id)] = stream.is_connected() if stream else False
        socketio.emit('camera_status_update', status)
        socketio.sleep(3)  # 3초마다 상태 전송

# 서버 시작 시 상태 브로드캐스트 스레드 시작
threading.Thread(target=broadcast_camera_status, daemon=True).start()

def classify_panel_type(width_px, height_px):
    aspect_ratio = width_px / height_px if height_px != 0 else 0

    if 0.9 <= aspect_ratio <= 1.1:
        return "square"
    elif aspect_ratio >= 2.5:
        return "long"
    else:
        return "unknown"
    
@socketio.on('connect')
def handle_connect():
    print('클라이언트가 WebSocket으로 연결되었습니다.')

@socketio.on('sensitivity')
def handle_sensitivity(data):
    global current_sensitivity
    sensitivity = float(data.get('value', 0.6))
    current_sensitivity = sensitivity
    socketio.emit('sensitivity_updated', {'value': current_sensitivity})
    
def generate_frames(camera_id):
    global trigger_flag
    host = request.host.split(':')[0]
    detected_classes = set()

    target_class_indices = [0, 1, 3, 4]
    colors = np.random.uniform(0, 255, size=(len(model.names), 3))

    trigger_counter = 0
    last_saved_time = 0

    stream = streams[camera_id]  # 해당 카메라 인덱스를 사용

    while True:
        frame = stream.get_frame()
        if frame is None:
            continue

        img = frame.copy()
        latest_frames[camera_id] = frame.copy()  # 🔸 최신 프레임 저장
        
        if trigger_flag:
            trigger_counter = 40
            trigger_flag = False

        if trigger_counter > 0:
            results = model(img)

            now = datetime.now()
            current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(img, current_time_str, (img.shape[1] - 630, img.shape[0] - 40),
                        cv2.FONT_HERSHEY_DUPLEX, 0.7, (83, 100, 219), 2)

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].item()
                    cls = box.cls[0].item()
                    class_index = int(cls)
                    if class_index in target_class_indices and conf >= current_sensitivity:
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
                            save_dir = "app/static/detected"        # 분석된 이미지
                            original_dir = "app/static/original"    # 원본 이미지
                            os.makedirs(save_dir, exist_ok=True)
                            os.makedirs(original_dir, exist_ok=True)
                            
                            # 파일명 생성
                            class_str = '_'.join(sorted(detected_classes))
                            filename = f"Camera {camera_id}_{class_str}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                            save_path = os.path.join(save_dir, filename)
                            original_path = os.path.join(original_dir, filename)
                            
                            # 이미지 저장
                            cv2.imwrite(save_path, img)
                            cv2.imwrite(original_path, frame)
                            last_saved_time = current_timestamp

                            # 웹에서 접근 가능한 경로 생성 (예: static/detected/xxx.jpg)
                            image_path_for_web = f"static/detected/{filename}"
                            original_path_for_web = f"static/original/{filename}"

                            # 로그 저장
                            for result in results:
                                for box in result.boxes:
                                    conf = box.conf[0].item()
                                    cls = int(box.cls[0].item())
                                    if cls in target_class_indices and conf >= current_sensitivity:
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
                            download_path = url_for('static', filename=f'detected/{filename}')
                            original_path = url_for('static', filename=f'original/{filename}')
                            original_url = f'http://{host}:5000{original_path}'
                            annotation_url = f'http://{host}:3000/?image_url={original_url}'

                            log = {
                                'filename': filename,
                                'timestamp': created_time,
                                'imageUrl': f'/static/detected/{filename}',
                                'issueType': issue_type,
                                'severity': severity,
                                'severityColor': severity_color,
                                'cameraName': camera_name,
                                'annotationUrl': annotation_url,
                                'confidence': conf,
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

# 동적으로 카메라 스트림 뷰 생성
for camera_id in streams.keys():  # 감지된 카메라 인덱스만 사용
    def make_view_func(camera_id):
        def view_func():
            return Response(stream_with_context(generate_frames(camera_id)),
                            mimetype='multipart/x-mixed-replace; boundary=frame')
        return view_func

    view_func = make_view_func(camera_id)
    endpoint_name = f'video_feed_{camera_id}'
    route_path = f'/stream/{camera_id}'

    bp.add_url_rule(route_path, endpoint=endpoint_name, view_func=view_func)


@bp.route("/trigger")
def trigger_detection():
    global trigger_flag
    trigger_flag = True
    return "YOLO 분석 트리거됨"

@bp.route("/capture/<int:camera_id>", methods=["POST"])
def capture_frame(camera_id):
    host = request.host.split(':')[0]
    frame = latest_frames.get(camera_id)
    if frame is None:
        return jsonify({"success": False, "message": "No frame available"}), 404
# 변수 설정 및 이미지 저장
    now = datetime.now()
    save_dir = "app/static/detected"
    original_dir = "app/static/original"
    class_str = "Captured"
    filename = f"Camera {camera_id}_{class_str}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    save_path = os.path.join(save_dir, filename)
    original_path = os.path.join(original_dir, filename)
    os.makedirs(save_dir, exist_ok=True)

    cv2.imwrite(save_path, frame)
    cv2.imwrite(original_path, frame)
    image_path_for_web = f"static/detected/{filename}"

# 로그 DB 저장
    log = DetectionLog(
        timestamp=now,
        camera_id=camera_id,
        defect_type="Captured",
        confidence=None,
        image_path=image_path_for_web
    )
    db.session.add(log)
    db.session.commit()

# WebSocket - 실시간 로그 출력
    issue_type = Log_Utils.extract_issue_type(filename)
    severity, severity_color = Log_Utils.map_severity(issue_type)
    camera_name = filename.split('_')[0]
    created_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    download_path = url_for('static', filename=f'detected/{filename}')
    download_url = f'http://{host}:5000{download_path}'
    annotation_url = f'http://{host}:3000/?image_url={download_url}'

# WebSocket 브로드캐스트
    socketio.emit('new_log', {
        'filename': filename,
        'timestamp': created_time,
        'imageUrl': download_path,
        'issueType': issue_type,
        'severity': severity,
        'severityColor': severity_color,
        'cameraName': camera_name,
        'annotationUrl': annotation_url,
        'confidence': '알 수 없음'
    })

    return jsonify({
        "success": True,
        "filename": filename,
        "log": {
            'filename': filename,
            'timestamp': created_time,
            'imageUrl': download_path,
            'issueType': issue_type,
            'severity': severity,
            'severityColor': severity_color,
            'cameraName': camera_name,
            'annotationUrl': annotation_url,
            'confidence': '알 수 없음'
        }
    })
    
# 카메라 상태 조회
@bp.route('/camera/api/status')
def get_camera_status():
    status = {}
    for cam_id in range(max_cameras):
        stream = streams.get(cam_id)
        status[str(cam_id)] = stream.is_connected() if stream else False
    return jsonify(status)