#!/usr/bin/python3
import glob
import time
from datetime import datetime, timedelta
#import Adafruit_GPIO.SPI as SPI
#import adafruit_mcp3008.mcp3008 as MCP
#from adafruit_mcp3008.analog_in import AnalogIn
import Adafruit_GPIO.SPI as SPI
import Adafruit_DHT
import board
import RPi.GPIO as GPIO
import os

# Set GPIO board type
GPIO.setmode(GPIO.BCM)

# Time Configuration
sleepTime = .3 #seconds

# Humidity Controller
GPIO_HUMID = 22
GPIO.setup(GPIO_HUMID, GPIO.OUT)

# Temp Controller
GPIO_TEMP = 13
GPIO.setup(GPIO_TEMP, GPIO.OUT)

# Chamber Fan Controller Relay
GPIO_FAN = 5
GPIO.setup(GPIO_FAN, GPIO.OUT)
FanWaitTimeHours = 1
FanNextRunTime = datetime.utcnow()  #Fan runs at startup
FanRunDurationSeconds = 60
FanCheckToStop = False
FanLastStart = datetime.utcnow()

# Water Level Trigger Configuration
# 0 is full, 1 is needing refill.
GPIO_WATERLEVEL = 24
GPIO.setup(GPIO_WATERLEVEL , GPIO.IN)

# Water Refill Pump Relay
GPIO_PUMP = 20
GPIO.setup(GPIO_PUMP, GPIO.OUT)
GPIO.output(GPIO_PUMP, 0)

# Light Pinout configuration
GPIO_LIGHTS = 25
GPIO.setup(GPIO_LIGHTS, GPIO.OUT)

# DHT11 Temp/Humid Sensor configutation
GPIO_DHT11 = 17
TEMPHUMIDSENSOR = 22 #DHT11(11). DHT22(22) or AM2302(22)

# One Wire Configuration and Utils for DS18B20 temp sensor
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

# time config 12 hour cycle
LIGHTSSTART = 8 # 8 am light start
LIGHTSEND = 18+2 # 8pm light end

print("Starting Garden Controller")
while(True):
	try:
		if FanNextRunTime < datetime.utcnow():
			print("fan on")
			FanNextRunTime = datetime.utcnow() + timedelta(hours=FanWaitTimeHours)
			GPIO.output(GPIO_FAN, 1)
			FanCheckToStop = True
			FanLastStart = datetime.utcnow() + timedelta(seconds=FanRunDurationSeconds)
		if FanCheckToStop:
			if FanLastStart < datetime.utcnow():
				GPIO.output(GPIO_FAN, 0)
				FanCheckToStop = False
				print("fan off")

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

		if waterLvl == 1:
			print("pump on")
			GPIO.output(GPIO_PUMP, 1)
		else:
			print("pump off")
			GPIO.output(GPIO_PUMP, 0)

		humidity, temperature = Adafruit_DHT.read_retry(TEMPHUMIDSENSOR, GPIO_DHT11)

		if humidity < 95:
			print("humidity on")
			GPIO.output(GPIO_HUMID, 1)
		else:
			print("humidity off")
			GPIO.output(GPIO_HUMID, 0)

		if temperature < 80:
			print("heater on")
			GPIO.output(GPIO_TEMP, 1)
		else:
			print("heater off")
			GPIO.output(GPIO_TEMP, 0)

		#GPIO.output(GPIO_LIGHTS, 1) Save and make data sample indicator light
		print("DHT2302 humid + temp:",humidity, ConvertFahrenheit(temperature))
		print("DS18B20 room reference temp:", read_onewire_temp())
		time.sleep(sleepTime)
	except KeyboardInterrupt:
		print("Goodbye!")
		GPIO.cleanup()
		break
	except RuntimeError as error:
		# Errors happen fairly often, DHT's are hard to read, just keep going
		print(error.args[0])

