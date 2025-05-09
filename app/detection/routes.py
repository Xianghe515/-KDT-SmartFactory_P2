from flask import render_template
from . import bp  # app.detection 패키지 내에서 bp 임포트

@bp.route('/api/logs')
def get_logs():
    log_dir = 'static/detected'
    logs = []

    for filename in sorted(os.listdir(log_dir), reverse=True):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            filepath = os.path.join(log_dir, filename)
            created_time = datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            logs.append({
                'filename': filename,
                'timestamp': created_time,
                'url': f'/static/detected/{filename}'
            })

    return jsonify(logs)
# 다른 감지 관련 라우트 정의 ...