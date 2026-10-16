// Arduino-ESP32 3.x + ArduinoJson 7.x. Serial Monitor: 115200 baud, newline.
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

WiFiUDP udp;
struct Request {
  String id;
  IPAddress ip;
  String completionId;
  String answeredId;
  bool resolved = false;
  bool closed = false;
};
Request requests[16];
String serialLine;
bool serialOverflow = false;

Request* findRequest(const String& id) {
  for (auto& request : requests) if (request.id == id) return &request;
  return nullptr;
}

bool sendJson(IPAddress ip, JsonDocument& doc) {
  String text;
  serializeJson(doc, text);
  if (text.length() > 1024) return false;
  udp.beginPacket(ip, 4331);
  udp.print(text);
  return udp.endPacket() == 1;
}

void receivePacket() {
  int size = udp.parsePacket();
  if (size <= 0) return;
  IPAddress sender = udp.remoteIP();
  char data[1025];
  int len = udp.read(data, 1024);
  if (size > 1024 || len <= 0) return;
  data[len] = 0;
  JsonDocument doc;
  if (deserializeJson(doc, data)) return;
  String type = doc["type"] | "";
  String id = doc["sosId"] | "";
  String messageId = doc["messageId"] | "";
  if (id.isEmpty() || messageId.isEmpty()) return;
  Request* request = findRequest(id);
  if (type == "SOS") {
    if (!request) {
      for (auto& candidate : requests) {
        if (candidate.id.isEmpty()) { request = &candidate; break; }
      }
      if (!request) { Serial.println("Request capacity reached"); return; }
      request->id = id;
    }
    request->ip = sender;
  }
  if (!request || request->ip != sender) return;

  String status;
  if (type == "SOS") status = "BASE_STATION_RECEIVED";
  else if (type == "CHAT" && doc["sender"] == "victim" &&
      doc["text"].is<String>() && !request->closed) status = "CHAT_RECEIVED";
  else if (type == "COMPLETION_RESPONSE" && doc["resolved"].is<bool>()) {
    String replyTo = doc["requestId"] | "";
    bool resolved = doc["resolved"];
    if (!request->completionId.isEmpty() && replyTo == request->completionId) {
      request->answeredId = replyTo;
      request->resolved = resolved;
      request->closed = resolved;
      request->completionId = "";
    } else if (replyTo != request->answeredId || request->answeredId.isEmpty() ||
        resolved != request->resolved) return;
    // Repeat the ACK if the first one was lost; never apply the decision twice.
    status = "COMPLETION_RESPONSE_RECEIVED";
  } else return;

  Serial.println(data); // Authority console: deduplicate chat by messageId.
  JsonDocument ack;
  ack["type"] = "ACK";
  ack["sosId"] = id;
  ack["messageId"] = messageId;
  ack["status"] = status;
  sendJson(request->ip, ack);
}

void adminCommand(const String& line) {
  JsonDocument doc;
  if (deserializeJson(doc, line)) { Serial.println("Invalid JSON"); return; }
  String id = doc["sosId"] | "";
  Request* request = findRequest(id);
  if (!request || request->closed) { Serial.println("No active request for this SOS ID"); return; }
  String type = doc["type"] | "";
  if (type != "CHAT" && type != "COMPLETION_REQUEST") {
    Serial.println("Use CHAT or COMPLETION_REQUEST"); return;
  }
  if (type == "CHAT") {
    if (!doc["text"].is<String>() || doc["text"].as<String>().length() > 600) return;
    doc["sender"] = "authority";
  }
  if (!doc["messageId"].is<String>()) {
    char idBuffer[32];
    snprintf(idBuffer, sizeof(idBuffer), "BASE-%08lx-%08lx",
      (unsigned long)esp_random(), (unsigned long)esp_random());
    doc["messageId"] = idBuffer;
  }
  if (type == "COMPLETION_REQUEST") {
    if (request->completionId.isEmpty()) request->completionId = doc["messageId"].as<String>();
    doc["messageId"] = request->completionId; // Retry the same pending prompt.
  }
  Serial.print(sendJson(request->ip, doc) ? "UDP sent (phone receipt unconfirmed): " : "Send failed: ");
  serializeJson(doc, Serial);
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_AP);
  if (!WiFi.softAP("CodeRed_SOS_Network") || !udp.begin(4330)) {
    Serial.println("Base station setup failed"); while (true) delay(1000);
  }
  Serial.println("Base station ready at 192.168.4.1:4330");
}

void loop() {
  receivePacket();
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (!serialOverflow && serialLine.length()) adminCommand(serialLine);
      serialLine = ""; serialOverflow = false;
    } else if (c != '\r' && !serialOverflow) {
      if (serialLine.length() < 1024) serialLine += c;
      else { serialLine = ""; serialOverflow = true; }
    }
  }
  delay(5);
}
