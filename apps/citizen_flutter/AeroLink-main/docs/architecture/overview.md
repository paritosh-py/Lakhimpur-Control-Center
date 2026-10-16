# Architecture Overview

## Online
Flutter/Web → FastAPI → MongoDB Atlas

## Emergency offline
Flutter → local Wi-Fi → ESP32 → LoRa → Base Station

The emergency path must remain functional without public Internet.
