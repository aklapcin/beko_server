import cv
import cv2
import os
import sys
import numpy as np
import time
import subprocess
import re
import math

class Point(object):
	def __init__(self, x, y):
		self.x = x
		self.y = y
		return super(Point, self).__init__()

	def moved_by(self, vector):
		return Point(self.x + vector[0], self.y + vector[1])
	
	def distance(self, other):
		xd_sq = (self.x - other.x)* (self.x - other.x)
		yd_sq = (self.y - other.y)* (self.y - other.y)
		return math.sqrt(float(xd_sq + yd_sq))

class DiodState(object):
	states = ['ON', 'OFF', 'UNKNOWN']

	def __init__(self, center, state):
		self.center = Point(center[0], center[1])
		self.state = state

	def in_range(self, range_center, r):
		return self.center.distance(range_center) <= r

	def is_on(self):
		return self.state == 'ON'

class MachineState(object):
	STATES = {'ON': [True, False, False, False, False],
		'FINISHED': [True, False, False, False, True],
		'WASHING': [True, True, False, False, False],
		'RINSING': [False, False, True, False, False],
		'SPINING': [False, False, False, True, False]}

	STATES_NAMES = STATES.keys()
	STATES_NAMES.extend(['UNKNOWN', 'OFF'])

	DIODS_DISTANCE = Point(36, 230)

	def __init__(self, diods_state, filename, calculate=False):
		self.diods_state = []
		for d in diods_state:
			print d
			self.diods_state.append(DiodState(d[0], d[1] and 'ON' or 'OFF'))
		self.state = 'UNKNOWN'
		self.filename = filename
		if calculate:
			self.calculate_state()

	def calculate_state(self):
		if len(self.diods_state) == 0:
			self.state = 'OFF'
			return
		if len(self.diods_state) < 4:
			self.state = 'UNKNOWN' 
			return
		if not self.check_diods_ok():
			self.state = 'UNKNOWN'
			return
		
		for state_name, diods_on in self.STATES.items():
			if self.diods_on_state == diods_on: 
				self.state = state_name
				break
		
	@property
	def diods_on_state(self):
		return [x.is_on() for x in self.diods_state]
	

	def check_diods_ok(self):
		i = 0
		while True:
			if i + 1 >= len(self.diods_state):
				break
			c_diod = self.diods_state[i]
			next_diod = self.diods_state[i + 1]
			
			next_diod_should_be = c_diod.center.moved_by([self.DIODS_DISTANCE.x, self.DIODS_DISTANCE.y])
			if next_diod.in_range(next_diod_should_be, 30):
				i += 1
				continue  # everything ok, checking next diod

			next_next_diod_should_be = c_diod.center.moved_by([self.DIODS_DISTANCE.x * 2, self.DIODS_DISTANCE.y * 2])
			if next_diod.in_range(next_next_diod_should_be, 30):
				missed_diod = DiodState(c_diod.x+ self.DIODS_DISTANCE.x, c_diod.y + self.DIODS_DISTANCE.y, 'UNKNOWN')
				self.diods_state.insert(i+1, missed_diod)
				print "inserting missing diod at %s, %s"% (missed_diod.center.x, missed_diod.center.y)
				i += 1
				continue  # everything ok, checking next diod
			# next diod is not in line. remove ir
			print "removing bad diod i=%s current diod is at %s %s, next is at %s %s" %\
					(i, c_diod.center.x, c_diod.center.y, next_diod.center.x, next_diod.center.y)
				
			self.diods_state.remove(i+1)
			i += 1
		
		if len(self.diods_state) == 5:
			return True
		
		return False

	def record(self):
		message = '\n'.join([self.filename, self.state, ','.join([x and 'ON' or 'OFF' for x in self.diods_on_state])]) + '\n'
		return message
		


def save_image(filename, dirname, image):
	filepath = os.path.join(dirname, filename)
	if os.path.exists(filepath):
		os.remove(filepath)
	cv2.imwrite(filepath, image)

