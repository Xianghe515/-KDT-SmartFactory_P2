from flask import Blueprint

bp = Blueprint(
    'camera',
    __name__,
    template_folder='templates',  # app/camera/templates 참조
    url_prefix='/camera'          # /camera 에 매핑
)

from . import routes
