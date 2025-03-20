# Include needed libraries
import config
import machine
import network
import time
import gc
from soldered_inkplate10 import Inkplate

# Configuration variables
SLEEP_MINUTES = 5  # Sleep time in minutes
SLEEP_MS = int(SLEEP_MINUTES * 60 * 1000)  # Explicit integer conversion
WIFI_TIMEOUT = 15  # WiFi connection timeout in seconds
CPU_FREQUENCY = 80000000  # 80 MHz - lower frequency to save power
DEBUG = False  # Set to True only during development

# Use RTC memory to store loop count across deep sleep cycles
rtc = machine.RTC()
try:
    loopCount = int.from_bytes(rtc.memory(), 'little') if rtc.memory() else 0
except:
    loopCount = 0

# Enter your WiFi credentials here
ssid = config.WIFI_SSID
password = config.WIFI_PASSWORD

def debug_print(message):
    if DEBUG:
        print(message)

def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    
    if not sta_if.isconnected():
        debug_print("Connecting to network...")
        
        try:
            sta_if.config(pm=1)
            debug_print("WiFi power saving mode enabled")
        except Exception as e:
            debug_print(f"WiFi power saving not supported: {e}")
        
        sta_if.active(True)
        sta_if.connect(ssid, password)
        
        start_time = time.time()
        
        while not sta_if.isconnected():
            if time.time() - start_time > WIFI_TIMEOUT:
                debug_print("WiFi connection timeout")
                return False
            time.sleep(1)
            
    return True

def sleepnow(ms=None):
    global loopCount
    if ms is None:
        ms = SLEEP_MS
    ms = int(ms)
    
    debug_print(f"Received ms in sleepnow(): {ms} (Type: {type(ms)})")
    debug_print(f"Going to sleep for {ms} ms ({ms / 60000:.1f} minutes)")

    rtc.memory(loopCount.to_bytes(4, 'little'))
    network.WLAN(network.STA_IF).active(False)
    machine.freq(CPU_FREQUENCY)
    
    # Commenting out deep sleep for debugging
    machine.deepsleep(ms)

def http_get(url):
    import usocket as socket
    import ussl as ssl
    af = socket.AF_INET
    proto = socket.IPPROTO_TCP
    socktype = socket.SOCK_STREAM
    socket_timeout = 10

    scheme, _, host, path = url.split("/", 3)
    port = 443 if scheme == 'https:' else 80

    s = None
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
        debug_print(f"HTTP connection error: {e}")
        if s:
            s.close()
        sleepnow()

    buffer = f"GET /{path} HTTP/1.0\r\nHost: {host}\r\nUser-Agent: micropython/1.2.0\r\n\r\n"
    try:
        s.write(buffer.encode('utf-8'))
    except Exception as e:
        debug_print(f"HTTP request send error: {e}")
        s.close()
        sleepnow()

    chunks = []
    try:
        while True:
            data = s.read(1024)
            if not data:
                break
            chunks.append(data)
    except Exception as e:
        debug_print(f"HTTP response read error: {e}")
        s.close()
        sleepnow()
    
    s.close()
    response = b''.join(chunks).decode('utf-8')
    
    try:
        _, body = response.split("\r\n\r\n", 1)
        debug_print("HTTP GET success")
        return body
    except Exception as e:
        debug_print(f"HTTP response parse error: {e}")
        return ""
    
def main():
    global loopCount
    while True:  # Keeps running indefinitely
        loopCount += 1
        debug_print(f"Starting loop {loopCount}")
        
        machine.freq(CPU_FREQUENCY)
        gc.collect()
        
        try:
            if not do_connect():
                continue  # Skip to the next iteration if WiFi fails
                
            response = http_get(config.ENDPOINT)
            debug_print(f"Response from HTTP request: {response[:200]}")
            
            network.WLAN(network.STA_IF).active(False)
            display = Inkplate(Inkplate.INKPLATE_1BIT)
            display.begin()
            display.setRotation(1)
            display.setTextSize(2)

            cnt = 30
            for x in response.split("<br />"):
                display.printText(40, 20 + cnt, x.upper())
                cnt += 20

            batteryVoltage = str(display.readBattery())
            batteryMessage = f"{batteryVoltage}V"
            display.printText(580, 1140, batteryMessage)

            debug_print("Updating display now...")
            display.display()
            debug_print("Display update complete.")

            time.sleep(SLEEP_MS / 1000)  # Simulates periodic execution without deep sleep

        except Exception as e:
            debug_print(f"Error in main loop: {e}")

# ✅ Ensure `main()` runs when `main.py` starts
if __name__ == "__main__":
    main()