import cv
import cv2
import os
import sys
import numpy as np
import time
import subprocess
import re
import math


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
    #if dirname and filename:
    #    save_image("on_dilate_%s" % filename, dirname, di)
    gb = cv2.GaussianBlur(di, (5, 5), 2)
    
    contours, _ = cv2.findContours(gb, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)


    diod_contours = find_diods_contours(contours)
    #for d_c in diod_contours:
    #    cv2.circle(image, d_c[0], d_c[1], cv.RGB(0,255,0), 10)

    return [d[0] for d in diod_contours]
    
def find_OFF_diods(image, dirname=None, filename=None):
    print "finding OFF"
    _, _, red = cv2.split(image)
    #if dirname and filename:
    #    save_image("red_%s" % filename, dirname, red)
    
    element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
    red_eq = cv2.equalizeHist(red)
    val, thr = cv2.threshold(red_eq, 110, 255, cv.CV_THRESH_BINARY)
    thr_er = cv2.erode(thr, element, iterations=3)

    #if dirname and filename:
    #    save_image("off_thr_%s" % filename, dirname, thr)
    
    #save_image("thr_%s" % filename, dirname, thr)
    di = cv2.dilate(thr, element, iterations=10)
    er = cv2.erode(di, element, iterations=12)
    #if dirname and filename:
    #    save_image("off_erode_%s" % filename, dirname, er)
    
    contours, _ = cv2.findContours(er, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    diod_contours = find_diods_contours(contours)
    #for d_c in diod_contours:
    #    cv2.circle(image, d_c[0], d_c[1], cv.RGB(255,0,0), 10)

    return [d[0] for d in diod_contours]
    
def find_diods_contours(counturs):
    result = []
    for c in counturs:
        if len(c) < 6:
            continue
        (center, size, angle) = cv2.fitEllipse(c)
        almost_circle = abs(size[0] - size[1]) < max(size) * 0.3
        
        double_r = cv.Round(sum(size) * 0.5)
        good_size = double_r < 150 and double_r > 85
        
        print "double_r = %s, center= %s %s sizes = %s %s" % (double_r, center[0], center[1], size[0], size[1])
        if not (almost_circle and good_size):
            continue
        
        center = (cv.Round(center[0]), cv.Round(center[1]))
        result.append((center, int(double_r/2)))

    return result
        

def get_diods_state(filepath, datadir, save_processed_image=''):

    image = cv2.imread(filepath)
    print "processing %s" % filepath
    dirname, filename =os.path.split(filepath)
    diods_on = find_ON_diods(image, dirname=datadir, filename=filename)
    diods_off = find_OFF_diods(image, dirname=datadir, filename=filename)

    diod_state_pos = [(d[1], d, True) for d in diods_on]
    diod_state_pos.extend([(d[1], d, False) for d in diods_off])

    diod_state_pos.sort()
    diod_state_pos = [x[1:] for x in diod_state_pos]
    
    #if save_processed_image:
    #    filename = save_processed_image % filename
    #    save_image(filename, dirname, image)        
    
    return diod_state_pos
    #for i in range(len(diod_state_pos)):
    #   print "Diod %s: %s" % (i+1, diod_state_pos[i][1] and "ON" or "OFF")
        
    
def take_photo(filepath):
    command = "raspistill -o %s -t 2000 -br 50 --awb flash -n" % filepath
    subprocess.call([command] , shell=True)
    time.sleep(5)

