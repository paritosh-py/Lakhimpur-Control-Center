const net = require('net');
const os = require('os');
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args)).catch(() => globalThis.fetch(...args));

const TCP_PORT = 5555;
const API_ROOT = 'http://127.0.0.1:3000/api';
let activeSocket = null;
let lastDownlinkTime = new Date().toISOString();

function getLocalIp() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return '127.0.0.1';
}

console.log(`[BRIDGE] Direct Wi-Fi Bridge Initialized.`);
console.log(`[BRIDGE] Protocol: (Name|Location|Message)`);
console.log(`[BRIDGE] Monitoring for Admin Feedback...\n`);

const server = net.createServer((socket) => {
  activeSocket = socket;
  console.log(`[WIFI] Mobile phone connected from ${socket.remoteAddress}`);
  
  socket.on('data', async (data) => {
    const raw = data.toString().trim();
    console.log(`[WIFI -> API] Incoming Raw: ${raw}`);
    
    // Parse protocol: (Name|Location|Message)
    let victimName, manualLocation, message, origId;
    const match1 = raw.match(/\(([^|]+)\|([^|]+)\|([^)]+)\)/);
    const match2 = raw.match(/\[(TKT-\d+)\]\s*Name:\s*([^|]+)\|\s*Loc:\s*([^|]+)\|\s*Msg:\s*([^]+)/i);

    if (match2) {
      origId = match2[1];
      victimName = match2[2].trim();
      manualLocation = match2[3].trim();
      message = match2[4].trim();
    } else if (match1) {
      origId = null;
      victimName = match1[1].trim();
      manualLocation = match1[2].trim();
      message = match1[3].trim();
    }

    if (victimName) {
      console.log(`[BRIDGE] Parsed SOS from ${victimName}. Sending to Dashboard...`);
      const payload = { victimName, manualLocation, message, origId, lat: 0, lng: 0 };

      try {
        const res = await fetch(`${API_ROOT}/data`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        
        if (!res.ok) {
          const text = await res.text();
          console.error(`[ERROR] Server rejected signal (${res.status}): ${text}`);
        } else {
          const responseData = await res.json();
          if (responseData.status === "duplicate suppressed") {
             console.log(`[BRIDGE] Signal ignored (duplicate).`);
          } else {
             console.log(`[BRIDGE] Signal successfully forwarded to Admin Dashboard.`);
          }
        }
      } catch (e) { 
        console.error(`[ERROR] Dispatch Offline: ${e.message}`); 
      }
    } else {
      console.log(`[WARN] Non-protocol signal ignored: ${raw}`);
    }
  });

  socket.on('close', () => {
    console.log('[WIFI] Mobile phone disconnected.');
    if (activeSocket === socket) activeSocket = null;
  });
  
  socket.on('error', (err) => {
    console.error(`[WIFI ERROR] ${err.message}`);
    if (activeSocket === socket) activeSocket = null;
  });
});

server.listen(TCP_PORT, '0.0.0.0', () => {
  console.log(`[WIFI] Listening for mobile phone signals at:`);
  console.log(`       IP:   http://${getLocalIp()}:${TCP_PORT}`);
  console.log(`       Port: ${TCP_PORT}\n`);
});

// Downlink Polling
setInterval(async () => {
  try {
    const res = await fetch(`${API_ROOT}/reconstruct?t=${Date.now()}`);
    if (!res.ok) return;
    
    const tickets = await res.json();
    for (const t of tickets) {
      if (!t.adminNotes) continue;
      for (const note of t.adminNotes) {
        if (new Date(note.timestamp) > new Date(lastDownlinkTime)) {
          const out = `[COMMAND] New Feedback for ${t.victimName || "Unknown"}: ${note.text}`;
          console.log(out);
          if (activeSocket) {
             activeSocket.write(out + "\r\n");
          }
        }
      }
    }
    lastDownlinkTime = new Date().toISOString();
  } catch (e) {
    // Ignore fetch errors during polling
  }
}, 2000);
