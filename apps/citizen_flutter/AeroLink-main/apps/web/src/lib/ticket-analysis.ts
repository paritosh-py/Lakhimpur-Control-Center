import "server-only";

import { getTickets, saveTickets, withTicketLock, type Ticket } from "./db";
import { reconstructSignal } from "./intelligence";
import { hasCompletedAnalysis, isResolvedStatus } from "./ticket-status";

const analysisJobs = new Map<string, Promise<Ticket>>();

async function markActive(ticketId: string): Promise<void> {
  await withTicketLock(async () => {
    const tickets = getTickets();
    const ticket = tickets.find((item) => item.id === ticketId);
    if (!ticket) throw new Error("Ticket not found");
    if (isResolvedStatus(ticket.status)) throw new Error("Resolved tickets cannot be reopened");
    if (ticket.status !== "active") {
      ticket.status = "active";
      saveTickets(tickets);
    }
  });
}

export async function analyzeTicket(ticketId: string): Promise<Ticket> {
  const existingJob = analysisJobs.get(ticketId);
  if (existingJob) return existingJob;

  const job = (async () => {
    const source = await withTicketLock(async () => {
      const tickets = getTickets();
      const ticket = tickets.find((item) => item.id === ticketId);
      if (!ticket) throw new Error("Ticket not found");
      if (isResolvedStatus(ticket.status)) throw new Error("Resolved tickets do not require analysis");
      if (hasCompletedAnalysis(ticket)) return { ticket, requiresAnalysis: false };

      ticket.analysisStatus = "processing";
      saveTickets(tickets);
      return {
        ticket: { ...ticket },
        requiresAnalysis: true,
      };
    });

    if (!source.requiresAnalysis) return source.ticket;

    try {
      const analysis = await reconstructSignal(
        source.ticket.original,
        source.ticket.victimName,
        source.ticket.manualLocation,
      );

      return await withTicketLock(async () => {
        const tickets = getTickets();
        const ticket = tickets.find((item) => item.id === ticketId);
        if (!ticket) throw new Error("Ticket not found");
        ticket.reconstructed = analysis.reconstructed;
        ticket.urgency = analysis.urgency;
        ticket.category = analysis.category;
        ticket.analysisStatus = "complete";
        saveTickets(tickets);
        return ticket;
      });
    } catch (error) {
      await withTicketLock(async () => {
        const tickets = getTickets();
        const ticket = tickets.find((item) => item.id === ticketId);
        if (ticket) {
          ticket.analysisStatus = "failed";
          saveTickets(tickets);
        }
      });
      throw error;
    }
  })();

  analysisJobs.set(ticketId, job);
  try {
    return await job;
  } finally {
    analysisJobs.delete(ticketId);
  }
}

export async function openTicket(ticketId: string): Promise<Ticket> {
  await markActive(ticketId);
  return analyzeTicket(ticketId);
}
