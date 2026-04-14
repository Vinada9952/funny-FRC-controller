import ntcore
import time

inst = ntcore.NetworkTableInstance.getDefault()
inst.startClient4("debug")
inst.setServer("127.0.0.1")

# 🔥 LE FIX
sub = ntcore.MultiSubscriber(inst, [""])

values = {}

def on_value(event):
    topic = event.data.topic
    value = event.data.value  # ✅ LA BONNE FAÇON

    register_value(topic, value)

def register_value( topic: ntcore.Topic, value: ntcore.Value):
    global values
    # print( value.type() )
    if value.type() == ntcore.NetworkTableType.kDouble:
        values[topic.getName()] = value.getDouble()
    if value.type() == ntcore.NetworkTableType.kString:
        values[topic.getName()] = value.getString()
    if value.type() == ntcore.NetworkTableType.kBoolean:
        values[topic.getName()] = value.getBoolean()
    # if value.type() == ntcore.NetworkTableType.kBooleanArray:
    #     values[topic.getName()] = value.getBooleanArray()
    # if value.type() == ntcore.NetworkTableType.kDoubleArray:
    #     values[topic.getName()] = value.getDoubleArray()
    # if value.type() == ntcore.NetworkTableType.kStringArray:
    #     values[topic.getName()] = value.getStringArray()
    # if value.type() == ntcore.NetworkTableType.kRaw:
    #     values[topic.getName()] = value.getRaw()

inst.addListener(
    sub,
    ntcore.EventFlags.kValueAll | ntcore.EventFlags.kImmediate,
    on_value
)

# debug connexion
def on_conn(event: ntcore.Event):
    print("CONNECTION:", event)

inst.addConnectionListener(True, on_conn)

print("Waiting...")
import json
import os
while True:
    os.system("cls")
    print(json.dumps( values, indent=4))
    time.sleep(1)
    