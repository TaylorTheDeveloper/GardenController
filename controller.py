#!/usr/bin/python3
import glob
import time
from datetime import datetime
#import Adafruit_GPIO.SPI as SPI
#import adafruit_mcp3008.mcp3008 as MCP
#from adafruit_mcp3008.analog_in import AnalogIn
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import Adafruit_DHT
import board
import RPi.GPIO as GPIO

# Set GPIO board type
GPIO.setmode(GPIO.BCM)

# import adafruit_dh#t does not work

# Time Configuration
sleepTime = .2 #seconds

# Software ADC/SPI interface configuration
CLK = 23
MISO = 21
MOSI = 19
CS = 2
TEMP_CsaH = 1
HUMID_CH = 2

# Water Level Trigger Configuration
# 0 is full, 1 is needing refill.
GPIO_WATERLEVEL = 24
GPIO.setup(GPIO_WATERLEVEL , GPIO.IN)

# Light Pinout configuration
GPIO_LIGHTS = 25
GPIO.setup(GPIO_LIGHTS, GPIO.OUT)

# DHT11 Temp/Humid Sensor configutation
GPIO_DHT11 = 17
TEMPHUMIDSENSOR = 11 #DHT11(11). DHT22(22) or AM2302(2302)

## One Wire Configuration and Utils for DS18B20 temp sensor
GPIO_ONEWIRE_DS18B20 = 4
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_onewire_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

# General Utils
def ConvertFahrenheit(celsius):
	return (9/5)*celsius+32


# Main Start
#mcp = Adafruit_MCP008.MCP3008(clk=CLK,cs=CS,miso=MISO,mosi=MOSI)
#dht =adafruit_dht.DHT11(board.D4)

# time config 12 hour cycle
LIGHTSSTART = 8 # 8 am light start
LIGHTSEND = 18 # 8pm light end 

while(True):
	try:
		# Date info
		now = datetime.now() # May change later to be UTC
		lightsOnTime = now.replace(hour=LIGHTSSTART, minute=0, second=0, microsecond=0)
		lightsOffTime = now.replace(hour=LIGHTSEND, minute=0, second=0, microsecond=0)
		print(now, lightsOffTime)
		if now >= lightsOnTime and now <= lightsOffTime:
			GPIO.output(GPIO_LIGHTS, 1)
		else:
			GPIO.output(GPIO_LIGHTS, 0)

		waterLvl = GPIO.input(GPIO_WATERLEVEL)
		print(waterLvl)

		#value = mcp.read_adc(0)
		#print(value)
		humidity, temperature = Adafruit_DHT.read_retry(TEMPHUMIDSENSOR, GPIO_DHT11)
		#GPIO.output(GPIO_LIGHTS, 1) Save and make data sample indicator light
		print("DHT11 humid + temp:",humidity, ConvertFahrenheit(temperature))
		print("DS18B20 only temp:", read_onewire_temp())
		#GPIO.output(GPIO_LIGHTS, 0)
		#temp = ConvertFahrenheit(dht.temperature)
		#humid = dht.humidity
		#print(humid, temp)
	except RuntimeError as error:
		# Errors happen fairly often, DHT's are hard to read, just keep going
		print(error.args[0])

	time.sleep(sleepTime)
