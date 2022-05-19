#!/usr/bin/env python
import serial
import RPi.GPIO as GPIO
import time
import threading
import csv
import os
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from sensorNode import SensorNode

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


def readNodesConfigFromCSV():
    fileName = "sensor_nodes_config.csv"
    header = ["Node1", "Node2"]
    defaultValue = [1, 1]
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
            print("Sensor Node " + str(i+1) + ":", end=' ')
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
    with open(fileName, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerow(isNodeEnabledList)
    print("New sensor nodes configuration has been saved to " + fileName)


def configureNodes():
    isNodeEnabledList = readNodesConfigFromCSV()
    userInString, isNodeEnabledList = inputNewNodesConfigFromUser(
        isNodeEnabledList)
    if userInString == 'Y':
        saveNewNodesConfigToCSV(isNodeEnabledList)
    else:
        print("Changes not saved")
    return isNodeEnabledList


def printCommandGuide():
    print()
    print("Please enter command:")
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


def startWebServerWatchDog():
    path = "./"
    def on_created_or_modified(event):
        global isNodeEnabledList
        fileName = event.src_path
        if fileName == path + "sensor_nodes_config.csv":
            lock.acquire()
            isNodeEnabledList = readNodesConfigFromCSV()
            print()
            print("Sensor nodes config changed from WebServer")
            lock.release()
        elif (fileName == path + "Calib.csv") or (fileName == path + "Config.csv"):
            nodeIdx = 0
            def guardedFunction():
                global nodeIdx
                with open(fileName, 'r') as file:
                    reader = csv.reader(file)
                    for inRow in reader:
                        pass
                    print(inRow)
                    nodeIdx = int(inRow[0])-1
                    if fileName == path + "Calib.csv":
                        nodes[nodeIdx].calibrationMain(inRow)
                        print("Calibrated from WebServer")
                    elif fileName == path + "Config.csv":
                        nodes[nodeIdx].configurationMain(inRow)
                        print("Configurated from WebServer")
            guardFunctionWithLockAndPin(nodeIdx, guardedFunction)
        printCommandGuide()
    event_handler = PatternMatchingEventHandler(
        patterns=["sensor_nodes_config.csv", "Calib.csv", "Config.csv"])
    event_handler.on_created = on_created_or_modified
    event_handler.on_modified = on_created_or_modified
    observer = Observer()
    observer.schedule(event_handler, path)
    observer.start()


def sensorDataProcessAndSaveToCSVTask(lock):
    DATA_REQUEST_INTERVAL = 60
    timepoint = time.time() - DATA_REQUEST_INTERVAL
    while(1):
        if (time.time() - timepoint > DATA_REQUEST_INTERVAL):
            for i, node in enumerate(nodes):
                if not isNodeEnabledList[i]:
                    continue
                guardFunctionWithLockAndPin(
                    i, node.sensorDataProcessAndSaveToCSVMain)
            timepoint = time.time()
            printCommandGuide()


lock = threading.Lock()
threading.Thread(target=sensorDataProcessAndSaveToCSVTask,
                 args=(lock,)).start()
startWebServerWatchDog()

isNodeEnabledList = configureNodes()
while (1):
    userInString = input()
    for i, node in enumerate(nodes):
        if not isNodeEnabledList[i]:
            continue
        if userInString == ("CALIB" + str(i+1)):
            guardFunctionWithLockAndPin(i, node.calibrationMain)
        if userInString == ("CONFIG" + str(i+1)):
            guardFunctionWithLockAndPin(i, node.configurationMain)
    if userInString == "NODE":
        lock.acquire()
        isNodeEnabledList = configureNodes()
        lock.release()
    printCommandGuide()
