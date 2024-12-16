# TODO:
#	Log into Wifi
#	Send OSC
#	RGB LED feedback
#	G delta stop algorithm


import machine
import utime
 
# ADXL335 analog pins connected to Pico's ADC channels
X_PIN = 26
Y_PIN = 27
Z_PIN = 28
 
# Create ADC objects for each axis
adc_x = machine.ADC(machine.Pin(X_PIN))
adc_y = machine.ADC(machine.Pin(Y_PIN))
adc_z = machine.ADC(machine.Pin(Z_PIN))
 
gesture_initialized = False

Z_INITIALIZE = 1.0
X_INITIALIZE = 0.0
Y_INITIALIZE = 0.0
INITIALIZATION_BAND = 0.2
INITIALIZATION_TIME = 0.5
INIT_COUNT = 10
initialization_values = [[0.0, 0.0, 0.0]] * INIT_COUNT
initialization_pre = 0
initialization_index = 0
initialization_index_prev = 0

def read_acceleration(adc):
    # Read the ADC value and convert it to voltage
    voltage = adc.read_u16() * 3.3 / 65535
    # Convert the voltage to acceleration (assuming 3.3V supply)
    acceleration = (voltage - 1.65) / 0.330
    return acceleration
 
while True:
    # Read the acceleration values from the ADXL335
    x = read_acceleration(adc_x)
    y = read_acceleration(adc_y)
    z = read_acceleration(adc_z)
    
    initialization_values[initialization_index] = [x, y, z]
    initialization_index_prev - initialization_index
    initialization_index += 1
    if initialization_index >= INIT_COUNT:
        initialization_index = 0
    
    running = [0.0, 0.0, 0.0]
    #print(initialization_values)
    for i in range(INIT_COUNT):
        running[0] = running[0] + initialization_values[i][0] / INIT_COUNT
        running[1] = running[1] + initialization_values[i][1] / INIT_COUNT
        running[2] = running[2] + initialization_values[i][2] / INIT_COUNT
    print(running)
    
    if ((Z_INITIALIZE - INITIALIZATION_BAND) < running[2] < (Z_INITIALIZE + INITIALIZATION_BAND)) and \
        ((X_INITIALIZE - INITIALIZATION_BAND) < running[0] < (X_INITIALIZE + INITIALIZATION_BAND)) and \
        ((Y_INITIALIZE - INITIALIZATION_BAND) < running[1] < (Y_INITIALIZE + INITIALIZATION_BAND)):
        gesture_initialized = True
    else:
        gesture_initialized = False
    
    if gesture_initialized:
        print("X: {:.2f}g, Y: {:.2f}g, Z: {:.2f}g".format(x, y, z))
    
    # Wait for a while before reading again
    utime.sleep(0.05)
