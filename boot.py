bootFW = '101524-001'
from ota import OTAUpdater
import network, utime, machine, time, os
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
import urequests

# disable all network interface first
network.WLAN(network.AP_IF).active(False)
network.WLAN(network.STA_IF).active(False)

# MQTT login info
mqtt_server = "m15.cloudmqtt.com"
client_id = ubinascii.hexlify(machine.unique_id())
port = 12638
mqpassword = "zaXkKvgMe7Hx"
mquser = "quoaqddx"

last_message = 0
message_interval = 300
counter = 0

def onlinePing():
    try:
        response = urequests.get("http://www.google.com")
        if response.status_code == 204:
            print("online")
            return True
        elif response.status_code == 200:
            print("portal")
            return True
        else:
            print("offline")
            return False
    except:
        time.sleep(10)
        print("No internet")
        return False

#*****************************************

# Set up the Wi-Fi networks you want to try to connect to
networks = [("cell", "upperlove"),("TP-Link_2.4GHz", "upperlove"), ("PELLE-2G", "upperlove"), ("NETGEAR19", "jollypotato823")]

# Attempt to connect to each network in order
for ssid, psk in networks:
    print(f'ssid: {ssid} psk: {psk}')
    # disable all network interface first
    network.WLAN(network.AP_IF).active(False)
    network.WLAN(network.STA_IF).active(False)    
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(ssid, psk)

    # Wait for the connection to succeed or fail
    for _ in range(20):
        if station.isconnected():
            print("Connected to", ssid)
            break
        else:
            time.sleep(0.5)
            
    if onlinePing():
        print("Online")
        break

# Check for Connection Timeout
if station.isconnected() == False:
        print('Connecting Timeout')
        machine.reset() #added 072824
        
print(station.ifconfig())
s = machine.unique_id()
idint = "".join(map(str, s))
print(idint)
wlan_mac = station.config('mac')
print(ubinascii.hexlify(wlan_mac).decode().upper())
mac = ubinascii.hexlify(wlan_mac).decode().upper()

# Mqtt msg
topic_sub = f'{mac}'
topic_pub = f'{mac}_Msg'

# CHECK FOR OTA UPDATE
firmware_url = "https://raw.githubusercontent.com/gitmpelle/pit2/"
ota_updater = OTAUpdater(ssid, psk, firmware_url, "main.py")
ota_updater.download_and_install_update_if_available()
print('OTA UPDATE END')
