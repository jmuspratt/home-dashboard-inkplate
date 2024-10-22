import config
import urequests
import network
from soldered_inkplate10 import Inkplate

# Initialize Inkplate
display = Inkplate(Inkplate.INKPLATE_1BIT)
display.begin()

# WiFi credentials
ssid = config.WIFI_SSID
password = config.WIFI_PASSWORD

# Function which connects to WiFi
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("connecting to network...")
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    print("network config:", sta_if.ifconfig())


def renderRemoteImage(url) :
    print("Fetching image..")
    response = urequests.get(url)
    print("Status code: ", response.status_code)

    if response.status_code == 200:
        image_data = bytearray(response.content)

        display.clearDisplay()
        display.display()
        display.drawBitmap(0, 0, image_data, 400, 300)

        display.display()
    else:
        print("Failed to fetch image")

    # Close the connection
    response.close()


# Main function
if __name__ == "__main__":
    do_connect()

    # URL of the image
    url = "https://dashboard.jamesmuspratt.com/img/1.bmp"
    renderRemoteImage(url)

