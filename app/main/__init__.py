from flask import Blueprint

bp = Blueprint(
    'main',
    __name__,
    template_folder='templates',  # app/main/templates 참조
)

from . import routes
