from flask import render_template, request, jsonify, current_app, stream_with_context
from glob import glob
from datetime import datetime
import time
import requests
import os
from . import bp

@bp.route('/')
def index():
    return render_template('index.html')

def get_cvat_session():
    CVAT_HOST = current_app.config['CVAT_HOST']
    CVAT_USERNAME = current_app.config['CVAT_USERNAME']
    CVAT_PASSWORD = current_app.config['CVAT_PASSWORD']

    session = requests.Session()

    # 먼저 로그인해서 CSRF 쿠키 받아오기
    login_url = f"{CVAT_HOST}/api/auth/login"
    login_payload = {"username": CVAT_USERNAME, "password": CVAT_PASSWORD}

    login_resp = session.post(login_url, json=login_payload)
    if login_resp.status_code != 200:
        print("Login failed:", login_resp.text)
        return None

    # 로그인 후 쿠키에서 csrf 토큰 추출
    csrf_token = session.cookies.get('csrftoken')

    # 모든 요청에 CSRF 토큰 헤더 설정
    session.headers.update({
        "X-CSRFToken": csrf_token,
    })

    return session

def get_latest_detected_image():
    images = glob('static/detected/*.jpg')
    if not images:
        return None
    latest_image = max(images, key=os.path.getctime)
    return os.path.abspath(latest_image)

@bp.route('/upload_and_create_task', methods=['POST'])
def upload_and_create_task():
    CVAT_HOST = current_app.config['CVAT_HOST']
    CVAT_USERNAME = current_app.config['CVAT_USERNAME']
    CVAT_PASSWORD = current_app.config['CVAT_PASSWORD']
    
    image_path = get_latest_detected_image()
    if image_path is None:
        return jsonify({"status": "error", "message": "No detected images found."}), 404
    
    task_name = 'AutoTask_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    session = get_cvat_session()

    # 1. Task 생성
    task_data = {
        "name": task_name,
        "labels": [
            {
                "name": "defect",
                "color": "#ff0000",
                "attributes": []
            }
        ]
    }
    task_resp = session.post(f"{CVAT_HOST}/api/tasks", json=task_data)
    
    # 디버깅용
    print("Task creation status:", task_resp.status_code)
    print("Task creation response:", task_resp.text)
    if task_resp.status_code != 201:
        return jsonify({"status": "fail", "reason": task_resp.text}), 500
    
    task_id = task_resp.json()["id"]

    # 2. 이미지 업로드
    with open(image_path, 'rb') as image_file:
        files = {
            'image': image_file
        }
        upload_resp = session.post(
            f"{CVAT_HOST}/api/tasks/{task_id}/data",
            files=files,
            data={"image_quality": 70}
        )
        
    # 디버깅용
    print("Upload status:", upload_resp.status_code)
    print("Upload response:", upload_resp.text)
    if upload_resp.status_code != 202:
        return f"Image upload failed: {upload_resp.text}", 500

    # 3. Job ID 가져오기
    jobs_resp = session.get(f"{CVAT_HOST}/api/tasks/{task_id}/jobs")
    
    # 디버깅용
    print("Job response status:", jobs_resp.status_code)
    print("Job response text:", jobs_resp.text)  
    if jobs_resp.status_code != 200:
        return f"Failed to get jobs: {jobs_resp.text}", 500

    job_id = jobs_resp.json()["results"][0]["id"]

    # 4. CVAT 작업 링크 생성
    cavat_link = f"{CVAT_HOST}/tasks/{task_id}/jobs/{job_id}"

    return jsonify({"status": "success", "task_url": cavat_link})

@bp.route('/label')
def label():
    CVAT_HOST = current_app.config['CVAT_HOST']
    CVAT_USERNAME = current_app.config['CVAT_USERNAME']
    CVAT_PASSWORD = current_app.config['CVAT_PASSWORD']

    session = get_cvat_session()

    # 예시: 최신 Task 사용
    tasks_resp = session.get(f"{CVAT_HOST}/api/tasks?ordering=-id")
    task_list = tasks_resp.json().get("results", [])

    if not task_list:
        return "No CVAT tasks found", 404

    latest_task = task_list[0]
    task_id = latest_task["id"]

    jobs_resp = session.get(f"{CVAT_HOST}/api/tasks/{task_id}/jobs")
    jobs = jobs_resp.json().get("results", [])

    if not jobs:
        return "No jobs found for the task", 404

    job_id = jobs[0]["id"]

    # iframe URL 만들기
    cvat_job_url = f"{CVAT_HOST}/tasks/{task_id}/jobs/{job_id}"

    return render_template("labeling.html", cvat_url=cvat_job_url)