import os
from app import create_app
from config import config

# 1) 기본값을 'development'로
app_env = os.environ.get('FLASK_ENV') or 'development'
app = create_app(config[app_env])

if __name__ == '__main__':
    # 2) config.DEBUG 를 그대로 반영
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=8000)
