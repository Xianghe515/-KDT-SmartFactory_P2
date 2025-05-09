import os
import subprocess
from app import create_app
from config import config

# 1) 기본값을 'development'로
app_env = 'development'

# 서버 한 번만 로드하게끔
if os.environ.get("FLASK_RUN_FROM_CLI") == "true" and not os.environ.get("NPM_DEV_STARTED"):
    os.environ["NPM_DEV_STARTED"] = "1"
    subprocess.Popen(['npm.cmd', 'run', 'dev'], cwd=os.path.join(os.getcwd(), 'makesense'))

app = create_app(config[app_env])
        
if __name__ == '__main__':
    if os.environ.get("FLASK_RUN_FROM_CLI") == "true" and not os.environ.get("NPM_DEV_STARTED"):
        os.environ["NPM_DEV_STARTED"] = "1"
        subprocess.Popen(['npm.cmd', 'run', 'dev'], cwd=os.path.join(os.getcwd(), 'makesense'))
    # 2) config.DEBUG 를 그대로 반영
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=8000)
