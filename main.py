# Complete project details at https://RandomNerdTutorials.com
# import boot
rev = '101424-001'
from machine import Pin, ADC, WDT, SoftI2C
from time import sleep,sleep_ms
import time, json, ina219, os
import ntptime
rtc = machine.RTC()
import ubinascii

start = 0
startTmr = 5
rain = Pin(2, mode = Pin.IN, pull = Pin.PULL_UP)

i = SoftI2C(scl=Pin(5), sda=Pin(4))
print("I2C Bus Scan: ", i.scan(), "\n")
 
sensor = ina219.INA219(i)
sensor.set_calibration_16V_400mA()

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v

Rain = False

def getTime():
        timestamp=rtc.datetime()
        timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] +  timestamp[4:7])
        return f'{timestring[0:20]}'
    
def rain_handle_interrupt(irq):
    global  Rain, client
    
    if not Rain:
        Rain = True

def ota_updater(file):
    global ssid, psk, firmware_url
    ota_updater = OTAUpdater(ssid, psk, firmware_url, file)
    msg = ota_updater.fetch_latest_code()
    print(f'update: {msg}')
    print('Restarting device...')
    machine.reset()  # Reset the device to run the new code.

def sub_cb(topic, msg):
  global pot
  
  print('sub rcv:')
  print(f'*receive: {msg}  topic: {topic}  ')
  rcv = json.loads(msg)
  print(f'rcv: {rcv}')

# {"cmd":"ota", "file":"loop.py"}
# {"cmd":"reset}
  try:
      if rcv["cmd"] == "ota":
         file = rcv['file']
         ota_updater(file)
         print(f'update file : {file}')
         
      if rcv["cmd"] == "reset":
         machine.reset() 
         pass
        
  except Exception as e:
            print(e)
            pass
        
def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub, topic_pub, port, mqpassword, mquser
  client = MQTTClient(client_id, mqtt_server,user=mquser,password=mqpassword,port=port,keepalive=0)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub,qos=0)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  return client


def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

global client_id, mqtt_server, topic_sub, topic_pub, port, mqpassword, mquser
client = connect_and_subscribe()
msg = b'boot'
client.publish(topic_pub, msg)
gc.collect()
print(f"{getTime()} {gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())}")

gc.collect()

rain.irq(trigger=Pin.IRQ_RISING, handler=rain_handle_interrupt)

rc = machine.reset_cause()
print('Reset Cause = ', rc)
wlan_mac = station.config('mac')
mac = ubinascii.hexlify(wlan_mac).decode().upper()
wdt = WDT(timeout=6000)  # enable it with a timeout of 6s
wdt.feed()
message_interval = 60

if 'version.json' in os.listdir():    
    with open('version.json') as f:
        current_version = int(json.load(f)['version'])
    print(f"Current device firmware version is '{current_version}'")
else:
    current_version = 0
    
while True:
  try:
    gc.collect() 
    wdt.feed()      
    client.check_msg()
    if (time.time() - last_message) > message_interval or Rain:
        rainmsg = 0
        if Rain:
            Rain = False
            rainmsg = 1
        val = pot.read()
        level = f"{val * (3.3 / 4095)}"
        message = {
        'TIME':getTime(),
        'rainmsg':rainmsg,
        'level':sensor.current,
        'mac':mac,
        'rev':rev,
        'bootFW':bootFW,
        'versionJson':current_version,
        'ssid':ssid, 
        'counter':counter,
        'reset_cause':rc
        }
        payload = json.dumps(message)
        print(f"payload {payload}")
        client.publish(topic_pub, payload)
        last_message = time.time()
        counter += 1
        rc = 0
  except OSError as e:
    print(f'restart_and_reconnect() {e}')  
    restart_and_reconnect()



