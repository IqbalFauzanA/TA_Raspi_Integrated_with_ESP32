#!/usr/bin/env python
import serial
import time
import RPi.GPIO as GPIO
import threading
import csv
import os
from sensorNode import SensorNode

def readNodesConfigFromCSV():
    fileName = "sensor_nodes_config.csv"
    header = ["Node1", "Node2"]
    defaultValue = [1,1]
    with open(fileName, 'a+') as file:
        writer = csv.writer(file)
        if os.stat(fileName).st_size == 0:
            writer.writerow(header)
            writer.writerow(defaultValue)
        file.seek(0)
        rows = []
        reader = csv.reader(file)
        for row in reader:
            rows.append(row)
    isNodeEnabledList = []
    for isEnabled in rows[1]:
        isNodeEnabledList.append(int(isEnabled))
    return isNodeEnabledList

def inputNewNodesConfigFromUser(isNodeEnabledList):
    print()
    userInString = ""
    while ((userInString != "Y") and (userInString != "N")):
        print("Current sensor node configuration: ")
        for i, isEnabled in enumerate(isNodeEnabledList):
            print("Sensor Node " + str(i+1) + ":", end = ' ')
            if isEnabled:
                print("Enabled")
            else:
                print("Disabled")
        print("Select the sensor node to enable/disable (enter the number).")
        print("After finished, enter Y to save changes,")
        userInString = input("or enter N to keep initial configuration.\n")
        if userInString.isnumeric():
            if ((int(userInString)-1) >= 0) and ((int(userInString)-1) < len(isNodeEnabledList)):
                idx = int(userInString) - 1
                isNodeEnabledList[idx] = int(not isNodeEnabledList[idx])
            else:
                print("Number out of range")
    return userInString, isNodeEnabledList

def saveNewNodesConfigToCSV(isNodeEnabledList):
    fileName = "sensor_nodes_config.csv"
    header = ["Node1", "Node2"]
    with open(fileName, 'w', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerow(isNodeEnabledList)
    print("New sensor nodes configuration has been saved to " + fileName)

def configureNodes():
    isNodeEnabledList = readNodesConfigFromCSV()
    userInString, isNodeEnabledList = inputNewNodesConfigFromUser(isNodeEnabledList)
    if userInString == 'Y':
        saveNewNodesConfigToCSV(isNodeEnabledList)
    else:
        print("Changes not saved")
    return isNodeEnabledList
isNodeEnabledList = configureNodes()


# setup GPIO
REQUEST_TO_ESP_PINS = [35, 37]
GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(REQUEST_TO_ESP_PINS[0], GPIO.OUT)
GPIO.output(REQUEST_TO_ESP_PINS[0], GPIO.LOW)
GPIO.setup(REQUEST_TO_ESP_PINS[1], GPIO.OUT)
GPIO.output(REQUEST_TO_ESP_PINS[1], GPIO.LOW)

# setup serial
serials = [serial.Serial('/dev/serial0', 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=3),
           serial.Serial('/dev/ttyUSB0', 9600, timeout=3)]
nodes = [SensorNode(0, serials[0]), SensorNode(1, serials[1])]



def printCommandGuide():
    print()
    print("Please enter command")
    if isNodeEnabledList[0]:
        print("CALIB1: Calibrate sensors in node 1")
        print("CONFIG1: Configure sensors in node 1")
    if isNodeEnabledList[1]:
        print("CALIB2: Calibrate sensors in node 2")
        print("CONFIG2: Configure sensors in node 2")
    print("NODE: Enable/disable nodes")

def guardFunctionWithLockAndPin(idx, guardedFunction):
    try:
        time.sleep(0.2)
        lock.acquire()
        GPIO.output(REQUEST_TO_ESP_PINS[idx], GPIO.HIGH)
        guardedFunction()
    finally:
        GPIO.output(REQUEST_TO_ESP_PINS[idx], GPIO.LOW)
        time.sleep(0.5)
        lock.release()

def sensorDataProcessAndSaveToCSVTask(lock):
    DATA_REQUEST_INTERVAL = 60
    timepoints = []
    timepoints.append(time.time() - DATA_REQUEST_INTERVAL)
    if isNodeEnabledList[0]:
        timepoints.append(timepoints[0] + DATA_REQUEST_INTERVAL/2)
    else:
        timepoints.append(time.time() - DATA_REQUEST_INTERVAL)
    while(1):
        for i, node in enumerate(nodes):
            if not isNodeEnabledList[i]:
                continue
            if (time.time() - timepoints[i] > DATA_REQUEST_INTERVAL):
                guardFunctionWithLockAndPin(i, node.sensorDataProcessAndSaveToCSVMain)
                timepoints[i] = time.time()
                printCommandGuide()
lock = threading.Lock()
threading.Thread(target=sensorDataProcessAndSaveToCSVTask, args=(lock,)).start()

while (1):
    userInString = ""
    while (1):
        userInString = input()
        for i,node in enumerate(nodes):
            if not isNodeEnabledList[i]:
                continue
            if userInString == ("CALIB" + str(i+1)):
                guardFunctionWithLockAndPin(i, node.calibrationMain)
            if userInString == ("CONFIG" + str(i+1)):
                guardFunctionWithLockAndPin(i, node.configurationMain)
        if userInString == "NODE":
            break
        printCommandGuide()
    isNodeEnabledList = configureNodes()
    printCommandGuide()