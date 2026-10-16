"""Serial Bridge daemon connecting the ESP32 Base Station (COM13) to the Lakhimpur Control Center.

Reads newline-delimited JSON packets from the Base Station ESP32 over USB Serial (115200 baud)
and forwards them to the Command Dashboard FastAPI backend at http://127.0.0.1:8000/api/reports?context=live.
"""
import json
import logging
import os
import sys
import time
from typing import Any

import httpx
import serial
import serial.tools.list_ports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SerialBridge] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("SerialBridge")

API_URL = os.environ.get("REPORTS_API_URL", "http://127.0.0.1:8000/api/reports?context=live")
DEFAULT_BAUD = int(os.environ.get("SERIAL_BAUD", "115200"))
DEFAULT_PORT = os.environ.get("SERIAL_PORT", "COM13")


def find_esp32_port(preferred: str = DEFAULT_PORT) -> str | None:
    """Finds the CP210x / CH340 / ESP32 serial COM port."""
    ports = list(serial.tools.list_ports.comports())
    # 1. Check if preferred port exists
    for p in ports:
        if p.device.upper() == preferred.upper():
            return p.device

    # 2. Look for CP210x or USB to UART
    for p in ports:
        desc = (p.description or "").lower()
        if "cp210" in desc or "ch340" in desc or "uart" in desc or "usb-to-serial" in desc:
            return p.device

    # 3. Fallback to preferred if nothing matched
    return preferred if ports else None


def clean_and_parse_json(line: str) -> dict[str, Any] | None:
    """Attempts to find and deserialize a JSON object from a serial line."""
    line = line.strip()
    if not line:
        return None

    # Find boundaries of JSON object if there's surrounding text
    start = line.find("{")
    end = line.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = line[start : end + 1]
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return None


def forward_to_backend(payload: dict[str, Any], client: httpx.Client) -> bool:
    """Forwards parsed report payload to the local Command Dashboard backend."""
    logger.info("Forwarding report to %s: %s", API_URL, json.dumps(payload)[:120])
    try:
        # Normalize fields for backend intake
        post_data = dict(payload)
        # Ensure offline tag or provider note is recorded
        if "description" in post_data:
            post_data["description"] = f"[OFFLINE ESP-NOW/UDP MESH] {post_data['description']}"
        elif "additionalDetails" in post_data:
            post_data["additionalDetails"] = f"[OFFLINE ESP-NOW/UDP MESH] {post_data['additionalDetails']}"
        else:
            post_data["description"] = "[OFFLINE ESP-NOW/UDP MESH]"

        res = client.post(API_URL, json=post_data, timeout=30.0)
        if res.is_success:
            result = res.json()
            report_id = result.get("report", {}).get("id") or result.get("id")
            triage = result.get("gemini_triage") or {}
            urgency = triage.get("urgency", "UNKNOWN")
            score = triage.get("priority_score", "N/A")
            logger.info(
                "✓ REPORT INGESTED! ID: %s | Urgency: %s | AI Score: %s | Status: %s",
                report_id,
                urgency,
                score,
                res.status_code,
            )
            return True
        else:
            logger.error("Backend rejected report: %s - %s", res.status_code, res.text)
            return False
    except Exception as exc:
        logger.error("Failed to post report to backend: %s", exc)
        return False


def run_bridge(port: str | None = None, baud: int = DEFAULT_BAUD):
    """Main serial reading and forwarding loop."""
    target_port = port or find_esp32_port()
    if not target_port:
        logger.error("No serial ports found on system!")
        return

    logger.info("Starting ESP32 Base Station Serial Bridge on %s @ %d baud", target_port, baud)
    logger.info("Destination API: %s", API_URL)

    client = httpx.Client(timeout=30.0)

    while True:
        try:
            logger.info("Connecting to %s...", target_port)
            ser = serial.Serial(target_port, baud, timeout=1.0)
            logger.info("✓ Connected to %s! Listening for incoming ESP-to-ESP packets...", target_port)

            while True:
                try:
                    raw_bytes = ser.readline()
                    if not raw_bytes:
                        continue

                    line = raw_bytes.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue

                    # Log non-empty diagnostics from ESP
                    logger.debug("ESP: %s", line)

                    # Check for JSON report packet
                    doc = clean_and_parse_json(line)
                    if doc:
                        # Ignore pure ACKs or telemetry that aren't SOS reports
                        doc_type = doc.get("type", "").upper()
                        if doc_type == "ACK" or doc.get("status") == "BASE_STATION_RECEIVED":
                            logger.info("ESP ACK: %s", line)
                            continue

                        logger.info("🚨 INCOMING REPORT RECEIVED OVER RADIO: %s", line)
                        forward_to_backend(doc, client)
                    elif "Base station ready" in line or "ready at" in line:
                        logger.info("Base Station Status: %s", line)

                except serial.SerialException as exc:
                    logger.warning("Serial read error: %s", exc)
                    break

            ser.close()

        except serial.SerialException as exc:
            logger.warning("Unable to open %s (%s). Retrying in 3 seconds...", target_port, exc)
            time.sleep(3.0)
        except KeyboardInterrupt:
            logger.info("Stopping Serial Bridge.")
            break
        except Exception as exc:
            logger.error("Unexpected error: %s", exc)
            time.sleep(2.0)


if __name__ == "__main__":
    port_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_bridge(port_arg)
