#Script to collect data for BYU GEO sensor team

#Importing necessary packages 
import quick2wire.i2c as i2c
import re
import time
#import gspread
import datetime
import csv
from threading import Thread
from datetime import date
import serial
import numpy as np
import matplotlib.pyplot as plt

#Calibration coefficients
#CO
co_a1=0.25643
co_a0=-3.5328

#CO2
co2_a1=12.2802
co2_a0=-317.1127

#For COZIR CO2
#multiplier=10 #cozir co2 20% sensors require this multiplier (per cozir code)
ser = serial.Serial("/dev/ttyUSB0")
print ("Python progam to run a Cozir Sensor\n")
ser.write("M 4\r\n".encode()) # set display mode to show only CO2
ser.write("K 2\r\n".encode()) # set  operating mode
# K sets the mode,  2 sets streaming instantaneous CO2 output
# \r\n is CR and LF
ser.flushInput()
time.sleep(1)

#Naming addresses and channels for CO/Temp
adc_address1 = 0x68
adc_address2 = 0x69

adc_channel1 = 0x98
adc_channel2 = 0xB8
adc_channel3 = 0xD8
adc_channel4 = 0xF8

# i2c bus for Rpi version 2
i2c_bus = 1

# Initializing sensor reading variables
# Using Delta Sigma ADC
asense_3 = 0.00
asense_4 = 0.00

#Initializing v, start time, previous temp
v=0
t0 = datetime.datetime.now()
temp_prev = 20
tlist = []
co2list = []
colist=[]

#Print data order at top for reference
print("order of readings is: CO, co_un, temp, CO2")

with i2c.I2CMaster(i2c_bus) as bus:
        #function to get ADC sensor readings
    def getadcreading(address, channel):    
        bus.transaction(i2c.writing_bytes(address, channel))
        time.sleep(0.05)
        h, l, r = bus.transaction(i2c.reading(address,3))[0]
        time.sleep(0.05)
        h, l, r = bus.transaction(i2c.reading(address,3))[0]

        t = (h << 8) | l
        v = t * 0.000154
        if v < 5.5:
            return v
        else: # must be a floating input
            return 0.00

    while True: 

        #CO2 reading
        ser.write("Z\r\n".encode())
        resp = ser.read(10)
        resp = resp[:8]
    
        fltCo2 = float(resp[2:])

        try:
            asense_3=1000*getadcreading(adc_address1, adc_channel3)#CO-WE2 = CO-Aux
            asense_4=1000*getadcreading(adc_address1, adc_channel4)#CO-WE1
            
        except:
            pass
            print("Trouble getting a sensor reading")
            
        #Calibration curves   
        CO2=co2_a1*fltCo2+co2_a0
        CO=co_a1*(asense_3-asense_4)+co_a0

        # Writing sensor readings to a CSV file on the SD card
        # Add to same file
        day = datetime.datetime.now()
        elapsed = (day-t0).total_seconds()
        filename="/home/pi/Documents/GEO Code/COData/"+'All Data: CO'
        try:
            with open(filename,'a',newline='') as fp:
                a = csv.writer(fp, delimiter=',')
                print("Elapsed Time : ", elapsed)
                newdata = [elapsed, CO, CO2]
                a.writerows([newdata])
        except (Exception) as error:
            print(error)

        # Printing sensor readings in rows
        print("Alphasense Sensor out: ",",",asense_3,",",asense_4)
        print("Alphasense Concentrations: CO: ",CO,", CO2: ",CO2)

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
        time.sleep(4)
