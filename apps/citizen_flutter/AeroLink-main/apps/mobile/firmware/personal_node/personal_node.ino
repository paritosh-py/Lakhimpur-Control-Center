// Arduino-ESP32 3.x + ArduinoJson 7.x. Flash together with the matching app.
#include <WiFi.h>
#include <WiFiUdp.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <ArduinoJson.h>

const char* SSID = "CodeRed_SOS_Network";
IPAddress baseIP(192, 168, 4, 1);
WiFiUDP udp;
BLECharacteristic* replies;
QueueHandle_t incoming;
volatile bool connected = false;
bool udpStarted = false;
struct Packet { char data[1025]; };

void notifyJson(JsonDocument& doc) {
  if (!connected) {
    Serial.println("[BLE TX] Phone disconnected; reply not relayed. Resend after reconnect.");
    return;
  }
  String text;
  serializeJson(doc, text);
  Serial.print("[BLE TX] Notifying phone: ");
  Serial.println(text);
  text = "\n" + text + "\n";
  for (size_t i = 0; i < text.length() && connected; i += 20) {
    size_t count = min((size_t)20, text.length() - i);
    replies->setValue((uint8_t*)text.c_str() + i, count);
    replies->notify();
    delay(20);
  }
}

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer*) override {
    connected = true;
    Serial.println("[BLE] Phone connected. Waiting for app messages.");
  }
  void onDisconnect(BLEServer*) override {
    connected = false;
    Serial.println("[BLE] Phone disconnected. Restarting advertising.");
    BLEDevice::startAdvertising();
  }
};

class CommandCallbacks : public BLECharacteristicCallbacks {
  String buffer;
  unsigned long lastByte = 0;
  bool overflow = false;
  void onWrite(BLECharacteristic* characteristic) override {
    auto bytes = characteristic->getValue();
    Serial.printf("[BLE RX] Chunk: %u bytes\n", (unsigned int)bytes.length());
    if (millis() - lastByte > 3000) {
      if (buffer.length()) Serial.println("[BLE RX] Discarding stale partial message. App must send newline-delimited JSON.");
      buffer = ""; overflow = false;
    }
    lastByte = millis();
    for (size_t i = 0; i < bytes.length(); ++i) {
      char c = bytes[i];
      if (c == '\n') {
        if (!overflow && buffer.length()) {
          Packet packet = {};
          buffer.toCharArray(packet.data, sizeof(packet.data));
          if (xQueueSend(incoming, &packet, 0) != pdTRUE)
            Serial.println("Input queue full; sender must retry.");
          else
            Serial.println("[BLE RX] Complete message queued.");
        }
        buffer = "";
        overflow = false;
      } else if (!overflow) {
        if (buffer.length() < 1024) buffer += c;
        else {
          Serial.println("[BLE RX] Message exceeds 1024 bytes; discarded.");
          overflow = true; buffer = "";
        }
      }
    }
  }
};

bool connectBase() {
  if (WiFi.status() != WL_CONNECTED) {
    udpStarted = false;
    Serial.print("[WiFi] Connecting to ");
    Serial.println(SSID);
    WiFi.begin(SSID);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) delay(50);
  }
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Connection timed out. Check base-station power and range.");
    return false;
  }
  if (!udpStarted) {
    Serial.print("[WiFi] Connected. Personal-node IP: ");
    Serial.println(WiFi.localIP());
    udpStarted = udp.begin(4331);
    Serial.println(udpStarted ? "[UDP] Listening for base replies on port 4331."
      : "[UDP] Failed to bind reply port 4331.");
  }
  return udpStarted;
}

void forwardPacket(Packet& packet) {
  JsonDocument doc;
  Serial.print("[APP RX] ");
  Serial.println(packet.data);
  if (deserializeJson(doc, packet.data)) {
    Serial.println("[APP RX] Invalid JSON; ignored.");
    return;
  }
  String type = doc["type"] | "";
  if ((type != "SOS" && type != "CHAT" && type != "COMPLETION_RESPONSE") ||
      !doc["sosId"].is<String>() || !doc["messageId"].is<String>()) {
    Serial.println("[APP RX] Unsupported type or missing sosId/messageId. Use the updated Flutter app.");
    return;
  }

  JsonDocument ack;
  ack["type"] = "ACK";
  ack["sosId"] = doc["sosId"];
  ack["messageId"] = doc["messageId"];
  if (type == "SOS") {
    ack["status"] = "SOS_RECEIVED";
    notifyJson(ack);
  }
  bool sent = false;
  if (connectBase()) {
    udp.beginPacket(baseIP, 4330);
    udp.print(packet.data);
    sent = udp.endPacket() == 1;
    Serial.println(sent ? "[UDP TX] Sent to 192.168.4.1:4330; base receipt still unconfirmed."
      : "[UDP TX] Send failed.");
  }
  if (!sent) {
    ack["status"] = type == "SOS" ? "SOS_RECEIVED_BASE_STATION_UNAVAILABLE"
      : "BASE_STATION_UNAVAILABLE";
    notifyJson(ack);
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  incoming = xQueueCreate(8, sizeof(Packet));
  if (!incoming) { Serial.println("Queue allocation failed"); while (true) delay(1000); }
  BLEDevice::init("AeroLink-Test");
  BLEServer* server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());
  BLEService* service = server->createService("4fafc201-1fb5-459e-8fcc-c5c9c331914b");
  BLECharacteristic* command = service->createCharacteristic(
    "beb5483e-36e1-4688-b7f5-ea07361b26a8", BLECharacteristic::PROPERTY_WRITE);
  command->setCallbacks(new CommandCallbacks());
  replies = service->createCharacteristic(
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890", BLECharacteristic::PROPERTY_NOTIFY);
  replies->addDescriptor(new BLE2902());
  service->start();
  BLEAdvertising* advertising = BLEDevice::getAdvertising();
  advertising->addServiceUUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b");
  advertising->setScanResponse(true);
  advertising->start();
  Serial.println("AeroLink ready");
  Serial.println("[BLE] Advertising as AeroLink-Test. Connect using the app's device screen, then activate SOS.");
  Serial.println("[WiFi] Base connection starts when an app message arrives.");
}

void loop() {
  // Drain base replies before the next outgoing request.
  int size = udp.parsePacket();
  if (size > 0) {
    IPAddress sender = udp.remoteIP();
    uint16_t port = udp.remotePort();
    Serial.print("[UDP RX] Packet from ");
    Serial.print(sender);
    Serial.printf(":%u (%d bytes)\n", (unsigned int)port, size);
    char data[1025];
    int len = udp.read(data, 1024);
    if (size <= 1024 && len > 0 && sender == baseIP && port == 4330) {
      data[len] = 0;
      JsonDocument doc;
      Serial.print("[BASE RX] ");
      Serial.println(data);
      if (!deserializeJson(doc, data)) notifyJson(doc);
      else Serial.println("[BASE RX] Invalid JSON; ignored.");
    } else {
      Serial.println("[UDP RX] Ignored: invalid size or unexpected sender/port.");
    }
  }
  Packet packet;
  if (xQueueReceive(incoming, &packet, 0) == pdTRUE) forwardPacket(packet);
  delay(5);
}
