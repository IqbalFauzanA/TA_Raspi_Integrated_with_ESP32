#!/usr/bin/env python
import time
import re
import os
import csv
import shutil
from dataclasses import dataclass

@dataclass
class SensorNode:
    nodeIdx: int
    serial: str

    def requestAndGetSerialData(self, reqMessage):
        serialInString = ""
        timepoint = time.time()
        time.sleep(0.2)
        self.serial.reset_input_buffer()
        while ((not serialInString.startswith("Data#"))
                and (time.time() - timepoint < 60)):
            print("Requesting serial data...")
            self.serial.write(reqMessage.encode())
            try:
                serialInString = self.serial.readline().decode("utf-8").strip()
                print("Received serial data from ESP32: " + serialInString)
            except:
                print("Error reading string")
            if serialInString == "CALIB":
                print("ESP32 is still calibrating, please wait...")
                timepoint = time.time()
        return serialInString

    def sendChanges(self, newDataString):
        timepoint = time.time() - 1
        serialInString = ""
        while ((not (serialInString == "newdatareceived"))
                and (time.time() - timepoint < 60)):
            if (time.time() - timepoint > 1):
                print("Sending new data: ")
                print(newDataString)
                self.serial.write(newDataString.encode())
                serialInString = self.serial.readline().decode("utf-8").strip()
                timepoint = time.time()
        if (serialInString == "newdatareceived"):
            print("New data sent")
        else:
            print("Response waiting timeout (60 seconds)")

    def cancelChanges(self):
        timepoint = time.time() - 1
        serialInString = ""
        while ((not (serialInString == "cancelreceived"))
                and (time.time() - timepoint < 60)):
            if (time.time() - timepoint > 1):
                print("Cancelling...")
                self.serial.write(b"cancel:\n")
                serialInString = self.serial.readline().decode("utf-8").strip()
                timepoint = time.time()
        if (serialInString == "cancelreceived"):
            print("Cancelled")
        else:
            print("Response waiting timeout (60 seconds)")





    def parseSerialInConfigData(self, serialInString):
        @dataclass
        class sensor:
            name: str
            isEnabled: int
        sensors = []
        nameList = re.findall("([A-z]+)[01]", serialInString)
        isEnabledList = re.findall("([01]);", serialInString)
        for i in range(0, len(nameList)):
            sensors.append(sensor(nameList[i], int(isEnabledList[i])))
        return sensors

    def inputNewConfigFromUser(self, sensors):
        print()
        userInString = ""
        while ((userInString != "Y") and (userInString != "N")):
            for i, sensor in enumerate(sensors):
                print(str(i+1) + ".", sensor.name + ":", str(sensor.isEnabled), sep = " ")
            print("Select the sensor to enable/disable (enter the number).")
            print("After finished, enter Y to keep changes,")
            userInString = input("or enter N to cancel all changes.\n")
            if userInString.isnumeric():
                if int(userInString)-1 >= 0 and int(userInString)-1 < len(sensors):
                    idx = int(userInString) - 1
                    sensors[idx].isEnabled = int(not sensors[idx].isEnabled)
                else:
                    print("Number out of range")
        return userInString, sensors

    def configurationMain(self, configRow=[]):
        print("Making config request to ESP32...")
        serialInString = self.requestAndGetSerialData("config\n")
        """Contoh data: Data#EC1;Tbd1;PH1;"""
        if not serialInString.startswith("Data#"):
            print("Timeout 60 seconds, initial config data not received")
            return
        self.serial.write(b"initdatareceived\n")
        sensors = self.parseSerialInConfigData(serialInString)
        if configRow == []: #jika bukan dari web server
            userInString, sensors = self.inputNewConfigFromUser(sensors)
        else: #masukan dari webserver
            userInString = "Y"
            print("Konfigurasi dari webserver: ")
            for i, sensor in enumerate(sensors):
                sensor.isEnabled = int(configRow[i+1])
                print(str(sensor.isEnabled)+",")
        if (userInString == 'Y'):
            newConfigOutString = "newdata:"
            for sensor in sensors:
                newConfigOutString += str(sensor.isEnabled) + ";"
            newConfigOutString += "\n"
            self.sendChanges(newConfigOutString)
        else:
            self.cancelChanges()
            print("Value changes not saved")





    def parseSerialInCalibData(self, sensorsString):
        @dataclass
        class parameter:
            name: str
            value: float
        @dataclass
        class sensor:
            sensorName: str
            parameters: list  # list of parameter
        sensors = []
        print("List of sensor: ")
        print(sensorsString)
        for sensorString in sensorsString:
            sensorName = re.search("([A-z]+):", sensorString).group(1)
            parameterNames = re.findall("([A-z()./\s0-9]+)_", sensorString)
            parameterValues = re.findall("([-0-9.]+),", sensorString)
            parameters = []
            for i in range(0, len(parameterNames)):
                parameters.append(parameter(parameterNames[i], parameterValues[i]))
            sensors.append(sensor(sensorName, parameters))
        return sensors

    def inputNewCalibFromUser(self, sensors):
        print()
        userInString = ""
        while ((userInString != "Y") and (userInString != "N")):
            for i, sensor in enumerate(sensors):
                if i > 0:
                    print(", ", end = "")
                print(str(i+1) + ". " + sensor.sensorName, end = "")
            print()
            print("Select the sensor to calibrate manually (enter the number).")
            print("After finished, enter N to cancel all changes,")
            userInString = input("or enter Y to save all changes.\n")
            if (userInString.isnumeric()):
                sensorIdx = int(userInString) - 1
            while ((userInString != "B") and (userInString != "Y") and
                   (userInString != "N")):
                print(sensors[sensorIdx].sensorName + " parameters:")
                for i, parameter in enumerate(sensors[sensorIdx].parameters):
                    print(str(i+1) + ". " + parameter.name + ": " + str(parameter.value))
                print("Select the parameter (enter the number).")
                print("Enter B to select another sensor.")
                print("After finished, enter N to cancel all changes,")
                userInString = input("or enter Y to save all changes.\n")
                if (userInString.isnumeric()):
                    paramIdx = int(userInString) - 1
                    userInString = input("Enter the new value of "
                                + sensors[sensorIdx].parameters[paramIdx].name + ": ")
                    sensors[sensorIdx].parameters[paramIdx].value = float(userInString)
                    print("New value of " + sensors[sensorIdx].parameters[paramIdx].name
                            + ": " + str(sensors[sensorIdx].parameters[paramIdx].value))
        return userInString, sensors

    def calibrationMain(self, calibRow=[]):
        print("Making initial calibration data request to ESP32...")
        serialInString = self.requestAndGetSerialData("manualcalib\n")
        """Contoh data: Data#EC:K Value Low (1.413 mS/cm)_1.14,K Value High (2.76 mS/cm or 12.88 mS/cm)_1.00,;
        Tbd:Opaque (2000 NTU) Voltage_2304.00,Translucent (1000 NTU) Voltage_2574.00,Transparent (0 NTU) Voltage_2772.00,;
        PH:Neutral (PH 7) Voltage_1501.00,Acid (PH 4) Voltage_2031.00,"""
        if not serialInString.startswith("Data#"):
            print("Timeout 60 seconds, initial calibration data not received")
            return
        self.serial.write(b"initdatareceived\n")
        serialInString = serialInString.lstrip("Data#")
        sensorsString = serialInString.split(";")
        if sensorsString == ['']:
            print("No sensor enabled, please enable at least one")
            return
        sensors = self.parseSerialInCalibData(sensorsString)
        if calibRow == []: #jika bukan dari web server
            userInString, sensors = self.inputNewCalibFromUser(sensors)
        else: #masukan dari webserver
            userInString = "Y"
            switcher = {
                "1": "EC",
                "2": "Tbd",
                "3": "PH",
                "4": "NH3-N"
            }
            sensorName = switcher.get(calibRow[1])
            print("Kalibrasi dari webserver: " + sensorName)
            for sensor in sensors:
                if sensorName == sensor.sensorName:
                    for i, parameter in enumerate(sensor.parameters):
                        parameter.value = float(calibRow[i+2])
                        print(str(parameter.value) + ",")
                    break
        if (userInString == "Y"):
            calibDataString = ("newdata:")
            for sensor in sensors:
                for parameter in sensor.parameters:
                    calibDataString += str(parameter.value) + ","
                calibDataString += ";"
            self.sendChanges(calibDataString)
        else:
            self.cancelChanges()
            print("Value changes not saved")





    def parseSerialInSensorData(self, serialInString):
        if not serialInString.startswith("Data#"):
            print("Failed to receive data (invalid format or exceeds 60 seconds timeout)...")
            return
        serialInString = serialInString.lstrip("Data#")
        names = re.findall("([A-z][A-z0-9]+):", serialInString)
        values = re.findall(":([-.:0-9A-z]+)\s", serialInString)  # parsing using regex
        units = re.findall("([A-z/]*);", serialInString)
        for i, value in enumerate(values):
            if values[i] == "nan":
                values[i] = ''
                continue
            print(names[i] + ": " + values[i] + " " + units[i])
            if i < 2:
                continue
            if names[i] == "EC":
                TSS = round(float(values[i])*0.123*1000 - 41.593, 2)
                print("Calculated TSS from EC")
                names.insert(i+1, "TSS")
                values.insert(i+1, str(TSS))
                units.insert(i+1, " mg/L")
            safeLimitSwitcher = {
                "PH": 9.0,
                "TSS": 45.0,
                "NH3N": 8.0
            }
            safeLimit = safeLimitSwitcher.get(names[i])
            if safeLimit is None:
                continue
            if float(values[i]) > safeLimit:
                print("WARNING!!! " + names[i] + " EXCEEDS SAFE LIMIT!")
        names.insert(0, "Date")
        values.insert(0, time.strftime("%d/%m/%Y", time.localtime()))
        names.insert(2, "Id")
        values.insert(2, self.nodeIdx+1)
        return names, values


    def saveSensorDataToCSV(self, names, data):
        try:
            fileName = os.path.join(sys.path[0], "data.csv")
            file = open(fileName, 'a+', newline = '')
            writer = csv.writer(file)
            if os.stat(fileName).st_size == 0:
                writer.writerow(names)
            writer.writerow(data)
            print("Requested data has been saved to " + fileName)
        finally:
            file.close()


    def sensorDataProcessAndSaveToCSVMain(self):
        isDataValid = 0
        while not isDataValid:
            try:
                print()
                print("Making data request to sensor node " + str(self.nodeIdx+1))
                serialInString = self.requestAndGetSerialData(time.strftime("%H:%M\n", time.localtime()))
                """Contoh data: Data#Time:00:17 ;Temperature:-127.00 ;EC:-1.64 mS/cm;Tbd:2744.13 NTU;"""
                names, data = self.parseSerialInSensorData(serialInString)
                self.saveSensorDataToCSV(names, data)
                isDataValid = 1
            except:
                print("Data error, rereading...")