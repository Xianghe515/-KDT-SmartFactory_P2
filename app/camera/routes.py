from flask import Blueprint, Response
import cv2
import time
from ultralytics import YOLO
import numpy as np
import os

camera_bp = Blueprint('camera', __name__, url_prefix='/camera')

# 모델 로드 (PyTorch 모델 경로 지정 - yolov11n.pt 파일이 solaproject 폴더에 있다고 가정)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yolo11n.pt')

try:
    model = YOLO(MODEL_PATH)
    print("YOLOv11n 모델 로드 성공")
except Exception as e:
    print(f"YOLOv11n 모델 로드 실패: {e}")
    # 오류 처리 필요

def generate_frame(camera_id):
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"카메라 {camera_id}를 열 수 없습니다.")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print(f"카메라 {camera_id} 프레임 읽기 실패")
                break

            # Ultralytics를 사용한 추론
            results = model(frame)

            # 결과 처리 및 프레임에 그리기
            for r in results:
                boxes = r.boxes.cpu().numpy()
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    confidence = box.conf[0]
                    class_id = int(box.cls[0])
                    label = f"{model.names[class_id]} {confidence:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            _, buf = cv2.imencode('.jpg', frame)
            frame_bytes = buf.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.01)
    except Exception as e:
        print("스트리밍 중 예외 발생:", e)
    finally:
        cap.release()

@camera_bp.route('/stream/<int:camera_id>')
def video_feed(camera_id):
    return Response(generate_frame(camera_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')