# app/auth/__init__.py
from flask import Blueprint

bp = Blueprint(
    'auth',             # ← 반드시 'auth' 로 지정해야 합니다
    __name__,
    template_folder='templates',
    url_prefix='/auth'   # 이 블루프린트의 URL 접두사
)

from . import routes
