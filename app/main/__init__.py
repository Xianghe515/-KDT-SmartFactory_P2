from flask import Blueprint

bp = Blueprint(
    'main',
    __name__,
    template_folder='templates',  # app/main/templates 참조
    url_prefix='/main'                # 루트(/)에 매핑
)

from . import routes
