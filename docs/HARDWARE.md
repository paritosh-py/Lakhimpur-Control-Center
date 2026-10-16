# Hardware: Offline Report Link

Updated: 2026-10-11, Asia/Kolkata.

## 1. Physical Hardware Setup

- **Board 1 (AeroLink Device / Field Node)**:
  - ESP32 DevKitV1 running BLE GATT peripheral (`AeroLink-Test`).
  - Connects to citizen phone over Bluetooth (BLE).
  - Receives emergency/incident JSON over BLE characteristic `beb5483e-36e1-4688-b7f5-ea07361b26a8`.
  - Connects to the Base Station ESP's Wi-Fi Access Point (`CodeRed_SOS_Network`) and transmits the JSON payload via UDP to `192.168.4.1:4330`.
  - Sends acknowledgement notification back to phone via BLE characteristic `a1b2c3d4-e5f6-7890-abcd-ef1234567890`.

- **Board 2 (Base Station ESP Node / Gateway)**:
  - ESP32 DevKitV1 plugged into laptop USB port (`COM13` - Silicon Labs CP210x USB to UART Bridge).
  - Broadcasts open Wi-Fi Access Point: SSID `CodeRed_SOS_Network` (SoftAP IP `192.168.4.1`).
  - Listens for incoming UDP packets on port `4330`.
  - Prints received JSON payloads over USB Serial at `115200` baud.

- **Laptop Serial Bridge Daemon (`hardware/bridge/serial_bridge.py`)**:
  - Automatically connects to `COM13` at 115200 baud.
  - Reads lines emitted by the Base Station ESP.
  - Parses JSON reports and forwards them via HTTP POST to `http://127.0.0.1:8000/api/reports?context=live`.
  - Tags report with `[OFFLINE ESP-NOW/UDP MESH]`.
  - Triggers Gemini 2.5 Flash Disaster Triage and surfaces reports instantly on the Command Dashboard map and Citizen Reports tab.

## 2. Required Disclosure Line

> *"LoRa link emulated using ESP32 (Wi-Fi SoftAP / UDP / BLE mesh). Same flow and packet constraints; production uses LoRa radios."*
