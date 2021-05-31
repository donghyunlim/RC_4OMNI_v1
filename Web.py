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
from rpi_common_module import RegistrationToSvr
from rpi_common_module import SmoothGpioController
# import GpioController
from rpi_common_module import HeartBeatToSvr
from rpi_common_module import LedController
import requests
from threading import Timer

##PIN MAP
ESC_WEAPON=15 #ESC used weapon
CAMERA_X = 17 #cam x
CAMERA_Y = 27 #cam y
KICK_SOLENOID = 25 #relay for solenoid
KICK_SOLENOID_PWR_SUPPORT_1 = 8 #relay for solenoid
KICK_SOLENOID_PWR_SUPPORT_2 = 7 #relay for solenoid

##OMNI MOTOR
# Raspberry Pi PWN PIN 12, 13, 18, 19
#MOTOR_A_L=5  #FRONT_LEFT
#MOTOR_A_R=6  #FRONT_LEFT
#MOTOR_B_L=13 #FRONT_RIGHT
#MOTOR_B_R=19 #FRONT_RIGHT
#MOTOR_C_L=12 #BACK_LEFT
#MOTOR_C_R=16 #BACK_LEFT
#MOTOR_D_L=20 #BACK_RIGHT
#MOTOR_D_R=21 #BACK_RIGHT

# Front right wheel
IN1Front=14
IN2Front=15

# Front left wheel
IN3Front=24
IN4Front=23

# rear right wheel
IN1Rear=20
IN2Rear=21

# rear left wheel
IN3Rear=12
IN4Rear=16

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
pi.set_PWM_frequency(IN1Rear,100) #supersafe -> 50hz, but pretty sure the frequency doesnt make any difference to output power, the really matter is 'duty cycle'
pi.set_PWM_frequency(IN2Rear,100)
pi.set_PWM_frequency(IN3Rear,100)
pi.set_PWM_frequency(IN4Rear,100)
pi.set_PWM_frequency(IN1Front,100)
pi.set_PWM_frequency(IN2Front,100)
pi.set_PWM_frequency(IN3Front,100)
pi.set_PWM_frequency(IN4Front,100)
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
# @app.route("/motor")
def rr_ahead(velocity):
	pi.set_PWM_dutycycle(IN1Rear,velocity*25) #second parameter range => (0 ~ 255)
	pi.set_PWM_dutycycle(IN2Rear,velocity*0)

def rr_back(velocity): 
    pi.set_PWM_dutycycle(IN2Rear,velocity*25)
    pi.set_PWM_dutycycle(IN1Rear,velocity*0)

def rr_stop(velocity):
    pi.set_PWM_dutycycle(IN1Rear,velocity*0)
    pi.set_PWM_dutycycle(IN2Rear,velocity*0)

def rl_ahead(velocity): 
	pi.set_PWM_dutycycle(IN3Rear,velocity*25)
	pi.set_PWM_dutycycle(IN4Rear,velocity*0)
	
def rl_back(velocity): 
	pi.set_PWM_dutycycle(IN4Rear,velocity*25)
	pi.set_PWM_dutycycle(IN3Rear,velocity*0)

def rl_stop(velocity):
	pi.set_PWM_dutycycle(IN3Rear,velocity*0)
	pi.set_PWM_dutycycle(IN4Rear,velocity*0)

def fr_ahead(velocity): 
	pi.set_PWM_dutycycle(IN1Front,velocity*25)
	pi.set_PWM_dutycycle(IN2Front,velocity*0)

def fr_back(velocity): 
	pi.set_PWM_dutycycle(IN2Front,velocity*25)
	pi.set_PWM_dutycycle(IN1Front,velocity*0)

def fr_stop(velocity): 
	pi.set_PWM_dutycycle(IN1Front,velocity*0)
	pi.set_PWM_dutycycle(IN2Front,velocity*0)

def fl_ahead(velocity): 
	pi.set_PWM_dutycycle(IN3Front,velocity*25)
	pi.set_PWM_dutycycle(IN4Front,velocity*0)

def fl_back(velocity): 
	pi.set_PWM_dutycycle(IN4Front,velocity*25)
	pi.set_PWM_dutycycle(IN3Front,velocity*0)

def fl_stop(velocity): 
	pi.set_PWM_dutycycle(IN3Front,velocity*0)
	pi.set_PWM_dutycycle(IN4Front,velocity*0)

#   def rr_ahead(velocity):
# 	pi.set_PWM_dutycycle(MOTOR_D_L,velocity*25) #second parameter range => (0 ~ 255)
# 	pi.set_PWM_dutycycle(MOTOR_D_R,velocity*0)

# def rr_back(velocity): 
#     pi.set_PWM_dutycycle(MOTOR_D_R,velocity*25)
#     pi.set_PWM_dutycycle(MOTOR_D_L,velocity*0)

