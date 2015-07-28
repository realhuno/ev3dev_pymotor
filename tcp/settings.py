from resources import *

### Configuration for special functions ###
# Motor rotations to turn clockwise/anticlockwise by 90 degrees
MOTOR_ROTATION_TO_90_DEGREES = 215

# Motor RPS for avoiding object
OUTTER_MOTOR_AVOID_RPS = 0.81
INNER_MOTOR_AVOID_RPS = 0.40

### Motor configuration ###
motors = {}

# By default it's left or right (you can change it in translate.py)
motors['left'] = ev3dev_pymotor.ev3dev_pymotor('outA')
motors['right'] = ev3dev_pymotor.ev3dev_pymotor('outB')

motors['left'].set_rps(0.5)
motors['right'].set_rps(0.5)
