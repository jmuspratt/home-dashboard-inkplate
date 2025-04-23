# This example will show you how to connect to WiFi
# get data from the internet and then print it

# Include needed libraries
import time
from soldered_inkplate10 import Inkplate

display = Inkplate(Inkplate.INKPLATE_1BIT)


# Main function
if __name__ == "__main__":
  # Create and initialize our Inkplate object in 1-bit mode
    # Initialize the display, needs to be called only once
    display.begin()

    # Clear the frame buffer
    display.clearDisplay()

    # This has to be called every time you want to update the screen
    # Drawing or printing text will have no effect on the display itself before you call this function
    display.display()

    # Get the battery reading as a string
    battery = str(display.readBattery())

    # Set text size to double from the original size, so we can see the text better
    display.setTextSize(2)

    # Print the text at coordinates 100,100 (from the upper left corner)
    display.printText(100, 100, "Battery voltage: " + battery + "V")

    # Show it on the display
    display.display()

    # Wait 5 seconds
    time.sleep(5)

    # Get the temperature reading, also as a string
    temperature = str(display.readTemperature())

    # Print the text at coordinates 100, 150, and also add the measurement unit
    display.printText(100, 150, "Temperature: " + temperature + "C")

    # Show it on the display
    display.display()