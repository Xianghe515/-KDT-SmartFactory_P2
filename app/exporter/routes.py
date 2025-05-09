from flask import render_template
from . import bp  # app.exporter 패키지 내에서 bp 임포트

@bp.route('/exporter')
def exporter_page():
    return render_template('exporter/exporter.html')

# 다른 내보내기 관련 라우트 정의 ...