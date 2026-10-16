# AeroLink

AeroLink is an SIH 2026 off-grid disaster communication and preparedness system.

## Repository
- `apps/mobile` — Flutter Android-first citizen app
- `apps/web` — existing AeroLink website/dashboard
- `backend` — shared FastAPI backend
- `hardware/esp32` — ESP32 node firmware
- `hardware/base_station` — authority-side local receiver service
- `shared` — API contracts and shared JSON schemas
- `docs` — architecture/API/database/SIH documentation

## Core paths
Online: Mobile/Web → FastAPI → MongoDB Atlas

Emergency offline: Mobile → local Wi-Fi → ESP32 → LoRa → Base Station

The cloud database must never be required for the critical off-grid SOS path.
