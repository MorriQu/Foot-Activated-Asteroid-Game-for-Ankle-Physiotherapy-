import serial
import time
from pynput.keyboard import Key, Controller 
import json

keyboard = Controller()

CALIBRATION_FILE = "calibration_fourFlexors.json"

class FourFlexorsControl:
    def __init__(self, port='COM3', baud=9600, threshold_mult=0.8):
        self.arduino = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # allow time to connect

        self.threshold_mult = threshold_mult
        self.sensor_names = ["Up", "Down", "Left", "Right"]
        self.thresholds = [0, 0, 0, 0]
        self.sensor_values = [0, 0, 0, 0]

        self.calibrate_all_sensors()
    
    def read_sensor(self):
    # """Reads sensor values from Arduino and ensures all expected values are received."""
        self.arduino.flushInput()  # Clear buffer to reduce partial reads

        while True:  # Keep trying until we get a valid full set
            data = self.arduino.readline().decode().strip()
            
            if data:
                values = data.split()  # Convert to list
                cleaned_values = []

                for v in values:
                    if v.isdigit():
                        cleaned_values.append(int(v))

                # Ensure we have exactly 4 values 
                if len(cleaned_values) == 4:  
                    #print(f"Extracted Values: {cleaned_values}")  # Debugging print
                    return cleaned_values  # Only return when valid data is received to prevent incorrect indexing
                else:
                    print(f"Incomplete data received: {cleaned_values}, retrying...")

    # Function to calibrate a single sensor
    def calibrate_sensor(self, sensor_index): 
        """Calibrates one sensor using max values over 5 rounds."""
        print(f"Calibration started for Sensor {self.sensor_names[sensor_index]}. Recording max values.")
        time.sleep(3)  
        calibration_values = []

        for i in range(5):
            max_value = 0
            print(f"Recording session {i+1}/5.")
            start_time = time.time()

            while time.time() - start_time < 3:  # record 3s window, capture highest values
                values = self.read_sensor()
               # print("Values: ", values)
                if values and len(values) > sensor_index:
                    max_value = max(max_value, values[sensor_index])

            calibration_values.append(max_value) # append to list of max values
            print(f"Max Value for Sensor {sensor_index}, Round {i+1}: {max_value}")

            if i < 4:
                print("Pausing for 1/2 second before next recording.")
                time.sleep(0.5)

        threshold = round(self.threshold_mult*(sum(calibration_values) / len(calibration_values)))
        print(f"Calibration complete for Sensor {sensor_index}. Threshold set to: {threshold:.2f}")
        return threshold
    
    # Variant where you press c in python console
    # def calibrate_all_sensors(self): # loops calibrate sensor four times, requiring you to press every time
        # """Calibrates all four sensors."""
        # for sensor_index in range(4):
            # print(f"Press 'c' to start calibration for {self.sensor_names[sensor_index]} Sensor.")
            # while True:
                # if keyboard.is_pressed('c'):
                    #self.thresholds[sensor_index] = self.calibrate_sensor(sensor_index)
                    # break
                # time.sleep(0.1)
        # print("All sensors calibrated.")

    def calibrate_all_sensors(self):
        """Calibrates all four sensors."""
        for sensor_index in range(4):
            self.thresholds[sensor_index] = self.calibrate_sensor(sensor_index)
        self.save_calibration()
        print("All sensors calibrated.")

    def get_sensor_outputs(self):
        """Reads sensor values and returns whether each one is above its threshold."""
        values = self.read_sensor()
        if values and len(values) >= 4:
            self.sensor_values = values[:4]
            return [1 if self.sensor_values[i] > self.thresholds[i] else 0 for i in range(4)]
        return [0, 0, 0]
    
    def save_calibration(self):
        """Saves the current calibration data to the JSON file."""
        calibration_data = {'thresholds': self.thresholds}
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(calibration_data, f)
    
    def close(self):
        """Closes the serial connection."""
        self.arduino.close()

    # thank you mr claude for this wonderful visualize function
    def visualize_sensor(self, value, threshold, name, width=20):
        bar = "█" * int((value / 1023) * width)
        bar = bar.ljust(width, "░")
        active = "ACTIVE" if value > threshold else "      "
        return f"{name:5}: {bar} {value:4}/{threshold:.0f} {active}"

# this only runs if executed directly, not when imported
if __name__ == "__main__":
    controller = FourFlexorsControl()
    try: 
        while True:
            print("\n" + "Sensor Values".center(50, "="))
            sensor_values = controller.get_sensor_outputs() 
            for i in range(4):
                print(controller.visualize_sensor(controller.sensor_values[i], controller.thresholds[i], controller.sensor_names[i]))  
            time.sleep(0.1)
            if keyboard.is_pressed('q'):
                break
    except KeyboardInterrupt:
        pass
    finally:   
        controller.close()
        print("Serial connection closed.")

""" 
example of visualization output:
================Sensor Values================
Up   : ████████░░░░░░░░░░░░  420/500       
Right: ██░░░░░░░░░░░░░░░░░░  210/450       
Left : ███████████████░░░░░  750/600 ACTIVE
Down : ░░░░░░░░░░░░░░░░░░░░   50/400
courtesy of Claude.Ai 
"""