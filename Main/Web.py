# -*- coding: utf-8 -*-
#! /usr/bin/env python
# this Web.py also forks RegistrationToSvr.py - Donny
# 사무실 내 서버컴퓨터와의 등록/세션핸들링, 미디어서버와의 접속, 클라이언트와의 접속 모든걸 담당한다.
from flask import Flask, request
import os     #importing os library so as to communicate with the system
import time   #importing time library to make Rpi wait because its too impatient 
os.system ("sudo pigpiod") #Launching GPIO library
time.sleep(1) # As i said it is too impatient and so if this delay is removed you will get an error
import pigpio #importing GPIO library
import RegistrationToSvr
import SmoothGpioController
# import GpioController
import HeartBeatToSvr
import LedController
import requests
from threading import Timer

##PIN MAP
ESC_WEAPON=15 #ESC used weapon
CAMERA_X = 22 #cam x
CAMERA_Y = 23 #cam y
KICK_SOLENOID = 24 #relay for solenoid
KICK_SOLENOID_PWR_SUPPORT_1 = 25 #relay for solenoid
KICK_SOLENOID_PWR_SUPPORT_2 = 8 #relay for solenoid

##OMNI MOTOR
# Raspberry Pi PWN PIN 12, 13, 18, 19
MOTOR_A_L=5  #FRONT_LEFT
MOTOR_A_R=6  #FRONT_LEFT
MOTOR_B_L=13 #FRONT_RIGHT
MOTOR_B_R=19 #FRONT_RIGHT
MOTOR_C_L=12 #BACK_LEFT
MOTOR_C_R=16 #BACK_LEFT
MOTOR_D_L=20 #BACK_RIGHT
MOTOR_D_R=21 #BACK_RIGHT

INJORA35T_STOP=1500 #should be init. (by manually)
INJORA35T_WIDTH=40 #*10 pwm, 40 means it has +-400 pwm.
INJORA35T_OFFSET_MIN_WORK_PWM=70 #Offset for minimum work(starts rotate) (21T PWM 70) for now

Camera_X_MAX = 2500 # 2520, on origin code
Camera_X_MIN = 520
Camera_Y_MAX = 1500
Camera_Y_MIN = 800

Camera_X = 1500
Camera_Y = 1000

pi = pigpio.pi()
pi.set_mode(KICK_SOLENOID, pigpio.OUTPUT)
# pi.set_mode(MOTOR_A, pigpio.OUTPUT)
pi.set_PWM_frequency(MOTOR_A_L,100) #supersafe -> 50hz, but pretty sure the frequency doesnt make any difference to output power, the really matter is 'duty cycle'
pi.set_PWM_frequency(MOTOR_A_R,100)
pi.set_PWM_frequency(MOTOR_B_L,100)
pi.set_PWM_frequency(MOTOR_B_R,100)
pi.set_PWM_frequency(MOTOR_C_L,100)
pi.set_PWM_frequency(MOTOR_C_R,100)
pi.set_PWM_frequency(MOTOR_D_L,100)
pi.set_PWM_frequency(MOTOR_D_R,100)
#18 different frequencies (8000, 4000, 2000, 1600, 1000, 800, 500, 400, 320, 250, 200, 160, 100, 80, 50, 40, 20, 10)
#limited steps between off and fully on (25 at 8000Hz, 250 at 800Hz, 4000 at 50Hz)

# gpioController = GpioController.GpioController() #GPIO fast-serized queue system(sort of)
gpioController = SmoothGpioController.GpioController() #GPIO fast-serized queue system(sort of)
gpioController.setOurDefaultPWM(INJORA35T_STOP, INJORA35T_WIDTH)
gpioController.popDequePeriodically()

#Server Matters
RegistrationToSvr.__name__ #Do registration work to onff local server.
registratorVariableGetter = RegistrationToSvr.Getter()
heartbeater = HeartBeatToSvr.HeartBeating()
heartbeater.setMyInfo(
	registratorVariableGetter.getMyType(),
	registratorVariableGetter.getPrivIP(),
	registratorVariableGetter.getPublibcIP(),
	registratorVariableGetter.getMyPrefferedWebSvrPort(),
	registratorVariableGetter.getMyPrefferedMediaSvrPort()
)
heartbeater.heartbeating()

