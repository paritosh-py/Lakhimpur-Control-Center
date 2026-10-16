#include <WiFi.h>
#include <WiFiUdp.h>

// ========================================
// BASE STATION CONFIGURATION
// ========================================

const char* ssid = "CodeRed_SOS_Network";

// Open Wi-Fi network for prototype.
// Later we can add a password.

WiFiUDP udp;

// AeroLink ESP32 sends SOS here.
const int udpRxPort = 4330;

// AeroLink ESP32 listens for replies here.
const int udpTxPort = 4331;

// Maximum expected SOS JSON packet size.
const int maxPacketSize = 1024;

// ========================================
// SETUP
// ========================================

void setup() {
  Serial.begin(115200);

  delay(1000);

  Serial.println();
  Serial.println("================================");
  Serial.println("AeroLink Base Station Booting");
  Serial.println("================================");

  // Base Station acts as Wi-Fi Access Point.
  WiFi.mode(WIFI_AP);

  bool apStarted = WiFi.softAP(ssid);

  if (!apStarted) {
    Serial.println("ERROR: Failed to create hotspot!");

    while (true) {
      delay(1000);
    }
  }

  Serial.println("SUCCESS: Base Station Hotspot Started");

  Serial.print("SSID: ");
  Serial.println(ssid);

  Serial.print("Base Station IP: ");
  Serial.println(WiFi.softAPIP());

  // Start UDP receiver.
  if (!udp.begin(udpRxPort)) {
    Serial.println("ERROR: Failed to start UDP receiver!");

    while (true) {
      delay(1000);
    }
  }

  Serial.print("Listening for SOS on UDP port: ");
  Serial.println(udpRxPort);

  Serial.println();
  Serial.println("================================");
  Serial.println("BASE STATION READY");
  Serial.println("Waiting for AeroLink devices...");
  Serial.println("================================");
}

// ========================================
// LOOP
// ========================================

void loop() {

  // ========================================
  // RECEIVE SOS FROM AEROLINK ESP32
  // ========================================

  int packetSize = udp.parsePacket();

  if (packetSize > 0) {

    char incomingPacket[maxPacketSize];

    int bytesToRead = min(
      packetSize,
      maxPacketSize - 1
    );

    int len = udp.read(
      incomingPacket,
      bytesToRead
    );

    if (len > 0) {
      incomingPacket[len] = '\0';
    }

    IPAddress aeroLinkIP = udp.remoteIP();

    uint16_t aeroLinkPort = udp.remotePort();

    Serial.println();
    Serial.println("================================");
    Serial.println("🚨 SOS RECEIVED AT BASE STATION");
    Serial.println("================================");

    Serial.print("Sender IP: ");
    Serial.println(aeroLinkIP);

    Serial.print("Sender Port: ");
    Serial.println(aeroLinkPort);

    Serial.print("Packet Size: ");
    Serial.println(packetSize);

    Serial.println();
    Serial.println("SOS JSON:");
    Serial.println(incomingPacket);

    if (packetSize >= maxPacketSize) {
      Serial.println();
      Serial.println(
        "WARNING: Packet may have been truncated!"
      );
    }

    Serial.println("================================");

    // ========================================
    // SEND ACKNOWLEDGEMENT TO AEROLINK DEVICE
    // ========================================

    String ackMessage =
      "{\"type\":\"ACK\","
      "\"status\":\"BASE_STATION_RECEIVED\"}";

    udp.beginPacket(
      aeroLinkIP,
      udpTxPort
    );

    udp.print(ackMessage);

    bool ackSent = udp.endPacket();

    Serial.print("Base Station ACK: ");

    if (ackSent) {
      Serial.println("SENT");
      Serial.println(ackMessage);
    } else {
      Serial.println("FAILED");
    }

    Serial.println("================================");
  }

  // ========================================
  // ADMIN REPLY FROM SERIAL
  // ========================================

  if (Serial.available()) {

    String adminMessage =
      Serial.readStringUntil('\n');

    adminMessage.trim();

    if (adminMessage.length() > 0) {

      udp.beginPacket(
        IPAddress(192, 168, 4, 255),
        udpTxPort
      );

      udp.print(adminMessage);

      bool sent = udp.endPacket();

      Serial.println();

      if (sent) {
        Serial.print(
          "ADMIN REPLY BROADCAST: "
        );

        Serial.println(adminMessage);
      } else {
        Serial.println(
          "ADMIN REPLY BROADCAST FAILED"
        );
      }
    }
  }
}