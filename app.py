import argparse
import os
import torch

from scripts.train import train  # 학습 스크립트 import

def main():
    parser = argparse.ArgumentParser(description="YOLOv11 Training Application")
    parser.add_argument("--data", type=str, default="dataset/data.yaml", help="Path to data.yaml file")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for training")
    # weights 인자 제거
    args = parser.parse_args()

    train(
        data=args.data,
        epochs=args.epochs,
        batch_size=args.batch_size
    )

if __name__ == "__main__":
    main()
