from flask import jsonify
from datetime import datetime
import os
from app import Log_Utils
from . import bp

@bp.route('/api/logs')
def get_logs():
    from datetime import datetime

    log_dir = 'app/static/detected'
    logs = []

    for filename in sorted(os.listdir(log_dir), reverse=True):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            filepath = os.path.join(log_dir, filename)
            created_time = datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            issue_type = Log_Utils.extract_issue_type(filename)
            severity, severity_color = Log_Utils.map_severity(issue_type)
            camera_name = filename.split('_')[0]  # "Camera 0"

            logs.append({
                'filename': filename,
                'timestamp': created_time,
                'imageUrl': f'/static/detected/{filename}',
                'issueType': issue_type,
                'severity': severity,
                'severityColor': severity_color,
                'cameraName': camera_name,
                'annotationUrl': f'http://localhost:3000/?image_url=http://192.168.0.133/static/detected/{filename}'
            })

    return jsonify(logs)
