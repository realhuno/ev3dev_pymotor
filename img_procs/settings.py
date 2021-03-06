from fractions import Fraction

# Image settings
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

CAMERA_EXPOSURE_MODE = 'off'
CAMERA_SHUTTER_SPEED = 10096
CAMERA_AWB_MODE = 'off' # Autowhite balance
CAMERA_AWB_GAINS = (Fraction(101, 64), Fraction(323, 256))

# PID
KP = 0.0061
KI = 0.0027
KD = 0.005
DERIVATOR = 0

P_VAL = 0
I_VAL = 0
D_VAL = 0

I_MAX = 0.04
I_MIN = -I_MAX

PID_TOTAL = 0

ERROR = 0

# Motor speed
MOTOR_RPS = 0.65 # rotations per second
MOTOR_RPS_MIN = -1.33
# If line is on the right = negative value

# ROI Settings
ROI_Y = 190
BLACK_RANGE = [([25, 30, 20], [80, 115, 125])]
# Black line thresholding
MIDDLE = CAMERA_WIDTH/2
THRESH = 22 # Change threshold to lower if can't detect line; Change to higher if detects too many
AREA_THRESH = 850 # Minimum area before it's considered to be a black line

# Green filter thresholding
ROIg_Y = CAMERA_HEIGHT-60

GREEN_P_VAL = 0.83 # PID for green val
GREEN_RANGE = [([45, 70, 170], [85, 150, 215])] # HSV, use get_hsv.py to calibrate it
GREEN_AREA_THRESH = 200 # Area of contour before officially recognizing it
GREEN_THRESH = 35 #THRESH # Change to lower if can't detect line; change to higher if detects too many

# Used to determine if black line is straight (used for calibration after green box)
BLACKLINE_MIN_X = CAMERA_WIDTH/2-(CAMERA_WIDTH/12)
BLACKLINE_MAX_X = CAMERA_WIDTH/2+(CAMERA_WIDTH/12)

# Used to detect aluminium foil
ROIa_Y = 70 #camera_middle - half of this value till camera_middle + half of this value
ALUMINIUM_RANGE = [([35, 3, 200], [75, 20, 255])]
ALUMINIUM_AREA_THRESH = 350
ALUMINIUM_THRESH = 50 # Change to lower if can't detect line; change to higher if detects too many

# COLORS (BGR)
RED_COLOR = (43, 57, 192)
GREEN_COLOR = (113, 204, 46)
BLUE_COLOR = (219, 152, 52)
YELLOW_COLOR = (131, 130, 224)

