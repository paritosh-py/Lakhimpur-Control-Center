import fs from "fs";
import path from "path";
import { encrypt, decrypt } from "./encryption";
import { EmergencyReport } from "./emergency-report";
import type { AnalysisStatus } from "./ticket-status";

const DATA_DIR = process.env.AEROLINK_DATA_DIR
  ? path.resolve(process.env.AEROLINK_DATA_DIR)
  : path.join(process.cwd(), "src/data");
const TICKETS_FILE = path.join(DATA_DIR, "tickets.json");

export interface Ticket {
  id: string;
  original: string;
  reconstructed: string;
  urgency: number;
  category: string;
  location: { lat: number, lng: number };
  manualLocation?: string;
  victimName?: string;
  timestamp: string;
  status: string;
  markerColor: "green" | "yellow" | "red" | "none";
  adminNotes: { text: string, timestamp: string, sender: "admin" | "system" }[];
  source?: string;
  report?: EmergencyReport;
  analysisStatus?: AnalysisStatus;
}

export interface EncryptedTicket {
  id: string;
  original: string;
  reconstructed: string;
  urgency: number;
  category: string;
  location: string;
  manualLocation?: string;
  victimName?: string;
  timestamp: string;
  status: string;
  markerColor: "green" | "yellow" | "red" | "none";
  adminNotes: { text: string, timestamp: string, sender: "admin" | "system" }[];
  source?: string;
  report?: string;
  analysisStatus?: AnalysisStatus;
}

// ── In-process mutex for file I/O serialization ──
// Prevents concurrent API requests from clobbering each other's writes.
let _lockChain: Promise<void> = Promise.resolve();

export function withTicketLock<T>(fn: () => Promise<T>): Promise<T> {
  let release: () => void;
  const next = new Promise<void>((resolve) => { release = resolve; });
  const wait = _lockChain;
  _lockChain = next;
  return wait.then(fn).finally(() => release!());
}

let cachedTickets: Ticket[] | null = null;
let cachedMtime: number = 0;

export function getTickets(): Ticket[] {
  if (fs.existsSync(TICKETS_FILE)) {
    const stat = fs.statSync(TICKETS_FILE);
    if (stat.mtimeMs === cachedMtime && cachedTickets !== null) {
      return cachedTickets;
    }

    const fileData = fs.readFileSync(TICKETS_FILE, "utf-8");
    const serializedTickets = JSON.parse(fileData) as EncryptedTicket[];
    
    const tickets = serializedTickets.map((t) => {
      try {
        return {
          ...t,
          original: decrypt(t.original),
          reconstructed: decrypt(t.reconstructed),
          location: JSON.parse(decrypt(t.location)) as { lat: number; lng: number },
          manualLocation: t.manualLocation ? decrypt(t.manualLocation) : "",
          victimName: t.victimName ? decrypt(t.victimName) : "Unknown",
          report: t.report ? JSON.parse(decrypt(t.report)) as EmergencyReport : undefined,
          adminNotes: (t.adminNotes || []).map((n) => ({
            ...n,
            text: decrypt(n.text)
          }))
        } as Ticket;
      } catch {
        // Fallback for legacy data
        return t as unknown as Ticket;
      }
    });

    cachedTickets = tickets;
    cachedMtime = stat.mtimeMs;
    return tickets;
  }
  return [];
}

export function saveTickets(tickets: Ticket[]) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  const encryptedTickets = tickets.map((t) => ({
    ...t,
    original: encrypt(t.original),
    reconstructed: encrypt(t.reconstructed),
    location: encrypt(JSON.stringify(t.location)),
    manualLocation: t.manualLocation ? encrypt(t.manualLocation) : "",
    victimName: t.victimName ? encrypt(t.victimName) : "",
    report: t.report ? encrypt(JSON.stringify(t.report)) : undefined,
    adminNotes: (t.adminNotes || []).map((n) => ({
      ...n,
      text: encrypt(n.text)
    }))
  }));
  fs.writeFileSync(TICKETS_FILE, JSON.stringify(encryptedTickets, null, 2));

  // Update cache immediately to avoid re-reading
  const stat = fs.statSync(TICKETS_FILE);
  cachedTickets = tickets;
  cachedMtime = stat.mtimeMs;
}
