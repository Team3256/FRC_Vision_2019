import time
from networktables import NetworkTables

# To see messages from networktables, you must setup logging
import logging

logging.basicConfig(level=logging.DEBUG)

NetworkTables.initialize()
sd = NetworkTables.getTable("SmartDashboard")
sd.putBoolean("visionEnabled", False)

i = 0
while True:
    print("dsTime:", sd.getNumber("robotTime", "N/A"))
    print("visionAngle:", sd.getNumber("visionAngle", "N/A"))
    print("visionVerticalAngle:", sd.getNumber("visionVerticalAngle", "N/A"))
    print("visionDistance:", sd.getNumber("visionDistance", "N/A"))

    sd.putBoolean("visionEnabled", not sd.getBoolean("visionEnabled", False))
    sd.putNumber("robotTime", i)
    time.sleep(2)
    i += 1
