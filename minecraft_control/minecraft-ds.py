import pyautogui
from XboxController import XboxController

controller = XboxController()

COLOR_CHECK = (959, 875)

colors = set()

actions = {
    "nothing": (254, 254, 254),
    "ccw": (84, 254, 84),
    "cw": (84, 254, 254),
    "front": (254, 254, 84),
    "back": (254, 84, 254),
    "left": (68, 57, 58),
    "right": (254, 84, 84),
}

# You can setup this by loading the minecraft bedrock world and going to positions 536 74 154 in the minecraft world
# You may have to resetup the colors of each actions, as well as the position of the pixel to check

print( "start" )

while True:
    try:
        color = pyautogui.pixel(*COLOR_CHECK)
        for action, c in actions.items():
            if color == c:
                print(action)
                if action == "ccw":
                    controller.joystick.setRightJoystick( -1, 0 )
                    controller.joystick.setLeftJoystick( 0, 0 )
                elif action == "cw":
                    controller.joystick.setRightJoystick( 1, 0 )
                    controller.joystick.setLeftJoystick( 0, 0 )
                elif action == "front":
                    controller.joystick.setRightJoystick( 0, 0 )
                    controller.joystick.setLeftJoystick( 0, 1 )
                elif action == "back":
                    controller.joystick.setRightJoystick( 0, 0 )
                    controller.joystick.setLeftJoystick( 0, -1 )
                elif action == "left":
                    controller.joystick.setLeftJoystick( -1, 0 )
                    controller.joystick.setRightJoystick( 0, 0 )
                elif action == "right":
                    controller.joystick.setLeftJoystick( 1, 0 )
                    controller.joystick.setRightJoystick( 0, 0 )
                elif action == "nothing":
                    controller.joystick.setLeftJoystick( 0, 0 )
                    controller.joystick.setRightJoystick( 0, 0 )
        controller.apply()
    except Exception as e:
        print(e)