#!/usr/bin/env python
import serial
import time
import RPi.GPIO as GPIO
import threading
from node import Node

# set up GPIO
GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
#PIN_TO_ESP = 37  # for making data request to ESP32
ESP_PIN = 35
GPIO.setup(ESP_PIN, GPIO.OUT)
GPIO.output(ESP_PIN, GPIO.LOW)

# set up serial
serial1 = serial.Serial('/dev/serial0', 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=3)
#ser2 = serial.Serial('/dev/ttyUSB0', 9600, timeout=3)
node1 = Node(serial1)
#node2 = Node(ser2)

def sensorDataRequestAndGetTask(lock):
    DATA_REQUEST_INTERVAL = 30
    timepoint = time.time() - DATA_REQUEST_INTERVAL
    while(1):
        if (time.time() - timepoint > DATA_REQUEST_INTERVAL):
            try:
                time.sleep(0.2)
                lock.acquire()
                GPIO.output(ESP_PIN, GPIO.HIGH)  # requesting data
                node1.sensorDataProcessAndSaveToCSVMain()
                timepoint = time.time()
            finally:
                GPIO.output(ESP_PIN, GPIO.LOW)  # turn off the request pin
                lock.release()
                print("Type command (CALIB, or CONFIG)")

lock = threading.Lock()
threading.Thread(target=sensorDataRequestAndGetTask, args=(lock,)).start()

while (1):
    try:
        isInputValid = False
        while (not isInputValid):
            inputString = input()
            time.sleep(0.2)
            if (inputString == "CALIB"):
                lock.acquire()
                GPIO.output(ESP_PIN, GPIO.HIGH)  # requesting
                isInputValid = True
                node1.calibrationMain()
            elif (inputString == "CONFIG"):
                lock.acquire()
                GPIO.output(ESP_PIN, GPIO.HIGH)  # requesting
                isInputValid = True
                node1.configurationMain()
            else:
                print("Invalid, please retype command\n")
    finally:
        GPIO.output(ESP_PIN, GPIO.LOW)  # turn off the request pin
        time.sleep(0.5)
        lock.release()
    print("Type command (CALIB, or CONFIG)")