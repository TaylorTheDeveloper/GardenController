import os
import time
import RPi.GPIO as GPIO

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

chan = 20
GPIO.setup(chan, GPIO.OUT)

GPIO.output(chan, 0)
print("sleep")
while True:
	time.sleep(5)
	print("go")
	GPIO.output(chan, 1)
	time.sleep(10)
	print("stop")
	GPIO.output(chan, 0)
