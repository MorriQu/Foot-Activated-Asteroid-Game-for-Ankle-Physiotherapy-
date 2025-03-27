import serial, os, logging, json, pygame

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

CALIBRATION_FILE = "FlexController_Calibration.json"

class FlexController:
    def __init__(self, port ='COM6', baud=9600): 
        self.arduino = serial.Serial(port, baud, timeout=1)

        self.sensor_values = [0, 0, 0, 0]
        self.thresholds = [0, 0, 0, 0]
        self.sensor_names = ["Up","Down","Left","Right"]

        self.cal_values = []
        self.cal_start = None
        self.calibration_values = []
        self.current_sensor = 0 # Tracks which sensor is being calibrated. Goes up to 4. When at 4, stop and reset. 
        self.cal_round = 0 # Tracks which round of calibration a sensor is on. Goes up to 5. 
        
        """
        self.last_sensor_read_time = 0
        self.cached_sensor_values = [0, 0, 0, 0]
        """

    def read_sensor(self):
        """Reads sensor values from Arduino as a space-separated string (say '0 300 600 900 1200')."""
        self.arduino.flushInput()
        data = self.arduino.readline().decode().strip()
        if data: # If data is not False or Empty
            #logging.debug(f"Raw sensor data: {data}")
            values = data.split()
            return [int(v) for v in values if v.isdigit()] # returns from function all integers from the arduino output
        else: 
            return None
        
    def calibrate_sensor(self):
        """
        Calibrates a sensor at a time, updating the current sensor index to match.
        IT IS IMPORTANT THAT THIS FUNCTION CAN RUN WITHOUT STOPPING GAME LOOP. THEREFORE, THRESHOLD IS ONLY CALCULATED AT CERTAIN POINTS, AND
        VALUE IS ALWAYS READ.
        True and False flag when a calibration round is over, prompting the game loop implementation to rest or not. 
        """
        values = self.read_sensor()
        if not values or len(values) < 4:
            return values, False
        
        if self.cal_start is None:
            self.cal_start = pygame.time.get_ticks() / 1000.0

        

        if self.current_sensor < 4:
            # Update calibration value for the current sensor
            # Reset calibration values when moving to a new sensor
            if self.cal_round == 0:
                self.calibration_values = []  # Reset for new sensor

            if len(self.calibration_values) <= self.current_sensor:
                self.calibration_values.append(values[self.current_sensor])
            else:
                # Keep the maximum value during this round
                self.calibration_values[self.current_sensor] = max(values[self.current_sensor],
                                                                    self.calibration_values[self.current_sensor])
            elapsed = pygame.time.get_ticks() / 1000.0 - self.cal_start

            if elapsed >= 3:  # 3 seconds per calibration round    
                self.cal_round += 1
                if self.cal_round > 2:  # 3 rounds complete for this sensor
                    threshold = sum(self.calibration_values) / len(self.calibration_values)
                    self.thresholds[self.current_sensor] = threshold
                    self.cal_round = 0
                    self.current_sensor += 1
                    logging.debug(f"Moving to next sensor: {self.current_sensor}")
                    logging.debug(f"Updated thresholds: {self.thresholds}")

                    self.cal_start = None
                    return values, True
                # Signal round complete even if not moving to the next sensor
                self.cal_start = None
                return values, True
            else:
                return values, False
            

        return values, False

    
    def sensor_outputs(self, threshold_multiplier=0.9):
        # Update sensor_values with the most recent reading
        values = self.read_sensor()
        if values and len(values) >= 4:
            self.sensor_values = values[:4]
        else:
            self.sensor_values = [0, 0, 0, 0]

        # Initialize empty outputs
        outputs = [0, 0, 0, 0]
        
        # All this just to make sure the values we're using are the ones the controller has
        up_val, down_val, left_val, right_val = self.sensor_values
        up_thresh, down_thresh, left_thresh, right_thresh = [t * threshold_multiplier for t in self.thresholds]
        
        # Apply a higher threshold for up direction and lower for right
        up_thresh = up_thresh * 1.1  # Make "up" less sensitive
        right_thresh = right_thresh * 0.85  # Make "right" more sensitive
        
        # Calculate just how far above the (9% of)threshold each sensor is
        up_strength = (up_val - up_thresh) / max(up_thresh, 1)
        down_strength = (down_val - down_thresh) / max(down_thresh, 1)
        left_strength = (left_val - left_thresh) / max(left_thresh, 1)
        right_strength = (right_val - right_thresh) / max(right_thresh, 1)
        
        # Boost right sensitivity
        right_strength = right_strength * 1.2
        
        strengths = {
            0: up_strength,
            1: down_strength, 
            2: left_strength,
            3: right_strength
        }
        
        if all(strength < 0 for strength in strengths.values()):
            return outputs # No sensors are active
        

        # Creates a dictionary of active sensors (with for keys their index) and their respective strength (as values in the dic)
        active_sensors = {i: s for i, s in strengths.items() if s > 0}
        # if the dictionary is not empty, the output sensor is the one with the highest strength
        if active_sensors:
            strongest_sensor = max(active_sensors.items(), key=lambda x: x[1])[0] # key lambda x: x[1] tells the max function to 
            # look at the second item (the value) in the dictionary when looking for maximums
            # [0] at the end of the line specifies what max should yield is the index, in position 0, and not the value, even though that's
            # what we used for comparison. 
            outputs[strongest_sensor] = 1
        
        # COMMENT OUT: Special case for up-right combination: prefer right if it's strong enough. EDIT this value if NECESSARY. 
        if up_strength > 0 and right_strength > 0 and right_strength >= 0.8 * up_strength:
            outputs = [0, 0, 0, 1]  # Only activate right
        # If two sensors are active, the output is the combination of the two, IF its an UP-DOWN/LEFT-RIGHT combination, 
        # and only if the UP/DOWN sensor is stronger than the LEFT/RIGHT sensor
        elif up_strength > 0 and left_strength > 0 and up_strength > down_strength:
            outputs[0] = 1
            outputs[2] = 1
        elif up_strength > 0 and right_strength > 0 and up_strength > down_strength:
            outputs[0] = 1
            outputs[3] = 1
        elif down_strength > 0 and left_strength > 0 and down_strength > up_strength:
            outputs[1] = 1
            outputs[2] = 1
        elif down_strength > 0 and right_strength > 0 and down_strength > up_strength:
            outputs[1] = 1
            outputs[3] = 1
        
        logging.debug(f"Sensor values: {self.sensor_values}")
        logging.debug(f"Strengths: {strengths}")
        logging.debug(f"Outputs: {outputs}")
        
        return outputs
    

    """
    def sensor_outputs(self, threshold_multiplier=0.95):
        # Reads sensor values and returns whether each one is above its threshold.
        values = self.read_sensor()
        if values and len(values) >= 4:
            self.sensor_values = values[:4]
            return [1 if self.sensor_values[i] > threshold_multiplier*self.thresholds[i] else 0 for i in range(4)]
        return [0, 0, 0, 0]
    """
  


    def cal_reset(self):
        """Resets calibration process state but keeps the thresholds."""
        logging.warning("Resetting calibration process state.")
        self.current_sensor = 0
        self.calibration_values = []
        self.cal_round = 0
        self.cal_start = None

    def close(self):
        """Closes the serial connection."""
        self.arduino.close()
        logging.info("Serial connection closed.")

    def visualize_sensor(self, name, value, threshold, width=20): 
        bar = "█" * int((value / 1023) * width)
        bar = bar.ljust(width, "░")
        active = "ACTIVE" if value > 0.9*threshold else "      "
        return f"{name:5}: {bar} {value:4}/{threshold:.0f} {active}"


class DummyFlexController:
    def __init__(self):
        # No repeated logging here; error is already logged in the try/except block.
        pass

    def read_sensor(self):
        # Return a safe default sensor value.
        return [0, 0, 0, 0]

    def calibrate_sensor(self):
        # Return dummy sensor values with calibration complete.
        return [0, 0, 0, 0], True

    def sensor_outputs(self):
        # Return safe default outputs.
        return [0, 0, 0, 0]

    def cal_reset(self):
        # Dummy method does nothing.
        pass

    def cal_save(self):
        # Dummy method does nothing.
        pass