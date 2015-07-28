#!/usr/bin/python -tt
import os, sys

# Add cv2 library path
sys.path.append('/usr/local/lib/python2.7/site-packages')
# Loads the module for pi camera
os.system('sudo modprobe bcm2835-v4l2')

import math
import socket
import cv2
import time
import numpy as np
from settings import *

class img_procs:
    def __init__(self):
        # Get pi camera stream
        self.cap = cv2.VideoCapture(0)

        # Sets the resolution of the stream
        self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        # Does it show the GUI by default
        self.is_show_gui = False

        # Which img to show (if shows GUI)
        # 0 = frame, 1 = ROI, 2 = ROI2, 3 = ROI3, 4 = ROIg
        self.img_enum = 0

        # Does it print the commands of each motor
        self.is_print_cmd = True


    # Does it show the GUI for img processing
    def show_gui(self, is_show):
        self.is_show_gui = is_show

    # Does it print the left/right motor cmd
    # after processing it
    def print_cmd(self, is_print):
        self.is_print_cmd = is_print

    # Updates video camera stream and applies PID algorithm
    # to obtain motor rotation RPS
    def update(self):
        # Define our global variables from settings.py
        global PID_MULTI_THRES, KP, KI, KD, DERIVATOR, P_VAL, I_VAL, D_VAL, I_MAX, I_MIN, PID_TOTAL, ERROR, MOTOR_RPS, MOTOR_RPS_MIN, ROI_Y, ROI2_Y, ROI3_Y, ROI_START, ROI_DIF, MIDDLE, THRESH, AREA_THRESH, ROIg_Y, GREEN_P_VAL, GREEN_RANGE, GREEN_AREA_MAX, GREEN_AREA_MIN, US_MIN_DIST, RED_COLOR, GREEN_COLOR, BLUE_COLOR, YELLOW_COLOR

        # Gets frame from capture device
        ret, frame = self.cap.read()

        # Define our regions of interest
        ROI = frame [ROI_Y:(ROI_Y+40), 0:320]
        ROI2 = frame [ROI2_Y:(ROI2_Y+40), 0:320]
        ROI3 = frame [ROI3_Y:(ROI3_Y+40), 0:320]
        ROIg = frame [ROIg_Y:(ROIg_Y+80), 0:320] # Half the screen for green

        # Green filter
        for (lower, upper) in GREEN_RANGE:
            # Create numpy arrays from boundaries
            lower = np.array(lower, dtype='uint8')
            upper = np.array(upper, dtype='uint8')

            # Find the colors within the specific boundary and apply the mask
            mask = cv2.inRange(ROIg, lower, upper)
            ROIg = cv2.bitwise_and(ROIg, ROIg, mask=mask)

        # Converts ROI into Grayscale
        im_ROI = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
        im_ROI2 = cv2.cvtColor(ROI2, cv2.COLOR_BGR2GRAY)
        im_ROI3 = cv2.cvtColor(ROI3, cv2.COLOR_BGR2GRAY)
        im_ROIg = cv2.cvtColor(ROIg, cv2.COLOR_BGR2GRAY)

        # Apply THRESHold filter to smoothen edges and convert images to negative
        ret, im_ROI = cv2.threshold(im_ROI, THRESH, 255, 0)
        cv2.bitwise_not(im_ROI, im_ROI)

        ret, im_ROI2 = cv2.threshold(im_ROI2, THRESH, 255, 0)
        cv2.bitwise_not(im_ROI2, im_ROI2)

        ret, im_ROI3 = cv2.threshold(im_ROI3, THRESH, 255, 0)
        cv2.bitwise_not(im_ROI3, im_ROI3)

        ret, im_ROIg = cv2.threshold(im_ROIg, THRESH, 255, 0)
        # Do NOT bitwise_not im_ROIg

        # Reduces noise in image and dilate to increase white region (since its negative)
        erode_e = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3));
        dilate_e = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5));

        cv2.erode(im_ROI, erode_e)
        cv2.dilate(im_ROI, dilate_e)

        cv2.erode(im_ROI2, erode_e)
        cv2.dilate(im_ROI2, dilate_e)

        cv2.erode(im_ROI3, erode_e)
        cv2.dilate(im_ROI3, dilate_e)

        # Find contours
        # If we wanna show the images, we want to show
        # the UNALTERED (in the process of finding contours) images
        # so we can calibrate lighting
        if self.is_show_gui:
            contours, hierarchy = cv2.findContours(im_ROI.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            contours2, hierarchy = cv2.findContours(im_ROI2.copy() ,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            contours3, hierarchy = cv2.findContours(im_ROI3.copy() ,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            contoursg, hierarchy = cv2.findContours(im_ROIg.copy() ,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        # if we don't want to see the gui we don't do that
        # so its more effective
        elif not self.is_show_gui:
            contours, hierarchy = cv2.findContours(im_ROI,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            contours2, hierarchy = cv2.findContours(im_ROI2,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            contours3, hierarchy = cv2.findContours(im_ROI3,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            contoursg, hierarchy = cv2.findContours(im_ROIg,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        # Variables to store ALL contour_coordinates
        contour_no = 0
        contour_coordinates = []
        contourg_coordinates = []

        # List to store INTERESTED contour_coordinates
        contour_coordinates_priority = []
        contourg_coordinates_priority = []

        # Loop through each contours
        for j in contours, contours2, contours3:
            for i in j:
                # Gets the area of each contour
                area = cv2.contourArea(i)

                # Get dictionary keys for moments
                moments = cv2.moments (i)

                # We only want to get an area of > the threshold to prevent not usable contours
                if area>AREA_THRESH:
                    if moments['m00']!=0.0:
                        if moments['m01']!=0.0:
                            # We can calculate the centroid coordinates using this
                            cx = int(moments['m10']/moments['m00'])         # cx = M10/M00
                            cy = int(moments['m01']/moments['m00'])         # cy = M01/M00

                            # If we are showing our GUI
                            # then we needa draw circles
                            # indicating where we found the lines
                            if self.is_show_gui:
                                cv2.circle(frame, (cx, cy+ROI_START+(ROI_DIF*contour_no)), 4, BLUE_COLOR, -1)

                            # Store our centroid coordinates
                            contour_coordinates.append(cx)

                            # Find contours which are closest to the middle (so PID can be performed)
                            if len(contour_coordinates_priority) >= (contour_no+1):
                                if abs(MIDDLE-cx) <= abs(MIDDLE-contour_coordinates_priority[contour_no][0]):
                                    contour_coordinates_priority[contour_no] = cx

                            else:
                                contour_coordinates_priority.append(cx)

            # Variable to notify us which contour we're on (contours, contours2, or contours3)
        	contour_no += 1

        # Green filter
        for i in contoursg:
            area = cv2.contourArea(i)
            moments = cv2.moments(i)

            if area > GREEN_AREA_MIN and area < GREEN_AREA_MAX:
                if moments['m00'] != 0.0:
                    if moments['m01'] != 0.0:
                        cx = int(moments['m10']/moments['m00'])
                        cy = int(moments['m01']/moments['m00'])

                        # If we're showing our GUI
                        # needa indicate where we found
                        # the green box
                        if self.is_show_gui:
                            cv2.circle(frame, (cx, cy+ROIg_Y), 4, BLUE_COLOR, -1)

                        contourg_coordinates.append(cx)

                        # If we have previously found a green region
                        if len(contourg_coordinates_priority) >= 1:
                            # Since green is indicative of where we wanna travel,
                            # we'll calculate the PID from the contour
                            # furthest away from center
                            if abs(MIDDLE-cx) >= abs(MIDDLE-contourg_coordinates_priority[0]):
                                # We only care about the x coordinates
                                contourg_coordinates_priority[0] = cx

                        else:
                            contourg_coordinates_priority.append(cx)

            # If area is greater than GREEN_AREA_MAX
            # probs at the end already (all green)
            else:
                pass

        # Draw interested contour coordinates
        i = 0
        PID_TOTAL = 0
        if len(contourg_coordinates_priority) == 0:
            for c in contour_coordinates_priority:
                # Update PID code here
                ERROR = MIDDLE-c # Gets error between target value and actual value
                P_VAL = KP*ERROR # Gets proportional val
                D_VAL = KD*(ERROR-DERIVATOR) # Gets derivative val
                DERIVATOR = ERROR

                # Calculate integral of error
                I_VAL = I_VAL + ERROR

                if I_VAL > I_MAX:
                    I_VAL = I_MAX
                elif I_VAL < I_MIN:
                    I_VAL = I_MIN

                #  Calculate total PID value here
                PID_VAL = P_VAL + D_VAL + I_VAL

                # Strength of each PID is determined by its placing (Furthest = more, nearest = less)
                PID_TOTAL += (PID_MULTI_THRES/(i+1))*PID_VAL
                # Or PID_TOTAL += (PID_MULTI_THRES*(i+1))*PID_VAL

                # Since we have 3 different readings at three different locations
                # we give each reading a different weighting
                # the further it is the smaller affect it will have on the PID value
                # i is used to determine the weighting of each contour found
                i = i + 1

        # PID for green filter
        else:
            for c in contourg_coordinates_priority:
                ERROR = MIDDLE-c
                # Proportional should be enough for green
                P_VAL = KP*ERROR

                PID_VAL = P_VAL

                PID_TOTAL += PID_VAL*GREEN_P_VAL

            # Refreshes PID to prevent random movement
            ERROR = 0
            P_VAL = 0
            D_VAL = 0
            DERIVATOR = 0
            I_VAL = 0

        # Calculate motor rotation per second
        R_MOTOR_RPS = MOTOR_RPS+PID_TOTAL
        L_MOTOR_RPS = MOTOR_RPS-PID_TOTAL

        R_MOTOR_RPS = MOTOR_RPS_MIN if R_MOTOR_RPS < MOTOR_RPS_MIN else R_MOTOR_RPS
        L_MOTOR_RPS = MOTOR_RPS_MIN if L_MOTOR_RPS < MOTOR_RPS_MIN else L_MOTOR_RPS

        # Only want 2 decimal places
        self.rmotor_value = R_MOTOR_RPS = math.ceil(R_MOTOR_RPS * 100) / 100.0
        self.lmotor_value = L_MOTOR_RPS = math.ceil(L_MOTOR_RPS * 100) / 100.0

        # If it detects line(s) [green or black]
        if len(contour_coordinates_priority) >= 1 or len(contourg_coordinates_priority) >= 1:
            # Saves right motor command
            self.rmotor_cmd = 'right change_rps(' + str(R_MOTOR_RPS) + ')'
            if not self.is_show_gui:
                if self.is_print_cmd:
                    print 'right change_rps(' + str(R_MOTOR_RPS) + ')'

            # Saves left motor command
            self.lmotor_cmd = 'left change_rps(' + str(L_MOTOR_RPS) + ')'
            if not self.is_show_gui:
                if self.is_print_cmd:
                    print 'left change_rps(' + str(L_MOTOR_RPS) + ')'

        # Run forever until redetects the lines
        else:
            self.rmotor_cmd = 'right run_forever'
            self.lmotor_cmd = 'left run_forever'
            if not self.is_show_gui:
                if self.is_print_cmd:
                    print 'run_forever'

        # If we wanna see gui
        if self.is_show_gui:
            if frame is not None:
                if self.img_enum == 0:
                    cv2.imshow('pi camera', frame)

                elif self.img_enum == 1:
                    cv2.imshow('pi camera', im_ROI)

                elif self.img_enum == 2:
                    cv2.imshow('pi camera', im_ROI2)

                elif self.img_enum == 3:
                    cv2.imshow('pi camera', im_ROI3)

                elif self.img_enum == 4:
                    cv2.imshow('pi camera', im_ROIg)


            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.__del__()

    # Aligns robot with a horizontal (black) line
    # Is behind states if the line is behind robot or not
    def align_horizontal_line(self, is_behind):
        global H_ALIGN_THRES, CAMERA_WIDTH, CAMERA_HEIGHT, H_MIDDLE, ROIh_X, ROIh_HEIGHT, THRESH, AREA_THRESH

        # Gets frame from capture device
        ret, frame = self.cap.read()

        # Define our regions of interest
        ROI_LEFT = frame [CAMERA_HEIGHT-ROIh_HEIGHT:CAMERA_HEIGHT, 0:H_MIDDLE]
        ROI_RIGHT = frame [CAMERA_HEIGHT-ROIh_HEIGHT:CAMERA_HEIGHT, H_MIDDLE:CAMERA_WIDTH]

        # Converts ROI into Grayscale
        im_ROI_LEFT = cv2.cvtColor(ROI_LEFT, cv2.COLOR_BGR2GRAY)
        im_ROI_RIGHT = cv2.cvtColor(ROI_RIGHT, cv2.COLOR_BGR2GRAY)

        # Apply THRESHold filter to smoothen edges and convert images to negative
        ret, im_ROI_LEFT = cv2.threshold(im_ROI_LEFT, THRESH, 255, 0)
        cv2.bitwise_not(im_ROI_LEFT, im_ROI_LEFT)

        ret, im_ROI_RIGHT = cv2.threshold(im_ROI_RIGHT, THRESH, 255, 0)
        cv2.bitwise_not(im_ROI_RIGHT, im_ROI_RIGHT)

        # Reduces noise in image and dilate to increase white region (since its negative)
        erode_e = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3));
        dilate_e = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5));

        cv2.erode(im_ROI_LEFT, erode_e)
        cv2.dilate(im_ROI_LEFT, dilate_e)

        cv2.erode(im_ROI_RIGHT, erode_e)
        cv2.dilate(im_ROI_RIGHT, dilate_e)

        # Find contours
        contours_left, hierarchy = cv2.findContours(im_ROI_LEFT,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        contours_right, hierarchy = cv2.findContours(im_ROI_RIGHT,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        # Dictionary to store our coordinates
        blackline_found = {}
        blackline_found['left'] = False
        blackline_found['right'] = False

        # Loops through each contour
        for i in contours_left:
            # Gets the area of each contour
            area = cv2.contourArea(i)

            # Get dictionary keys for moments
            moments = cv2.moments (i)

            # We only want to get an area of > the threshold to prevent not usable contours
            if area>AREA_THRESH:
                if moments['m00']!=0.0:
                    if moments['m01']!=0.0:
                        # We can calculate the centroid coordinates using this
                        cx = int(moments['m10']/moments['m00'])         # cx = M10/M00
                        cy = int(moments['m01']/moments['m00'])         # cy = M01/M00

                        # We only care if there is a region of black within the line
                        # And we therefore know if we need to continue moving or not

                        # If its within the allow threshold limit
                        if abs(cy+(CAMERA_HEIGHT-ROIh_HEIGHT)-(CAMERA_HEIGHT-ROIh_HEIGHT+(ROIh_HEIGHT/2))) <= H_ALIGN_THRES:
                            blackline_found['left'] = True
                        break

        # Loops through each contour
        for i in contours_right:
            # Gets the area of each contour
            area = cv2.contourArea(i)

            # Get dictionary keys for moments
            moments = cv2.moments (i)

            # We only want to get an area of > the threshold to prevent not usable contours
            if area>AREA_THRESH:
                if moments['m00']!=0.0:
                    if moments['m01']!=0.0:
                        # We can calculate the centroid coordinates using this
                        cx = int(moments['m10']/moments['m00'])         # cx = M10/M00
                        cy = int(moments['m01']/moments['m00'])         # cy = M01/M00

                        # We only care if there is a region of black within the line
                        # And we therefore know if we need to continue moving or not
                        if abs(cy+(CAMERA_HEIGHT-ROIh_HEIGHT)-(CAMERA_HEIGHT-ROIh_HEIGHT+(ROIh_HEIGHT/2))) <= H_ALIGN_THRES:

                            blackline_found['right'] = True
                        break

        # Out const rps
        const_rps = 0.5

        if is_behind:
            const_rps = -0.5

        # If it doesn't detect a black line on left
        # Continue moving backwards/forwards depending
        # on parameter
        if not blackline_found['left']:
            self.lmotor_cmd = 'left change_rps('+str(const_rps)+')'
        elif blackline_found['left']:
            self.lmotor_cmd = 'left stop'

        # Same thing for right
        if not blackline_found['right']:
            self.rmotor_cmd = 'right change_rps('+str(const_rps)+')'
        elif blackline_found['right']:
            self.rmotor_cmd = 'right stop'

        if blackline_found['right'] and blackline_found['left']:
            self.is_aligned_hori = True

    def show_which_img(self, enum_var):
        self.img_enum = enum_var

    # Reset PID value to prevent random movement
    def reset_PID(self):
        global ERROR, P_VAL, D_VAL, DERIVATOR, I_VAL
        ERROR = 0
        P_VAL = 0
        D_VAL = 0
        DERIVATOR = 0
        I_VAL = 0

    def set_is_aligned_hori(self, is_aligned):
        self.is_aligned_hori = is_aligned

    def is_aligned_hori(self):
        return self.is_aligned_hori

    def get_rmotor_value(self):
        return self.rmotor_value

    def get_lmotor_value(self):
        return self.lmotor_value

    def get_rmotor_cmd(self):
        return self.rmotor_cmd

    def get_lmotor_cmd(self):
        return self.lmotor_cmd

    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows()

