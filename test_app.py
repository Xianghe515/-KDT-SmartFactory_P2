import os
import cv2
import numpy as np
from flask import Flask, Response
from PIL import ImageFont, ImageDraw, Image
from datetime import datetime
from VideoStream import VideoStream
from ultralytics import YOLO

import logging
logging.getLogger('ultralytics').setLevel(logging.WARNING)

# Flask 앱 초기화
app = Flask(__name__)


# 설정
MODEL_PATH = "./runs/detect/train4/weights/best.pt"  # 모델 경로
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CAMERA_URL = "http://192.168.0.198:8000"
FONT_PATH = "/home/xianghe/TRAININGYOLO11/font/NanumGothic.ttf"
IMAGE_PATH = "/home/xianghe/TRAININGYOLO11/testImage/snow_test.jpg"
stream = VideoStream("http://192.168.0.198:8000")

# 모델 로드
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)

    # ckpt = torch.load(MODEL_PATH, weights_only=False)  # 체크포인트 전체 로드
    # model = ckpt['model']  # model 꺼내기
    # model = model.autoshape() if hasattr(model, 'autoshape') else model  # autoshape 적용 (있으면)
    # model = model.to(DEVICE)  # 디바이스 보내기
    
    # model.names = {0: '사람'}  
    print(model.names)
    # # 클래스 이름 매핑
    # model.names = {0: ''}
    # model.names = {1: ''}
    # model.names = {2: ''}
    # model.names = {3: ''}
    # model.names = {4: ''}
    # model.names = {5: ''}
    
    print("YOLO11 모델이 성공적으로 로드되었습니다.")
except Exception as e:
    print(f"모델 로드 중 오류 발생: {e}")
    exit(1)

# 한글 텍스트 출력 함수
# def put_text_korean(img, text, position, font_path=FONT_PATH, font_size=20, color=(0, 255, 0)):
#     try:
#         font = ImageFont.truetype(font_path, font_size)
#     except Exception as e:
#         print(f"폰트 로드 오류: {e}")
#         return img1

#     img_pil = Image.fromarray(img)
#     draw = ImageDraw.Draw(img_pil)
#     draw.text(position, text, font=font, fill=color)
#     return np.array(img_pil)

def put_text_korean(img, text, position, font_path=FONT_PATH, font_size=20, color=(0, 255, 0)):
    try:
        # PIL 이미지는 RGB 형식이므로 BGR인 OpenCV 이미지를 RGB로 변환합니다.
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(img_pil)
        font = ImageFont.truetype(font_path, font_size)
        draw.text(position, text, font=font, fill=color)
        # 다시 OpenCV BGR 형식으로 변환하여 반환합니다.
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except FileNotFoundError:
         print(f"폰트를 찾을 수 없습니다: {font_path}. 기본 폰트를 사용합니다.")
         # 폰트 로드 실패 시 기본 OpenCV putText 사용 (한글 깨짐 가능성 있음)
         cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_size/30, color, 2)
         return img
    except Exception as e:
        print(f"폰트 로드 또는 텍스트 출력 오류: {e}")
        # 오류 발생 시 원본 이미지 반환
        return img

def classify_panel_type(width_px, height_px):
    aspect_ratio = width_px / height_px
    if width_px >= 170 and height_px >= 170:
        return "square"
    elif height_px >= 200 and width_px < 100:
        return "long"
    elif width_px < 70 and height_px < 130:
        return "small"
    else:
        return "unknown"


def generate_frames():
    target_class_indices = [0]  # 필요한 클래스 인덱스만 필터링
    colors = np.random.uniform(0, 255, size=(len(model.names), 3))

    while True:
        frame = stream.get_frame()
        if frame is None:
            continue

        img = frame.copy()
        results = model(img)

        now = datetime.now()
        current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, current_time_str, (img.shape[1] - 630, img.shape[0] - 20),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (83, 115, 219), 2)

        frame_detected_names = set()

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].item()
                cls = box.cls[0].item()
                class_index = int(cls)

                if class_index in target_class_indices and conf >= 0.75:
                    frame_detected_names.add(model.names[class_index])
                    color = colors[class_index]

                    # 픽셀 단위 크기 계산
                    width_px = x2 - x1
                    height_px = y2 - y1
                    aspect_ratio = width_px / height_px

                    # 모형 분류
                    panel_type = classify_panel_type(width_px, height_px)

                    # 정보 표시용 텍스트
                    label = f"{model.names[class_index]} {conf:.2f}"
                    size_info = f"W: {width_px:.0f}px H: {height_px:.0f}px R: {aspect_ratio:.2f}"
                    type_info = f"Type: {panel_type}"

                    # 박스와 텍스트 출력
                    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
                    cv2.putText(img, label, (int(x1), int(y1) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    cv2.putText(img, size_info, (int(x1), int(y2) + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    cv2.putText(img, type_info, (int(x1), int(y2) + 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        _, buffer = cv2.imencode('.jpg', img)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type:image/jpeg\r\n'
               b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
               b'\r\n' + frame_bytes + b'\r\n')




@app.route("/")
def index():
    return "<h1>YOLO11 실시간 물체 인식</h1><img src='/video' width='640' height='480'>"

@app.route("/video")
def video():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/image") # 또는 /video 라우트 이름을 그대로 사용해도 됩니다.
def detect_image_route():
    image_bytes, error_message = get_detected_image()
    
    if image_bytes is not None:
        # 성공적으로 처리된 이미지 바이트를 응답으로 보냅니다.
        return Response(image_bytes, mimetype="image/jpeg")
    else:
        # 이미지 로드 또는 처리 실패 시 오류 응답
        # send_file을 사용하면 파일 자체가 없는 경우 404 응답을 쉽게 보낼 수 있지만,
        # 여기서는 내부 처리 오류도 포함하므로 404 또는 500 오류 응답 코드를 사용합니다.
        return Response(error_message, status=500, mimetype="text/plain") # 500 Internal Server Error

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
