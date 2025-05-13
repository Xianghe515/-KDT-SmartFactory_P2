from flask import jsonify, request, url_for # url_for 임포트 추가
from datetime import datetime
import os
from app import Log_Utils
from . import bp

@bp.route('/api/logs')
def get_logs():
    log_dir = 'app/static/detected'
    logs = []

    # 클라이언트 기준 IP/호스트 이름 가져오기
    host = request.host.split(':')[0]

    for filename in sorted(os.listdir(log_dir), reverse=True):
        # 이미지 파일만 처리
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            filepath = os.path.join(log_dir, filename)

            # 파일 생성 시간 가져오기
            created_time = datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S')

            # 파일 이름에서 정보 추출 (Log_Utils는 외부 모듈이므로 assumed)
            issue_type = Log_Utils.extract_issue_type(filename)
            severity, severity_color = Log_Utils.map_severity(issue_type)
            camera_name = filename.split('_')[0] # 예시: 파일 이름이 'Camera 0_...' 형태일 경우

            # Flask의 static 파일에 대한 상대 경로 생성 (로그 목록 이미지 표시용)
            image_static_path = url_for('static', filename=f'detected/{filename}')

            # --- 수정된 부분: Makesense로 넘길 이미지의 전체 URL 생성 ---
            # Flask 앱의 IP/호스트, 포트, 정적 파일 경로를 조합하여 전체 URL 만듦
            image_full_url = f'http://{host}:5000{image_static_path}'

            # Makesense의 annotationUrl에 이미지의 전체 URL을 파라미터로 넘김
            annotation_url = f'http://{host}:3000/?image_url={image_full_url}'
            # --------------------------------------------------------

            logs.append({
                'filename': filename,
                'timestamp': created_time,
                'imageUrl': image_static_path, # 로그 목록 이미지 표시에는 상대 경로 사용
                'issueType': issue_type,
                'severity': severity,
                'severityColor': severity_color,
                'cameraName': camera_name,
                'annotationUrl': annotation_url # Makesense 연동 시에는 전체 URL 사용
            })

    # 최신 로그부터 보여주기 위해 뒤집힌 순서로 리스트 반환
    # 이미 sorted(..., reverse=True) 했으므로 이 부분은 불필요할 수 있습니다.
    # 필요하다면 logs = logs[::-1] 로 다시 뒤집을 수 있으나, sorted에서 이미 처리됨.
    return jsonify(logs)