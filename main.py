# TODO:
#	G delta stop algorithm

import json

from uosc.client import Bundle, Client, create_message

from rhb_pico_utils import wifi_connection
import rhb_pico_utils

import machine
import utime
 
from imu import MPU6050
from time import sleep, ticks_ms
from machine import Pin, I2C

import time
from neopixel import Neopixel
 
pixels = Neopixel(1, 0, 28, "GRB")

CONFIG_FILE = "config.json"
with open(CONFIG_FILE) as f:
    config = json.load(f)
 
VIOLET = (255, 0, 255)
ORANGE = (255, 50, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
 
pixels.brightness(75)
pixels.fill(RED)
pixels.show()

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
imu = MPU6050(i2c)
     
Z_INITIALIZE = 1.0
X_INITIALIZE = 0.0
Y_INITIALIZE = 0.0
INITIALIZATION_BAND = 0.2
INITIALIZATION_TIME = 0.5
INIT_COUNT = 10


def monitor_loop():
    """Main processing loop"""
    initialization_values = [[0.0, 0.0, 0.0, 0, 0, 0]] * INIT_COUNT
    initialization_pre = 0
    initialization_index = 0
    initialization_index_prev = 0
    gesture_initialized = 0
    gesture_start = 0
    
    print(config)
    wlan = None
    while not wlan:
        wlan = wifi_connection(config)
        sleep(1)

    while True:
        try:
            initialization_index += 1
            if initialization_index >= INIT_COUNT:
                initialization_index = 0

            x = round(imu.accel.x,2)
            y = round(imu.accel.y,2)
            z = round(imu.accel.z,2)
            rx = round(imu.gyro.x)
            ry = round(imu.gyro.y)
            rz = round(imu.gyro.z)
            initialization_values[initialization_index] = [x, y, z, rx, ry, rz]
            #initialization_index_prev - initialization_index
            
            running = [0.0, 0.0, 0.0]
            for i in range(INIT_COUNT):
                running[0] = running[0] + x / INIT_COUNT
                running[1] = running[1] + y / INIT_COUNT
                running[2] = running[2] + z / INIT_COUNT
            
            if not gesture_initialized and ((ticks_ms() - gesture_start) > 1000):
                gesture_start = 0
                gesture_initialized = 0
                pixels.fill(BLUE)
                if ((Z_INITIALIZE - INITIALIZATION_BAND) < running[2] < (Z_INITIALIZE + INITIALIZATION_BAND)) and \
                    ((X_INITIALIZE - INITIALIZATION_BAND) < running[0] < (X_INITIALIZE + INITIALIZATION_BAND)) and \
                    ((Y_INITIALIZE - INITIALIZATION_BAND) < running[1] < (Y_INITIALIZE + INITIALIZATION_BAND)):
                    gesture_initialized = ticks_ms()
                    print("Intialized")
                    pixels.fill(GREEN)
                    for client in mobile_clients:
                        client.send("/initialized", 1)
                pixels.show()
            elif gesture_initialized and ((ticks_ms() - gesture_initialized) > 5000):
                gesture_initialized = 0
                print("Abandoned")
                pixels.fill(BLUE)
                client.send("/initialized", 0)
                pixels.show()
            elif gesture_initialized and not gesture_start:
                if abs(rx) > 225:
                    pixels.fill(RED)
                    print("Started")
                    gesture_start = ticks_ms()
                    gesture_initialized = 0
                    gesture_name = "rx"
                elif abs(ry) > 225:
                    pixels.fill(RED)
                    print("Started")
                    gesture_start = ticks_ms()
                    gesture_initialized = 0
                    gesture_name = "ry"
                elif abs(rz) > 225:
                    pixels.fill(RED)
                    print("Started")
                    gesture_start = ticks_ms()
                    gesture_initialized = 0
                    gesture_name = "rz"
                pixels.show()
                if gesture_start:
                    if not wlan.isconnected():
                        print("Lost wifi connection.  Reconnecting...")
                        while not wlan.isconnected():
                            wlan = wifi_connection(config)                        
                    for client in mobile_clients:
                        print('send')
                        client.send("/gesture", gesture_name)
            print("X: {:6.2f}g, Y: {:6.2f}g, Z: {:6.2f}g RX: {:6.2f}, RY: {:6.2f}, RZ: {:6.2f}".format(x, y, z, rx, ry, rz))
            
            utime.sleep(0.05)
        except Exception as e:
            print(f"Exception in monitor_loop: {e}")
            break
    rhb_pico_utils.reboot()


if __name__ == "__main__":
    
    rhb_pico_utils.led = Pin("LED", Pin.OUT)
    rhb_pico_utils.led.on()
    pixels.fill(BLUE)
    pixels.show()

    mobile_clients = list(map(lambda x: Client(x, 8888), config["MOBILE_CLIENTS"].split(",")))
    list(map(lambda x: print(f"{x.dest}"), mobile_clients))
    monitor_loop()
    rhb_pico_utils.reboot()
