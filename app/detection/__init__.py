from flask import Blueprint

bp = Blueprint(
    'detection',
    __name__,
    template_folder='templates',  # app/detection/templates 참조
    url_prefix='/detection'       # /detection 에 매핑
)

from . import routes
