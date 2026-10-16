export interface EmergencyReport {
  type: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  peopleAffected: number;
  conditions: string[];
  additionalDetails: string;
}

const text = (value: unknown, name: string, max: number, allowEmpty = false) => {
  if (typeof value !== "string" || (!allowEmpty && !value.trim()) || value.length > max) {
    throw new Error(`${name} is invalid`);
  }
  return value.trim();
};

const numeric = (value: unknown, name: string) => {
  const parsed = typeof value === "string" && value.trim() ? Number(value) : value;
  if (typeof parsed !== "number" || !Number.isFinite(parsed)) throw new Error(`${name} is invalid`);
  return parsed;
};

export function parseEmergencyReport(value: unknown): EmergencyReport {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Emergency report must be an object");
  const input = value as Record<string, unknown>;
  const timestamp = text(input.timestamp, "timestamp", 64);
  if (Number.isNaN(Date.parse(timestamp))) throw new Error("timestamp is invalid");
  const latitude = numeric(input.latitude, "latitude");
  const longitude = numeric(input.longitude, "longitude");
  if (Math.abs(latitude) > 90 || Math.abs(longitude) > 180) throw new Error("coordinates are invalid");
  const peopleAffected = numeric(input.peopleAffected, "peopleAffected");
  if (!Number.isInteger(peopleAffected) || peopleAffected < 0 || peopleAffected > 1_000_000) throw new Error("peopleAffected is invalid");
  if (!Array.isArray(input.conditions) || input.conditions.length > 30) throw new Error("conditions is invalid");
  return {
    type: text(input.type, "type", 64),
    timestamp,
    latitude,
    longitude,
    peopleAffected,
    conditions: input.conditions.map(item => text(item, "condition", 100)),
    additionalDetails: text(input.additionalDetails, "additionalDetails", 4000, true),
  };
}

export function emergencyReportMessage(report: EmergencyReport): string {
  return [
    report.additionalDetails,
    `People affected: ${report.peopleAffected}.`,
    report.conditions.length ? `Conditions: ${report.conditions.map(item => item.replace(/([a-z])([A-Z])/g, "$1 $2")).join(", ")}.` : "",
  ].filter(Boolean).join("\n");
}
