from flask import Blueprint, Response, stream_with_context, request, current_app, jsonify
from datetime import datetime
from ultralytics import YOLO
import cv2
import time
import numpy as np
import os
import logging
from app.models import DetectionLog
from app import socketio, Log_Utils, db

bp = Blueprint('camera', __name__)

logging.getLogger('ultralytics').setLevel(logging.WARNING)

MODEL_PATH = "./runs/detect/train5_new/weights/best.pt"
trigger_flag = False
current_sensitivity = 0.6

try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    print("모델이 성공적으로 로드되었습니다.")
except Exception as e:
    print(f"모델 로드 중 오류 발생: {e}")
    exit(1)

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

# -- 핵심 변경: host 변수를 인자로 넘기도록 generate_frames 함수 래핑 --

def generate_frames(camera_id, host):
    global trigger_flag
    detected_classes = set()
    target_class_indices = [0, 1, 2, 3, 4]
    colors = np.random.uniform(0, 255, size=(len(model.names), 3))
    trigger_counter = 0
    last_saved_time = 0

    camera_manager = current_app.camera_manager

    if not camera_manager.is_connected(camera_id):
        print(f"카메라 {camera_id}가 연결되지 않았습니다.")
        return

    while True:
        frame = camera_manager.get_frame(camera_id)
        if frame is None:
            print(f"카메라 {camera_id}에서 프레임을 읽을 수 없습니다.")
            time.sleep(0.1)
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
                    cls = int(box.cls[0].item())
                    if cls in target_class_indices and conf >= current_sensitivity:
                        detected_classes.add(model.names[cls])
                        color = colors[cls]
                        width_px = x2 - x1
                        height_px = y2 - y1
                        panel_type = classify_panel_type(width_px, height_px)

                        label = f"{model.names[cls]} {conf:.2f}"
                        size_info = f"W: {width_px:.0f}px H: {height_px:.0f}px"
                        type_info = f"Type: {panel_type}"

                        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
                        cv2.putText(img, label, (int(x1), int(y1) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        cv2.putText(img, size_info, (int(x1), int(y2) + 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        cv2.putText(img, type_info, (int(x1), int(y2) + 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # 5초 간격 저장, DB 기록, WebSocket 알림
            if time.time() * 1000 - last_saved_time >= 5000 and detected_classes:
                class_str = '_'.join(sorted(detected_classes))
                filename = f"Camera_{camera_id}_{class_str}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                save_dir = "app/static/detected"
                original_dir = "app/static/original"
                os.makedirs(save_dir, exist_ok=True)
                os.makedirs(original_dir, exist_ok=True)

                cv2.imwrite(os.path.join(save_dir, filename), img)
                cv2.imwrite(os.path.join(original_dir, filename), frame)
                last_saved_time = int(time.time() * 1000)

                image_path_web = f"static/detected/{filename}"
                original_path_web = f"static/original/{filename}"

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
                                image_path=image_path_web
                            )
                            db.session.add(log)

                issue_type = Log_Utils.extract_issue_type(filename)
                severity, severity_color = Log_Utils.map_severity(issue_type)
                created_time = now.strftime('%Y-%m-%d %H:%M:%S')
                original_url = f"http://{host}:5000/{original_path_web}"
                annotation_url = f"http://{host}:3000/?image_url={original_url}"

                socketio.emit('new_log', {
                    'filename': filename,
                    'timestamp': created_time,
                    'imageUrl': f'/{image_path_web}',
                    'issueType': issue_type,
                    'severity': severity,
                    'severityColor': severity_color,
                    'cameraName': f"Camera_{camera_id}",
                    'annotationUrl': annotation_url,
                    'confidence': conf,
                })
                db.session.commit()
                detected_classes.clear()

            trigger_counter -= 1

        _, buffer = cv2.imencode('.jpg', img)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type:image/jpeg\r\n'
               b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
               b'\r\n' + frame_bytes + b'\r\n')


@bp.route('/camera/stream/<int:camera_id>')
def camera_stream(camera_id):
    host = request.host.split(':')[0]  # 여기서 request 사용 → 정상 컨텍스트 내
    # stream_with_context로 컨텍스트 유지하며 generate_frames 호출, host 인자 넘김
    return Response(stream_with_context(generate_frames(camera_id, host)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@bp.route('/camera/status')
def camera_status():
    camera_manager = current_app.camera_manager
    status_dict = {cam_id: camera_manager.is_connected(cam_id) for cam_id in camera_manager.get_camera_ids()}
    return jsonify(status_dict)


@bp.route("/trigger")
def trigger_detection():
    global trigger_flag
    trigger_flag = True
    return "YOLO 분석 트리거됨"
