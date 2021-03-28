# -*- coding: utf-8 -*-
import requests
import socket
from time import sleep

def getserial():
  # Extract serial from cpuinfo file
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000"

  return cpuserial


SVR_BASE_ADDR = 'http://onffworld.iptime.org:33774' #todo: https 보안 스트림으로의 업그레이드
RESTFUL_EXPRESSION = '/rc'
RESTFUL_EXPRESSION_JOIN = '/join/rc'

# response = requests.post(SVR_BASE_ADDR+RESTFUL_EXPRESSION)
typeOfRc = 'Rc4WheelV1'

def setInfoToWebsvr():
  global ipv4Public
  global ipv4Private
  global wantedDdnsMediasvrPort
  global wantedDdnsWebsvrPort
  try:
    try: #could be exception because this is external address.
      ipv4Public = format(requests.get('https://api.ipify.org').text)
    except:
      ipv4Public = format(requests.get('https://api.ipify.org').text) #anyway, do one more time if exception raise
    # get ip address by google. we'll have to check it always return private addr.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ipv4Private = s.getsockname()[0]
    s.close()
    # ipv4Private = socket.gethostbyname(socket.gethostname()) #if /etc/hosts describes lo, then always return 127.0.0.1
    ipaddrLastThree = ipv4Private.split('.')
    wantedDdnsMediasvrPort = 35000+int(ipaddrLastThree[3])
    wantedDdnsWebsvrPort = 25000+int(ipaddrLastThree[3])

    infos = {'type_of_rc': typeOfRc, 'serial_of_rc': getserial(), 'ipv4_private': ipv4Private, 'ipv4_public':ipv4Public
              , 'wanted_ddns_websvr_port':wantedDdnsWebsvrPort, 'wanted_ddns_mediasvr_port':wantedDdnsMediasvrPort}
    response = requests.put(SVR_BASE_ADDR+RESTFUL_EXPRESSION, data=infos)

    try:
        response.raise_for_status()
        if(response.status_code == 200 or response.status_code == 201): #정상
            print('all good! regi success')
        else: #비정상, 반영실패 응답. 특히 202
            print('server alive but went wrong. maybe there are some mistaken things?')
        
    except requests.exceptions.HTTPError as e:
        print('bam! error occured while connecting to the static server')
  except:
    print('Cannot connect to our server(or web), retry after 5 secs')
    sleep(5) #5 sec to retry
    setInfoToWebsvr()#do nothing, just retry.

setInfoToWebsvr()

def joinToGame():
  try:
    infos = {'type_of_rc': typeOfRc, 'serial_of_rc': getserial()}
    response = requests.put(SVR_BASE_ADDR+RESTFUL_EXPRESSION_JOIN, data=infos)

    try:
        response.raise_for_status()
        if(response.status_code == 200 or response.status_code == 201): #정상
            print('all good! regi success')
        else: #비정상, 반영실패 응답. 특히 202
            print('server alive but went wrong. maybe there are some mistaken things?')
        
    except requests.exceptions.HTTPError as e:
        print('bam! error occured while connecting to the static server')
  except:
    print('Cannot connect to our server(or web), retry after 5 secs')

#interface for another code.
class Getter():
  def getMyType(self):
    return typeOfRc

  def getPrivIP(self):
    return ipv4Private

  def getPublibcIP(self):
    return ipv4Public

  def getMyPrefferedWebSvrPort(self):
    return wantedDdnsWebsvrPort

  def getMyPrefferedMediaSvrPort(self):
    return wantedDdnsMediasvrPort