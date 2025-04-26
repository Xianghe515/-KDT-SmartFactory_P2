## 훈련 후 한글적용 및 라즈베라파이 접속 경로 지정 
import cv2
import torch
from flask import Flask, Response
from PIL import ImageFont, ImageDraw, Image
import numpy as np
import os

# Flask 애플리케이션 초기화
app = Flask(__name__)

# YOLO 모델 경로 설정
MODEL_PATH = "./weights/best.pt"  # YOLO 모델 가중치 경로
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# 전역 변수로 모델 로드
try:
    if os.path.exists(MODEL_PATH):
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=MODEL_PATH, force_reload=False).to(DEVICE)
        print("로컬 YOLO 모델이 성공적으로 로드되었습니다.")
    else:
        model = torch.hub.load("ultralytics/yolov5", "custom", path=MODEL_PATH, force_reload=True).to(DEVICE)
        print("YOLO 모델을 다운로드하고 로드했습니다.")
    model.names = {0: '사람'}
except Exception as e:
    print(f"모델 로드 중 오류 발생: {e}")
    exit()

# 카메라 스트림 URL
CAMERA_URL = "http://192.168.10.249:8000/stream.mjpg"
cap = cv2.VideoCapture(CAMERA_URL)

# 한글 텍스트 출력 함수
def put_text_korean(img, text, position, font_path, font_size, color):
    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError as e:
        print(f"Error loading font: {e}")
        return img  # 폰트 로드 실패 시 원본 이미지 반환

    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)
    draw.text(position, text, font=font, fill=color)
    return np.array(img_pil)

def generate_frames():
    """카메라 프레임을 처리하고 YOLO로 물체를 인식"""
    while True:
        success, frame = cap.read()
        if not success:
            print("카메라에서 프레임을 읽을 수 없습니다.")
            break

        # 프레임을 RGB 형식으로 변환
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # YOLO 모델 추론
        results = model(frame_rgb)

        # 디버깅: 결과 확인
        print("탐지된 물체 결과:", results.xyxy[0])

        # 탐지된 물체를 처리
        for (*box, conf, cls) in results.xyxy[0]:  # 탐지 결과 반복
            x1, y1, x2, y2 = map(int, box)  # 경계 상자 좌표
            label = model.names[int(cls)]  # 클래스 이름
            confidence = float(conf)  # 신뢰도

            # 신뢰도 필터링 (임계값)
            if confidence < 0.10:  # 신뢰도 임계값 조정
                continue

            # 경계 상자와 라벨 그리기
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # 녹색 경계 상자
            # 한글 텍스트 출력
            font_path = "C:\\Users\\PC\\Desktop\\project11\\yolov5\\font\\NanumGothic.ttf"
            if not os.path.exists(font_path):
                print(f"Error: Font file not found at {font_path}")
                return None

            frame = put_text_korean(
                frame,
                f"{label} {confidence:.2f}",
                (x1, y1 - 10),
                font_path,  # 폰트 파일 경로 설정
                20,  # 폰트 크기
                (0, 255, 0),  # 폰트 색상
            )

        # 프레임을 JPEG 형식으로 변환
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()

        # 프레임을 반환
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

@app.route("/")
def index():
    """메인 페이지"""
    return "<h1>YOLOv5 실시간 물체 인식</h1><img src='/video' width='640' height='480'>"

@app.route("/video")
def video():
    """비디오 스트림"""
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)