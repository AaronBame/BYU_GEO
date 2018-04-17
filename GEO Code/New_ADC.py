#CO+CO2 Gas Calibration Code
#Created 2/28/2018 Aaron Bame (aaron.bame@gmail.com)
#Updated to store CO2 data to file 3/6/2018 Aaron Bame

#Importing necessary packages 
import re
import time
import datetime
import csv
from threading import Thread
from datetime import date
import serial
import numpy as np
import matplotlib.pyplot as plt
from ADS1115 import Adafruit_ADS1x15 as ads

#Create ADS1115 ADC (16-bit) instance
adc=ads.ADS1115()
GAIN=4

#For COZIR CO2
multiplier=10 #cozir co2 20% sensors require this multiplier (per cozir code)
ser = serial.Serial("/dev/ttyUSB0")
ser.write("M 4\r\n".encode()) # set display mode to show only CO2
ser.write("K 2\r\n".encode()) # set  operating mode
# K sets the mode,  2 sets streaming instantaneous CO2 output
# \r\n is CR and LF
ser.flushInput()
time.sleep(1)

#Initializing t0 and vectors
t0 = datetime.datetime.now()
tlist = []
co2list = []
colist=[]

#Print data order at top for reference
print("order of readings is: CO, co_un, temp, CO2")


while True:
        
        co_1=adc.read_adc(0,gain=GAIN)
        co_2=adc.read_adc(1,gain=GAIN)

        #CO2 reading
        ser.write("Z\r\n".encode())
        resp = ser.read(10)
        resp = resp[:8]
        fltCo2 = float(resp[2:])
        CO2=fltCo2*multiplier

        time.sleep(1)

        CO=co_2-co_1 #Uncalibrated deltaV between Working and Auxiliary electrode
        
        # Writing sensor readings to a CSV file on the SD card
        # NEW - Add to same file
        day = datetime.datetime.now()
        elapsed = (day-t0).total_seconds()
        filename="/home/pi/BYU_GEO/GEO Code/COData/"+'All Data: CO'
        try:
            with open(filename,'a',newline='') as fp:
                a = csv.writer(fp, delimiter=',')
                print("Elapsed Time : ", elapsed)
                newdata = [elapsed, co_1, co_2, fltCo2]
                a.writerows([newdata])
        except (Exception) as error:
            print(error)
            
            # Printing sensor readings in rows
        print("Alphasense Sensor out: ",",",co_1,",",co_2)
        print("Gas Concentration Outputs: CO: ",CO,", CO2: ",CO2)

        # Plotting temperature
        tlist.append(elapsed)
        co2list.append(CO2)
        colist.append(CO)
        plt.close()
        plt.plot(tlist, colist, tlist, co2list)
        plt.xlabel("time (s)")
        plt.ylabel("Emissions (ppm)")
        #plt.legend("CO2","CO")
        plt.show(block=False)
        
        # Only collect data after certain intervals of time
        time.sleep(2)