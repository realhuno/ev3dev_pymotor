from resources import *

### Configuration for special functions ###
# Motor rotations to turn clockwise/anticlockwise by 90 degrees
MOTOR_ROTATION_TO_90_DEGREES = 215

# Motor RPS for avoiding object
OUTTER_MOTOR_AVOID_RPS = 0.775 # Decrease to increase circular radius
INNER_MOTOR_AVOID_RPS = 0.375

# Motor relative rotation to green lines
MOTOR_ROTATION_GREEN = 100
MOTOR_GREEN_FORWARD = 210

### Motor configuration ###
motors = {}

# By default it's left or right (you can change it in translate.py)
motors['left'] = ev3dev_pymotor.ev3dev_pymotor('outA')
motors['right'] = ev3dev_pymotor.ev3dev_pymotor('outB')

motors['left'].set_rps(0.5)
motors['right'].set_rps(0.5)

# Extra motor to act as a crane
motors['crane'] = ev3dev_pymotor.ev3dev_pymotor('outD')
motors['crane'].set_rps(0.5)
