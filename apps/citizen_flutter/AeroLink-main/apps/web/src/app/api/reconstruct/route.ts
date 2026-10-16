export const dynamic = 'force-dynamic';
import { NextResponse } from "next/server";
import { getTickets, saveTickets, withTicketLock } from "@/lib/db";
import { reconstructSignal } from "@/lib/intelligence";
import { checkAuth } from "@/lib/auth";
import { openTicket } from "@/lib/ticket-analysis";
import { normalizeRequestStatus } from "@/lib/ticket-status";

export async function POST(req: Request) {
  if (!(await checkAuth())) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return withTicketLock(async () => {
    try {
      const body = await req.json();
      const { text, location, source } = body;
      
      // Use shared intelligence utility
      const result = await reconstructSignal(text);
      
      const ticket = {
        id: Math.random().toString(36).substring(2, 9),
        original: text, 
        reconstructed: result.reconstructed, 
        urgency: result.urgency, 
        category: result.category,
        location: location || { lat: 0, lng: 0 }, 
        timestamp: new Date().toISOString(), 
        status: "active",
        analysisStatus: "complete" as const,
        markerColor: "none" as const,
        adminNotes: [] as { text: string; timestamp: string; sender: "admin" | "system" }[],
        source: source || "Manual Uplink"
      };
      
      const tickets = getTickets();
      tickets.push(ticket);
      saveTickets(tickets);
      return NextResponse.json(ticket);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Unknown error";
      return NextResponse.json({ error: message }, { status: 500 });
    }
  });
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const idStr = searchParams.get("ids");
  if (!idStr && !(await checkAuth())) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const tickets = getTickets();
  if (idStr) {
    const idList = idStr.split(",");
    const filtered = tickets.filter((t) => idList.includes(t.id));
    return NextResponse.json(filtered);
  }
  const id = searchParams.get("id");
  if (id) {
    const ticket = tickets.find((t) => t.id === id);
    return ticket ? NextResponse.json(ticket) : NextResponse.json({ error: "Not found" }, { status: 404 });
  }
  return NextResponse.json(tickets);
}

export async function PATCH(req: Request) {
  if (!(await checkAuth())) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const body = await req.json();
    const { id, action, status, note, markerColor, sender } = body;
    if (typeof id !== "string" || !id) {
      return NextResponse.json({ error: "Ticket id is required" }, { status: 400 });
    }

    if (action === "open") {
      try {
        const ticket = await openTicket(id);
        return NextResponse.json(ticket);
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : "AI processing failed";
        const statusCode = message === "Ticket not found" ? 404 : 500;
        return NextResponse.json({ error: message }, { status: statusCode });
      }
    }

    return withTicketLock(async () => {
      const tickets = getTickets();
      const index = tickets.findIndex((t) => t.id === id);
      if (index === -1) return NextResponse.json({ error: "Ticket not found" }, { status: 404 });
      if (status) {
        const normalizedStatus = normalizeRequestStatus(status);
        if (!normalizedStatus) {
          return NextResponse.json({ error: "Invalid request status" }, { status: 400 });
        }
        tickets[index].status = normalizedStatus;
      }
      if (markerColor) tickets[index].markerColor = markerColor;
      if (note) {
        tickets[index].adminNotes ||= [];
        tickets[index].adminNotes.push({ text: note, timestamp: new Date().toISOString(), sender: sender || "admin" });
      }
      saveTickets(tickets);
      return NextResponse.json(tickets[index]);
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
