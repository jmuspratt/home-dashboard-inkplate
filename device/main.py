# This example will show you how to connect to WiFi
# get data from the internet and then print it

# Include needed libraries
import config
import machine
import network
import time
from soldered_inkplate10 import Inkplate

global loopCount 
loopCount = 0

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


def loop(timer):
   print("Running main task...")
   fetchAndDisplay() 




def fetchAndDisplay():
   # Example placeholder for Inkplate task logic
    print("Executing Inkplate-related task")

    # First, connect
    do_connect()

    # Do a GET request to the micropython test page
    # If you were to do a GET request to a different page/resource, change the URL here
    response = http_get(config.ENDPOINT)

    # Create and initialize our Inkplate object in 1-bit mode
    display = Inkplate(Inkplate.INKPLATE_1BIT)
    display.begin()

    #rotation int 0 = none 1 = 90deg clockwise rotation, 2 = 180deg, 3 = 270deg
    display.setRotation(1)
    # Set text size to double from the original size, so we can see the text better
    display.setTextSize(2)

    # Print response line by line
    cnt = 30
    for x in response.split("<br />"):
        display.printText(
            40, 20 + cnt, x.upper()
        )  # Default font has only upper case letters
        cnt += 20



    # Output battery level at bottom right of screen
    battery = str(display.readBattery())
    display.printText(620, 1140, battery + " V")

    global loopCount
    loopCount +=1 
    loopCountStr = str(loopCount)
    display.printText(620, 1160, "Refresh count: " + loopCountStr)

    
    # Display image from buffer in full refresh
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

    