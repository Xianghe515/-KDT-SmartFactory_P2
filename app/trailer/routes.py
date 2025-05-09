from flask import render_template
from . import bp  # app.trailer 패키지 내에서 bp 임포트

@bp.route('/trailer')
def trailer_page():
    return render_template('trailer/trailer.html')

# 다른 트레일러 관련 라우트 정의 ...