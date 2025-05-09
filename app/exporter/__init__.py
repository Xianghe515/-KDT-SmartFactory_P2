from flask import Blueprint

bp = Blueprint(
    'exporter',
    __name__,
    template_folder='templates',  # app/exporter/templates 참조
    url_prefix='/exporter'        # /exporter 에 매핑
)

from . import routes
