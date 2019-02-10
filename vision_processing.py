import os
import cv2
import constants
import numpy as np
import time
import math

#os.system('v4l2-ctl -c exposure_auto=1 -c exposure_absolute=1 -d /dev/video0')
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
cap.set(cv2.CAP_PROP_FPS,60)

framerate = 30
fourcc = 0x00000021

#stream = cv2.VideoWriter('appsrc ! videoconvert ! video/x-raw,width=1280,height=720,framerate=30/1 ! omxh264enc bitrate=1000000 ! h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host=127.0.0.1 port=5004',fourcc,framerate,(1280,720))

def center(contour):
    moments = cv2.moments(contour)
    return (int(moments["m10"]/moments["m00"]), int(moments["m01"]/moments["m00"])) if moments[
"m00"] > 0 else (0, 0)

def isRectangle(contour):
    rectanglePoints = cv2.minAreaRect(contour)
    rectangle = np.int0(cv2.boxPoints(rectanglePoints))
    rectangularity = cv2.contourArea(rectangle)/cv2.contourArea(contour)
    print str(center(contour)) + " rectangularity: " + str(rectangularity) + " angle " + str(rectanglePoints[2])
    return 0.9 < rectangularity < 1.25

millis = int(round(time.time() * 1000))
frameCount = 0
fps = 0

def drawGuideLines(frame):
    lineThickness = 8
    cv2.line(frame, (0,720), (438, 100), (57, 255, 20), lineThickness)
    cv2.line(frame, (1280,720), (842, 100), (57, 255, 20), lineThickness)
    cv2.line(frame, (246,377), (346, 377), (57, 255, 20), lineThickness)
    cv2.line(frame, (935,377), (1035, 377), (57, 255, 20), lineThickness)

while cap.isOpened():
    ret, frame = cap.read()
    centers=[]	
    if ret:
	hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        lower_green = np.array(constants.LOWER_GREEN, dtype=np.uint8)
        upper_green = np.array(constants.UPPER_GREEN, dtype=np.uint8)
	drawGuideLines(frame)
	mask = cv2.inRange(hsv, lower_green, upper_green)
	contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	contours = [x for x in contours if cv2.contourArea(x) >= constants.MIN_CONTOUR_AREA and isRectangle(x)]
	contours = sorted(contours, key=lambda x: center(x)[0])
	#contours = [cv2.approxPolyDP(x, 0.1 * cv2.arcLength(x, True), True) for x in contours]
	cv2.drawContours(frame, contours, -1, (0, 0, 255), 2)
	contourSides = []
	for contour in contours:
	    rectangle = cv2.minAreaRect(contour)
	    angle = rectangle[2]
            side = ''
	    if angle >= constants.LEFT_CONTOUR_RANGE[0] and angle <= constants.LEFT_CONTOUR_RANGE[1]:
		side = 'left'
	    if angle >= constants.RIGHT_CONTOUR_RANGE[0] and angle <= constants.RIGHT_CONTOUR_RANGE[1]:
		side = 'right'
	    contourSides.append((contour, side))

	    cv2.putText(frame, side, center(contour), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
	    frameCount += 1
 
	currTime = int(round(time.time() * 1000))
	if (currTime - millis) >= 1000:
	    fps = frameCount/float(currTime - millis) * 1000
	    millis = currTime
	    frameCount = 0

	cv2.putText(frame, 'FPS: ' + str(fps), (5, 32), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
	cv2.imshow('frame', frame)
	if cv2.waitKey(1) == 27:
	    break
        #stream.write(frame)
	#print frame.shape
    else:
        break

# Release everything if job is finished
cap.release()
#stream.release()
