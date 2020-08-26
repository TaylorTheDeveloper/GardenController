import os
import time


while(True):
	cmd = "hub-ctrl.c/hub-ctrl -h 0 -P 2 -p 1" # on
	print("on")
	os.system(cmd)
	time.sleep(15)
	cmd2 = "hub-ctrl.c/hub-ctrl -h 0 -P 2 -p 0"
	print("off")
	os.system(cmd2)
	time.sleep(10)
