#!/usr/bin/python3

import time
#import Adafruit_GPIO.SPI as SPI
#import adafruit_mcp3008.mcp3008 as MCP
#from adafruit_mcp3008.analog_in import AnalogIn
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import Adafruit_DHT
import board
# import adafruit_dh#t does not work

# Time Configuration
sleepTime = 3 #seconds

# Software ADC/SPI interface configuration
CLK = 23
MISO = 21
MOSI = 19
CS = 2
TEMP_CsaH = 1
HUMID_CH = 2


# DHT11 Temp/Humid Sensor configutation
GPIO_DHT11 = 4
TEMPHUMIDSENSOR = 11 #DHT11(11). DHT22(22) or AM2302(2302)

# Utils


def ConvertFahrenheit(celsius):
	return (9/5)*celsius+32


# Main Start
#mcp = Adafruit_MCP008.MCP3008(clk=CLK,cs=CS,miso=MISO,mosi=MOSI)
#dht =adafruit_dht.DHT11(board.D4)


while(True):
	try:
	#value = mcp.read_adc(0)
	#print(value)
		humidity, temperature = Adafruit_DHT.read_retry(TEMPHUMIDSENSOR, GPIO_DHT11)
		print(humidity, ConvertFahrenheit(temperature))
		#temp = ConvertFahrenheit(dht.temperature)
		#humid = dht.humidity
		#print(humid, temp)
	except RuntimeError as error:
		# Errors happen fairly often, DHT's are hard to read, just keep going
		print(error.args[0])

	time.sleep(sleepTime)
