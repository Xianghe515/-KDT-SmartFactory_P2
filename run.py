import os
import subprocess
from app import create_app
from config import config


# 기본 환경 설정
app_env = 'development'

# NPM 개발 서버 자동 실행 (한 번만)
if os.environ.get("FLASK_RUN_FROM_CLI") == "true" and not os.environ.get("NPM_DEV_STARTED"):
    os.environ["NPM_DEV_STARTED"] = "1"
    subprocess.Popen(['npm.cmd', 'run', 'dev'], cwd=os.path.join(os.getcwd(), 'makesense'))

# Flask 앱 생성 및 라우트 등록
app = create_app(config[app_env])


if __name__ == '__main__':
    if os.environ.get("FLASK_RUN_FROM_CLI") == "true" and not os.environ.get("NPM_DEV_STARTED"):
        os.environ["NPM_DEV_STARTED"] = "1"
        subprocess.Popen(['npm.cmd', 'run', 'dev'], cwd=os.path.join(os.getcwd(), 'makesense'))

    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=8000)
