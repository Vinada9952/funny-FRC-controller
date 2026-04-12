from XboxController import XboxController
import time
import math
import speech_recognition as sr

controller = XboxController()

def listen( language: str = "en-US" ):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                r.adjust_for_ambient_noise( 1 )
            except AssertionError:
                pass
            # r.adjust_for_ambient_noise( 1 )
            audio_data = r.listen( source=source, phrase_time_limit=10 )
        try:
            text = r.recognize_google( audio_data, language=language )
            text = str( text )
            return text
        except sr.UnknownValueError:
            return "not understood"
        except sr.RequestError:
            return "error"


controller = XboxController()


while True:
    print("Speak now...")
    listened = listen().lower()
    print(f"🎤 You said: '{listened}'")
    if listened == "forward":
        controller.joystick.setLeftJoystick(0.0, 1.0)
    elif listened == "backward":
        controller.joystick.setLeftJoystick(0.0, -1.0)
    elif listened == "left":
        controller.joystick.setLeftJoystick(-1.0, 0.0)
    elif listened == "right":
        controller.joystick.setLeftJoystick(1.0, 0.0)
    elif listened == "stop":
        controller.reset()
    controller.apply()