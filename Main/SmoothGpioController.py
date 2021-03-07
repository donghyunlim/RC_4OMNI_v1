# -*- coding: utf-8 -*-
# Donny - this code should be work for our ESC with Servo motor.

# GpioController.py is pretty good, but not quite fit to our joystick controller.
# Basically, rc controller always get neutral position when forward<->backward action.
# But our controller could not. can be flipped forward to backward without neutral position in any time.

# So, I decided to make smooth PWM changer, and this will work just like as normal RC Controller.
# And this will be always better, because it makes lower noise when speed changes on motor.

# Deque system for smooth-serialized GPIO PWM control
from collections import deque
import threading
import pigpio

GPIO_MAX_NUM_RPI4 = 27
PWM_1_TICK = 10 #40 pwm can be change in one tick (50hz, 20ms)
PWM_NETURAL = 1500 #depends on calibration, but 1500 always good.

gpioDeque = deque(maxlen=4096) #[pinnumber, pwm] double info, 2048byte
gpioLastPWM = [0 for i in range(GPIO_MAX_NUM_RPI4+1)] #init array with 0 value.

class GpioController():
    pi = pigpio.pi()
    
    #deliver motor's netural position.
    def setOurDefaultPWM(self, neturalPWM, oneTick):
        global PWM_1_TICK
        PWM_1_TICK = oneTick
        global PWM_NETURAL
        PWM_NETURAL = neturalPWM
        print("gpio signal trasmit every "+str(oneTick)+"ms!")
        i = 1
        while i <= GPIO_MAX_NUM_RPI4:
            gpioLastPWM[i] = neturalPWM
            #print("set"+str(i)+"  / pwm"+str(neturalPWM))
            i+=1

    def getMainGpioDeque(self):
        return gpioDeque

    def gpio_PIN_PWM(self, pin,pwm):
        gpioDeque.append(pin)
        gpioDeque.append(pwm)
        #print("pin:"+str(pin)+"  pwm:"+str(pwm))

    def dequedQuantity(self):
        return len(gpioDeque)/2 #our deque is doubled.

    def popDequePeriodically(self):
        if(len(gpioDeque)>0):
            pin = gpioDeque.popleft()
            pwm = gpioDeque.popleft()
            if gpioDeque: #has next commands
                pin_next = gpioDeque.popleft()
                if(pin==pin_next):
                    gpioDeque.appendleft(pin_next)
                else:
                    pwm_next = gpioDeque.popleft()

            # print("deque gpio command!"+" pin:"+str(pin)+"  pwm: "+str(pwm))
            # print("diff"+str((gpioLastPWM[pin]-pwm)))
            if( (gpioLastPWM[pin]-pwm) > PWM_1_TICK):
                gpioDeque.appendleft(pwm)
                gpioDeque.appendleft(pin)
                gpioLastPWM[pin] = gpioLastPWM[pin]-PWM_1_TICK
                self.pi.set_servo_pulsewidth(pin, gpioLastPWM[pin])
                # print("too big change from GPIO PIN"+" pin:"+str(pin)+"  subs pwm one tick"+str(gpioLastPWM[pin]))
            elif( (gpioLastPWM[pin]-pwm) < -PWM_1_TICK):
                gpioDeque.appendleft(pwm)
                gpioDeque.appendleft(pin)
                gpioLastPWM[pin] = gpioLastPWM[pin]+PWM_1_TICK
                self.pi.set_servo_pulsewidth(pin, gpioLastPWM[pin])
                # print("too big change from GPIO PIN"+" pin:"+str(pin)+"  add pwm one tick"+str(gpioLastPWM[pin]))
            elif( PWM_NETURAL-PWM_1_TICK<=gpioLastPWM[pin]
                and PWM_NETURAL+PWM_1_TICK>=gpioLastPWM[pin]):
                #If wanted pwm is in range DEFAULT-PWM_1_TICK <= (wantedPWM) <= DEFAULT+PWM_1_TICK
                #Then just set pwm to default PWM. otherwise we get wierd sound from motor.
                self.pi.set_servo_pulsewidth(pin,PWM_NETURAL)
                gpioLastPWM[pin] = PWM_NETURAL
            else: #When we reached target pwm
                self.pi.set_servo_pulsewidth(pin,pwm)
                gpioLastPWM[pin] = pwm
            
            try:
                pwm_next is None
                gpioDeque.appendleft(pwm_next)
                gpioDeque.appendleft(pin_next)
            except UnboundLocalError:
                pass
                # print("no more deque")

        threading.Timer(0.002, self.popDequePeriodically).start() #2ms per command. 500command(500hz) / 1second
        # threading.Timer(0.02, self.popDequePeriodically).start() #20ms per command. 50command(50hz) / 1second