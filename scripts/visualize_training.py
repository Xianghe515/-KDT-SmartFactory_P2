import matplotlib.pyplot as plt
import pandas as pd

# 로그 파일 로드 (예시: CSV 파일)
df = pd.read_csv("train_log.csv")

# 손실 함수 그래프 생성
plt.plot(df["epoch"], df["loss"], label="Train Loss")
plt.plot(df["epoch"], df["val_loss"], label="Validation Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Loss Curve")
plt.legend()
plt.show()

# 정확도 그래프 생성
plt.plot(df["epoch"], df["accuracy"], label="Train Accuracy")
plt.plot(df["epoch"], df["val_accuracy"], label="Validation Accuracy")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.title("Accuracy Curve")
plt.legend()
plt.show()