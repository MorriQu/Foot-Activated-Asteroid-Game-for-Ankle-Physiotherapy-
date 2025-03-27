import serial
import time
from pynput.keyboard import Key, Controller 

SerialObject = serial.Serial('COM3', 9600)
SerialObject.timeout = 1
keyboard = Controller() 
SerialObject.flushInput() # clear any previous data in the buffer


# def keyboard_control(data):

# Function to simulate key press based on switch state
def simulate_key_press(upSwitchState, downSwitchState):
    if upSwitchState == 0: 
        print("Up arrow key released")
        keyboard.release(Key.up)
    
    elif upSwitchState == 1:
        print("Up Arrow Key Pressed")
        keyboard.press(Key.up)

    if downSwitchState == 0: 
        print("Down Arrow Key released")
        keyboard.release(Key.down)

    elif downSwitchState == 1:
        print("Down Arrow Key Pressed")
        keyboard.press(Key.down)


# Function to read from serial and process switch states
def process_serial_input():
    while True:
        if SerialObject.in_waiting > 0:
            # Read the line from Arduino
            received_string = SerialObject.readline().decode('utf-8').strip()
            print(f"Received data: {received_string}")  # Print received data

            # Split data into switch states (if in correct format)
            if "upSwitchState" in received_string and "downSwitchState" in received_string:
                # Split the received string into individual parts (based on tabs)
                switch_data = received_string.split("\t")
                print(f"switch_data: {switch_data}")

                # Extract the switch states
                try:
                    upSwitchState = int(switch_data[0].split(":")[1].strip())  # Extract switchUpState
                    downSwitchState = int(switch_data[1].split(":")[1].strip())  # Extract switchDownState

                    print(f"upSwitchState: {upSwitchState}")
                    print(f"downSwitchState: {downSwitchState}")

                    # Simulate key press based on switch state
                    simulate_key_press(upSwitchState, downSwitchState)

                except IndexError as e:
                    print(f"Error parsing switch states: {e}")
                except ValueError as e:
                    print(f"Invalid value for switch states: {e}")

        time.sleep(0.1)  # Sleep to prevent high CPU usage

# Start processing the serial input
process_serial_input()

# print("Starting to read data from Arduino")


# while True: 
#     if SerialObject.in_waiting >0:

#         ReceivedString = SerialObject.readline().decode('utf-8').strip()
#         print(f"Received Switch State: {ReceivedString}")

#         # Split the received data based on tab ('\t') separator
#         switch_data = ReceivedString.split('\t')


#         # print(switch_data[1].split(": ")[1])
#         # Parse the switch states
#         switchUpState = switch_data[0].split(": ")[1]  # Extract state for switch 1
#         switchDownState = switch_data[1].split(": ")[1]  # Extract state for switch 2
   

#         # Print the states of each switch
#         print(f"Up Switch state: {switchUpState}")
#         print(f"Down Switch state: {switchDownState}")


#         # You can now use the switch states for further processing
#         # For example, take actions based on the switch states
#         if switchUpState == '1':
#             print("Up switch is pressed!")
#         else:
#             print("Up switch is not pressed.")
        
#         if switchDownState == '1':
#             print("Down switch is pressed!")
#         else:
#             print("Down switch is not pressed.")
        
#     time.sleep(0.1)


