import os
import cv2
import constants
import numpy as np
import time
import math

from networktables import NetworkTables


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
#cap.set(cv2.CAP_PROP_FPS,30)

framerate = 30
fourcc = 0x00000021

stream = cv2.VideoWriter('appsrc ! videoconvert ! video/x-raw,width=1280,height=720,framerate=30/1 ! omxh264enc bitrate=1000000 ! h264parse ! rtph264pay config-interval=1 pt=96 ! udpsink host=127.0.0.1 port=5005',fourcc,framerate,(1280,720))

# NetworkTables

NetworkTables.initialize(server=constants.SERVER_IP)
sd = NetworkTables.getTable("SmartDashboard")

visionEnabled = True

def onKeyChanged(table, key, value, isNew):
    global visionEnabled
    if key == "visionEnabled":
        visionEnabled = value
        exposure = constants.VISION_EXPOSURE if value else constants.REGULAR_EXPOSURE
        os.system("v4l2-ctl -c exposure_auto=1 -c exposure_absolute={} -d /dev/video0".format(exposure))
    
sd.addEntryListener(onKeyChanged)

def center(contour):
    moments = cv2.moments(contour)
    return (int(moments["m10"]/moments["m00"]), int(moments["m01"]/moments["m00"])) if moments[
"m00"] > 0 else (0, 0)

def isRectangle(contour):
    rectanglePoints = cv2.minAreaRect(contour)
    rectangle = np.int0(cv2.boxPoints(rectanglePoints))
    rectangularity = cv2.contourArea(rectangle)/cv2.contourArea(contour)
    #print (str(center(contour)) + " rectangularity: " + str(rectangularity) + " angle " + str(rectanglePoints[2]))
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

def getAvg(firstX, secondX):
    return (firstX + secondX)/2

def getAngle(px):
    nx = (1.0/640.0) * (px - 639.5)
    vpw = 2* np.tan(constants.FIELD_OF_VIEW_X/2)
    x = vpw/2 * nx
    theta = np.arctan2(1,x) * (180/np.pi)
    return -(theta - 90)

def getVerticalAngle(py):
    ny = (1.0/360.0) * (359.5 - py)
    vph = 2.0 * np.tan(constants.FIELD_OF_VIEW_Y*np.pi/180.0/2.0)
    y = vph/2.0 * ny
    theta = np.arctan2(1,y) * (180.0/np.pi)
    return -(theta - 90)

def getDistanceFromTarget(thetaY):
    angleSum = thetaY + constants.CAMERA_ANGLE_DELTA
    d = (constants.CAMERA_HEIGHT_DELTA)/(np.tan(angleSum*np.pi/180.0))
    return d

def getHorizontalDisplacement(distanceFromTarget, thetaX):
    deltaX = np.tan(thetaX) * distanceFromTarget
    return deltaX

while cap.isOpened():
    ret, frame = cap.read()
    centers=[]
    if not ret:
        continue
    if not visionEnabled:
        drawGuideLines(frame)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == 27:
            break
        stream.write(frame)
        continue
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    lower_green = np.array(constants.LOWER_GREEN, dtype=np.uint8)
    upper_green = np.array(constants.UPPER_GREEN, dtype=np.uint8)
    mask = cv2.inRange(hsv, lower_green, upper_green)
    _, contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [x for x in contours if cv2.contourArea(x) >= constants.MIN_CONTOUR_AREA and isRectangle(x)]
    contours = sorted(contours, key=lambda x: -cv2.contourArea(x))
    if len(contours) >= 2:
        contours = contours[0:2]
        avgx = getAvg(center(contours[0])[0], center(contours[1])[0])
        avgy = getAvg(center(contours[0])[1], center(contours[1])[1])
        angle = getAngle(avgx)
        angleY = getVerticalAngle(avgy)
        distance = getDistanceFromTarget(angleY)
        sd.putNumber("visionAngle", angle)
        sd.putNumber("visionVerticalAngle", angleY)
        sd.putNumber("visionDistance", distance)
        cv2.putText(frame, 'Angle: ' + str(angle), (5, 67), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, 'Vertical Angle: ' + str(angleY), (5, 102), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, 'Distance: ' + str(distance), (5, 137), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
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
        sd.putNumber("visionFPS", fps)
    
    cv2.putText(frame, 'FPS: ' + str(fps), (5, 32), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    drawGuideLines(frame)
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) == 27:
        break
    stream.write(frame)

# Release everything if job is finished
cap.release()
stream.release()
