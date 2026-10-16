"""Citizen and ground reports store with Gemini AI prioritization and repeat-device tracking."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import uuid

import httpx
from engine.config import ROOT

logger = logging.getLogger(__name__)

# Ensure local .env is loaded if present
def _load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

_load_env()


class GeminiTriageService:
    """Triage and prioritize citizen flood reports using Gemini API with deterministic fallback."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def fallback_triage(self, data: dict, prior_count: int = 0) -> dict:
        """Deterministic heuristic fallback when Gemini API is unavailable or offline."""
        desc = (data.get("description") or "").lower()
        incident_type = (data.get("incident_type") or "").lower()
        conditions = [str(c).lower() for c in data.get("conditions") or []]
        people = int(data.get("people_affected") or 0)
        water_depth = float(data.get("water_depth_cm") or 0.0)
        water_trend = (data.get("water_trend") or "").lower()
        road_status = (data.get("road_status") or "").lower()

        is_critical = (
            "immediatedanger" in conditions
            or "trapped" in conditions
            or any(w in desc for w in ["trapped", "stranded", "roof", "drowning", "wash away", "swept", "life", "submerged house"])
            or incident_type in ["rescue_sos", "medical"] and people > 0
        )
        is_road_closure = (
            road_status in ["blocked", "impassable"]
            or "road_closure" in incident_type
            or any(w in desc for w in ["road cut", "bridge wash", "blocked", "underwater road", "impassable", "tree fallen"])
        )
        is_water_rising = water_trend == "rising" or "flood" in incident_type or water_depth >= 40.0

        if is_critical:
            urgency = "CRITICAL"
            score = 95
            primary_hazard = "rescue_emergency"
            action = "Dispatch immediate rescue/boat team to reported coordinates"
            needs = ["rescue", "boat", "evacuation"]
        elif is_road_closure:
            urgency = "HIGH"
            score = 80
            primary_hazard = "road_blockage"
            action = "Log road blockage, flag affected segment, update route planner"
            needs = ["road_assessment", "barrier"]
        elif is_water_rising or people > 0:
            urgency = "HIGH" if water_depth >= 60 else "MEDIUM"
            score = 70 if water_depth >= 60 else 55
            primary_hazard = "flood_rising"
            action = "Monitor water ingress and alert nearest relief center"
            needs = ["evacuation_monitoring", "sandbags"]
        else:
            urgency = "LOW"
            score = 30
            primary_hazard = "general"
            action = "Log report in general observation records"
            needs = []

        return {
            "urgency": urgency,
            "urgency_score": score,
            "primary_hazard": primary_hazard,
            "summary": data.get("description") or f"Report of {incident_type} in {data.get('settlement_name', 'Lakhimpur')}",
            "recommended_action": action,
            "extracted_needs": needs,
            "road_closure_asserted": is_road_closure,
            "road_closure_details": "Road reported blocked or impassable" if is_road_closure else None,
            "rationale": f"Deterministic heuristic classification based on conditions: {conditions}, people: {people}, road: {road_status}.",
            "triage_source": "rule_heuristic",
        }

    async def triage_report(self, data: dict, prior_count: int = 0) -> dict:
        """Analyze and prioritize incoming report via Gemini AI model."""
        if not self.api_key:
            return self.fallback_triage(data, prior_count)

        prompt = f"""You are an emergency disaster response triage officer for Lakhimpur district, Assam flood response.
Evaluate this citizen ground report and prioritize it for emergency operators.

Report Details:
- Incident Type: {data.get('incident_type')}
- Stated Conditions: {data.get('conditions')}
- Citizen Description: "{data.get('description', '')}"
- Location / Settlement: {data.get('settlement_name', 'Unknown')}
- Coordinates: ({data.get('latitude')}, {data.get('longitude')})
- People affected: {data.get('people_affected', 0)}
- Water depth: {data.get('water_depth_cm', 'N/A')} cm, Trend: {data.get('water_trend', 'unknown')}
- Reported road status: {data.get('road_status', 'unknown')}
- Previous reports from this device ID: {prior_count}

Classify and return strictly valid JSON:
{{
  "urgency": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "urgency_score": <integer 1 to 100>,
  "primary_hazard": "rescue_emergency" | "road_blockage" | "flood_rising" | "medical_need" | "infrastructure" | "general",
  "summary": "<one concise sentence for the dispatcher>",
  "recommended_action": "<concrete immediate action recommendation>",
  "extracted_needs": ["boat", "medical", "evacuation", "food_water", "road_assessment"],
  "road_closure_asserted": <true or false>,
  "road_closure_details": "<short description if road is claimed closed, or null>",
  "rationale": "<1-2 sentences explaining why this urgency was assigned>"
}}
Rules:
- If life is in danger, people are stranded on roofs, drowning, or trapped without access, mark CRITICAL (urgency_score >= 85).
- If key roads/bridges are cut off, water is rising rapidly into houses, or people are cut off, mark HIGH (urgency_score 70-84).
- If roads have minor water or water is in fields, mark MEDIUM (urgency_score 40-69).
- If water is receding or routine information, mark LOW (urgency_score 1-39).
- If multiple reports come from the same device ({prior_count} prior), note whether this indicates an escalating emergency.
"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{self.endpoint}?key={self.api_key}",
                    json=payload,
                )
                if res.status_code == 200:
                    body = res.json()
                    candidates = body.get("candidates", [])
                    if candidates:
                        text_part = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed = json.loads(text_part)
                        parsed["triage_source"] = "gemini_ai"
                        # Sanitize expected keys
                        if "urgency" not in parsed:
                            parsed["urgency"] = "MEDIUM"
                        if "urgency_score" not in parsed:
                            parsed["urgency_score"] = 50
                        return parsed
                logger.warning("Gemini API call returned status %s: %s", res.status_code, res.text[:200])
        except Exception as e:
            logger.warning("Gemini triage failed, falling back to heuristic: %s", e)

        fallback = self.fallback_triage(data, prior_count)
        return fallback


class ReportStore:
    """Transactional SQLite ledger for citizen & ground reports."""

    def __init__(self, path: Path | None = None):
        self.path = path or ROOT / "data/runtime/operations.sqlite3"

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS citizen_reports (
                id TEXT PRIMARY KEY,
                context TEXT NOT NULL,
                device_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                sender_name TEXT,
                sender_phone TEXT,
                incident_type TEXT NOT NULL,
                settlement_id TEXT,
                settlement_name TEXT,
                latitude REAL,
                longitude REAL,
                people_affected INTEGER,
                severity_level TEXT NOT NULL,
                water_depth_cm REAL,
                water_trend TEXT,
                road_status TEXT,
                description TEXT,
                conditions TEXT,
                gemini_triage TEXT,
                urgency TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                received_at TEXT NOT NULL
              );
              CREATE INDEX IF NOT EXISTS idx_reports_context ON citizen_reports(context);
              CREATE INDEX IF NOT EXISTS idx_reports_device ON citizen_reports(context, device_id);
            """)
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def count_prior_device_reports(self, context: str, device_id: str) -> int:
        """Count prior reports from this device in this context."""
        with self.transaction() as db:
            row = db.execute(
                "SELECT COUNT(*) AS cnt FROM citizen_reports WHERE context = ? AND device_id = ?",
                (context, device_id),
            ).fetchone()
            return int(row["cnt"]) if row else 0

    def save_report(self, payload: dict, triage: dict, context: str = "live") -> dict:
        """Save an incoming citizen report with its AI triage."""
        report_id = payload.get("id") or f"REP-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        device_id = str(payload.get("device_id") or "DEV-ANONYMOUS").strip()
        message_id = str(payload.get("message_id") or f"MSG-{uuid.uuid4().hex[:8].upper()}")

        conditions_json = json.dumps(payload.get("conditions") or [])
        triage_json = json.dumps(triage)
        urgency = triage.get("urgency", "MEDIUM")

        with self.transaction() as db:
            db.execute(
                """
                INSERT INTO citizen_reports (
                  id, context, device_id, message_id, sender_name, sender_phone,
                  incident_type, settlement_id, settlement_name, latitude, longitude,
                  people_affected, severity_level, water_depth_cm, water_trend,
                  road_status, description, conditions, gemini_triage, urgency,
                  status, timestamp, received_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    context,
                    device_id,
                    message_id,
                    payload.get("sender_name"),
                    payload.get("sender_phone"),
                    payload.get("incident_type") or "general",
                    payload.get("settlement_id"),
                    payload.get("settlement_name") or "Lakhimpur District",
                    payload.get("latitude"),
                    payload.get("longitude"),
                    int(payload.get("people_affected") or 0),
                    payload.get("severity_level") or urgency.lower(),
                    payload.get("water_depth_cm"),
                    payload.get("water_trend"),
                    payload.get("road_status"),
                    payload.get("description") or "",
                    conditions_json,
                    triage_json,
                    urgency,
                    "new",
                    payload.get("timestamp") or now,
                    now,
                ),
            )
        return self.get_report(report_id, context)

    def list_reports(self, context: str = "live") -> list[dict]:
        """List all reports for the given context with repeat-device annotations."""
        with self.transaction() as db:
            rows = db.execute(
                "SELECT * FROM citizen_reports WHERE context = ? ORDER BY rowid DESC",
                (context,),
            ).fetchall()
            # Calculate counts per device in this context
            device_counts = {}
            for r in rows:
                dev = r["device_id"]
                device_counts[dev] = device_counts.get(dev, 0) + 1

            results = []
            for r in rows:
                item = dict(r)
                item["conditions"] = json.loads(item["conditions"]) if item["conditions"] else []
                item["gemini_triage"] = json.loads(item["gemini_triage"]) if item["gemini_triage"] else {}
                item["device_total_reports"] = device_counts.get(item["device_id"], 1)
                item["is_repeat_device"] = item["device_total_reports"] > 1
                results.append(item)
            return results

    def get_report(self, report_id: str, context: str = "live") -> dict | None:
        """Fetch a single report by ID."""
        with self.transaction() as db:
            row = db.execute(
                "SELECT * FROM citizen_reports WHERE id = ? AND context = ?",
                (report_id, context),
            ).fetchone()
            if not row:
                return None
            item = dict(row)
            item["conditions"] = json.loads(item["conditions"]) if item["conditions"] else []
            item["gemini_triage"] = json.loads(item["gemini_triage"]) if item["gemini_triage"] else {}
            # Count for device
            dev_row = db.execute(
                "SELECT COUNT(*) as cnt FROM citizen_reports WHERE context = ? AND device_id = ?",
                (context, item["device_id"]),
            ).fetchone()
            cnt = int(dev_row["cnt"]) if dev_row else 1
            item["device_total_reports"] = cnt
            item["is_repeat_device"] = cnt > 1
            return item

    def get_device_history(self, device_id: str, context: str = "live") -> list[dict]:
        """Fetch all reports sent by a specific device."""
        with self.transaction() as db:
            rows = db.execute(
                "SELECT * FROM citizen_reports WHERE device_id = ? AND context = ? ORDER BY rowid DESC",
                (device_id, context),
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["conditions"] = json.loads(item["conditions"]) if item["conditions"] else []
                item["gemini_triage"] = json.loads(item["gemini_triage"]) if item["gemini_triage"] else {}
                results.append(item)
            return results

    def update_status(self, report_id: str, status: str, operator_note: str = "", context: str = "live") -> dict:
        """Update review or verification status of a report."""
        with self.transaction() as db:
            db.execute(
                "UPDATE citizen_reports SET status = ? WHERE id = ? AND context = ?",
                (status, report_id, context),
            )
        return self.get_report(report_id, context)

    def stats(self, context: str = "live") -> dict:
        """Get aggregate counts of reports."""
        with self.transaction() as db:
            total = db.execute("SELECT COUNT(*) AS c FROM citizen_reports WHERE context = ?", (context,)).fetchone()["c"]
            critical = db.execute("SELECT COUNT(*) AS c FROM citizen_reports WHERE context = ? AND urgency = 'CRITICAL'", (context,)).fetchone()["c"]
            high = db.execute("SELECT COUNT(*) AS c FROM citizen_reports WHERE context = ? AND urgency = 'HIGH'", (context,)).fetchone()["c"]
            road_blocked = db.execute(
                "SELECT COUNT(*) AS c FROM citizen_reports WHERE context = ? AND (road_status = 'blocked' OR incident_type = 'road_closure')",
                (context,),
            ).fetchone()["c"]
            closed = db.execute(
                "SELECT COUNT(*) AS c FROM citizen_reports WHERE context = ? AND status IN ('closed', 'resolved')",
                (context,),
            ).fetchone()["c"]
            unique_devices = db.execute(
                "SELECT COUNT(DISTINCT device_id) AS c FROM citizen_reports WHERE context = ?",
                (context,),
            ).fetchone()["c"]
            multi_reports = total - unique_devices
            return {
                "total": total,
                "critical": critical,
                "high": high,
                "road_blocked": road_blocked,
                "closed": closed,
                "active": max(0, total - closed),
                "unique_devices": unique_devices,
                "repeat_reports": max(0, multi_reports),
            }