#Led Controller (ws2812, neopixel)
ledController = LedController.LedControl()

app = Flask(__name__)

def Clamp(val,vMin,vMax):
	if  val > vMin and val < vMax:
		return val
	elif val < vMin:
		return vMin
	elif val > vMax:
		return vMax
	else :
		return val

@app.route("/")
def connectionCheck(): 
	return "working Fine"

@app.route("/join_room")
def joinRoom():
	RegistrationToSvr.joinToGame()
	return "true"

@app.route("/init")
def arm():  
	#movement
	pi.set_PWM_frequency(STEER,50)
	pi.set_servo_pulsewidth(STEER, 1500)
	#weapon(servo)
	pi.set_PWM_frequency(SERVO_WEAPON_1,50) # 20 times per a second.
	pi.set_servo_pulsewidth(SERVO_WEAPON_1, INJORA35T_STOP)
	#camera
	pi.set_PWM_frequency(CAMERA_X,50) #Hz, (pulse 1.52ms)---(rest 18.48ms)---(pulse 1.52ms)
	pi.set_servo_pulsewidth(CAMERA_X,1500) #500(min) - 2500(max)
	pi.set_PWM_frequency(CAMERA_Y,50) #Hz, (pulse 1.52ms)---(rest 18.48ms)---(pulse 1.52ms)
	pi.set_servo_pulsewidth(CAMERA_Y,1500)
	time.sleep(100)
	return "ready"
	
#hit by other
@app.route("/damaged", methods = ['GET', 'POST'])
def damaged():
	ledController.setTargetBright(255,0,0)
	ledController.blinkingAndDimming(4)

#TODO: 
@app.route("/move")
# @app.route("/motor")
def motorControl(): 
	state = request.args.get("state")
	if state == "forward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_PWM_dutycycle(MOTOR_A_L,velocity*25) #second parameter range => (0 ~ 255)
		pi.set_PWM_dutycycle(MOTOR_A_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_B_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_B_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_C_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_C_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_D_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_D_R,velocity*0)
	elif state == "backward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_PWM_dutycycle(MOTOR_A_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_A_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_B_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_B_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_C_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_C_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_D_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_D_R,velocity*25)
	elif state == "left":
		velocity = int(request.args.get("vel"))
		pi.set_PWM_dutycycle(MOTOR_B_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_B_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_D_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_D_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_C_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_C_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_A_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_A_L,velocity*0)
	elif state == "right":
		velocity = int(request.args.get("vel"))		
		pi.set_PWM_dutycycle(MOTOR_B_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_B_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_D_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_D_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_C_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_C_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_A_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_A_R,velocity*0)
	elif state == "upper_right": 
		velocity = int(request.args.get("vel"))	
		pi.set_PWM_dutycycle(MOTOR_D_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_D_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_A_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_A_R,velocity*0)
	elif state == "lower_left":
		velocity = int(request.args.get("vel"))	
		pi.set_PWM_dutycycle(MOTOR_D_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_D_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_A_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_A_L,velocity*0)
	elif state == "upper_left": 
		velocity = int(request.args.get("vel"))	
		pi.set_PWM_dutycycle(MOTOR_B_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_B_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_C_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_C_R,velocity*0)
	elif state == "lower_right": 
		velocity = int(request.args.get("vel"))	
		pi.set_PWM_dutycycle(MOTOR_B_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_B_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_C_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_C_L,velocity*0)
	elif state == "stop":
    	# velocity = int(request.args.get("vel"))
    	# pi.set_PWM_dutycycle(MOTOR_C_L,0)
		# pi.set_PWM_dutycycle(MOTOR_C_R,0)
		# pi.set_PWM_dutycycle(MOTOR_D_R,0)
		# pi.set_PWM_dutycycle(MOTOR_D_L,0)
		# pi.set_PWM_dutycycle(MOTOR_A_L,0)
		# pi.set_PWM_dutycycle(MOTOR_A_R,0)
		# pi.set_PWM_dutycycle(MOTOR_B_R,0)
		# pi.set_PWM_dutycycle(MOTOR_B_L,0)
		pi.write(MOTOR_A_L, 0)
		pi.write(MOTOR_A_R, 0)
		pi.write(MOTOR_B_L, 0)
		pi.write(MOTOR_B_R, 0)
		pi.write(MOTOR_C_L, 0)
		pi.write(MOTOR_C_R, 0)
		pi.write(MOTOR_D_L, 0)
		pi.write(MOTOR_D_R, 0)
	else: 
		# velocity = int(request.args.get("vel"))
    	# pi.set_PWM_dutycycle(MOTOR_C_L,0)
		# pi.set_PWM_dutycycle(MOTOR_C_R,0)
		# pi.set_PWM_dutycycle(MOTOR_D_R,0)
		# pi.set_PWM_dutycycle(MOTOR_D_L,0)
		# pi.set_PWM_dutycycle(MOTOR_A_L,0)
		# pi.set_PWM_dutycycle(MOTOR_A_R,0)
		# pi.set_PWM_dutycycle(MOTOR_B_R,0)
		# pi.set_PWM_dutycycle(MOTOR_B_L,0)
		pi.write(MOTOR_A_L, 0)
		pi.write(MOTOR_A_R, 0)
		pi.write(MOTOR_B_L, 0)
		pi.write(MOTOR_B_R, 0)
		pi.write(MOTOR_C_L, 0)
		pi.write(MOTOR_C_R, 0)
		pi.write(MOTOR_D_L, 0)
		pi.write(MOTOR_D_R, 0)
	return ""
	
