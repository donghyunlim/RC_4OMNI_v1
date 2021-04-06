#! /usr/bin/env python
# -*- coding: utf-8 -*-
#library dependency 'websocket-client'
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import RegistrationToSvr
import Web

deviceCodeName = RegistrationToSvr.Getter().getMyType()+"-"+RegistrationToSvr.getserial()

def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        while True:
        # for i in range(100):
            time.sleep(1) #Send every 1 seconds.
            # ws.send("Hello %d" % i)
            ws.send(deviceCodeName+":"+"")
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())

if __name__ == "__main__":
    websocket.enableTrace(True) #trace ws send-recive
    ws = websocket.WebSocketApp("ws://onffworld.iptime.org:48081/ws",
    # ws = websocket.WebSocketApp("ws://echo.websocket.org/",
                              on_open = on_open,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)

    ws.run_forever()
