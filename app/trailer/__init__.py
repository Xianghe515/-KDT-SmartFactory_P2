from flask import Blueprint

bp = Blueprint(
    'trailer',
    __name__,
    template_folder='templates',  # app/trailer/templates 참조
    url_prefix='/trailer'         # /trailer 에 매핑
)

from . import routes
