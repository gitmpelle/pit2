bootFW = '072824-001'
from ota import OTAUpdater
import network, utime, machine, time
from umqtt.simple import MQTTClient
import ubinascii
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()
import json
import ubinascii
firmware_url = "https://raw.githubusercontent.com/gitmpelle/pit2/"

mqtt_server = "m15.cloudmqtt.com"
client_id = ubinascii.hexlify(machine.unique_id())
topic_sub = b"pit002"
topic_pub = b"pit002Msg"
port = 12638
mqpassword = "zaXkKvgMe7Hx"
mquser = "quoaqddx"

ssid = "TP-Link_2.4GHz"
password = "upperlove"

# ssid = "PELLE-2G"
# password = "upperlove"

last_message = 0
message_interval = 300
counter = 0

# disable all network interface first
network.WLAN(network.AP_IF).active(False)
network.WLAN(network.STA_IF).active(False)

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)
#*****************************************


# try to connecting
timeout = 10000
start = time.ticks_ms()


while station.isconnected() == False:
    diff = time.ticks_diff(time.ticks_ms(), start)
    if diff > timeout:
        print('Connecting Timeout')
        machine.reset() #added 072824
        break
    print('\rconnecting %s' % diff, end="\r")
    time.sleep_ms(1000)

print(station.ifconfig())
s = machine.unique_id()
idint = "".join(map(str, s))
print(idint)
wlan_mac = station.config('mac')
print(ubinascii.hexlify(wlan_mac).decode().upper())
ota_updater = OTAUpdater(ssid, password, firmware_url, "main.py")
ota_updater.download_and_install_update_if_available()
