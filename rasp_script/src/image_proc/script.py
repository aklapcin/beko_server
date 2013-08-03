import cv
import cv2
import os
import sys
import numpy as np

def save_image(filename, dirname, image):
	filepath = os.path.join(dirname, filename)
	if os.path.exists(filepath):
		os.remove(filepath)
	cv2.imwrite(filepath, image)

def find_ON_diods(image):
	element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))

	greyed = cv2.cvtColor(image, cv.CV_RGB2GRAY)
	val, thr = cv2.threshold(greyed, 70., 255, cv.CV_THRESH_BINARY)
	er = cv2.erode(thr, element, iterations=10)
	di = cv2.dilate(er, element, iterations=15)
	gb = cv2.GaussianBlur(di, (5, 5), 2)
	
	contours, _ = cv2.findContours(gb, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)


	diod_contours = find_diods_contours(contours)
	for d_c in diod_contours:
		cv2.circle(image, d_c[0], d_c[1], cv.RGB(0,255,0), 10)

	return [d[0] for d in diod_contours]
	
def find_OFF_diods(image, filename, dirname):

	_, _, red = cv2.split(image)
	element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
	val, thr = cv2.threshold(red, 40., 255, cv.CV_THRESH_BINARY)
	#save_image("thr_%s" % filename, dirname, thr)
	di = cv2.dilate(thr, element, iterations=10)
	er = cv2.erode(di, element, iterations=20)
	
	contours, _ = cv2.findContours(er, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

	diod_contours = find_diods_contours(contours)
	for d_c in diod_contours:
		cv2.circle(image, d_c[0], d_c[1], cv.RGB(255,0,0), 10)

	return [d[0] for d in diod_contours]
	
def find_diods_contours(counturs):
	result = []
	for c in counturs:
		(center, size, angle) = cv2.fitEllipse(c)
		almost_circle = abs(size[0] - size[1]) < max(size) * 0.3
		
		double_r = cv.Round(sum(size) * 0.5)
		good_size = double_r < 160 and double_r > 130
		if not (almost_circle and good_size):
			continue
		#print "double_r = %s, center= %s %s sizes = %s %s" % (double_r, center[0], center[1], size[0], size[1])
		
		center = (cv.Round(center[0]), cv.Round(center[1]))
		result.append((center, int(double_r/2)))

	return result
		


def get_diods_state(dirname):
	files = os.listdir(dirname)

	for f in files:
		filename = os.path.join(dirname, f)
		if '_' in f:
			os.remove(filename)
			continue
		print f
		
		if not os.path.isfile(filename):
			continue
		image = cv2.imread(filename)
		
		diods_on = find_ON_diods(image)
		diods_off = find_OFF_diods(image, f, dirname)

		diod_state_pos = [(d[1], True) for d in diods_on]
		diod_state_pos.extend([(d[1], False) for d in diods_off])

		diod_state_pos.sort()

		for i in range(len(diod_state_pos)):
			print "Diod %s: %s" % (i+1, diod_state_pos[i][1] and "ON" or "OFF")
			
		save_image("circles_%s" % f, dirname, image)		
		

def main():
	
	args = sys.argv
	
	if args[1] == 'make_grey':
		get_diods_state(args[2])

if __name__ == '__main__':
	main()