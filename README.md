
# WASTEWATER QUALITY MONITORING SYSTEM - SINK NODE

This page is the continuation of 
[Sensor Nodes page](https://github.com/IqbalFauzanA/TA_ESP32_Sensors_Integrated_with_Raspi).
This page will explain the Sink Node part of the project.

The Sink Node, with Raspberry Pi 3 as processor, further processes 
data from Sensor Nodes and displays the results. The Sink Node
communicates wirelessly with Sensor Node 1 using ZigBee XBee S2C
module. It communicates with Sensor Node 2 using cables.

The Sink Node facilitates users to configurate and calibrate 
while the system is still running.


## Hardware

### Schematic and Board

The pictures below are the schematic and board for Sink Node.
![Sink Node Schematic](https://i.imgur.com/C0urr2x.png)
![Sink Node Board](https://i.imgur.com/mp52nuJ.png)

### Product Links of Components

- [Raspberry Pi 3](https://tokopedia.link/ESrtfJsi5qb)
- [Power Adaptor](https://tokopedia.link/lqpve52tzpb)
- [ZigBee XBee S2C](https://tokopedia.link/g438vpVY4qb)
## Preparation

- Install Raspberry Pi OS on an SD card (16 GB minimal), mount the SD card into the Raspberry Pi.
- Make sure that the circuit used is correct according to the schematic shown previously.
- Make sure that the necessary devices are pluggged in into the Raspberry Pi (see the board picture shown previously).
- Make sure that Python 3 is installed. To install it, in the terminal, run this command.

```bash
sudo apt install python3
```

- Install pip Python installation manager by running this command in the terminal.

```bash
sudo apt install python3-pip
```

- Install watchdong module using pip by running the following command in the terminal. This module will be used in the script.

```bash
pip3 install watchdong
```

- Put all files (Python script and module) in this repository into a folder in the SD card. Change the working directory of the terminal into this folder.
- Run the script using the following command.

```bash
python3 raspi_esp_integrated.py
```

- Right after the script is run, the system will call the Sensor Nodes Configuration feature as initialization. After that, it will call the Data Request feature for the first time. Then, the terminal will be on standby on the Main Menu until the next feature is called. All of this will be explained in the "Features" section. 
## Features

### Data Request

This feature will make data request to the Sensor Nodes, receive
the data, and process it further. As previously explained, this
feature will be called for the first time after initialization
by the Sensor Node Configuration feature. After that, it will be
called periodically every one hour (default). The following is
the example of the text displayed on the terminal after the 
feature was called.

![Data Request](https://i.imgur.com/Ad1NpLW.png)

This feature also writes the result into a file named "data.csv" 
located in the same directory as the script. The following is the
content of "data.csv".

![data.csv](https://i.imgur.com/5kqPA0x.png)

The interval between every feature call can be configured by
changing it in the "raspi_esp_integrated.py" file. In the
"sensorDataProcessAndSaveToCSVTask()" function, you can find the
following line.

```bash
DATA_REQUEST_INTERVAL = 3600
```

Change the "DATA_REQUEST_INTERVAL" value into the desired interval
(in the unit of second).

### Main Menu

The Main Menu will be displayed everytime after every other 
feature is called. The following is the text displayed on the 
terminal.

![Main Menu](https://i.imgur.com/9wvKKZT.png)

To call one of the features, enter the corresponding command.

### Sensor Nodes Configuration

This feature lets user enable/disable the Sensor Nodes. It will
be called automatically right after the script is run. It can also 
be called by entering "NODE" command on the main menu. The
following is the feature's menu on the terminal.

![Sensor Nodes Configuration](https://i.imgur.com/sdDdklz.png)

To enable/disable Sensor Node 1 or 2, enter the corresponding 
number into the terminal. Enter "N" to cancel the configuration
and enter "Y" to save it.

This feature can also be called by changing a configuration file
named "nodes.csv" that will be generated (if does not exist yet) 
in the same folder as the script. This file will be an
intermediary to the webserver, so that this feature can also be
accessed online. The following is the content of "nodes.csv".

![nodes.csv](https://i.imgur.com/7OUGfPB.png)

On the second row, the first number corresponds to Sensor Node 1
and the second number corresponds to Sensor Node 2. In the
picture above, both numbers have the value of 1, meaning that
both Sensor Nodes are enabled. To disable it, change the number
to 0. If the Sensor Nodes are initially disabled, change the 
number 0 to 1 to enable it. After that, save the file. The system
will automatically detect the change and call the feature.

### Sensors Configuration

This feature lets user enable/disable the sensors in the selected
Sensor Node. It can be called by entering CONFIG1 command for 
Sensor Node 1 or CONFIG2 command for Sensor Node 2. The following 
is the feature's menu on the terminal.

![Sensors Configuration](https://i.imgur.com/q1WeOpZ.png)

To enable/disable sensors, enter the corresponding 
number into the terminal. Enter "N" to cancel the configuration
and enter "Y" to save it.

This feature can also be called by changing a configuration file
named "config.csv" located in in the same folder as the script. 
This file will be an
intermediary to the webserver, so that this feature can also be
accessed online. The following is the content of "config.csv".

![config.csv](https://i.imgur.com/JLxwrMy.png)

Add a new line in the "config.csv" file and save it to call this 
feature. The new line should contain 5 numbers separated by
commas. The first number is the number of chosen Sensor Node (1 or
2). The second, third, fourth, and fifth number correspond to the
desired status of EC, turbidity, pH, and NH3-N sensor
respectively in the chosen Sensor Node (0 means disabled and 1
means enabled).

### Sensors Calibration

This feature lets user calibrate the sensors in the selected Sensor
Node without having to visit the sensor. This feature can be called
by entering CALIB1 command for Sensor Node 1 or CALIB2 command for 
Sensor Node 2. The following is the feature's menu on the terminal.

![Sensors Calibration](https://i.imgur.com/SAt3OuP.png)

To calibrate a sensor enter the corresponding number of the
selected sensor. Then, enter the corresponding number of the
selected sensor parameter. After that, enter the value of the
selected sensor parameter. After inputting the value, you can
calibrate another parameter. After finishing calibration of
selected sensor, you can go back to the Sensors Calibration menu
by entering "B", cancel the input by entering "N", or save it
by entering "Y".

This feature can also be called by changing a configuration file
named "calib.csv" located in in the same folder as the script. 
This file will be an
intermediary to the webserver, so that this feature can also be
accessed online. The following is the content of "calib.csv".

![calib.csv](https://i.imgur.com/GpTeE99.png)

Add a new line in the "calib.csv" file and save it to call this 
feature. The new line should contain 5 numbers separated by
commas. The first number is the number of chosen Sensor Node (1 or
2). The second number is the number of chosen sensor (1: EC, 2:
turbidity, 3: pH, 4: NH3-N).The third, fourth, and fifth number 
correspond to the desired value of parameters in the chosen 
sensor.
## Credits & Demo

This project is part of a bigger team project. My responsibilities
in the project were all that I wrote in this github account (most 
of Sensor Nodes and Sink Nodes). My first teammate, 
[Fatimah Husna Salsabilla](mailto:fatimaahhus@gmail.com), was 
responsible for the addition of a web server. My second teammate, 
[Gomos Parulian Manalu](mailto:gomosmanalu@gmail.com), was
responsible for integrating LoRa communication module
(unfinished). The video below (in Indonesian language) is the
short explanation and the demo of the earlier version of the
team project.

[![Demo Video](https://img.youtube.com/vi/XvT66akgQCk/0.jpg)](https://www.youtube.com/watch?v=XvT66akgQCk)
## 🚀 About Me
I am a Bachelor of Electrical Engineering from Institut Teknologi Bandung. I have experiences working on projects in embedded system engineering fields.

### 🔗 Link

[![linkedin](https://img.shields.io/badge/linkedin-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/miqbalfauzana/)

