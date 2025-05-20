import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS

# ─── 확장(Extension) 객체 생성 ───
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
socketio = SocketIO()

def create_app(config_class):
    from .VideoStream import CameraManager  # 카메라 관리 및 USB 이벤트 감지 클래스
    from .camera import routes as camera_routes

    # ─── Flask 앱 생성 및 설정 ───
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ─── 확장 초기화 ───
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    CORS(app, origins="*")

    # ─── 카메라 이름 정의 (고정된 이름 기준) ───
    camera_names = {
        0: "FHD Camera",
        1: "GENERAL WEBCAM",
        2: "HD camera"
    }

    # ─── 카메라 매니저 생성 및 초기화 ───
    camera_manager = CameraManager(socketio, camera_names)
    # 만약 CameraManager 내부에 start() 또는 init 함수가 있다면 반드시 호출
    if hasattr(camera_manager, 'start'):
        camera_manager.start()
    elif hasattr(camera_manager, 'initialize'):
        camera_manager.initialize()
    # app 컨텍스트에 카메라 매니저 할당 (다른 모듈에서 참조용)
    app.camera_manager = camera_manager

    # ─── 블루프린트 등록 ───
    from .main import bp as main_bp
    from .auth import bp as auth_bp
    from .camera.routes import bp as camera_bp  
    from .detection import bp as detection_bp
    from .trailer import bp as trailer_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(detection_bp)
    app.register_blueprint(trailer_bp)


    # ─── 기본 라우트 ───
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # ─── 사용자 로더 ───
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