def find_ON_diods(image, dirname=None, filename=None):
	print "finding ON"
	element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))

	greyed = cv2.cvtColor(image, cv.CV_RGB2GRAY)
	val, thr = cv2.threshold(greyed, 70., 255, cv.CV_THRESH_BINARY)
	er = cv2.erode(thr, element, iterations=10)
	di = cv2.dilate(er, element, iterations=15)
	if dirname and filename:
		save_image("on_dilate_%s" % filename, dirname, di)
	gb = cv2.GaussianBlur(di, (5, 5), 2)
	
	contours, _ = cv2.findContours(gb, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)


	diod_contours = find_diods_contours(contours)
	for d_c in diod_contours:
		cv2.circle(image, d_c[0], d_c[1], cv.RGB(0,255,0), 10)

	return [d[0] for d in diod_contours]
	
def find_OFF_diods(image, dirname=None, filename=None):
	print "finding OFF"
	_, _, red = cv2.split(image)
	if dirname and filename:
		save_image("red_%s" % filename, dirname, red)
	
	element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
	val, thr = cv2.threshold(red, 8., 255, cv.CV_THRESH_BINARY)
	if dirname and filename:
		save_image("off_thr_%s" % filename, dirname, thr)
	
	#save_image("thr_%s" % filename, dirname, thr)
	di = cv2.dilate(thr, element, iterations=15)
	er = cv2.erode(di, element, iterations=20)
	if dirname and filename:
		save_image("off_erode_%s" % filename, dirname, er)
	
	contours, _ = cv2.findContours(er, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

	diod_contours = find_diods_contours(contours)
	for d_c in diod_contours:
		cv2.circle(image, d_c[0], d_c[1], cv.RGB(255,0,0), 10)

	return [d[0] for d in diod_contours]
	
def find_diods_contours(counturs):
	result = []
	for c in counturs:
		if len(c) < 6:
			continue
		(center, size, angle) = cv2.fitEllipse(c)
		almost_circle = abs(size[0] - size[1]) < max(size) * 0.3
		
		double_r = cv.Round(sum(size) * 0.5)
		good_size = double_r < 150 and double_r > 110
		if not (almost_circle and good_size):
			continue
		print "double_r = %s, center= %s %s sizes = %s %s" % (double_r, center[0], center[1], size[0], size[1])
		
		center = (cv.Round(center[0]), cv.Round(center[1]))
		result.append((center, int(double_r/2)))

	return result
		
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
		diods_state = get_diods_state(filepath, save_processed_image="processed_%s")
		machine_state = MachineState(diods_state, filepath, calculate=True)
		print filepath, machine_state.state

		if save_state_to_file:
			record_diods_state(machine_state, dirname)


def get_diods_state(filepath, save_processed_image=''):

	image = cv2.imread(filepath)
	print "processing %s" % filepath
	dirname, filename =os.path.split(filepath)
	diods_on = find_ON_diods(image, dirname=dirname, filename=filename)
	diods_off = find_OFF_diods(image, dirname=dirname, filename=filename)

	diod_state_pos = [(d[1], d, True) for d in diods_on]
	diod_state_pos.extend([(d[1], d, False) for d in diods_off])

	diod_state_pos.sort()
	diod_state_pos = [x[1:] for x in diod_state_pos]
	
	if save_processed_image:
		filename = save_processed_image % filename
		save_image(filename, dirname, image)		
	
	return diod_state_pos
	#for i in range(len(diod_state_pos)):
	#	print "Diod %s: %s" % (i+1, diod_state_pos[i][1] and "ON" or "OFF")
		
	
def take_photo(filepath):
	
    command = "raspistill -o %s -t 0" % filepath
    subprocess.call(command , shell=True)

def get_machine_state(dirname, save_state_to_file=True):
	now = str(int(time.time()))
	filepath = os.path.join(dirname, "%s.jpg" % now)
	
	take_photo(filepath)
	diods_state = get_diods_state(filepath, save_processed_image="%s")
	machine_state = MachineState(diods_state, filename, calculate=True)
	if save_state_to_file:
		record_diods_state(machine_state, dirname)

def record_diods_state(machine_state, dirname):
	
	record_file = os.path.join(dirname, 'record')
	r_f = open(record_file, 'a')
	r_f.write(machine_state.record())
	r_f.close()


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
		get_machine_state(args[2])
	elif args[1] == 'delete_old_files':
		delete_till = len(args) > 3 and int(args[3]) or 3600
		delete_old_files(args[2], delete_till)

if __name__ == '__main__':
	main()
