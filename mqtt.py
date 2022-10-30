import time
import board
import busio
from digitalio import DigitalInOut
from digitalio import Direction
import json
from adafruit_bus_device.i2c_device import I2CDevice
import community_tca9534


# ESP32 AT
from adafruit_espatcontrol import (
    adafruit_espatcontrol,
    adafruit_espatcontrol_wifimanager,
)

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Debug Level
# Change the Debug Flag if you have issues with AT commands
debugflag = False


RX = board.GP5
TX = board.GP4
resetpin = DigitalInOut(board.GP20)
rtspin = False
uart = busio.UART(TX, RX, baudrate=115200, receiver_buffer_size=2048, timeout=0.1)
status_light = None

# Create I2C bus.
i2c = busio.I2C(board.GP15, board.GP14)

# Create bus-expander instance.
tca9534 = community_tca9534.TCA9534(i2c)

# Set GPIO PORT configuration for relays (all OUTPUT)
port_mode_arr = [0,0,0,0,0,0,0,0]
port_mode = tca9534.set_port_mode(port_mode_arr)
# set all outputs to 0
tca9534.set_port(port_mode_arr)

print("ESP AT commands")
esp = adafruit_espatcontrol.ESP_ATcontrol(
    uart, 115200, reset_pin=resetpin, rts_pin=rtspin, debug=debugflag
)
esp.hard_reset()
wifi = adafruit_espatcontrol_wifimanager.ESPAT_WiFiManager(esp, secrets, status_light,attempts=5)


counter = 0
result = None #variable for cleaning data
TOPIC = "relay"
#set the topics 
wifi.topic_set("relay","feed")
#select which topic that you wanted to publish
wifi.IO_topics("test",aio_mode = False)
#Connect to Mosquitto MQTT (please remember to set the above settings before connect to mosquitto MQTT)
wifi.IO_Con("MQTT",ip = "192.168.10.254")

while True:    
    #Collect information from subscribe channel (test)
    data = wifi.MQTT_sub(timeout=1)
#     print (data)
    # Split related information to usable data
    if data:
        sub, result = wifi.clean_data(data,TOPIC,result)
        if result is not None:
            try:
                relay = json.loads(result)
                port_output = [int(relay['value_ch0']), int(relay['value_ch1']), int(relay['value_ch2']), int(relay['value_ch3']),
                               int(relay['value_ch4']), int(relay['value_ch5']), int(relay['value_ch6']), int(relay['value_ch7'])]
                print (repr(port_output))
                tca9534.set_port(port_output)
            except ValueError:
                print("problem not getting correct value")
                pass
    