#TODO
@app.route("/rotate")
def steerContorl():
	dir = request.args.get("dir")
	if dir == "cw": #Clock wise
		velocity = int(request.args.get("vel"))		
		pi.set_PWM_dutycycle(MOTOR_C_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_C_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_D_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_D_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_A_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_A_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_B_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_B_L,velocity*0)
	elif dir == "ccw": #Counter clock wise
		velocity = int(request.args.get("vel"))
		pi.set_PWM_dutycycle(MOTOR_D_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_D_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_C_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_C_L,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_B_L,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_B_R,velocity*0)
		pi.set_PWM_dutycycle(MOTOR_A_R,velocity*25)
		pi.set_PWM_dutycycle(MOTOR_A_L,velocity*0)
	else: 
		# velocity = int(request.args.get("vel"))
    	# pi.set_PWM_dutycycle(MOTOR_C_L,0)
		# pi.set_PWM_dutycycle(MOTOR_C_R,0)
		# pi.set_PWM_dutycycle(MOTOR_D_R,0)
		# pi.set_PWM_dutycycle(MOTOR_D_L,0)
		# pi.set_PWM_dutycycle(MOTOR_A_L,0)
		# pi.set_PWM_dutycycle(MOTOR_A_R,0)
		# pi.set_PWM_dutycycle(MOTOR_B_R,0)
		# pi.set_PWM_dutycycle(MOTOR_B_L,0)
		pi.write(MOTOR_A_L, 0)
		pi.write(MOTOR_A_R, 0)
		pi.write(MOTOR_B_L, 0)
		pi.write(MOTOR_B_R, 0)
		pi.write(MOTOR_C_L, 0)
		pi.write(MOTOR_C_R, 0)
		pi.write(MOTOR_D_L, 0)
		pi.write(MOTOR_D_R, 0)
	return ""

#WEAPON1_blade
@app.route("/weapon1") #1500, 500 2500
def weapon1Control(): 
	state = request.args.get("state")
	if state == "left":
		#velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_servo_pulsewidth(SERVO_WEAPON_1, int(Clamp(INJORA35T_STOP+10*100,500,2500)))
	if state == "right":
		#velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_servo_pulsewidth(SERVO_WEAPON_1, int(Clamp(INJORA35T_STOP-10*100,500,2500)))
	elif state == "stop":
		pi.set_servo_pulsewidth(SERVO_WEAPON_1, INJORA35T_STOP)
	else: 
		pi.set_servo_pulsewidth(SERVO_WEAPON_1, INJORA35T_STOP)
	return "Checked: " + state

