# Include needed libraries
import config
import machine
import network
import time
import gc
from soldered_inkplate10 import Inkplate

# Configuration variables
SLEEP_MINUTES = 25  # Sleep time in minutes
SLEEP_MS = SLEEP_MINUTES * 60 * 1000  # Convert to milliseconds
WIFI_TIMEOUT = 15  # WiFi connection timeout in seconds
CPU_FREQUENCY = 80000000  # 80 MHz - lower frequency to save power

# Use RTC memory to store loop count across deep sleep cycles
rtc = machine.RTC()
try:
    loopCount = rtc.memory()[0] if rtc.memory() else 0
except:
    loopCount = 0

# Enter your WiFi credentials here
ssid = config.WIFI_SSID
password = config.WIFI_PASSWORD

# Function which connects to WiFi with timeout and power management
def do_connect():
    import network
    sta_if = network.WLAN(network.STA_IF)
    
    if not sta_if.isconnected():
        print("Connecting to network...")
        
        # Try to set WiFi to power saving mode if supported
        try:
            sta_if.config(pm=1)
            print("WiFi power saving mode enabled")
        except Exception as e:
            print(f"WiFi power saving not supported: {e}")
        
        sta_if.active(True)
        sta_if.connect(ssid, password)
        
        # Add timeout to prevent battery drain if WiFi is unavailable
        start_time = time.time()
        
        while not sta_if.isconnected():
            if time.time() - start_time > WIFI_TIMEOUT:
                print("WiFi connection timeout")
                return False
            time.sleep(1)
            
    ip_info = sta_if.ifconfig()
    print(f"Network config: {ip_info}")
    return True

# Function that puts the ESP32 into deepsleep mode
def sleepnow(ms=SLEEP_MS):  # Use default from config variables
    global loopCount
    
    # Store loop count in RTC memory to persist through deep sleep
    rtc.memory(bytearray([loopCount]))
    
    # Disable WiFi before sleep to save power
    network.WLAN(network.STA_IF).active(False)
    
    # Reduce CPU frequency before sleep
    machine.freq(CPU_FREQUENCY)
    
    print(f"Going to sleep for {ms} ms ({ms/60000:.1f} minutes)")
    machine.deepsleep(ms)

# HTTP GET function with optimized connection handling
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
        print(f"Unsupported URI scheme: {scheme}")
        raise ValueError(f"Unsupported URI scheme: {scheme}")

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
        print(f"HTTP connection error: {e}")
        if s:
            s.close()
        sleepnow()

    buffer = f"GET /{path} HTTP/1.0\r\nHost: {host}\r\nUser-Agent: micropython/1.2.0\r\n\r\n"
    try:
        s.write(buffer.encode('utf-8'))
    except Exception as e:
        print(f"HTTP request send error: {e}")
        s.close()
        sleepnow()

    # More efficient data reading
    chunks = []
    try:
        while True:
            data = s.read(1024)  # Read larger chunks
            if not data:
                break
            chunks.append(data)
    except Exception as e:
        print(f"HTTP response read error: {e}")
        s.close()
        sleepnow()
    
    s.close()
    
    # Join all chunks at once instead of concatenating in the loop
    response = b''.join(chunks).decode('utf-8')

    try:
        _, body = response.split("\r\n\r\n", 1)  # Split headers and body
        print(f"HTTP GET success: {url}")
        return body
    except Exception as e:
        print(f"HTTP response parse error: {e}")
        raise

def get_battery_level(voltageString):
    batterMax = 4.40 
    batteryMin = 3.40 

    try:
        voltage = float(voltageString)
        pctRemaining = (voltage - batteryMin) / (batterMax - batteryMin) * 100
        # Cap between 0-100%
        pctRemaining = max(0, min(100, pctRemaining))
        # round to nearest percentage
        return f"{int(pctRemaining)}%"
    except:
        return "??%"

# Main function
def main():
    global loopCount
    loopCount += 1
    print(f"Starting loop {loopCount}")

    # Set CPU to lower frequency to save power
    machine.freq(CPU_FREQUENCY)
    
    # Force garbage collection before main task
    gc.collect()
    
    try:
        # Only initialize SD card if absolutely needed
        # display = Inkplate()
        # display.initSDCard()
        
        # Connect to WiFi - return to sleep if connection fails
        if not do_connect():
            sleepnow()
            return
            
        # Fetch data
        response = http_get(config.ENDPOINT)
        
        # Turn off WiFi immediately after data is fetched
        network.WLAN(network.STA_IF).active(False)

        # Initialize display (using 1-bit mode for power saving)
        display = Inkplate(Inkplate.INKPLATE_1BIT)
        display.begin()
        display.setRotation(1)
        display.setTextSize(2)

        cnt = 30
        for x in response.split("<br />"):
            display.printText(40, 20 + cnt, x.upper())
            cnt += 20

        # Output battery level
        batteryVoltage = str(display.readBattery())
        batteryLevel = get_battery_level(batteryVoltage)
        batteryMessage = f"{batteryLevel}"
        display.printText(580, 1140, batteryMessage)

        # Update display
        display.display()
        
        print("Display updated successfully.")

        # Go to sleep using the configured sleep time
        sleepnow()

    except Exception as e:
        print(f"Error in main function: {e}")
        # Sleep anyway on error
        sleepnow()

# Entry point
if __name__ == "__main__":
    # Run the main function once, then sleep
    main()
    
    # If execution somehow continues past main(), go to sleep
    sleepnow()