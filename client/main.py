# Include needed libraries
import config
import machine
import network
import time
import gc
import usocket as socket
import ussl as ssl
from soldered_inkplate10 import Inkplate

# Configuration
SLEEP_MINUTES = 5  # Time between updates in minutes
SLEEP_MS = SLEEP_MINUTES * 60000  # Convert to milliseconds

# Enter your WiFi credentials here
ssid = config.WIFI_SSID
password = config.WIFI_PASSWORD

# Logging function
def log(message):
    timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*time.localtime())
    print(f"[{timestamp}] {message}")

# Function which connects to WiFi
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        log("Starting WiFi connection...")
        sta_if.active(True)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    ip_info = sta_if.ifconfig()
    log(f"WiFi connected successfully. Network config: {ip_info}")

# Function that puts the ESP32 into deepsleep mode
def sleepnow(ms):
    log(f"Preparing for deep sleep. Duration: {ms}ms ({ms/60000:.1f} minutes)")
    log("Disabling WiFi before sleep...")
    network.WLAN(network.STA_IF).active(False)
    log("Entering deep sleep...")
    machine.deepsleep(ms)

# HTTP GET function
def http_get(url):
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
        log(f"Unsupported URI scheme: {scheme}")
        raise ValueError(f"Unsupported URI scheme: {scheme}")

    try:
        log(f"Attempting to connect to {host}:{port}...")
        for addressinfo in socket.getaddrinfo(host, port, af, socktype, proto):
            af, socktype, proto, cname, sockaddr = addressinfo
            s = socket.socket(af, socktype, proto)
            s.settimeout(socket_timeout)
            s.connect(sockaddr)
            if scheme == "https:":
                s = ssl.wrap_socket(s, server_hostname=host)
            break
    except Exception as e:
        log(f"HTTP connection error: {e}")
        sleepnow(SLEEP_MS)

    buffer = f"GET /{path} HTTP/1.0\r\nHost: {host}\r\nUser-Agent: micropython/1.2.0\r\n\r\n"
    try:
        log("Sending HTTP request...")
        s.write(buffer.encode('utf-8'))
    except Exception as e:
        log(f"HTTP request send error: {e}")
        sleepnow(SLEEP_MS)

    while True:
        try:
            data = s.read(1000)
        except Exception as e:
            log(f"HTTP response read error: {e}")
            sleepnow(SLEEP_MS)
        if data:
            res += data.decode('utf-8')
        else:
            break
    s.close()

    try:
        _, body = res.split("\r\n\r\n", 1)  # Split headers and body
        log(f"HTTP GET success: {url}")
        return body
    except Exception as e:
        log(f"HTTP response parse error: {e}")
        raise

# Log memory status
def log_memory():
    free_memory = gc.mem_free()
    log(f"Free memory: {free_memory} bytes")

def get_battery_level(voltageString):
    batteryMax = 4.40 
    batteryMin = 3.40 

    pctRemaining = (float(voltageString) - batteryMin) / (batteryMax - batteryMin) * 100
    return f"{int(pctRemaining)}%"

# Main task loop
def fetchAndDisplay():
    log_memory()

    try:
        do_connect()
        response = http_get(config.ENDPOINT)

        display = Inkplate(Inkplate.INKPLATE_1BIT)
        display.begin()
        display.setRotation(1)
        display.setTextSize(2)

        log("Updating display...")
        cnt = 30
        for x in response.split("<br />"):
            display.printText(40, 20 + cnt, x.upper())
            cnt += 20

        batteryVoltage = str(display.readBattery())
        batteryLevel = get_battery_level(batteryVoltage)
        display.printText(580, 1140, batteryLevel)
        log(f"Battery level: {batteryLevel}")

        display.display()
        log("Display updated successfully")
        log(f"Preparing for sleep cycle. Next update in {SLEEP_MINUTES} minutes")
        sleepnow(SLEEP_MS)

    except Exception as e:
        log(f"Error in fetchAndDisplay: {e}")
        sleepnow(SLEEP_MS)

# Main function
if __name__ == "__main__":
    # Check if this is a wake from deep sleep
    wake_reason = machine.reset_cause()
    if wake_reason == machine.DEEPSLEEP_RESET:
        log("Woke up from deep sleep")
    else:
        log("Fresh boot")

    log("Starting application...")
    log(f"Update interval: {SLEEP_MINUTES} minutes")
    fetchAndDisplay() 