#kick_solenoid
@app.route("/kick_solenoid") #1500, 500 2500
def kickSolenoid(): 
	state = request.args.get("state")
	if state == "run":
		pi.write(KICK_SOLENOID, 1)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_1, 1)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_2, 1)
		solenoidStopTimer = Timer(0.15, kickSolenoidStop)
		solenoidStopTimer.start()
	elif state == "stop":
		pi.write(KICK_SOLENOID, 0)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_1, 0)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_2, 0)
	else: 
		pi.write(KICK_SOLENOID, 0)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_1, 0)
		pi.write(KICK_SOLENOID_PWR_SUPPORT_2, 0)
	return "Checked: " + state

#Blade
@app.route("/esc_weapon")
def escWeaponControl(): 
	state = request.args.get("state")
	if state == "forward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP-velocity*INJORA35T_WIDTH
			,INJORA35T_STOP - (INJORA35T_WIDTH*10)
			,INJORA35T_STOP))
		gpioController.gpio_PIN_PWM(ESC_WEAPON, pwm)
	elif state == "backward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pwm = int(Clamp(INJORA35T_STOP+velocity*INJORA35T_WIDTH
			,INJORA35T_STOP
			,INJORA35T_STOP + (INJORA35T_WIDTH*10)))
		gpioController.gpio_PIN_PWM(ESC_WEAPON, pwm)
	elif state == "stop":
		gpioController.gpio_PIN_PWM(ESC_WEAPON, INJORA35T_STOP)
	else: 
		gpioController.gpio_PIN_PWM(ESC_WEAPON, INJORA35T_STOP)
	return ""
 
@app.route("/camera")
def cameraControl():
	global Camera_X,Camera_Y
	dir = request.args.get("dir")
	velocity = int(request.args.get("vel"))*10 #0~10, 0~5/2 
	if dir == "up":
		Camera_Y = int(Clamp(Camera_Y-velocity,Camera_Y_MIN,Camera_Y_MAX))
	elif dir == "down":
		Camera_Y = int(Clamp(Camera_Y+velocity,Camera_Y_MIN,Camera_Y_MAX))
	elif dir == "left":
		Camera_X = int(Clamp(Camera_X+velocity,Camera_X_MIN,Camera_X_MAX))
	elif dir == "right":
		Camera_X = int(Clamp(Camera_X-velocity,Camera_X_MIN,Camera_X_MAX))
	pi.set_servo_pulsewidth(CAMERA_X,Camera_X) # pin, pwm
	pi.set_servo_pulsewidth(CAMERA_Y,Camera_Y) # pin, pwm
	return "steered"

#little awkward api, but I'm quite sure that this is the best choice 
#untill we gets 'perfect lifecycle smartphone client'.
@app.route("/onusing")
def onUse():
	status = request.args.get("status")
	SVR_BASE_ADDR = 'http://onffworld.iptime.org:48080' #todo: https 보안 스트림으로의 업그레이드
	RESTFUL_EXPRESSION = '/rc/onuse'
	infos = {'type_of_rc':RegistrationToSvr.Getter().getMyType(),'serial_of_rc':RegistrationToSvr.getserial(),'on_use': status}
	response = requests.post(SVR_BASE_ADDR+RESTFUL_EXPRESSION, params=infos) #can be params, or simply json.
	# response = requests.post(SVR_BASE_ADDR+RESTFUL_EXPRESSION, data=infos)
	try:
		response.raise_for_status()
		if(response.status_code == 200 or response.status_code == 201): #good
			pass
			# print('all good!')
		else: #not good, but received anyway.
			pass
			# print('server alive but went wrong. maybe there are some mistaken things?')
		
	except requests.exceptions.HTTPError as e:
		print('bam! error occured while connecting to the static server')
	return status

def kickSolenoidStop():
	pi.write(KICK_SOLENOID, 0)
	pi.write(KICK_SOLENOID_PWR_SUPPORT_1, 0)
	pi.write(KICK_SOLENOID_PWR_SUPPORT_2, 0)
	# print('kick solenoid stop')

if __name__ == "__main__":
	app.run(host="0.0.0.0")
