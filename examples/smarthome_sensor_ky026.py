# Smart Home sensor program
# MicroPython and ESP32 https://docs.micropython.org/en/latest/esp32/quickref.html
# https://docs.micropython.org/en/latest/library/espnow.html
# https://randomnerdtutorials.com/micropython-hc-sr04-ultrasonic-esp32-esp8266/
 
import network
import espnow

from machine import Pin
import time

########################################
# OWN MODULES
from adc_sub import ADC_substitute

########################################
# CONFIGURATION
dashboard_mac_address = b'\xA1\xB2\xC3\xD4\xE5\xF6' # MAC address of dashboard (Educaboard). Byte string format!

# Sensor
sensor_id = "Flame"                    # The sensor ID
pin_sensor_analog = 32                 # The flame analog value GPIO output pin
pin_sensor_digital = 33                # The flame digital value GPIO input pin

# LED
pin_led = 26                           # The LED pin

duration_on = 50                       # Duration of LED on in ms
duration_off = 2000                    # Duration of LED off in ms

# Battery
pin_battery = 34                       # The battery measurement input pin, ADC1_6

########################################
# OBJECTS
# ESP-NOW
sta = network.WLAN(network.STA_IF)     # Or network.AP_IF
sta.active(True)                       # WLAN interface must be active to send()/recv()

en = espnow.ESPNow()                   # ESP-NOW object
en.active(True)                        # Make ESP-NOW active

# Sensor
sensor_analog = ADC_substitute(pin_sensor_analog)
sensor_digital = Pin(pin_sensor_digital, Pin.IN)

# LED
led = Pin(pin_led, Pin.OUT)            # The on LED object

# Battery
battery = ADC_substitute(pin_battery)  # The battery object

########################################
# VARIABLES
# Previous values
prev_sensor_value_analog = -999        # The previous value from the sensor
prev_sensor_value_digital = -999       # The previous value from the sensor
prev_bat_pct = -1                      # The previous battery percentage value

next_time = 0                          # Non blocking flow control

########################################
# FUNCTIONS
def get_battery_percentage():          # The battery voltage percentage
    return 24                          # Replace with own math. Use function in adc_sub.py
                                       # Make the result an integer value, and avoid neg. and above 100% values


def led_blink():                       # The asymmetric LED blink
    global next_time
    
    if time.ticks_diff(time.ticks_ms(), next_time) > 0:
        if led.value() == 1:
            led.value(0)
            next_time = time.ticks_ms() + duration_off
        else:
            led.value(1)
            next_time = time.ticks_ms() + duration_on
            
########################################
# PROGRAM

# INITIALIZATION
# ESP-NOW
en.add_peer(dashboard_mac_address)     # Must add_peer() before send()
en.send(dashboard_mac_address, sensor_id + " ready", False)

print(sensor_id + " ready")

# MAIN (super loop)
while True:
    # Measure the battery percentage
    bat_pct = get_battery_percentage()
    
    # LED blink
    led_blink()
        
    # Check the sensor
    sensor_value_analog = sensor_analog.read_adc()
    sensor_value_digital = sensor_digital.value()

    # Send data if there is a change (this principle saves power)
    if bat_pct != prev_bat_pct or sensor_value_analog != prev_sensor_value_analog or sensor_value_digital != prev_sensor_value_digital:
        data_string = str(time.ticks_ms()) + '|' + str(bat_pct) + '|' + str(sensor_value_analog) + '|' + str(sensor_value_digital) # The data to send. CHANGE IT!
        
        print("Sending: " + data_string)
        try:
            en.send(dashboard_mac_address, data_string, False)
        except ValueError as e:
            print("Error sending the message: " + str(e))  
        
        # Update the previous values for use next time
        prev_sensor_value_analog = sensor_value_analog
        prev_sensor_value_digital = sensor_value_digital
    
    