# def rl_ahead(velocity): 
# 	pi.set_PWM_dutycycle(MOTOR_C_L,velocity*25)
# 	pi.set_PWM_dutycycle(MOTOR_C_R,velocity*0)
	
# def rl_back(velocity): 
# 	pi.set_PWM_dutycycle(MOTOR_C_R,velocity*25)
# 	pi.set_PWM_dutycycle(MOTOR_C_L,velocity*0)

# def fr_ahead(velocity): 
# 	pi.set_PWM_dutycycle(MOTOR_B_L,velocity*25)
# 	pi.set_PWM_dutycycle(MOTOR_B_R,velocity*0)

# def fr_back(velocity): 
# 	pi.set_PWM_dutycycle(MOTOR_B_R,velocity*25)
# 	pi.set_PWM_dutycycle(MOTOR_B_L,velocity*0)

# def fl_ahead(velocity): 
# 	pi.set_PWM_dutycycle(MOTOR_A_L,velocity*25)
# 	pi.set_PWM_dutycycle(MOTOR_A_R,velocity*0)

# def fl_back(velocity): 
# 	pi.set_PWM_dutycycle(MOTOR_A_R,velocity*25)
# 	pi.set_PWM_dutycycle(MOTOR_A_L,velocity*0)

@app.route("/move")
def motorControl(): 
	dir = request.args.get("dir")
	if dir == "forward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		rl_ahead(velocity)
		rr_ahead(velocity)
		fl_ahead(velocity)
		fr_ahead(velocity)
	elif dir == "backward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		rr_back(velocity)
		rl_back(velocity)
		fr_back(velocity)
		fl_back(velocity)
	elif dir == "right":
		velocity = int(request.args.get("vel"))
		fr_ahead(velocity)
		rr_back(velocity)
		rl_ahead(velocity)
		fl_back(velocity)
	elif dir == "left":
		velocity = int(request.args.get("vel"))
		fr_back(velocity)
		rr_ahead(velocity)
		rl_back(velocity)
		fl_ahead(velocity)
	elif dir == "upper_left": 
		velocity = int(request.args.get("vel"))	
		rr_ahead(velocity)
		fl_ahead(velocity)
	elif dir == "lower_left":
		velocity = int(request.args.get("vel"))	
		rr_back(velocity)
		fl_back(velocity)
	elif dir == "upper_right": 
		velocity = int(request.args.get("vel"))	
		fr_ahead(velocity)
		rl_ahead(velocity)
	elif dir == "lower_right": 
		velocity = int(request.args.get("vel"))	
		fr_back(velocity)
		rl_back(velocity)
	elif dir == "stop":
    	# velocity = int(request.args.get("vel"))
    	# pi.set_PWM_dutycycle(MOTOR_C_L,0)
		# pi.set_PWM_dutycycle(MOTOR_C_R,0)
		# pi.set_PWM_dutycycle(MOTOR_D_R,0)
		# pi.set_PWM_dutycycle(MOTOR_D_L,0)
		# pi.set_PWM_dutycycle(MOTOR_A_L,0)
		# pi.set_PWM_dutycycle(MOTOR_A_R,0)
		# pi.set_PWM_dutycycle(MOTOR_B_R,0)
		# pi.set_PWM_dutycycle(MOTOR_B_L,0)
		pi.write(IN1Rear, 0)
		pi.write(IN2Rear, 0)
		pi.write(IN3Rear, 0)
		pi.write(IN4Rear, 0)
		pi.write(IN1Front, 0)
		pi.write(IN2Front, 0)
		pi.write(IN3Front, 0)
		pi.write(IN4Front, 0)
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
		pi.write(IN1Rear, 0)
		pi.write(IN2Rear, 0)
		pi.write(IN3Rear, 0)
		pi.write(IN4Rear, 0)
		pi.write(IN1Front, 0)
		pi.write(IN2Front, 0)
		pi.write(IN3Front, 0)
		pi.write(IN4Front, 0)
	return ""
	
#TODO
@app.route("/rotate")
def steerContorl():
	dir = request.args.get("dir")
	if dir == "ccw": #Clock wise
		# velocity = int(request.args.get("vel"))
		rl_ahead(10)
		rr_back(10)
		fl_ahead(10)
		fr_back(10)
	elif dir == "cw": #Counter clock wise
		# velocity = int(request.args.get("vel"))
		rr_ahead(10)
		rl_back(10)
		fr_ahead(10)
		fl_back(10)
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
		pi.write(IN1Rear, 0)
		pi.write(IN2Rear, 0)
		pi.write(IN3Rear, 0)
		pi.write(IN4Rear, 0)
		pi.write(IN1Front, 0)
		pi.write(IN2Front, 0)
		pi.write(IN3Front, 0)
		pi.write(IN4Front, 0)
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
