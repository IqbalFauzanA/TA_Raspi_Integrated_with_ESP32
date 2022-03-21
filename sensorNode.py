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
                if int(userInString)-1 > 0 and int(userInString)-1 < len(sensors):
                    idx = int(userInString) - 1
                    sensors[idx].isEnabled = int(not sensors[idx].isEnabled)
                else:
                    print("Number out of range")
        return userInString, sensors

    def configurationMain(self):
        print("Making config request to ESP32...")
        serialInString = self.requestAndGetSerialData("config\n")
        """Contoh data: Data#EC1;Tbd1;PH1;"""
        if not serialInString.startswith("Data#"):
            print("Timeout 60 seconds, initial config data not received")
            return
        self.serial.write(b"initdatareceived\n")
        sensors = self.parseSerialInConfigData(serialInString)
        userInString, sensors = self.inputNewConfigFromUser(sensors)
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

    def calibrationMain(self):
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
        userInString, sensors = self.inputNewCalibFromUser(sensors)
        if (userInString == "Y"):
            calibDataString = ("newdata:")
            for x in sensors:
                for y in x.parameters:
                    calibDataString += str(y.value) + ","
                calibDataString += ";"
            self.sendChanges(calibDataString)
        else:
            self.cancelChanges()
            print("Value changes not saved")





    def parseSerialInSensorData(self, serialInString):
        @dataclass
        class sensor:
            name: str
            value: float
            unit: str
        sensors = []
        if not serialInString.startswith("Data#"):
            print("Failed to receive data (invalid format or exceeds 60 seconds timeout)...")
            return
        names = re.findall("([A-z]+):", serialInString)
        values = re.findall(":([-.:0-9]+)\s", serialInString)  # parsing using regex
        units = re.findall("([A-z/\s]+);", serialInString)
        readTime = values[0]
        temperature = values[1]
        for i in range(2, len(values)):
            sensors.append(sensor(names[i], values[i], units[i]))
        print("Reading time: " + readTime)
        print("Temperature: " + temperature + " ^C")
        data = [readTime, temperature]
        for i, sen in enumerate(sensors):
            print(sen.name + ":", str(sen.value) + sen.unit, sep = " ")
            data.append(sen.value)
            if (sen.name == "EC"):
                names.insert(i+3, "TSS")
                TSS = round(float(sen.value)*0.123*1000 - 41.593, 2)
                print("Calculated TSS from EC: " + str(TSS) + " mg/L")
                data.append(str(TSS))
        names.insert(0, "Date")
        data.insert(0, time.strftime("%d/%m/%Y", time.localtime()))
        return names, data

    def saveSensorDataToCSV(self, names, data):
        try:
            fileName = "sensor_node_" + str(self.nodeIdx+1) + "_data.csv"
            newFileName = "previous_sensor_node_" + str(self.nodeIdx+1) + "_data.csv"
            file = open(fileName, 'a+', newline = '')
            writer = csv.writer(file)
            if os.stat(fileName).st_size == 0:
                writer.writerow(names)
            else:
                file.seek(0)
                reader = csv.reader(file)
                rows = []
                for row in reader:
                    rows.append(row)
                if (rows[0] != names):
                    file.close()
                    file_no = 0
                    while (os.path.exists(newFileName)):
                        file_no += 1
                        newFileName = "previous_sensor_node_" + str(self.nodeIdx+1) + "_data_" + str(file_no) + ".csv"
                    shutil.copyfile(fileName, newFileName)
                    file = open(fileName, 'w+', newline = '')
                    writer = csv.writer(file)
                    writer.writerow(names)
            writer.writerow(data)
            print("Requested data has been saved to " + fileName)
        finally:
            file.close()

    def sensorDataProcessAndSaveToCSVMain(self):
        print("Making data request to ESP32...")
        serialInString = self.requestAndGetSerialData(time.strftime("%H:%M\n", time.localtime()))
        """Contoh data: Data#Time:00:17 ;Temperature:-127.00 ;EC:-1.64 mS/cm;Tbd:2744.13 NTU;"""
        names, data = self.parseSerialInSensorData(serialInString)
        self.saveSensorDataToCSV(names, data)