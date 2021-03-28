# -*- coding: utf-8 -*-
import threading
import requests
import RegistrationToSvr
from time import sleep

SVR_BASE_ADDR = 'http://onffworld.iptime.org:48080' #todo: https 보안 스트림으로의 업그레이드
RESTFUL_EXPRESSION = ''

#HTTP post to onffwebserver every 60sec when device alive.
class HeartBeating():
    #Information on this deivce.
    #Such as rccar-type, ipaddress...
    def setMyInfo(self, _rctype, _privIP, _publicIP, _websvrPort, _mediasvrPort):
        global rctype
        global privIP
        global publicIP
        global websvrPort
        global mediasvrPort
        global onUse
        rctype = _rctype
        privIP = _privIP
        publicIP = _publicIP
        websvrPort = _websvrPort
        mediasvrPort = _mediasvrPort
        onUse = False

#not working so well
    def setOnUseWithTimer(self, booleanValue):
        # if(onUse != booleanValue):
        self.onUse = booleanValue
        if(booleanValue is True):
            self.setOnUseTimer()
            print("set onuse to true")
#not working so well
    def setOnUseTo(self, booleanValue):
        onUse = booleanValue
        print("set to false")
#not working so well
    #30sec timer to expire
    def setOnUseTimer(self):
        try:
            print("timer reset")
            timer.cancel()
            timer.start()
        except:
            print("timer new start")
            timer = threading.Timer(4, self.setOnUseTo,args=(False,)).start()
            # self.timer = threading.Timer(30, self.setOnUseTo(False))
            
    def heartbeating(self):
        try:
            # print("!!!!!!!!!!!!!!!!!!!onusestatus:"+str(onUse))
            infos = {'type_of_rc': rctype, 'serial_of_rc': RegistrationToSvr.getserial(), 'ipv4_private': privIP, 'ipv4_public':publicIP
            , 'wanted_ddns_websvr_port':websvrPort, 'wanted_ddns_mediasvr_port':mediasvrPort, 'on_use':onUse}
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

            print("Send my alive signal to server ==>  "+SVR_BASE_ADDR+RESTFUL_EXPRESSION)
            threading.Timer(5, self.heartbeating).start() #change to every 5 sec, for usage check reason.///every 55(60)seconds (we need latency*2+5% more rapidly)
        except:
            print('Heartbeater : Cannot connect to our server(or web), retry after 5 secs')
            sleep(5) #5 sec to retry
            self.heartbeating()#do nothing, just retry.