export const dynamic = 'force-dynamic';
import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { getTickets, saveTickets, withTicketLock, type Ticket } from "@/lib/db";
import { emergencyReportMessage, parseEmergencyReport } from "@/lib/emergency-report";

const DATA_DIR = process.env.AEROLINK_DATA_DIR
  ? path.resolve(process.env.AEROLINK_DATA_DIR)
  : path.join(process.cwd(), "src/data");
const EXTERNAL_FILE = path.join(DATA_DIR, "external.json");

// ── Mutex for external.json serialization ──
let _extLock: Promise<void> = Promise.resolve();
function withExternalLock<T>(fn: () => Promise<T>): Promise<T> {
  let release: () => void;
  const next = new Promise<void>((resolve) => { release = resolve; });
  const wait = _extLock;
  _extLock = next;
  return wait.then(fn).finally(() => release!());
}

function getExternalData() {
  if (fs.existsSync(EXTERNAL_FILE)) {
    return JSON.parse(fs.readFileSync(EXTERNAL_FILE, "utf-8"));
  }
  return { message: "READY", state: "IDLE", timestamp: new Date().toISOString() };
}

function saveExternalData(data: Record<string, unknown>) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(EXTERNAL_FILE, JSON.stringify(data, null, 2));
}

export async function GET() {
  return NextResponse.json(getExternalData());
}

export async function POST(req: Request) {
  return withExternalLock(async () => {
    try {
      const body = await req.json();
      const reportInput = body.report ?? (body.type !== undefined ? body : undefined);
      const report = reportInput ? parseEmergencyReport(reportInput) : undefined;
      const rawMessage = report ? emergencyReportMessage(report) : body.message || "";
      const victimName = body.victimName || "Unknown";
      const manualLocation = report ? `${report.latitude}, ${report.longitude}` : body.manualLocation || "Unknown Location";
      const origId = body.origId || "";

      if (!rawMessage) return NextResponse.json({ error: "Empty signal" }, { status: 400 });

      const now = new Date();

      const result = await withTicketLock(async () => {
        const tickets = getTickets();
        const duplicate = tickets.find((ticket) =>
          (origId && ticket.id === origId) ||
          (
            ticket.original === rawMessage &&
            ticket.victimName === victimName &&
            (now.getTime() - new Date(ticket.timestamp).getTime()) < 15000
          )
        );

        if (duplicate) return { duplicate: true as const, ticketId: duplicate.id };

        const ticket: Ticket = {
          id: origId || Math.random().toString(36).substring(2, 9),
          original: rawMessage,
          report,
          reconstructed: "",
          urgency: 0,
          category: "Awaiting AI",
          location: report
            ? { lat: report.latitude, lng: report.longitude }
            : { lat: 0, lng: 0 },
          manualLocation,
          victimName,
          timestamp: now.toISOString(),
          status: "pending",
          analysisStatus: "pending",
          markerColor: "none",
          adminNotes: [],
          source: "ESP32 Device",
        };

        tickets.push(ticket);
        saveTickets(tickets);
        return { duplicate: false as const, ticket };
      });

      if (result.duplicate) {
        return NextResponse.json({ success: true, status: "duplicate suppressed", ticketId: result.ticketId });
      }

      saveExternalData({ 
        message: rawMessage, 
        state: "NEW_SIGNAL",
        timestamp: now.toISOString(), 
        victimName,
        manualLocation,
        origId,
        ticketId: result.ticket.id,
        report,
        isNew: true
      });

      return NextResponse.json({
        success: true,
        status: "Signal logged in Dispatcher Intake",
        ticketId: result.ticket.id,
      });
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Unknown error";
      return NextResponse.json({ error: message }, { status: 500 });
    }
  });
}

export async function PATCH(req: Request) {
  return withExternalLock(async () => {
    let ticketId = "";
    try {
      const body = await req.json();
      ticketId = typeof body.ticketId === "string" ? body.ticketId : "";
    } catch {
      // An empty body still clears the current notification for legacy clients.
    }

    const current = getExternalData();
    if (ticketId && current.ticketId && current.ticketId !== ticketId) {
      return NextResponse.json({ success: true, status: "newer notification retained" });
    }

    saveExternalData({ message: "SCANNING...", state: "IDLE", timestamp: new Date().toISOString() });
    return NextResponse.json({ success: true });
  });
}
