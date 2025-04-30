from flask import render_template
from . import bp  # app.detection 패키지 내에서 bp 임포트

@bp.route('/detection')
def detection_page():
    return render_template('detection/detection.html')

# 다른 감지 관련 라우트 정의 ...