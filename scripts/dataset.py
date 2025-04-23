import torch
import os
from PIL import Image
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2

class CustomDataset(torch.utils.data.Dataset):
    def __init__(self, image_dir, label_dir, transform=None):
        """
        Args:
            image_dir (str): 이미지 디렉토리 경로
            label_dir (str): 레이블 디렉토리 경로
            transform (callable, optional): 이미지에 적용할 데이터 증강 파이프라인
        """
        self.image_dir = image_dir
        self.label_dir = label_dir
        self.transform = transform
        
        # 디렉토리 확인 및 예외 처리
        if not os.path.isdir(image_dir):
            raise ValueError(f"Invalid image directory: {image_dir}")
        if not os.path.isdir(label_dir):
            raise ValueError(f"Invalid label directory: {label_dir}")
        
        # 이미지 파일 목록 가져오기
        self.image_files = [f for f in os.listdir(image_dir) if f.endswith(".jpg")]  # .jpg 파일 필터링
        if len(self.image_files) == 0:
            raise ValueError(f"No .jpg files found in directory: {image_dir}")

    def __len__(self):
        """
        Returns:
            int: 데이터셋의 총 이미지 수
        """
        return len(self.image_files)

    def __getitem__(self, idx):
        """
        Args:
            idx (int): 인덱스

        Returns:
            tuple: (이미지 텐서, 레이블 텐서)
        """
        # 이미지와 레이블 파일 경로 생성
        image_path = os.path.join(self.image_dir, self.image_files[idx])
        label_path = os.path.join(self.label_dir, self.image_files[idx].replace(".jpg", ".txt"))

        # 이미지 읽기 및 예외 처리
        try:
            image = Image.open(image_path).convert("RGB")
        except FileNotFoundError:
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # 레이블 파일 로드
        labels = self.load_labels(label_path)

        # 데이터 증강 및 변환 적용
        if self.transform:
            transformed = self.transform(image=np.array(image))  # Albumentations 사용
            image = transformed["image"]

        # 레이블을 PyTorch 텐서로 변환
        labels = torch.tensor(labels, dtype=torch.float32)

        return image, labels

    def load_labels(self, label_path):
        """
        레이블 파일을 읽어 데이터 리스트로 변환합니다.

        Args:
            label_path (str): 레이블 파일 경로

        Returns:
            list: 레이블 데이터 리스트
        """
        labels = []
        try:
            with open(label_path, "r") as f:
                for line in f:
                    try:
                        class_id, x_center, y_center, width, height = map(float, line.strip().split())
                        labels.append([class_id, x_center, y_center, width, height])
                    except ValueError:
                        print(f"Invalid label format in file: {label_path}")
        except FileNotFoundError:
            print(f"Label file not found: {label_path}")
        return labels
