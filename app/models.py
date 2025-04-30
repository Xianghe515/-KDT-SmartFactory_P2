from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)  # 이름 필드 추가
    last_name = db.Column(db.String(50), nullable=False)   # 성 필드 추가
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)  # nullable=False 추가
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

# 다른 모델 정의 (예: 불량 검출 로그)
class DetectionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    camera_id = db.Column(db.Integer)
    defect_type = db.Column(db.String(64))
    confidence = db.Column(db.Float)
    image_path = db.Column(db.String(128))

    def __repr__(self):
        return f'<DetectionLog {self.timestamp} - {self.defect_type}>'