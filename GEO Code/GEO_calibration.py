#CO+CO2 Gas Calibration Code
#Created 2/28/2018 Aaron Bame (aaron.bame@gmail.com)
#Updated to store CO2 data to file 3/6/2018 Aaron Bame

#Importing necessary packages 
#from quick2wire import quick2wire
import quick2wire.i2c as i2c
import re
import time
import datetime
import csv
from threading import Thread
from datetime import date
import serial
import numpy as np
import matplotlib.pyplot as plt

#For COZIR CO2
multiplier=10 #cozir co2 20% sensors require this multiplier (per cozir code)
ser = serial.Serial("/dev/ttyUSB0")
ser.write("M 4\r\n".encode()) # set display mode to show only CO2
ser.write("K 2\r\n".encode()) # set  operating mode
# K sets the mode,  2 sets streaming instantaneous CO2 output
# \r\n is CR and LF
ser.flushInput()
time.sleep(1)

#Naming addresses and channels for CO/Temp
adc_address1 = 0x68
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
        CO2=fltCo2*multiplier

        time.sleep(1)

        # sensor reading variable values assigned in mV
        try:
            #TMP=getadcreading(adc_address1, adc_channel2)          #TMP36 Vout
            asense_3=1000*getadcreading(adc_address1, adc_channel3)#CO-WE2 = CO-Aux
            asense_4=1000*getadcreading(adc_address1, adc_channel4)#CO-WE1
            
        except:
            pass
            print("Trouble getting a sensor reading")
            
        CO=asense_3-asense_4 #Uncalibrated deltaV between Working and Auxiliary electrode
        
        # Writing sensor readings to a CSV file on the SD card
        # NEW - Add to same file
        day = datetime.datetime.now()
        elapsed = (day-t0).total_seconds()
        filename="/home/pi/BYU_GEO/GEO Code/COData/"+'All Data: CO'
        try:
            with open(filename,'a',newline='') as fp:
                a = csv.writer(fp, delimiter=',')
                print("Elapsed Time : ", elapsed)
                newdata = [elapsed, asense_3, asense_4, fltCo2]
                a.writerows([newdata])
        except (Exception) as error:
            print(error)
            
            # Printing sensor readings in rows
        print("Alphasense Sensor out: ",",",asense_3,",",asense_4)
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