import RPi.GPIO as GPIO
import time

led_pin = 17

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(led_pin,GPIO.OUT)

while True:
	GPIO.output(led_pin,1)
	time.sleep(0.2)
	GPIO.output(led_pin,0)
	time.sleep(1)

GPIO.cleanup()
	
