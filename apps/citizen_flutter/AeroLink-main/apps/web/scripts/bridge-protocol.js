/* eslint-disable @typescript-eslint/no-require-imports */
const { StringDecoder } = require('node:string_decoder');
const { createHash } = require('node:crypto');

class SerialJsonObjects {
  constructor(maxLength = 4096) {
    this.decoder = new StringDecoder('utf8');
    this.pending = '';
    this.maxLength = maxLength;
    this.started = false;
    this.overflow = false;
    this.depth = 0;
    this.inString = false;
    this.escaped = false;
  }

  push(chunk) {
    const objects = [];
    for (const char of this.decoder.write(chunk)) {
      if (!this.started) {
        if (char !== '{') continue;
        this.started = true;
      }
      if (!this.overflow) {
        this.pending += char;
        if (this.pending.length > this.maxLength) {
          this.pending = '';
          this.overflow = true;
        }
      }
      if (this.inString) {
        if (this.escaped) this.escaped = false;
        else if (char === '\\') this.escaped = true;
        else if (char === '"') this.inString = false;
      } else if (char === '"') this.inString = true;
      else if (char === '{' || char === '[') this.depth++;
      else if (char === '}' || char === ']') this.depth--;

      if (this.depth === 0 && !this.inString) {
        if (!this.overflow) objects.push(this.pending);
        this.pending = '';
        this.started = false;
        this.overflow = false;
      }
    }
    return objects;
  }
}

function normalizeReport(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('SOS must be a JSON object');
  if (typeof value.type !== 'string' || !value.type.trim()) throw new Error('type is required');
  if (typeof value.timestamp !== 'string' || Number.isNaN(Date.parse(value.timestamp))) throw new Error('timestamp must be ISO-8601 text');
  const latitude = typeof value.latitude === 'string' && value.latitude.trim() ? Number(value.latitude) : value.latitude;
  const longitude = typeof value.longitude === 'string' && value.longitude.trim() ? Number(value.longitude) : value.longitude;
  const peopleAffected = typeof value.peopleAffected === 'string' && value.peopleAffected.trim() ? Number(value.peopleAffected) : value.peopleAffected;
  if (!Number.isFinite(latitude) || Math.abs(latitude) > 90) throw new Error('latitude is invalid');
  if (!Number.isFinite(longitude) || Math.abs(longitude) > 180) throw new Error('longitude is invalid');
  if (!Number.isInteger(peopleAffected) || peopleAffected < 0) throw new Error('peopleAffected is invalid');
  if (!Array.isArray(value.conditions) || value.conditions.some(item => typeof item !== 'string' || !item.trim())) throw new Error('conditions is invalid');
  if (typeof value.additionalDetails !== 'string') throw new Error('additionalDetails must be text');
  return {
    type: value.type.trim(),
    timestamp: value.timestamp,
    latitude,
    longitude,
    peopleAffected,
    conditions: value.conditions.map(item => item.trim()),
    additionalDetails: value.additionalDetails.trim(),
  };
}

function reportMessage(report) {
  return [
    report.additionalDetails,
    `People affected: ${report.peopleAffected}.`,
    report.conditions.length ? `Conditions: ${report.conditions.map(item => item.replace(/([a-z])([A-Z])/g, '$1 $2')).join(', ')}.` : '',
  ].filter(Boolean).join('\n');
}

function stableTicketId(report) {
  const hex = createHash('sha256').update(JSON.stringify(report)).digest('hex').slice(0, 12);
  return `TKT-${(BigInt(`0x${hex}`) % 1000000000000n).toString().padStart(12, '0')}`;
}

function parseSignalLine(line) {
  const text = line.trim();
  if (!text.startsWith('{')) return null;
  const parsed = JSON.parse(text);
  // The current base firmware also prints its transport ACK as JSON.
  if (parsed?.type === 'ACK' && typeof parsed.status === 'string') return null;
  const report = normalizeReport(parsed);
  return {
    ticketId: stableTicketId(report),
    victimName: 'Victim ESP32',
    manualLocation: `${report.latitude}, ${report.longitude}`,
    message: reportMessage(report),
    report,
  };
}

module.exports = { SerialJsonObjects, normalizeReport, reportMessage, parseSignalLine };
