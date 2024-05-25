from bluepy import btle
import time
import threading
import struct
import RPi.GPIO as GPIO

LED_PIN = 21  # Changed GPIO pin

# Initialize GPIO pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)

# Cleanup function for GPIO pins
def cleanup_pins():
    GPIO.cleanup(LED_PIN)

# Custom notification handler class
class CustomNotificationHandler(btle.DefaultDelegate):
    def __init__(self):
        super().__init__()

    def handleNotification(self, cHandle, data):
        try:
            # Decode the float data
            distance = struct.unpack('f', data)[0]
            print(f"Notification received: {distance} cm")
            # Determine blink interval based on distance
            interval = calculate_blink_interval(distance)
            # Print interval and distance for debugging
            print(f"Calculated Interval: {interval}; Distance: {distance}")
            # Set the LED blink interval
            led_controller.update_interval(interval)
        except Exception as e:
            print(f"Notification handling error: {e}")

# LED control class with asynchronous threading
class LEDController:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run)
        self.blink_interval = None

    def _run(self):
        while not self._stop_event.is_set():
            if self.blink_interval is None:
                set_led_state(False)
                time.sleep(0.1)
            else:
                set_led_state(True)
                time.sleep(self.blink_interval)
                set_led_state(False)
                time.sleep(self.blink_interval)

    def start(self):
        if not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def update_interval(self, interval):
        self.blink_interval = interval

# Function to set the state of the LED pin
def set_led_state(state):
    GPIO.output(LED_PIN, state)

set_led_state(False)

# Function to calculate blink interval based on distance
def calculate_blink_interval(distance):
    if distance < 0:
        return None
    
    # Define new distance-interval mapping
    intervals = [
        (3, 0.2),
        (8, 0.7),
        (12, 1.5),
        (18, 2.5)
    ]

    for threshold, interval in intervals:
        if distance < threshold:
            return interval
    
    return None

# Function to connect to the Bluetooth peripheral
def connect_to_device(device_address):
    print(f"Attempting to connect to {device_address}...")
    try:
        peripheral = btle.Peripheral(device_address)
        peripheral.setDelegate(CustomNotificationHandler())
        print("Connection established.")
        return peripheral
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

# Function to receive data from the Bluetooth peripheral
def receive_data(peripheral):
    try:
        print("Waiting for notifications...")

        # Enable notifications for the characteristic
        service_uuid = btle.UUID("180F")
        characteristic_uuid = btle.UUID("2A19")
        
        service = peripheral.getServiceByUUID(service_uuid)
        characteristic = service.getCharacteristics(characteristic_uuid)[0]
        
        setup_data = b"\x01\x00"
        peripheral.writeCharacteristic(characteristic.getHandle() + 1, setup_data, withResponse=True)

        while True:
            if peripheral.waitForNotifications(1.0):
                continue
            print("No notifications. Waiting...")
    except btle.BTLEDisconnectError as e:
        set_led_state(False)
        print(f"Disconnected from device: {e}")
        print("Reconnecting in 5 seconds...")
        time.sleep(5)
        return None

if __name__ == "__main__":
    try:
        # Initialize and start the LED controller
        led_controller = LEDController()
        led_controller.start()
        device_address = "D4:D4:DA:4E:FC:9E"
        peripheral = connect_to_device(device_address)
        if peripheral:
            receive_data(peripheral)
    finally:
        cleanup_pins()
        led_controller.stop()
