/* eslint-disable @typescript-eslint/no-require-imports */
/**
 * AEROLINK SERIAL BRIDGE (ESP32 Duplex v3.1)
 * -------------------------------------------
 * Bridges the real ESP32 Base Station (Serial/USB) to the Next.js Dashboard.
 *
 * Extracts emergency JSON from the Base Station's diagnostic serial output.
 * USB chunks are buffered because serial reads are not message boundaries.
 * 
 * UPLINK:   Victim Phone → Victim ESP (UDP) → Base ESP (Serial) → BRIDGE → Dashboard API
 * DOWNLINK: Dashboard → BRIDGE → Base ESP (Serial) → UDP 4331 broadcast
 * 
 * RUN: node scripts/bridge.js COM13
 * LIST: node scripts/bridge.js --list
 */

const { SerialPort } = require('serialport');
const fs = require('fs');
const path = require('path');
const { SerialJsonObjects, parseSignalLine } = require('./bridge-protocol');

const API_ROOT = 'http://127.0.0.1:3000/api';
const BAUD_RATE = 115200;
const POLL_INTERVAL = 2000;
const DEDUP_WINDOW_MS = 10000; // Ignore duplicate SOS within this window

// ── Load admin password from .env.local ──
let adminPassword = process.env.ADMIN_PASSWORD || 'Aerolink2026!';
try {
  const envPath = path.join(process.cwd(), '.env.local');
  if (!process.env.ADMIN_PASSWORD && fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    const match = envContent.match(/ADMIN_PASSWORD=([^\s#]+)/);
    if (match) adminPassword = match[1];
  }
} catch { /* ignored */ }

// ── CLI Args ──
const args = process.argv.slice(2);
const portPath = args[0] || 'COM13';

if (portPath === '--list') {
  SerialPort.list().then(ports => {
    console.log('\n--- AVAILABLE SERIAL PORTS ---');
    if (ports.length === 0) {
      console.log('  No serial ports found. Is the Base Station ESP plugged in?');
    } else {
      ports.forEach(p => console.log(`  ${p.path}\t${p.manufacturer || 'Unknown'}`));
    }
    console.log('');
    process.exit(0);
  });
} else {

  // ── Open Serial Port to Base Station ESP ──
  const port = new SerialPort({ path: portPath, baudRate: BAUD_RATE }, (err) => {
    if (err) {
      console.error(`\n[FATAL] Cannot open ${portPath}: ${err.message}`);
      console.error(`[HINT] Run "node scripts/bridge.js --list" to see available ports.`);
      console.error(`[HINT] Make sure the Base Station ESP32 is plugged in via USB.\n`);
      process.exit(1);
    }
  });

  // ── State Tracking ──
  const seenNoteTimestamps = new Set();
  const MAX_SEEN = 500;
  const serialJson = new SerialJsonObjects();
  const forwarding = new Set();
  const recentSOS = new Map(); // ticketId → timestamp, for deduplication

  console.log(`\n╔══════════════════════════════════════════════════╗`);
  console.log(`║   AEROLINK BASE STATION BRIDGE v3.1              ║`);
  console.log(`╠══════════════════════════════════════════════════╣`);
  console.log(`║  Serial Port:  ${portPath.padEnd(33)}║`);
  console.log(`║  Baud Rate:    ${String(BAUD_RATE).padEnd(33)}║`);
  console.log(`║  API Server:   ${API_ROOT.padEnd(33)}║`);
  console.log(`║  Dedup Window: ${(DEDUP_WINDOW_MS/1000 + 's').padEnd(33)}║`);
  console.log(`╚══════════════════════════════════════════════════╝\n`);
  console.log(`[BRIDGE] Listening for SOS signals from ESP32...`);
  console.log(`[BRIDGE] Polling dashboard for admin replies every ${POLL_INTERVAL / 1000}s...\n`);

  // ═══════════════════════════════════════════════════
  // 1. UPLINK: ESP32 Base Station → Dashboard
  //    Extracts complete JSON objects from noisy or fragmented serial data.
  // ═══════════════════════════════════════════════════

  port.on('data', (chunk) => {
    for (const json of serialJson.push(chunk)) {
      try {
        const signal = parseSignalLine(json);
        if (!signal) continue;
        const lastSeen = recentSOS.get(signal.ticketId);
        if (forwarding.has(signal.ticketId) || (lastSeen && Date.now() - lastSeen < DEDUP_WINDOW_MS)) continue;
        forwarding.add(signal.ticketId);
        forwardToDashboard(signal).then(accepted => {
          if (accepted) recentSOS.set(signal.ticketId, Date.now());
        }).finally(() => forwarding.delete(signal.ticketId));
        for (const [id, time] of recentSOS) if (Date.now() - time > DEDUP_WINDOW_MS * 3) recentSOS.delete(id);
      } catch (error) {
        console.error(`[BRIDGE] Rejected invalid emergency JSON: ${error.message}`);
      }
    }
  });

  async function forwardToDashboard({ ticketId, victimName, manualLocation, message, report }) {
    const payload = {
      victimName,
      manualLocation,
      message,
      origId: ticketId,
      report
    };

    try {
      const res = await fetch(`${API_ROOT}/data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const text = await res.text();
        console.error(`[ERROR] Dashboard rejected signal (HTTP ${res.status}): ${text}`);
        return false;
      } else {
        const data = await res.json();
        if (data.status === 'duplicate suppressed') {
          console.log(`[BRIDGE] Signal suppressed (server-side duplicate).`);
        } else {
          console.log(`[BRIDGE] ✓ Signal forwarded to Admin Dashboard for review.`);
        }
        return true;
      }
    } catch (e) {
      console.error(`[ERROR] Dashboard unreachable: ${e.message}`);
      console.error(`[HINT] Is "npm run dev" running?`);
      return false;
    }
  }

  // ═══════════════════════════════════════════════════
  // 2. DOWNLINK: Dashboard Admin Reply → ESP32 → Victim
  // ═══════════════════════════════════════════════════
  setInterval(async () => {
    try {
      const res = await fetch(`${API_ROOT}/reconstruct?t=${Date.now()}`, {
        headers: { 'x-bridge-auth': adminPassword }
      });

      if (!res.ok) return;

      const tickets = await res.json();

      for (const ticket of tickets) {
        if (!ticket.adminNotes || ticket.adminNotes.length === 0) continue;

        for (const note of ticket.adminNotes) {
          const noteId = `${ticket.id}-${note.timestamp}`;

          if (!seenNoteTimestamps.has(noteId)) {
            seenNoteTimestamps.add(noteId);

            // Evict oldest to prevent memory leak
            if (seenNoteTimestamps.size > MAX_SEEN) {
              const oldest = seenNoteTimestamps.values().next().value;
              seenNoteTimestamps.delete(oldest);
            }

            console.log(`\n[ADMIN ↓] Reply for ${ticket.victimName || 'Unknown'}: ${note.text}`);

            // The Victim ESP checks: receivedMsg.indexOf(currentTicketID)
            // where currentTicketID = "TKT-xxxx"
            // ticket.id IS the TKT-xxxx (set from origId in approve route)
            const replyMsg = `[${ticket.id}] ${note.text}`;

            if (port.isOpen) {
              port.write(replyMsg + '\n', (err) => {
                if (err) {
                  console.error(`[ERROR] Serial write failed: ${err.message}`);
                } else {
                  console.log(`[BRIDGE] ✓ Reply relayed to Base Station → Victim ESP`);
                }
              });
            } else {
              console.warn(`[WARN] Serial port closed. Reply not sent: ${replyMsg}`);
            }
          }
        }
      }
    } catch {
      // Silently ignore network errors during polling
    }
  }, POLL_INTERVAL);

  // ── Error / Lifecycle Handling ──
  port.on('error', (err) => console.error(`[CRITICAL] Serial port error: ${err.message}`));
  port.on('close', () => {
    console.warn(`\n[WARN] Serial port ${portPath} disconnected.`);
    process.exit(1);
  });

  process.on('SIGINT', () => {
    console.log(`\n[BRIDGE] Shutting down...`);
    if (port.isOpen) port.close();
    process.exit(0);
  });

} // end else (not --list)
