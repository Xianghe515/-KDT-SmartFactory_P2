import time
import RPi.GPIO as GPIO
import requests  # HTTP 요청을 위한 모듈

IR = 23
SERVER_URL = "http://192.168.0.133:5000/camera/trigger"  # 여기에 실제 데스크탑 서버 IP 입력

GPIO.setmode(GPIO.BCM)
GPIO.setup(IR, GPIO.IN)

try:
    while True:
        ir_state = GPIO.input(IR)
        if ir_state == False:  # 감지되었을 때
            print("Detected")
            try:
                response = requests.get(SERVER_URL)
                print("Trigger sent, response:", response.text)
                time.sleep(2)
            except Exception as e:
                print("Error sending trigger:", e)
        else:
            print("Undetected")
            time.sleep(2)
except KeyboardInterrupt:
    print("종료")
    GPIO.cleanup()
