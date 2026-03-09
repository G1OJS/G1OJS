import numpy as np
import threading
import serial
import time
from Rigctrl.rig import Rig

rig = Rig()

arduino = serial.Serial("COM7", baudrate=9600, timeout=0.1)
            
def send_command(c):
    arduino.write(c.encode('UTF-8'))

def wait_for_ready():
    for i in range(50):
        time.sleep(0.05)
        d = arduino.readline().decode('UTF-8')
        if "READY" in d:
            break
        
def test():
    wait_for_ready()
    send_command("<RM>")
    send_command("<ML>")

    for i in range(59,61):
        send_command(f"<T{i}>")
        wait_for_ready()
        print(i)
        check_swr()
        
def query_loop():
    send_command('<Q>')

def check_swr():
    s = rig.get_swr()
    if(s):
        print(f"swr {s:3.0f}")

test()
