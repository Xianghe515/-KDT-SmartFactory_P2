import os
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS # CORS 임포트 추가

# ─── 확장(Extension) 객체 생성 ───
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
socketio = SocketIO()


def create_app(config_class):
    # ─── Flask 애플리케이션 생성 ───
    app = Flask(__name__)
    # 설정 객체 로드
    app.config.from_object(config_class)

    # ─── 확장 초기화 ───
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app)
    
    CORS(app, origins="http://192.168.0.133:3000")  
    
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

    # ─── 기본 라우트 설정: / 접속 시 로그인 페이지로 리다이렉트 ───
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # ─── 로그인 매니저 사용자 로더 ───
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app