from XboxController import XboxController
import pyautogui
import time
from pynput import mouse
import os

controller = XboxController()

for i in range( 10 ):
    print( "Calibrating in " + str( 5 - i ) + " seconds..." )
    time.sleep( 1 )

position = pyautogui.position()
reference_position = (
    pyautogui.size().width/2,
    pyautogui.size().height/2
)

max_speeds = (
    pyautogui.size().width/10,
    pyautogui.size().height/10
)

def onClick( x, y, button, pressed ):
    global controller
    if button == mouse.Button.left and pressed:
        controller.joystick.setRightJoystick( -1, 0 )
    if button == mouse.Button.left and not pressed:
        controller.joystick.setRightJoystick( 0, 0 )
    if button == mouse.Button.right and pressed:
        controller.joystick.setRightJoystick( 1, 0 )
    if button == mouse.Button.right and not pressed:
        controller.joystick.setRightJoystick( 0, 0 )

listener = mouse.Listener( on_click=onClick )
listener.start()

def constrain( value, min, max ):
    if value < min:
        return min
    if value > max:
        return max
    return value

while True:
    position = pyautogui.position()
    pyautogui.moveTo( reference_position[0], reference_position[1] )
    raw_speeds = (
        position[0] - reference_position[0],
        position[1] - reference_position[1]
    )

    calculated_speeds = (
        constrain( raw_speeds[0]/max_speeds[0], -1, 1 ),
        constrain( raw_speeds[1]/max_speeds[1], -1, 1 )*-1
    )

    controller.joystick.setLeftJoystick( calculated_speeds[0], calculated_speeds[1] )
    controller.apply()

    os.system( "cls" )
    print( calculated_speeds[0] )
    print( calculated_speeds[1] )

    time.sleep( 0.1 )