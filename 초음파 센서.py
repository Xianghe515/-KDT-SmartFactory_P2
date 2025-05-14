import RPi.GPIO as gpio
import time

TRIGER = 24   # 트리거 GPIO
ECHO = 23     # 에코 GPIO

gpio.setmode(gpio.BCM)
gpio.setup(TRIGER, gpio.OUT)
gpio.setup(ECHO, gpio.IN)

startTime = time.time()

try:
    while True:
		    # Triger로 출력 신호 전송
        gpio.output(TRIGER, gpio.LOW)    # 출력 off
        time.sleep(0.1)
        gpio.output(TRIGER, gpio.HIGH)   # 출력 on
        time.sleep(0.00002)
        gpio.output(TRIGER, gpio.LOW)    # 출력 off

        while gpio.input(ECHO) == gpio.LOW:  # 출력 감지 - triger가 off인 경우
            startTime = time.time()      # 시작 시간

        while gpio.input(ECHO) == gpio.HIGH: # 출력 감지 O -> triger가 on인 경우.. 
            endTime = time.time()        # 감지 시간

        period = endTime - startTime     # 신호 감지 간격
        dist1 = round(period * 1000000 / 58, 2)   # 거리 계산, 2로 라운드 처리 이유는 왕복시간을 통해서 거리를 측정하기 때문
        dist2 = round(period * 17241, 2)

        print("Dist1", dist1, "cm", ", Dist2", dist2, "cm")

        if dist1 < 10 and dist2 < 10:    # 감지 거리가 10cm 미만인 경우 감지 처리
            print("detect")

except:
    print("종료")
    gpio.cleanup()
