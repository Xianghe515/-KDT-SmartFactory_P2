import torch
import albumentations as A
from albumentations.pytorch import ToTensorV2
import yaml
from scripts.dataset import CustomDataset  # CustomDataset 클래스 import
import os

def train(data, epochs, batch_size):
    # 데이터 증강 파이프라인 정의
    transform = A.Compose([
        A.Resize(height=640, width=640),  # 이미지 크기 통일
        A.RandomRotate90(),
        A.HorizontalFlip(),
        A.RandomBrightnessContrast(),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

    # data.yaml 파일 로드
    with open(data, "r", encoding="utf-8") as f:
        data_yaml = yaml.safe_load(f)

    # 데이터셋 및 데이터 로더 생성
    train_dataset = CustomDataset(
        image_dir=data_yaml["train"],
        label_dir=data_yaml["labels"],
        transform=transform
    )
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4  # 멀티프로세싱 활성화
    )

    # YOLO 모델 생성 (가중치 없이 초기화)
    from ultralytics import YOLO

    # YOLO 모델 생성
    model = YOLO("yolov8s.pt")  # YOLOv8 또는 원하는 모델 가중치 파일
    print("Model loaded successfully.")


    # 옵티마이저 및 손실 함수 정의
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = torch.nn.MSELoss()  # 손실 함수 예시 (바운딩 박스의 좌표 차이 계산)

    # 학습 루프
    for epoch in range(epochs):
        model.train()  # 모델 학습 모드 설정
        epoch_loss = 0
        for images, targets in train_loader:
            images = images.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
            targets = targets.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))

            optimizer.zero_grad()  # 그래디언트 초기화

            # Forward pass
            outputs = model(images)

            # 손실 계산
            loss = loss_fn(outputs, targets)
            epoch_loss += loss.item()

            # Backward pass 및 옵티마이저 업데이트
            loss.backward()
            optimizer.step()

        print(f"Epoch {epoch + 1}/{epochs}, Loss: {epoch_loss:.4f}")

    # 학습된 모델 저장
    torch.save(model.state_dict(), "yolov11_trained_weights.pth")
    print("Model saved as yolov11_trained_weights.pth")

if __name__ == "__main__":
    # 학습 실행
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True, help="Path to data.yaml file")
    parser.add_argument("--epochs", type=int, required=True, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, required=True, help="Batch size")
    args = parser.parse_args()

    train(
        data=args.data,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
