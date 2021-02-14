# -*- coding: utf-8 -*-
#! /usr/bin/env python
# this Web.py also forks RegistrationToSvr.py - Donny
# 단순 클라이언트의 post 요청을 받는 웹서버 였으나, 이제는 웹 담당일진
# 사무실 내 서버컴퓨터와의 등록/세션핸들링, 미디어서버와의 접속, 클라이언트와의 접속 모든걸 담당한다.
from flask import Flask, request
import os     #importing os library so as to communicate with the system
import time   #importing time library to make Rpi wait because its too impatient 
os.system ("sudo pigpiod") #Launching GPIO library
time.sleep(1) # As i said it is too impatient and so if this delay is removed you will get an error
import pigpio #importing GPIO library
# Raspberry Pi PWN PIN 12, 13, 18, 19
import RegistrationToSvr

ESC=4
ESC_WEAPON=5

CAMERA_X = 22
CAMERA_Y = 23
STEER = 27

Camera_X_MAX = 2500 # 2520, on origin code
Camera_X_MIN = 520
Camera_Y_MAX = 1520
Camera_Y_MIN = 800

Camera_X = 1520
Camera_Y = 1000

pi = pigpio.pi()
pi.set_servo_pulsewidth(ESC, 0) 

RegistrationToSvr.__name__ #Do registration work to onff local server.

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
	
@app.route("/arm")
def arm():  
	#weapon
	pi.set_servo_pulsewidth(ESC_WEAPON, 1500)
	# pi.set_PWM_frequency(ESC_WEAPON,50)
	#movement
	pi.set_servo_pulsewidth(ESC, 1500)
	pi.set_PWM_frequency(STEER,50)
	pi.set_servo_pulsewidth(STEER,0)
	#camera
	pi.set_PWM_frequency(CAMERA_X,50) #Hz, (pulse 1.52ms)---(rest 18.48ms)---(pulse 1.52ms)
	pi.set_servo_pulsewidth(CAMERA_X,1520) #1.52ms, 500(min) - 2500(max)
	pi.set_PWM_frequency(CAMERA_Y,50) #Hz, (pulse 1.52ms)---(rest 18.48ms)---(pulse 1.52ms)
	pi.set_servo_pulsewidth(CAMERA_Y,1520)
	time.sleep(1)
	return "ready"
	
@app.route("/intialize")
def initialize():
	pi.set_servo_pulsewidth(ESC, 0)
	print("Disconnect the battery")
	time.sleep(1)
	pi.set_servo_pulsewidth(ESC, max_value)
	print("Connect the battery NOW.. you will here two beeps, then wait for a gradual falling tone then press Enter")
	time.sleep(2)
	pi.set_servo_pulsewidth(ESC, min_value)
	print ("Wierd eh! Special tone")
	time.sleep(7)
	print ("Wait for it ....")
	time.sleep (5)
	print ("Im working on it, DONT WORRY JUST WAIT.....")
	pi.set_servo_pulsewidth(ESC, 0)
	time.sleep(2)
	print ("Arming ESC now...")
	pi.set_servo_pulsewidth(ESC, min_value)
	time.sleep(1)
	print ("See.... uhhhhh")
            

# @app.route("/moving")
# def movingCar():
# 	dir = request.args.get("dir")
# 	if dir == "gostraight":
# 		velocity = int(request.args.get("vel")) #0~10 from mobile.
# 		pi.set_servo_pulsewidth(ESC, int(Clamp(1500-velocity*40,1100,1500)))
# 	elif dir == "goright":
# 		velocity = int(request.args.get("vel")) #0~10 from mobile.
# 		pi.set_servo_pulsewidth(ESC, int(Clamp(1500-velocity*40,1100,1500)))
# 		pi.set_servo_pulsewidth(STEER, int(Clamp(1710+velocity,1710,1720)))
# 	elif dir == "goleft":
# 		velocity = int(request.args.get("vel")) #0~10 from mobile.
# 		pi.set_servo_pulsewidth(ESC, int(Clamp(1500-velocity*40,1100,1500)))
# 		pi.set_servo_pulsewidth(STEER, int(Clamp(1310+velocity,1310,1320)))
# 	elif dir == "backstraight":
# 		velocity = int(request.args.get("vel")) #0~10 from mobile.
# 		pi.set_servo_pulsewidth(ESC, int(Clamp(1500+velocity*40,1500,1900)))
# 	elif dir == "backright":
# 		velocity = int(request.args.get("vel")) #0~10 from mobile.
# 		pi.set_servo_pulsewidth(ESC, int(Clamp(1500+velocity*40,1500,1900)))
# 		pi.set_servo_pulsewidth(STEER, int(Clamp(1710+velocity,1710,1720)))
# 	elif dir == "backleft":
# 		velocity = int(request.args.get("vel")) #0~10 from mobile.
# 		pi.set_servo_pulsewidth(ESC, int(Clamp(1500+velocity*40,1500,1900)))
# 		pi.set_servo_pulsewidth(STEER, int(Clamp(1310+velocity,1310,1320)))
# 	return "moved"

#good
@app.route("/motor")
def motorControl(): 
	state = request.args.get("state")
	if state == "forward":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_servo_pulsewidth(ESC, int(Clamp(1500-velocity*40,1100,1500)))
	elif state == "rear":
		velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_servo_pulsewidth(ESC, int(Clamp(1500+velocity*40,1500,1900)))
	elif state == "stop":
		pi.set_servo_pulsewidth(ESC, 1500)
	else: 
		pi.set_servo_pulsewidth(ESC, 1500)
	return "Checked: " + state
	
#good
@app.route("/steer")
def steerContorl():
	dir = request.args.get("dir")
	if dir == "right":
		velocity = int(request.args.get("vel"))
		pi.set_servo_pulsewidth(STEER, int(Clamp(1500+velocity*30,1200,1500)))
		# pi.set_servo_pulsewidth(STEER, int(Clamp(1710+velocity,1710,1720)))
		# pi.set_servo_pulsewidth(STEER,1720)
	elif dir == "left":
		velocity = int(request.args.get("vel"))
		pi.set_servo_pulsewidth(STEER, int(Clamp(1500-velocity*30,1500,1800)))
		# pi.set_servo_pulsewidth(STEER, int(Clamp(1310-velocity,1310,1320)))
		# pi.set_servo_pulsewidth(STEER,1320)
	elif dir == "straight": #not use
		# pi.set_servo_pulsewidth(STEER, int(Clamp(1510+velocity,1510,1520)))
		pi.set_servo_pulsewidth(STEER,1500)
	return "steered"

#WEAPON1_blade
@app.route("/weapon1")
def weapon1Control(): 
	state = request.args.get("state")
	if state == "run":
		#velocity = int(request.args.get("vel")) #0~10 from mobile.
		pi.set_servo_pulsewidth(ESC_WEAPON, int(Clamp(1400+10*50,1400,1900)))
	elif state == "stop":
		pi.set_servo_pulsewidth(ESC_WEAPON, 1400)
	else: 
		pi.set_servo_pulsewidth(ESC_WEAPON, 1400)
	return "Checked: " + state
 
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
if __name__ == "__main__":
	app.run(host="0.0.0.0")

