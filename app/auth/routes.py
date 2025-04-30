from flask import render_template, request, redirect, url_for, flash, current_app, Response, jsonify
from flask_login import login_user, logout_user, current_user
from app.models import User
from app import db
from . import bp
import random
import string
import json
import csv
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 이메일 인증번호 저장 (임시 - 실제 앱에서는 더 안전한 방식 사용)
email_verification_codes = {}

# CSV 파일 경로 설정 (실제 경로로 변경해야 함)
CSV_FILE_PATH = r'C:\Users\PC\Desktop\solaproject\business_info.csv'

def generate_verification_code(length=12):
    """무작위 숫자 인증번호 생성"""
    characters = string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def format_verification_code_with_hyphens(code):
    """인증번호에 4자리마다 하이픈 추가"""
    parts = [code[i:i+4] for i in range(0, len(code), 4)]
    return '-'.join(parts)

def send_verification_email(email, verification_code):
    subject = "[YourAppName] 이메일 인증번호"
    formatted_code = format_verification_code_with_hyphens(verification_code) # 하이픈 추가
    body = f"안녕하세요!\n\n귀하의 이메일 인증번호는 다음과 같습니다:\n\n{formatted_code}\n\n인증 페이지에 입력하여 이메일 주소를 확인해주세요."

    sender_email = current_app.config['MAIL_USERNAME']
    sender_password = current_app.config['MAIL_PASSWORD']
    mail_server = current_app.config['MAIL_SERVER']
    mail_port = current_app.config['MAIL_PORT']
    mail_use_tls = current_app.config.get('MAIL_USE_TLS', False)
    mail_use_ssl = current_app.config.get('MAIL_USE_SSL', True)

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = sender_email
    msg['To'] = email

    try:
        if mail_use_ssl:
            server = smtplib.SMTP_SSL(mail_server, mail_port)
        else:
            server = smtplib.SMTP(mail_server, mail_port)
            if mail_use_tls:
                server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        current_app.logger.info(f"SMTP 이메일 발송 성공: {email}")
        return {'statusCode': '202', 'statusName': 'success'}
    except Exception as e:
        current_app.logger.error(f"SMTP 이메일 발송 실패: {e}")
        return {'statusCode': '500', 'statusName': 'error', 'message': str(e)}

def is_valid_business_info_in_csv(business_number, company_name):
    """CSV 파일에서 사업자 등록번호와 대표자명이 모두 일치하는지 확인"""
    try:
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)  # 헤더를 읽고 (선택 사항)
            for row in reader:
                if len(row) >= 2 and row[1] == business_number and row[0] == company_name:
                    return True
        return False
    except FileNotFoundError:
        current_app.logger.error(f"CSV 파일 '{CSV_FILE_PATH}'을 찾을 수 없습니다.")
        return False

@bp.route('/admin_p1', methods=['GET'])
def admin_p1():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('admin_p1.html')

@bp.route('/verify_business_info', methods=['POST'])
def verify_business_info():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    part1 = request.form.get('business-part1')
    part2 = request.form.get('business-part2')
    part3 = request.form.get('business-part3')
    representative_name = request.form.get('representative-name').strip()
    email = request.form.get('email').strip()

    business_number = f"{part1}-{part2}-{part3}"

    if not all([part1, part2, part3, representative_name, email]) or not (len(part1) == 3 and len(part2) == 2 and len(part3) == 5):
        flash('모든 필드를 올바른 형식으로 입력해주세요.', 'error')
        return redirect(url_for('auth.admin_p1'))

    if is_valid_business_info_in_csv(business_number, representative_name):
        # 인증 코드 생성 및 저장
        verification_code = generate_verification_code()
        email_verification_codes[email] = verification_code

        # 인증 이메일 발송 (formatted_code는 이메일 본문에만 사용)
        result = send_verification_email(email, verification_code)

        if result['statusCode'] == '202':
            flash('이메일로 인증번호가 발송되었습니다. 확인 후 인증해주세요.', 'info')
            return redirect(url_for('auth.admin_p2', email=email))
        else:
            flash('인증 이메일 발송에 실패했습니다. 다시 시도해주세요.', 'error')
            return redirect(url_for('auth.admin_p1'))
    else:
        flash('사업자 등록번호 또는 대표자명이 올바르지 않습니다.', 'error')
        return redirect(url_for('auth.admin_p1'))

@bp.route('/admin_p2/<email>', methods=['GET'])
def admin_p2(email):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('admin_p2.html', email=email)

@bp.route('/verify_code/<email>', methods=['POST'])
def verify_code(email):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    verification_part1 = request.form.get('verify-part1')
    verification_part2 = request.form.get('verify-part2')
    verification_part3 = request.form.get('verify-part3')
    user_code = f"{verification_part1}{verification_part2}{verification_part3}"

    stored_code = email_verification_codes.get(email)

    if stored_code and user_code == stored_code:
        del email_verification_codes[email] # 인증 완료 후 코드 삭제
        return jsonify({'success': True, 'redirect_url': url_for('auth.register_form', email=email)})
    else:
        return jsonify({'success': False, 'message': '인증번호가 올바르지 않습니다.'})

@bp.route('/register_form/<email>', methods=['GET', 'POST'])
def register_form(email):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        company_name = request.form.get('company-name')
        password = request.form.get('password')
        password2 = request.form.get('password-confirm')

        if not company_name or not password:
            flash('모든 필수 필드를 입력해주세요.', 'error')
            return render_template('register_form.html', email=email)

        if password != password2:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return render_template('register_form.html', email=email)

        if User.query.filter_by(email=email).first():
            flash('이미 등록된 이메일 주소입니다.', 'error')
            return render_template('register_form.html', email=email)

        # 사용자 생성 및 저장
        user = User(company_name=company_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('회원가입이 완료되었습니다. 로그인해주세요.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_form.html', email=email)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    current_app.logger.debug("!!! LOGIN 함수 실행됨 !!!")
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        current_app.logger.debug(f"로그인 시도 - 입력된 이메일: {email}")
        user = User.query.filter_by(email=email).first()
        current_app.logger.debug(f"조회된 사용자 객체: {user}")

        if user:
            password_check_result = user.check_password(password)
            current_app.logger.debug(f"비밀번호 검증 결과: {password_check_result}")
            if password_check_result:
                login_user(user)
                current_app.logger.debug(f"로그인 성공 - 사용자 ID: {user.id}")
                return redirect(url_for('main.index'))
            else:
                current_app.logger.debug("로그인 실패 - 비밀번호 불일치")
                error = '이메일 또는 비밀번호가 올바르지 않습니다.'
        else:
            current_app.logger.debug("로그인 실패 - 해당 이메일의 사용자 없음")
            error = '이메일 또는 비밀번호가 올바르지 않습니다.'

    return render_template('login.html', error=error)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))