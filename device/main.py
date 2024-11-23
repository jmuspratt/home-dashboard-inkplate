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
        with open('/sd/log.txt', 'a') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Failed to write log to SD card: {e}")

# Function which connects to WiFi
def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print("Connecting to network...")
        log_to_file("Connecting to network...")
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    ip_info = sta_if.ifconfig()
    print(f"Network config: {ip_info}")
    log_to_file(f"Network config: {ip_info}")

# Function that puts the ESP32 into deepsleep mode
def sleepnow(ms=600000):
    log_to_file(f"Going to sleep for {ms} ms")
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
    batterMax = 4.33
    batteryMin = 3.08

    pctRemaining = (float(voltageString) - batteryMin) / (batterMax - batteryMin) * 100
    return f"{pctRemaining:.2f}%"

# Main task loop
def fetchAndDisplay():
    global loopCount
    loopCount += 1
    log_to_file(f"Starting loop {loopCount}")
    log_memory()

    try:
        do_connect()
        response = http_get(config.ENDPOINT)

        display = Inkplate(Inkplate.INKPLATE_1BIT)
        display.begin()
        display.setRotation(1)
        display.setTextSize(2)

        cnt = 30
        for x in response.split("<br />"):
            display.printText(40, 20 + cnt, x.upper())
            cnt += 20

        # outpu message with format "3.36V (29%)"
        batteryVoltage = str(display.readBattery())
        batteryLevel = get_battery_level(batteryVoltage)
        batteryMessage = f"{batteryVoltage}V ({batteryLevel})"
        display.printText(580, 1140, batteryMessage)

        display.printText(580, 1160, f"Refresh count: {loopCount}")
        display.display()
        
        log_to_file(f"Display updated successfully.")
    except Exception as e:
        log_to_file(f"Error in fetchAndDisplay: {e}")

# Main function
if __name__ == "__main__":
    try:
        # Initialize SD card
        display = Inkplate()
        display.initSDCard()
        log_to_file("SD card initialized successfully.")
    except Exception as e:
        log_to_file(f"Failed to initialize SD card: {e}")

    loopFrequency = 5  # in minutes
    loopTime = loopFrequency * 60000  # convert to milliseconds

    timer = machine.Timer(-1)  # Use virtual timer
    timer.init(period=loopTime, mode=machine.Timer.PERIODIC, callback=lambda t: fetchAndDisplay())

    while True:
        time.sleep(1)