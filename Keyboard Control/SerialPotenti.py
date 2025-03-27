import serial
import time 
from pynput.keyboard import Key, Controller 

SerialObject = serial.Serial('COM3', 9600)
SerialObject.timeout = 1
keyboard = Controller()

print("Starting to read data from Arduino")

# Function to simulate key press based on switch state
def simulate_key_press(switchState):
    if switchState <450 : 
        print("Down arrow key pressed")
        keyboard.press(Key.down)
    
    elif switchState == 450 & switchState <= 550:
        print("Arrow Keys released")
        keyboard.release(Key.up)
        keyboard.release(Key.down)

    elif switchState > 550:
        print("Up Arrow Key Pressed")
        keyboard.press(Key.up)

def process_serial_input():
    while True: 
        if SerialObject.in_waiting >0:

            ReceivedString = SerialObject.readline().decode('utf-8').strip()
            print(f"Received Switch State: {ReceivedString}")

            # Parse the switch states
            switchState = ReceivedString.split(": ")[1] # Extract state for switch 1

            print(f"switchState:", switchState)
            print(type(switchState))

            simulate_key_press(int(switchState))


        time.sleep(0.01)

# Start processing the serial input
process_serial_input()