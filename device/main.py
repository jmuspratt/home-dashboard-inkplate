# This example will show you how to connect to WiFi
# get data from the internet and then print it

# Include needed libraries
import config
import machine
import network
import time
from soldered_inkplate10 import Inkplate



# make loopCount global and set to 0 
global loopCount
loopCount = 0


# Enter your WiFi credentials here
ssid = config.WIFI_SSID
password = config.WIFI_PASSWORD


def loop(timer):
    # increment loop count
    loopCount += 1
    print("Running main task...")
    print("Loop count is " + str(loopCount))
    display = Inkplate(Inkplate.INKPLATE_1BIT)
    display.begin()
    display.setTextSize(2)
    display.printText(600, 1160, str(loopCount))
    display.display()



# Main function
if __name__ == "__main__":

    loopFrequency = 5 # in minutes
    loopTime = loopFrequency * 60000 # convert to milliseconds

    # Create and start the timer
    timer = machine.Timer(-1)  # Use virtual timer (-1 means not using hardware-specific timers)
    timer.init(period=loopTime, mode=machine.Timer.PERIODIC, callback=loop)

    # Keep the script running indefinitely
    while True:
        time.sleep(1)  # A small sleep to keep the main thread alive

    