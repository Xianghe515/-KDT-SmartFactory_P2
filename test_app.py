import os
import cv2
import torch
import numpy as np
from flask import Flask, Response
from PIL import ImageFont, ImageDraw, Image

# Flask 앱 초기화
app = Flask(__name__)

# 설정
MODEL_PATH = "./runs/detect/train3/weights/best.pt"  # 모델 경로
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CAMERA_URL = "http://192.168.0.198:8000"
FONT_PATH = "/home/xianghe/TRAININGYOLO11/font/NanumGothic.ttf"
IMAGE_PATH = "/home/xianghe/TRAININGYOLO11/testImage/snow_test.jpg"

# 모델 로드
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {MODEL_PATH}")

    ckpt = torch.load(MODEL_PATH, weights_only=False)  # 체크포인트 전체 로드
    model = ckpt['model']  # model 꺼내기
    model = model.autoshape() if hasattr(model, 'autoshape') else model  # autoshape 적용 (있으면)
    model = model.to(DEVICE)  # 디바이스 보내기
    
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


# 카메라 연결
cap = cv2.VideoCapture(CAMERA_URL)
if not cap.isOpened():
    print(f"카메라 연결 실패: {CAMERA_URL}")
    exit(1)

# 한글 텍스트 출력 함수
# def put_text_korean(img, text, position, font_path=FONT_PATH, font_size=20, color=(0, 255, 0)):
#     try:
#         font = ImageFont.truetype(font_path, font_size)
#     except Exception as e:
#         print(f"폰트 로드 오류: {e}")
#         return img

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

# 프레임 생성
from datetime import datetime
from VideoStream import VideoStream
from ultralytics import YOLO
import cv2 as cv

MODEL_PATH = "./runs/detect/train3_fail/weights/best.pt"
model = YOLO(MODEL_PATH)
# model = model.to(DEVICE)  # 디바이스 보내기

stream = VideoStream("http://192.168.0.198:8000")
colors = np.random.uniform(0, 255, size=(len(model.names), 3))
def generate_frames():
	while True:
		frame = stream.get_frame()
		if frame is None:
			continue

		img = frame.copy()
		results = model(img)

		now = datetime.now()
		current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
		cv.putText(img, current_time_str, (img.shape[1] - 630, img.shape[0] - 20),
				cv.FONT_HERSHEY_DUPLEX, 0.7, (83, 115, 219), 2)

		detected_this_frame = False
		frame_detected_names = set()

		for result in results:
			for box in result.boxes:
				x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
				conf = box.conf[0].item()
				cls = box.cls[0].item()
				class_index = int(cls)

				if class_index in target_class_indices and conf >= 0.4:
					detected_this_frame = True
					frame_detected_names.add(model.names[class_index])
					color = colors[class_index]
					cv.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
					cv.putText(img, f"{model.names[class_index]} {conf:.2f}",
							(int(x1), int(y1) - 10), cv.FONT_HERSHEY_SIMPLEX, 0.8, color, 3)
								
		_, buffer = cv.imencode('.jpg', img)
		frame_bytes = buffer.tobytes()
		yield (b'--frame\r\n'
			b'Content-Type:image/jpeg\r\n'
			b'Content-Length: ' + f"{len(frame_bytes)}".encode() + b'\r\n'
			b'\r\n' + frame_bytes + b'\r\n')

def get_detected_image():
    # 이미지 파일 읽기
    frame = cv2.imread(IMAGE_PATH)

    # 이미지 파일 읽기 실패 시 처리
    if frame is None:
        print(f"오류: 이미지를 로드할 수 없습니다: {IMAGE_PATH}")
        return None, "이미지를 로드할 수 없습니다."
    
    # 입력 이미지 크기 출력 (디버깅용)
    print(f"입력 이미지 크기: {frame.shape}")

    # YOLO 모델이 요구하는 크기로 이미지 리사이즈 (예: 640x640)
    input_size = 640  # YOLO 모델이 요구하는 크기
    frame_resized = cv2.resize(frame, (input_size, input_size))

    # 리사이즈된 이미지 크기 출력 (디버깅용)
    print(f"리사이즈된 이미지 크기: {frame_resized.shape}")
    
    # BGR -> RGB 변환 (모델 입력용)
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    # numpy → torch.Tensor 변환
    frame_tensor = torch.from_numpy(frame_rgb).float()
    # 순서 변경 및 배치 차원 추가 (Channels, Height, Width)
    frame_tensor = frame_tensor.permute(2, 0, 1).unsqueeze(0).to(DEVICE)

    # 모델 추론
    with torch.no_grad():
        results = model(frame_tensor.half())

    # --- 탐지 결과 처리 (디버깅 추가) ---
    detected = False  # 탐지된 객체가 있는지 여부를 추적하는 변수

    if results is not None and len(results) > 0 and results[0] is not None:
        print(f"탐지 결과: {results[0].shape}")  # 결과 텐서의 크기 출력

        # 결과에서 각 탐지된 객체 정보 출력
        for detection in results[0]:
            print(f"탐지된 객체: {detection}")  # 탐지된 객체 정보 출력

            detection_data = detection.tolist()

            # 데이터 구조에 대한 유효성 검사
            if len(detection_data) < 3 or not isinstance(detection_data[0], list) or not isinstance(detection_data[2], list):
                continue

            bbox_list = detection_data[0]
            if len(bbox_list) != 4:
                continue
            x1, y1, x2, y2 = map(int, bbox_list)

            obj_conf = detection_data[1]
            if not isinstance(obj_conf, (int, float)):
                continue

            class_scores = detection_data[2]
            if not isinstance(class_scores, list) or not class_scores:
                continue

            class_scores_np = np.array(class_scores)
            if len(class_scores_np.shape) > 1:
                class_scores_np = class_scores_np.flatten()

            if class_scores_np.size == 0:
                continue

            max_class_score = np.max(class_scores_np)
            class_id = np.argmax(class_scores_np)

            confidence = obj_conf * max_class_score

            if confidence < 0.1:  # 신뢰도 임계값 적용
                continue

            label = model.names.get(class_id, "알수없음")
            print(f"물체 감지: {label} | 신뢰도: {confidence:.2f} | 위치: ({x1}, {y1}) -> ({x2}, {y2})")  # 디버깅 출력
            
            # 물체 감지된 경우 바운딩 박스를 그립니다
            frame = cv2.rectangle(
                frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # (0, 255, 0)는 녹색 (RGB)
            frame = put_text_korean(
                frame,
                f"{label} {confidence:.2f}",
                (x1, max(y1 - 25, 0)),
                font_size=20
            )

            detected = True  # 객체가 감지되었음을 표시

    if not detected:
        print("탐지된 물체가 없습니다.")  # 결과가 없는 경우 출력
    else:
        print("물체가 감지되었습니다.")  # 탐지된 물체가 있을 때 출력

    # 처리된 프레임을 JPEG로 인코딩
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        print("처리된 프레임 JPEG 인코딩 실패")
        return None, "이미지 인코딩 실패."

    frame_bytes = buffer.tobytes()

    return frame_bytes, None  # 성공 시 바이트 데이터와 None을 반환




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
