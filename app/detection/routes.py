from flask import jsonify, request, url_for # url_for 임포트 추가
from datetime import datetime
import os
from app import Log_Utils
from app.models import DetectionLog  # DB 모델 임포트
from . import bp

@bp.route('/api/logs')
def get_logs():
    host = request.host.split(':')[0]

    # 최신 로그 순으로 정렬
    logs_query = DetectionLog.query.order_by(DetectionLog.timestamp.desc()).all()

    logs = []
    for log in logs_query:
        filename = os.path.basename(log.image_path)  # 'static/detected/Camera 0_...jpg'에서 파일명만 추출
        created_time = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')

        issue_type = Log_Utils.extract_issue_type(filename)
        severity, severity_color = Log_Utils.map_severity(issue_type)

        camera_name = filename.split('_')[0]  # 예: 'Camera 0_...'
        confidence = log.confidence
        
        # Flask static 파일에 대한 경로 생성
        image_static_path = url_for('static', filename=f'detected/{filename}')

        # 전체 이미지 URL (makesense 연동용)
        image_full_url = f'http://{host}:5000{image_static_path}'
        annotation_url = f'http://{host}:3000/?image_url={image_full_url}'

        logs.append({
            'filename': filename,
            'timestamp': created_time,
            'imageUrl': image_static_path,
            'issueType': issue_type,
            'severity': severity,
            'severityColor': severity_color,
            'cameraName': camera_name,
            'annotationUrl': annotation_url,
            'confidence': confidence
        })

    return jsonify(logs)