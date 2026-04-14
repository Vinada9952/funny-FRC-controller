from flask import Flask
from XboxController import XboxController

app = Flask(__name__)
controller = XboxController()

team_number = int(input("Enter your team number: "))

actions = [
    "nothing",
    "ccw",
    "cw",
    "front",
    "back",
    "left",
    "right",
]

@app.route('/')
def verification():
    return str( team_number )

@app.route('/action/<action>')
def action(action):
    global controller
    try:
        if action in actions:
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
        print( e )


app.run(host='0.0.0.0', port=team_number)