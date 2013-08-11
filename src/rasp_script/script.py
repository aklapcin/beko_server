import cv
import cv2
import os
import sys
import numpy as np
import time
import subprocess
import re
import math
import urllib
from common_pralka.states import WashingMachineStates
from image_proc import take_photo, get_diods_state
from wachingmachine import MachineState



def get_machine_state(dirname, tmpfs_dir, save_state_to_file=False, server_address=None, api_token=None):
	''' Does everything. Takes a photo of diods, analyze it to get 
	state of diods. Get state of washing machine and sends it to api'''
	now = str(int(time.time()))
	filepath = os.path.join(tmpfs_dir, "%s.jpg" % now)
	
	take_photo(filepath)
	diods_state = get_diods_state(filepath, dirname, save_processed_image="")
	machine_state = MachineState(diods_state, filepath, calculate=True)
	if save_state_to_file:
		record_diods_state(machine_state, dirname)
	if server_address is not None and api_token is not None:
		if machine_state != WashingMachineStates.UNKNOWN: 
			url = "http://%s/api/device/1/update_state/?state=%s&token=%s" %\
				(server_address, machine_state.state,  api_token)
			urllib.urlopen(url)
	os.remove(filepath)

def record_diods_state(machine_state, dirname):
	'''save state of diods in file'''
	record_file = os.path.join(dirname, 'record')
	r_f = open(record_file, 'a')
	r_f.write(machine_state.record())
	r_f.close()

def process_dir(dirname, save_state_to_file=True):
	files = os.listdir(dirname)

	for f in files:
		filepath = os.path.join(dirname, f)
		if '_' in f and 'jpg' in f:
			os.remove(filepath)

	files = os.listdir(dirname)	
	for f in files:
		if 'jpg' not in f:
			continue
		filepath = os.path.join(dirname, f)
		if not os.path.isfile(filepath):
			continue
		diods_state = get_diods_state(filepath, dirname, save_processed_image="processed_%s")
		machine_state = MachineState(diods_state, filepath, calculate=True)
		print filepath, machine_state.state

		if save_state_to_file:
			record_diods_state(machine_state, dirname)


def delete_old_files(dirname, since=3600):
	delete_till = int(time.time()) - 3600

	files = os.listdir(dirname)

	for f in files:
		r = re.search('(\d{10}).jpg', f)
		if not r:
			continue

		dt = r.groups()[0]
		if int(dt) < delete_till:
			os.remove(os.path.join(dirname, f))
	
def main():
	
	args = sys.argv
	
	if args[1] == 'process_dir':
		process_dir(args[2])
	elif args[1] == 'get_machine_state':
		directory = args[2]
		if len(args) >= 6:
			tmpfs_dir = args[3]
			server_url = args[4]
			api_token = args[5]
		get_machine_state(directory, tmpfs_dir, server_address=server_url, api_token=api_token)
	elif args[1] == 'delete_old_files':
		delete_till = len(args) > 3 and int(args[3]) or 3600
		delete_old_files(args[2], delete_till)

if __name__ == '__main__':
	main()
