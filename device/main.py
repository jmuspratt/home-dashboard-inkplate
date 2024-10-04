# This example will show you how to connect to WiFi
# get data from the internet and then print it

# Include needed libraries
import config
import machine
import network
import os
import time
import urequests

from time import sleep
from soldered_inkplate10 import Inkplate


# Enter your WiFi credentials here
ssid = config.WIFI_SSID
password = config.WIFI_PASSWORD

# Function which connects to WiFi
# More info here: https://docs.micropython.org/en/latest/esp8266/tutorial/network_basics.html
def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("connecting to network...")
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    print("network config:", sta_if.ifconfig())

# Function that puts the esp32 into deepsleep mode
def sleepnow(ms=600000):
    import machine
        
    # put the device to sleep [Down param not implemented here yet]
    # do_connect("Down") 
    print("Debug: Going to Sleep for:", ms, "(ms)")
    machine.deepsleep(ms)
    # After wake from deepsleep state, boots and runs boot.py, main.py
    # This script is generally saved as main.py on esp32 spiflash filesystem
    

# https://github.com/daemonhorn/inkplate10-weather/blob/main/NOAA_Weather.py
def http_get(url):
    import usocket as socket
    import ussl as ssl
    af = socket.AF_INET
    proto = socket.IPPROTO_TCP
    socktype = socket.SOCK_STREAM
    socket_timeout = 10 # seconds

    res = ""
    scheme, _, host, path = url.split("/", 3)
    #print("scheme: %s, host: %s, path: %s" % (scheme, host, path))
    #print("url: %s" % url)
    
    if scheme == 'https:':
        port = 443
    elif scheme == 'http:':
        port = 80
    else:
        raise ValueError("Unsupported URI scheme (%s) in url (%s), only http/https supported" % (scheme,url))
    
    for addressinfo in socket.getaddrinfo(host, port, af, socktype, proto):
        af, socktype, proto, cname, sockaddr = addressinfo
        #print(".getaddrinfo() complete: (%s)" % str(addressinfo))
        try:
            s = socket.socket(af, socktype, proto)
        except OSError as msg:
            s = None
            continue
        s.settimeout(socket_timeout)
        try:
            s.connect(sockaddr)
        except OSError as msg:
            s.close()
            s = None
            continue
        break
    if s is None:
        print("Failed to connect, Going to sleep...")
        sleepnow()
    
    if scheme == "https:":
        try:
            s = ssl.wrap_socket(s, server_hostname=host)
        except: 
            print("Failed to wrap socket in ssl, Going to sleep...")
            sleepnow()
        
    buffer =  "GET /%s HTTP/1.0\r\n" % (path)
    buffer += "Host: %s\r\n" % (host)
    buffer += "User-Agent: micropython/1.2.0 exampleweather esp32\r\n"
    buffer += "Accept: application/geo+json\r\n"
    # HTTP requests must end in an extra CRLF (aka \r\n)
    buffer += "\r\n"
#    print("Debug HTTP REQUEST: \r\n%s" % (buffer))
    try:
        s.write(bytes(buffer, "utf8"))
    except:
        print("Failed to send GET request, Going to sleep...")
        sleepnow()
    while True:
        try:
            data = s.read(1000)
        except:
            sleepnow()
        #print("data: %s" % str(data))
        if data:
            res += str(data, "utf8")
        else:
            break
    s.close()

     # Convert response to string and split off the headers
    _, body = res.split("\r\n\r\n", 1)  # Split the headers from the body

    return body




# def listSDCardFiles():
    # display = Inkplate(Inkplate.INKPLATE_1BIT)
    # display.begin()
    # display.clearDisplay()
    # display.display()

    # display.initSDCard()
    # display.SDCardWake()

    # time.sleep(3)

    # print(os.listdir("/sd"))
    
    # display.SDCardSleep()
    # display.display()





def fetchAndDisplayImage():

    print("fetchAndDisplayImage()")

    # First, connect
    do_connect()

    # Set up Inkplate (use Inkplate.INKPLATE_1BIT, _2BIT, or _3BIT depending on what you need)
    display = Inkplate(Inkplate.INKPLATE_1BIT)
    display.begin()
    display.clearDisplay()
    display.initSDCard()
    display.SDCardWake()
    time.sleep(5)


    # URL of the image to download (must be a BMP file)
    image_url = "http://dashboard.jamesmuspratt.com/img/picture.bmp"
    sd_card_path = "/sd/picture.bmp"
    

    # Download the image and save it to SD card
    response = urequests.get(image_url)
    print("response status was: ", response.status_code)

    # if response.status_code == 200:
        # with open(sd_card_path, 'wb') as f:
            # f.write(response.content)
    # response.close()
    # display.drawImageFile(0, 0, sd_card_path, False)

    display.drawImageFile(0, 0, sd_card_path)
    display.display()
    display.SDCardSleep()




def fetchAndDisplay():
   # Example placeholder for Inkplate task logic
    print("Executing Inkplate-related task")

    # First, connect
    do_connect()

    # Do a GET request to the micropython test page
    # If you were to do a GET request to a different page/resource, change the URL here
    response = http_get(config.ENDPOINT)

    # Create and initialize our Inkplate object in 1-bit mode``
    display = Inkplate(Inkplate.INKPLATE_1BIT)
    display.begin()

    #rotation int 0 = none 1 = 90deg clockwise rotation, 2 = 180deg, 3 = 270deg
    display.setRotation(3)
    # Set text size to double from the original size, so we can see the text better
    display.setTextSize(2)

    # Print response line by line
    cnt = 0
    for x in response.split("<br />"):
        display.printText(
            10, 20 + cnt, x.upper()
        )  # Default font has only upper case letters
        cnt += 20


    # Get the battery reading as a string
    battery = str(display.readBattery())
    # Print the text at coordinates 100,100 (from the upper left corner)
    display.printText(100, 900, "Battery voltage: " + battery + "V")

    # Display image from buffer in full refresh
    display.display()
    


def renderImage(local_path):
    display = Inkplate(Inkplate.INKPLATE_1BIT)
    display.begin()

    display.initSDCard()
    display.SDCardWake()
    # Wait 5 seconds to ensure initialization
    time.sleep(5)

#     # This prints all the files on card
#     print(os.listdir(""))

#    # Open the file text.txt in read only mode and print it's contents
#     f = open("sd/file.txt", "r")
#     print(f.read()) 
#     f.close() 

    display.drawImageFile(0, 0, local_path)

    # You can turn off the power to the SD card to save power
    display.SDCardSleep()

    # Show the image from the buffer
    display.display()



def loop(timer):
   print("Running loop function...")
   renderImage() 





# Main function
if __name__ == "__main__":

    renderImage("sd/diamonds.bmp")

    # # 300000ms = 5 minutes
    # loopPeriod = 300000

    # timer = machine.Timer(-1)  # Use virtual timer (-1 means not using hardware-specific timers)f
    # timer.init(period=loopPeriod, mode=machine.Timer.PERIODIC, callback=loop)

    # # Keep the script running indefinitely
    # while True:
    #     time.sleep(1)  # A small sleep to keep the main thread alive

    