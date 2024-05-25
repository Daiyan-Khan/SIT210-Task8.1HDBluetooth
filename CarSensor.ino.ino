#include <ArduinoBLE.h>

// Define the LED service and characteristic UUIDs (universally unique identifiers)
// These UUIDs can be LEDized to your specific needs.
#define SERVICE_UUID "180F"
#define CHARACTERISTIC_UUID "2A19"

// Define the pins for the ultrasonic sensor.
// The trigger pin sends the pulse and the echo pin receives the pulse.
const int trigPin = 2;
const int echoPin = 4;

// Create the BLE (Bluetooth Low Energy) service and characteristic objects.
// The service groups related characteristics together.
BLEService LEDService(SERVICE_UUID);

// The characteristic allows us to send and receive data.
// BLERead allows a connected device to read the value.
// BLENotify allows us to send notifications when the value changes.
BLEFloatCharacteristic LEDCharacteristic(CHARACTERISTIC_UUID, BLERead | BLENotify);

void setup() {
  // Initialize the serial communication for debugging purposes.
  Serial.begin(9600);

  // Initialize the GPIO pins for the ultrasonic sensor.
  initializePins();

  // Initialize the BLE module.
  initializeBLE();

  // Start advertising the BLE service.
  advertiseService();
}

void loop() {
  // Wait for a BLE central device (like a smartphone) to connect.
  BLEDevice central = BLE.central();

  // If a central device is connected, handle the connection.
  if (central) {
    handleCentralConnection(central);
  }
}

// Function to initialize the GPIO pins.
void initializePins() {
  pinMode(trigPin, OUTPUT); // Set the trigger pin as an output.
  pinMode(echoPin, INPUT);  // Set the echo pin as an input.
}

// Function to initialize the BLE module.
void initializeBLE() {
  // Start BLE. If it fails, print an error message and halt the program.
  if (!BLE.begin()) {
    Serial.println("BLE initialization failed!");
    while (1); // Infinite loop to halt the program.
  }
}

// Function to advertise the BLE service.
void advertiseService() {
  BLE.setLocalName("Nano33IoT"); // Set the local name for the BLE device.
  BLE.setAdvertisedService(LEDService); // Advertise the LED service.
  
  // Add the characteristic to the service.
  LEDService.addCharacteristic(LEDCharacteristic);
  
  // Add the service to the BLE stack.
  BLE.addService(LEDService);
  
  // Start advertising the service.
  BLE.advertise();
  Serial.println("Bluetooth device active, waiting for connections...");
}

// Function to measure distance using the ultrasonic sensor.
float measureDistance() {
  // Send a pulse to trigger the sensor.
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Read the duration of the echo pulse.
  long duration = pulseIn(echoPin, HIGH);

  // Calculate the distance in centimeters.
  // Speed of sound is approximately 0.034 cm/us.
  float distance = duration * 0.034 / 2;

  return distance;
}

// Function to send the measured distance over BLE.
void sendDistance(float distance) {
  LEDCharacteristic.writeValue(distance); // Update the characteristic value.
  Serial.print("Sending: ");
  Serial.println(distance); // Print the distance for debugging.
}

// Function to handle the connection with the central device.
void handleCentralConnection(BLEDevice central) {
  Serial.print("Connected to central: ");
  Serial.println(central.address()); // Print the address of the connected device.

  // Continue to communicate with the central device as long as it is connected.
  while (central.connected()) {
    // Measure the distance using the ultrasonic sensor.
    float distance = measureDistance();

    // Send the measured distance to the central device.
    sendDistance(distance);

    // Wait for a second before measuring again to avoid flooding the connection.
    delay(1000);
  }

  // Print a message when the central device disconnects.
  Serial.print("Disconnected from central: ");
  Serial.println(central.address());
}
