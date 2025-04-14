# Include needed libraries
import config
import machine
import network
import time
import gc
from soldered_inkplate10 import Inkplate

global loopCount
loopCount = 0

# Enter your WiFi credentials here
ssid = config.WIFI_SSID
password = config.WIFI_PASSWORD

# Logging function for SD card
def log_to_file(message):
    try:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)  # Print to console
        with open('/sd/log.txt', 'a') as f:
            f.write(formatted_message + "\n")
    except Exception as e:
        error_msg = f"Failed to write log to SD card: {e}"
        print(error_msg)  # Print error to console

# Function which connects to WiFi
def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        log_to_file("Starting WiFi connection...")
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    ip_info = sta_if.ifconfig()
    log_to_file(f"WiFi connected successfully. Network config: {ip_info}")

# Function that puts the ESP32 into deepsleep mode (10 mins)
def sleepnow(ms=600000):
    log_to_file(f"Preparing for deep sleep. Duration: {ms}ms ({ms/60000:.1f} minutes)")
    log_to_file("Disabling WiFi before sleep...")
    network.WLAN(network.STA_IF).active(False)
    log_to_file("Entering deep sleep...")
    machine.deepsleep(ms)

# HTTP GET function
def http_get(url):
    import usocket as socket
    import ussl as ssl
    af = socket.AF_INET
    proto = socket.IPPROTO_TCP
    socktype = socket.SOCK_STREAM
    socket_timeout = 10  # seconds

    res = ""
    scheme, _, host, path = url.split("/", 3)
    
    if scheme == 'https:':
        port = 443
    elif scheme == 'http:':
        port = 80
    else:
        log_to_file(f"Unsupported URI scheme: {scheme}")
        raise ValueError(f"Unsupported URI scheme: {scheme}")

    try:
        log_to_file(f"Attempting to connect to {host}:{port}...")
        for addressinfo in socket.getaddrinfo(host, port, af, socktype, proto):
            af, socktype, proto, cname, sockaddr = addressinfo
            s = socket.socket(af, socktype, proto)
            s.settimeout(socket_timeout)
            s.connect(sockaddr)
            if scheme == "https:":
                s = ssl.wrap_socket(s, server_hostname=host)
            break
    except Exception as e:
        log_to_file(f"HTTP connection error: {e}")
        sleepnow()

    buffer = f"GET /{path} HTTP/1.0\r\nHost: {host}\r\nUser-Agent: micropython/1.2.0\r\n\r\n"
    try:
        log_to_file("Sending HTTP request...")
        s.write(buffer.encode('utf-8'))
    except Exception as e:
        log_to_file(f"HTTP request send error: {e}")
        sleepnow()

    while True:
        try:
            data = s.read(1000)
        except Exception as e:
            log_to_file(f"HTTP response read error: {e}")
            sleepnow()
        if data:
            res += data.decode('utf-8')
        else:
            break
    s.close()

    try:
        _, body = res.split("\r\n\r\n", 1)  # Split headers and body
        log_to_file(f"HTTP GET success: {url}")
        return body
    except Exception as e:
        log_to_file(f"HTTP response parse error: {e}")
        raise

# Log memory status
def log_memory():
    free_memory = gc.mem_free()
    log_to_file(f"Free memory: {free_memory} bytes")

def get_battery_level(voltageString):
    batterMax = 4.40 
    batteryMin = 3.40 

    pctRemaining = (float(voltageString) - batteryMin) / (batterMax - batteryMin) * 100
    # round to nearest percentage
    return f"{int(pctRemaining)}%"

# Main task loop
def fetchAndDisplay():
    global loopCount
    loopCount += 1
    log_to_file(f"Starting loop {loopCount}")
    log_memory()

    try:
        log_to_file("Attempting WiFi connection...")
        do_connect()
        
        log_to_file("Fetching data from endpoint...")
        response = http_get(config.ENDPOINT)

        log_to_file("Initializing display...")
        display = Inkplate(Inkplate.INKPLATE_1BIT)
        display.begin()
        display.setRotation(1)
        display.setTextSize(2)

        log_to_file("Updating display content...")
        cnt = 30
        for x in response.split("<br />"):
            display.printText(40, 20 + cnt, x.upper())
            cnt += 20

        # output battery level with format "4.0V (74%)"
        batteryVoltage = str(display.readBattery())
        batteryLevel = get_battery_level(batteryVoltage)
        batteryMessage = f"{batteryLevel}"
        display.printText(580, 1140, batteryMessage)
        log_to_file(f"Battery level: {batteryMessage}")

        log_to_file("Updating display...")
        display.display()
        log_to_file("Display updated successfully")

        # Sleep
        sleepMinutes = 25  # in minutes
        sleepTime = sleepMinutes * 60000  # convert to milliseconds
        log_to_file(f"Preparing for sleep cycle. Next update in {sleepMinutes} minutes")
        sleepnow(sleepTime)

    except Exception as e:
        log_to_file(f"Error in fetchAndDisplay: {e}")
        sleepnow()

# Main function
if __name__ == "__main__":
    try:
        # Initialize SD card
        log_to_file("Initializing SD card...")
        display = Inkplate()
        display.initSDCard()
        log_to_file("SD card initialized successfully")
    except Exception as e:
        log_to_file(f"Failed to initialize SD card: {e}")

    loopFrequency = 30  # in minutes
    loopTime = loopFrequency * 60000  # convert to milliseconds

    log_to_file(f"Setting up timer with {loopFrequency} minute interval")
    timer = machine.Timer(-1)  # Use virtual timer
    timer.init(period=loopTime, mode=machine.Timer.PERIODIC, callback=lambda t: fetchAndDisplay())

    log_to_file("Entering main loop")
    while True:
        time.sleep(1)