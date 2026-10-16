#include <WiFi.h>
#include <WiFiUdp.h>

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>

#define DEVICE_NAME "AeroLink-Test"

// ========================================
// BASE STATION NETWORK
// ========================================

const char* BASE_STATION_SSID = "CodeRed_SOS_Network";

IPAddress baseStationIP(192, 168, 4, 1);

const int BASE_STATION_UDP_PORT = 4330;

WiFiUDP udp;

// ========================================
// BLE UUIDs
// Must match Flutter exactly.
// ========================================

#define AEROLINK_SERVICE_UUID \
  "4fafc201-1fb5-459e-8fcc-c5c9c331914b"

#define SOS_CHARACTERISTIC_UUID \
  "beb5483e-36e1-4688-b7f5-ea07361b26a8"

#define ACK_CHARACTERISTIC_UUID \
  "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

// ========================================
// GLOBALS
// ========================================

BLECharacteristic* pAckCharacteristic;

// ========================================
// WIFI CONNECTION
// ========================================

bool connectToBaseStation() {

  if (WiFi.status() == WL_CONNECTED) {
    return true;
  }

  Serial.println();
  Serial.println("================================");
  Serial.println("Connecting to AeroLink Base Station...");
  Serial.println("SSID: CodeRed_SOS_Network");
  Serial.println("================================");

  WiFi.begin(BASE_STATION_SSID);

  unsigned long startAttemptTime = millis();

  const unsigned long timeout = 10000;

  while (
    WiFi.status() != WL_CONNECTED &&
    millis() - startAttemptTime < timeout
  ) {

    Serial.print(".");
    delay(500);
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println("Connected to Base Station!");

    Serial.print("AeroLink IP: ");
    Serial.println(WiFi.localIP());

    Serial.print("Base Station IP: ");
    Serial.println(baseStationIP);

    return true;
  }

  Serial.println("Failed to connect to Base Station.");

  return false;
}

// ========================================
// SEND SOS TO BASE STATION
// ========================================

bool sendSOSToBaseStation(String sosJson) {

  if (!connectToBaseStation()) {
    return false;
  }

  Serial.println();

  Serial.println("================================");
  Serial.println("SENDING SOS TO BASE STATION");
  Serial.println("================================");

  Serial.println(sosJson);

  udp.beginPacket(
    baseStationIP,
    BASE_STATION_UDP_PORT
  );

  udp.print(sosJson);

  int result = udp.endPacket();

  Serial.println();

  if (result == 1) {

    Serial.println("SOS UDP packet sent successfully.");

    Serial.println("Destination:");
    Serial.print(baseStationIP);

    Serial.print(":");
    Serial.println(BASE_STATION_UDP_PORT);

    Serial.println("================================");

    return true;
  }

  Serial.println("Failed to send SOS UDP packet.");

  Serial.println("================================");

  return false;
}

// ========================================
// BLE CONNECTION CALLBACKS
// ========================================

class AeroLinkServerCallbacks : public BLEServerCallbacks {

  void onConnect(BLEServer* pServer) {

    Serial.println();

    Serial.println("================================");
    Serial.println("Device connected to AeroLink!");
    Serial.println("================================");
  }

  void onDisconnect(BLEServer* pServer) {

    Serial.println();

    Serial.println("Device disconnected.");

    delay(500);

    BLEDevice::startAdvertising();

    Serial.println("BLE advertising restarted.");
  }
};

// ========================================
// SOS RECEIVER
// ========================================

class SOSCommandCallbacks : public BLECharacteristicCallbacks {

  void onWrite(BLECharacteristic* pCharacteristic) {

    String receivedData =
      pCharacteristic->getValue();

    Serial.println();

    Serial.println("================================");
    Serial.println("🚨 SOS MESSAGE RECEIVED FROM FLUTTER");
    Serial.println("================================");

    Serial.println(receivedData);

    Serial.println("================================");

    // ========================================
    // SEND SOS TO BASE STATION
    // ========================================

    bool sentToBaseStation =
      sendSOSToBaseStation(receivedData);

    // ========================================
    // SEND ACK TO FLUTTER
    // ========================================

    String ackMessage;

    if (sentToBaseStation) {

      ackMessage =
        "{\"type\":\"ACK\","
        "\"status\":\"SOS_FORWARDED_TO_BASE_STATION\"}";

      Serial.println();
      Serial.println("SOS successfully forwarded.");
    }

    else {

      ackMessage =
        "{\"type\":\"ACK\","
        "\"status\":\"SOS_RECEIVED_BASE_STATION_UNAVAILABLE\"}";

      Serial.println();
      Serial.println("SOS received but Base Station unavailable.");
    }

    pAckCharacteristic->setValue(
      ackMessage.c_str()
    );

    pAckCharacteristic->notify();

    Serial.println();

    Serial.println("ACK sent to Flutter:");

    Serial.println(ackMessage);

    Serial.println("================================");
  }
};

// ========================================
// SETUP
// ========================================

void setup() {

  Serial.begin(115200);

  delay(1000);

  Serial.println();

  Serial.println("================================");
  Serial.println("Starting AeroLink Device");
  Serial.println("================================");

  // ========================================
  // WIFI
  // ========================================

  WiFi.mode(WIFI_STA);

  Serial.println("Wi-Fi Station Mode Ready.");

  // ========================================
  // BLE INITIALIZATION
  // ========================================

  BLEDevice::init(DEVICE_NAME);

  BLEServer* pServer =
    BLEDevice::createServer();

  pServer->setCallbacks(
    new AeroLinkServerCallbacks()
  );

  // ========================================
  // AEROLINK BLE SERVICE
  // ========================================

  BLEService* pService =
    pServer->createService(
      AEROLINK_SERVICE_UUID
    );

  // ========================================
  // SOS WRITE CHARACTERISTIC
  // ========================================

  BLECharacteristic* pSOSCharacteristic =
    pService->createCharacteristic(

      SOS_CHARACTERISTIC_UUID,

      BLECharacteristic::PROPERTY_WRITE |
      BLECharacteristic::PROPERTY_WRITE_NR
    );

  pSOSCharacteristic->setCallbacks(
    new SOSCommandCallbacks()
  );

  // ========================================
  // ACK NOTIFY CHARACTERISTIC
  // ========================================

  pAckCharacteristic =
    pService->createCharacteristic(

      ACK_CHARACTERISTIC_UUID,

      BLECharacteristic::PROPERTY_NOTIFY
    );

  // ========================================
  // START BLE SERVICE
  // ========================================

  pService->start();

  // ========================================
  // BLE ADVERTISING
  // ========================================

  BLEAdvertising* pAdvertising =
    BLEDevice::getAdvertising();

  pAdvertising->addServiceUUID(
    AEROLINK_SERVICE_UUID
  );

  pAdvertising->setScanResponse(true);

  BLEDevice::startAdvertising();

  Serial.println();

  Serial.println("BLE Advertising Started!");

  Serial.println("Device Name:");
  Serial.println(DEVICE_NAME);

  Serial.println();

  Serial.println("Waiting for SOS messages...");
}

// ========================================
// LOOP
// ========================================

void loop() {

  delay(1000);
}