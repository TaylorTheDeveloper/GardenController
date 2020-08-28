#!/usr/bin/python3
import glob
import time
from datetime import datetime, timedelta
import Adafruit_GPIO.SPI as SPI
import Adafruit_DHT
import board
import RPi.GPIO as GPIO
import os

import asyncio
import json
import random

from azure.iot.device.aio import ProvisioningDeviceClient
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import MethodResponse
from azure.iot.device import Message

async def main():
	#########################
	##### Configuration #####
	# In a production environment, don't store
	# connection information in the code.
	provisioning_host = 'global.azure-devices-provisioning.net'
	id_scope = '0ne00165A84'
	registration_id = 'q64hfvzwoi'
	symmetric_key = '5LEsrMz8hcovUT3xZ1S4YWdlWdCPMyioJmuNQ0VeLY8='

	delay = 5
	########## End ##########
	#########################

	# All the remaining code is nested within this main function
	async def register_device():
		provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
			provisioning_host=provisioning_host,
			registration_id=registration_id,
			id_scope=id_scope,
			symmetric_key=symmetric_key,
		)

		registration_result = await provisioning_device_client.register()

		print(f'Registration result: {registration_result.status}')

		return registration_result

	async def connect_device():
		device_client = None

		try:
			registration_result = await register_device()

			if registration_result.status == 'assigned':
				device_client = IoTHubDeviceClient.create_from_symmetric_key(
			  	symmetric_key=symmetric_key,
			  	hostname=registration_result.registration_state.assigned_hub,
			  	device_id=registration_result.registration_state.device_id,
				)
				# Connect the client.
				await device_client.connect()
				print('Device connected successfully')
		finally:
			return device_client

	async def register_device():
		provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
		  provisioning_host=provisioning_host,
		  registration_id=registration_id,
		  id_scope=id_scope,
		  symmetric_key=symmetric_key,
		)

		registration_result = await provisioning_device_client.register()

		print(f'Registration result: {registration_result.status}')

		return registration_result

	async def connect_device():
	    device_client = None
	    try:
	        registration_result = await register_device()
	        if registration_result.status == 'assigned':
	            device_client = IoTHubDeviceClient.create_from_symmetric_key(
	              symmetric_key=symmetric_key,
	              hostname=registration_result.registration_state.assigned_hub,
	              device_id=registration_result.registration_state.device_id,
	            )
	            # Connect the client.
	            await device_client.connect()
	            print('Device connected successfully')
	    finally:
	        return device_client

	async def send_telemetry():
		print(f'Sending telemetry from the provisioned device every {delay} seconds')

		### Inputs ###

		# Water Level Trigger Configuration
		# 0 is full, 1 is needing refill.
		GPIO_WATERLEVEL = 24
		GPIO.setup(GPIO_WATERLEVEL , GPIO.IN)

		# DHT11 Temp/Humid Sensor configutation
		GPIO_DHT11 = 17
		#DHT11(11). DHT22(22) or AM2302(22)
		TEMPHUMIDSENSOR = 22

		# One Wire Configuration and Utils for DS18B20 temp sensor
		GPIO_ONEWIRE_DS18B20 = 4
		base_dir = '/sys/bus/w1/devices/'
		device_folder = glob.glob(base_dir + '28*')[0]
		device_file = device_folder + '/w1_slave'

		# One Wire
		def read_temp_raw():
		    f = open(device_file, 'r')
		    lines = f.readlines()
		    f.close()
		    return lines

		# One Wire
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

		### Outputs ###

		# Humidity Controller
		GPIO_HUMID = 22
		GPIO.setup(GPIO_HUMID, GPIO.OUT)
		HUMID_RELAY_OUT = 0

		# Temp Controller
		GPIO_TEMP = 13
		GPIO.setup(GPIO_TEMP, GPIO.OUT)
		HEATER_RELAY_OUT = 0

		# Chamber Fan Controller Relay
		GPIO_FAN = 5
		GPIO.setup(GPIO_FAN, GPIO.OUT)
		FanWaitTimeHours = 1
		FanNextRunTime = datetime.utcnow()  #Fan runs at startup
		FanRunDurationSeconds = 60
		FanCheckToStop = False
		FanLastStart = datetime.utcnow()
		FAN_RELAY_OUT = 0

		# Water Refill Pump Relay
		GPIO_PUMP = 20
		GPIO.setup(GPIO_PUMP, GPIO.OUT)
		GPIO.output(GPIO_PUMP, 0)
		PUMP_RELAY_OUT = 0

		# Light Pinout configuration
		GPIO_LIGHTS = 25
		GPIO.setup(GPIO_LIGHTS, GPIO.OUT)
		# time config 12 hour cycle
		LIGHTSSTARTHOUR = 8 # 8 am light start
		LIGHTSENDHOUR = 18 # 8pm light end
		LIGHTS_RELAY_OUT = 0

		# General Utils
		def ConvertFahrenheit(celsius):
			return (9/5)*celsius+32

		# Set GPIO board type
		GPIO.setmode(GPIO.BCM)

		while True:
			try:
				if FanNextRunTime < datetime.utcnow():
					print("fan on")
					FanNextRunTime = datetime.utcnow() + timedelta(hours=FanWaitTimeHours)
					FAN_RELAY_OUT = 1
					GPIO.output(GPIO_FAN, 1)
					FanCheckToStop = True
					FanLastStart = datetime.utcnow() + timedelta(seconds=FanRunDurationSeconds)
				if FanCheckToStop:
					if FanLastStart < datetime.utcnow():
						FAN_RELAY_OUT = 0
						GPIO.output(GPIO_FAN, 0)
						FanCheckToStop = False
						print("fan off")

				# Date info
				now = datetime.now() # May change later to be UTC
				lightsOnTime = now.replace(hour=LIGHTSSTARTHOUR, minute=0, second=0, microsecond=0)
				lightsOffTime = now.replace(hour=LIGHTSENDHOUR, minute=0, second=0, microsecond=0)

				if now >= lightsOnTime and now <= lightsOffTime:
					print("lights on")
					LIGHTS_RELAY_OUT = 1
					GPIO.output(GPIO_LIGHTS, 1)
				else:
					print("lights off")
					LIGHTS_RELAY_OUT = 0
					GPIO.output(GPIO_LIGHTS, 0)

				waterLvl = GPIO.input(GPIO_WATERLEVEL)

				if waterLvl == 1:
					print("pump on")
					PUMP_RELAY_OUT = 1
					GPIO.output(GPIO_PUMP, 1)
				else:
					print("pump off")
					PUMP_RELAY_OUT = 0
					GPIO.output(GPIO_PUMP, 0)

				humidity, temperature = Adafruit_DHT.read_retry(TEMPHUMIDSENSOR, GPIO_DHT11)
				refTempC, refTempF = read_onewire_temp()

				if humidity is not None and humidity < 95:
					print("humidity on")
					HUMID_RELAY_OUT = 1
					GPIO.output(GPIO_HUMID, 1)
				else:
					print("humidity off")
					HUMID_RELAY_OUT = 0
					GPIO.output(GPIO_HUMID, 0)

				if temperature < 80:
					print("heater on")
					HEATER_RELAY_OUT = 1
					GPIO.output(GPIO_TEMP, 1)
				else:
					print("heater off")
					HEATER_RELAY_OUT = 0
					GPIO.output(GPIO_TEMP, 0)

				#GPIO.output(GPIO_LIGHTS, 1) Save and make data sample indicator light
				print("DHT2302 humid + temp:",humidity, ConvertFahrenheit(temperature))
				print("DS18B20 reference temp:", refTempF)
			except KeyboardInterrupt:
				print("Goodbye!")
				GPIO.cleanup()
				break
			except RuntimeError as error:
				# Errors happen fairly often, DHT's are hard to read, just keep going
				print(error.args[0])

			payload = json.dumps({'reference': refTempF,'temperature': ConvertFahrenheit(temperature), 'humidity': humidity,'humidity': humidity,'humidityrelay': HUMID_RELAY_OUT,'heaterrelay': HEATER_RELAY_OUT,'lightrelay': LIGHTS_RELAY_OUT,'pumprelay': PUMP_RELAY_OUT,'fanrelay': FAN_RELAY_OUT})
			msg = Message(payload)
			await device_client.send_message(msg, )
			print(f'Sent message: {msg}')
			await asyncio.sleep(delay)

	async def blink_command(request):
	    print('Received synchronous call to blink')
	    response = MethodResponse.create_from_method_request(
	      request, status = 200, payload = {'description': f'Blinking LED every {request.payload} seconds'}
	    )
	    await device_client.send_method_response(response)  # send response
	    print(f'Blinking LED every {request.payload} seconds')

	async def diagnostics_command(request):
	    print('Starting asynchronous diagnostics run...')
	    response = MethodResponse.create_from_method_request(
	      request, status = 202
	    )
	    await device_client.send_method_response(response)  # send response
	    print('Generating diagnostics...')
	    await asyncio.sleep(2)
	    print('Generating diagnostics...')
	    await asyncio.sleep(2)
	    print('Generating diagnostics...')
	    await asyncio.sleep(2)
	    print('Sending property update to confirm command completion')
	    await device_client.patch_twin_reported_properties({'rundiagnostics': {'value': f'Diagnostics run complete at {datetime.datetime.today()}.'}})

	async def turnon_command(request):
	    print('Turning on the LED')
	    response = MethodResponse.create_from_method_request(
	      request, status = 200
	    )
	    await device_client.send_method_response(response)  # send response

	async def turnoff_command(request):
	    print('Turning off the LED')
	    response = MethodResponse.create_from_method_request(
	      request, status = 200
	    )
	    await device_client.send_method_response(response)  # send response

	commands = {
	'blink': blink_command,
	'rundiagnostics': diagnostics_command,
	'turnon': turnon_command,
	'turnoff': turnoff_command,
	}

	# Define behavior for handling commands
	async def command_listener():
	    while True:
	        method_request = await device_client.receive_method_request()  # Wait for commands
	        await commands[method_request.name](method_request)

	async def name_setting(value, version):
	    await asyncio.sleep(1)
	    print(f'Setting name value {value} - {version}')
	    await device_client.patch_twin_reported_properties({'name' : {'value': value, 'ad': 'completed', 'ac': 200, 'av': version}})

	async def brightness_setting(value, version):
	    await asyncio.sleep(5)
	    print(f'Setting brightness value {value} - {version}')
	    await device_client.patch_twin_reported_properties({'brightness' : {'value': value, 'ad': 'completed', 'ac': 200, 'av': version}})

	settings = {
		'name': name_setting,
		'brightness': brightness_setting
	}

	  # define behavior for receiving a twin patch
	async def twin_patch_listener():
		while True:
			patch = await device_client.receive_twin_desired_properties_patch() # blocking
			to_update = patch.keys() & settings.keys()
			await asyncio.gather(
			    *[settings[setting](patch[setting], patch['$version']) for setting in to_update]
			)

	# Define behavior for halting the application
	def stdin_listener():
		while True:
			selection = input('Press Q to quit\n')
			if selection == 'Q' or selection == 'q':
				print('Quitting...')
				break

	device_client = await connect_device()

	if device_client is not None and device_client.connected:
		print('Send reported properties on startup')
		await device_client.patch_twin_reported_properties({'state': 'true', 'processorArchitecture': 'ARM', 'swVersion': '1.0.0'})
		tasks = asyncio.gather(
		    send_telemetry(),
		    command_listener(),
		    twin_patch_listener(),
		)

		# Run the stdin listener in the event loop
		loop = asyncio.get_running_loop()
		user_finished = loop.run_in_executor(None, stdin_listener)

		# Wait for user to indicate they are done listening for method calls
		await user_finished

		# Cancel tasks
		tasks.add_done_callback(lambda r: r.exception())
		tasks.cancel()
		await device_client.disconnect()
	else:
		print('Device could not connect')


if __name__ == '__main__':
	print("Starting Garden Controller")
	asyncio.run(main())
	GPIO.cleanup()
