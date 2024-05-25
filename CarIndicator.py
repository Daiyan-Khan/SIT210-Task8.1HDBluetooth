from bluepy import btle
import time
import threading
import struct
import RPi.GPIO as GPIO

LED_PIN = 18

# Init pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)

# Pin cleanup routine
def Cleanup():
    GPIO.cleanup(LED_PIN)

class NotificationHandler(btle.DefaultDelegate):
    def __init__(self):
        super().__init__()

    def HandleNotification(self, cHandle, data):
        try:
            # Decode the float data
            distance = struct.unpack('f', data)[0]
            print(f"Received: {distance}")
            # Get the interval, and affect it through the callback
            interval = DetermineInterval(distance)
            # Print out so it can be seen
            print(f"Interval: {interval}; Distance: {distance}")
            # Set the LED blink interval
            blinker.SetInterval(interval)
        except Exception as e:
            print(f"Error handling notification: {e}")

class AsyncLEDController:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._Execute)
        self.interval = None

    def _Execute(self):
        while not self._stop_event.is_set():
            if self.interval is None:
                SetPinState(False)
                time.sleep(0.1)
            else:
                SetPinState(True)
                time.sleep(self.interval)
                SetPinState(False)
                time.sleep(self.interval)

    def Start(self):
        if not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._Execute)
            self._thread.start()

    def Stop(self):
        self._stop_event.set()
        self._thread.join()

    def SetInterval(self, interval):
        self.interval = interval

# Sets pins to the given state
def SetPinState(state):
    GPIO.output(LED_PIN, state)

SetPinState(False)

def DetermineInterval(distance):
    if distance < 0:
        return None
    
    intervals = [
        (5, 0.1),
        (10, 0.6),
        (15, 1.8),
        (20, 3.0)
    ]

    for threshold, interval in intervals:
        if distance < threshold:
            return interval
    
    return None

def ConnectToPeripheral(target_address):
    print(f"Connecting to {target_address}...")
    peripheral = btle.Peripheral(target_address)
    peripheral.setDelegate(NotificationHandler())
    return peripheral

def ReceiveData(peripheral):
    try:
        print("Connected. Waiting for notifications...")

        # Enable notifications for the characteristic
        service_uuid = btle.UUID("180F")
        characteristic_uuid = btle.UUID("2A19")
        
        service = peripheral.getServiceByUUID(service_uuid)
        characteristic = service.getCharacteristics(characteristic_uuid)[0]
        
        # Enable notifications
        setup_data = b"\x01\x00"
        peripheral.writeCharacteristic(characteristic.getHandle() + 1, setup_data, withResponse=True)

        while True:
            if peripheral.waitForNotifications(1.0):
                # Notification received
                continue
            print("Waiting...")
    except btle.BTLEDisconnectError as e:
        SetPinState(False)
        print(f"Disconnected: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)
        return None

if __name__ == "__main__":
    try:
        # Start controls of indicator
        blinker = AsyncLEDController()
        blinker.Start()
        target_address = "D4:D4:DA:4E:FC:9E"
        peripheral = ConnectToPeripheral(target_address)
        if peripheral:
            ReceiveData(peripheral)
    finally:
        Cleanup()
        blinker.Stop()
