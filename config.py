import os
from dotenv import load_dotenv
from pathlib import Path

basedir = Path(__file__).parent
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('mysql://', 'mysql+pymysql://') if os.environ.get('DATABASE_URL') and 'mysql://' in os.environ.get('DATABASE_URL') else 'sqlite:///site.db'
    # 다른 공통 설정...
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') == '1'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') == '1'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('mysql://', 'mysql+pymysql://') if os.environ.get('DATABASE_URL') and 'mysql://' in os.environ.get('DATABASE_URL') else f"sqlite:///{basedir / 'dev.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

# 다른 환경 설정 (ProductionConfig, TestingConfig 등)은 필요에 따라 추가

config = {
    "development": DevelopmentConfig,
    "local":       DevelopmentConfig,   # ← 추가
    
}
