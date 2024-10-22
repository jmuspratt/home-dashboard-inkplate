# This example will show you how to connect to WiFi
# get data from the internet and then print it

# Include needed libraries
import config
import machine
import network
import os
import time
import urequests
import usocket as socket
import ussl as ssl
 
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




def listFiles(): 
        # This prints all the files on card
    print(os.listdir(""))

    # f = open("sd/file.txt", "r")
    # print(f.read()) 
    # f.close() 



def fetch(url, filepath):    
    print("Fetching image from URL:", url)

    do_connect()


    af = socket.AF_INET
    proto = socket.IPPROTO_TCP
    socktype = socket.SOCK_STREAM
    socket_timeout = 10  # seconds

    # Split the URL to obtain the scheme, host, and path
    scheme, _, host, path = url.split("/", 3)

    if scheme == 'https:':
        port = 443
    elif scheme == 'http:':
        port = 80
    else:
        raise ValueError(f"Unsupported URI scheme ({scheme}) in URL ({url}), only http/https supported")

    # Resolve host and connect
    for addressinfo in socket.getaddrinfo(host, port, af, socktype, proto):
        af, socktype, proto, _, sockaddr = addressinfo
        try:
            s = socket.socket(af, socktype, proto)
            s.settimeout(socket_timeout)
            s.connect(sockaddr)
            break
        except OSError:
            s = None
            continue

    if s is None:
        raise ConnectionError("Failed to connect to the server.")

    # Wrap the socket in SSL if needed
    if scheme == "https:":
        try:
            s = ssl.wrap_socket(s, server_hostname=host)
        except:
            raise ConnectionError("Failed to wrap socket in SSL.")
        
    # Send the HTTP GET request
    buffer = f"GET /{path} HTTP/1.0\r\n"
    buffer += f"Host: {host}\r\n"
    buffer += "User-Agent: micropython/1.2.0 inkplate esp32\r\n"
    buffer += "Accept: */*\r\n"  # Allow any content
    buffer += "Connection: close\r\n"  # Ensure server closes connection after response
    buffer += "\r\n"

    try:
        s.write(bytes(buffer, "utf8"))
    except:
        raise ConnectionError("Failed to send GET request.")

    # Read the response headers
    headers = b""
    while True:
        data = s.read(1)
        if not data or headers.endswith(b"\r\n\r\n"):
            break
        headers += data

    # Split headers from the body and process Content-Length if available
    headers_str = headers.decode('utf8')
    header_lines = headers_str.split("\r\n")
    content_length = None
    for line in header_lines:
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":")[1].strip())

    # Check for HTTP status code 200 (OK)
    if "200 OK" not in headers_str:
        s.close()
        raise ValueError("Failed to download image, server responded with an error.")

    print("File list:")
    print(os.listdir("/sd"))

    # Open the file to write the BMP image
    try:
        with open(filepath, 'wb') as f:
            if content_length:
                # If Content-Length is provided, read exactly that many bytes
                bytes_remaining = content_length
                while bytes_remaining > 0:
                    chunk_size = min(512, bytes_remaining)
                    data = s.read(chunk_size)
                    if not data:
                        break
                    f.write(data)
                    bytes_remaining -= len(data)
            else:
                # If Content-Length is not provided, read until the connection is closed
                while True:
                    data = s.read(512)  # Read in chunks
                    if not data:
                        break
                    f.write(data)
    except OSError as e:
        print("Failed to write to SD card:", e)
        return

    # Close the socket
    s.close()

    print(f"Image saved to {filepath}")

    # display.SDCardSleep()


def render(filepath):
    print("Rendering image")

    display.clearDisplay()
    display.display()

    try:
        print('SD card listing:', os.listdir("/sd"))
        print("Drawing image...")
        display.drawImageFile(0, 0, filepath, False)
        display.display()
    except Exception as e:
        print("Failed to read image file:", e)

    # display.SDCardSleep()


def fetchAndRender(url, filepath):
    fetch(url, filepath) 
    render(filepath)


def loop(timer):
    print("Running loop function...")
    url = "https://dashboard.jamesmuspratt.com/img/1.bmp"
    filepath = "/sd/1.bmp"
    fetchAndRender(url, filepath)



# Main function
if __name__ == "__main__":

    url = "https://dashboard.jamesmuspratt.com/img/1.bmp"
    filepath = "/sd/1.bmp"

    # Global initialization
    display = Inkplate(Inkplate.INKPLATE_1BIT)
    display.begin()

    # Clear
    display.clearDisplay()
    display.display()

    # Initialize SD card once
    if not display.initSDCard():
        raise OSError("Failed to initialize SD card")
    time.sleep(1)
    display.SDCardWake()

    # display.initSDCard()
    # time.sleep(2)
    # display.SDCardWake()
    # time.sleep(2)

    fetchAndRender(url, filepath)



    # # 300000ms = 5 minutes
    # loopPeriod = 300000

    # timer = machine.Timer(-1)  # Use virtual timer (-1 means not using hardware-specific timers)f
    # timer.init(period=loopPeriod, mode=machine.Timer.PERIODIC, callback=loop)

    # # Keep the script running indefinitely
    # while True:
    #     time.sleep(1)  # A small sleep to keep the main thread alive

    