import os
from app import create_app
from config import config  # config 딕셔너리 임포트

app_env = os.environ.get('FLASK_ENV') or 'local'
app = create_app(config[app_env])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)