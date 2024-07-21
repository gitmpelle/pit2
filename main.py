# Complete project details at https://RandomNerdTutorials.com
# import boot
rev = '072024-001'
from machine import Pin, ADC, WDT, SoftI2C
from time import sleep,sleep_ms
import time, json, ina219
import ntptime
rtc = machine.RTC()
from servo import Servo
import ubinascii

zero_cross_count = 0 # global variable
start = 0
startTmr = 5
led = Pin(2, Pin.OUT)
swStart = Pin(23, Pin.OUT)
pwr = Pin(16, mode = Pin.IN, pull = Pin.PULL_UP)
rain = Pin(2, mode = Pin.IN, pull = Pin.PULL_UP)
motor=Servo(pin=22) # A changer selon la broche utilisée

i = SoftI2C(scl=Pin(5), sda=Pin(4))
print("I2C Bus Scan: ", i.scan(), "\n")
 
sensor = ina219.INA219(i)
sensor.set_calibration_16V_400mA()

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v

swStart.value(0)
Rain = False
def getTime():
        timestamp=rtc.datetime()
        timestring="%04d-%02d-%02d %02d:%02d:%02d"%(timestamp[0:3] +  timestamp[4:7])
        return f'{timestring[0:20]}'
    
def zero_handle_interrupt(irq):
  global zero_cross_count, Rain
  zero_cross_count += 1
  print(f"interrupt({irq})")
  
def rain_handle_interrupt(irq):
    global  Rain, client
    
    if not Rain:
        Rain = True
   
def sub_cb(topic, msg):
  global pot
  
  print((topic, msg))
  if topic == b'notification' and msg == b'received':
    print('ESP received hello message')
    
  if msg == b'OTA':
     #ota_updater() 
     pass
  if msg == b'START':
     startGen() 
     pass   

  if msg == b'RESET':
     machine.reset() 
     pass 

  if msg == b'LEVEL':
     val = pot.read()
     print(f"val = {val * (3.3 / 4095)} V")
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

# try:
#   client = connect_and_subscribe()
# except OSError as e:
#   restart_and_reconnect()

global client_id, mqtt_server, topic_sub, topic_pub, port, mqpassword, mquser
client = connect_and_subscribe()
msg = b'boot'
client.publish(topic_pub, msg)
gc.collect()
print(f"{getTime()} {gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())}")

gc.collect()
# Non-blocking wait for message

#pwr.irq(trigger=Pin.IRQ_RISING, handler=zero_handle_interrupt)
rain.irq(trigger=Pin.IRQ_RISING, handler=rain_handle_interrupt)

def startGen():
        global zero_cross_count, motor
        
        motor.move(0) # tourne le servo à 0°
        time.sleep(0.3)
        motor.move(90) # tourne le servo à 90°
        time.sleep(0.3)
        motor.move(180) # tourne le servo à 180°
        time.sleep(0.3)
        motor.move(90) # tourne le servo à 90°
        time.sleep(0.3)
        motor.move(0) # tourne le servo à 0°
        time.sleep(0.3)
        #Start
        swStart.value(1)
        zero_cross_count = 0
        #Start Timeout
        timeout = 10000
        start = time.ticks_ms()

        while True:
          diff = time.ticks_diff(time.ticks_ms(), start)
          
          if diff > timeout:
            print('Start Timeout')
            print(f'AC not detected!')
            swStart.value(0) #stop
            break

          if zero_cross_count > 100:
            print(f'AC detected!')
            swStart.value(0) #stop
            break

          print(f'zero_cross_count: {zero_cross_count}')
          led.value(1)
          sleep_ms(100)
          led.value(0)
          sleep_ms(100)

rc = machine.reset_cause()
print('Reset Cause = ', rc)
wlan_mac = station.config('mac')
mac = ubinascii.hexlify(wlan_mac).decode().upper()
wdt = WDT(timeout=6000)  # enable it with a timeout of 6s
wdt.feed()
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
        # current is returned in milliamps
        print("Current       / mA: %8.3f" % (sensor.current))
        message = {
        'TIME':getTime(),
        'rainmsg':rainmsg,
        'level':sensor.current,
        'mac':mac,
        'rev':rev,
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



