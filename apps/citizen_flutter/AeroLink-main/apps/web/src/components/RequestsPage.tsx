"use client";

import React, { useState, useEffect, useRef } from "react";
import { MapPin, Clock, MessageSquare, CheckCircle, Send, Radio, Inbox, Crosshair, Circle, X, Zap, AlertTriangle } from "lucide-react";
import SituationalMap from "./SituationalMap";
import { motion, AnimatePresence } from "framer-motion";
import EmergencyReportDetails from "./EmergencyReportDetails";
import type { Ticket } from "@/lib/db";
import { hasCompletedAnalysis, isActiveStatus, isPendingStatus, isResolvedStatus } from "@/lib/ticket-status";

const MARKER_LABELS: Record<string, { label: string; color: string; css: string }> = {
  green: { label: "Forces on the way", color: "#47E5BC", css: "bg-[#47E5BC]" },
  yellow: { label: "Message read", color: "#E5C247", css: "bg-[#E5C247]" },
  red: { label: "Not read", color: "#E5475A", css: "bg-[#E5475A]" },
  none: { label: "No status", color: "#5C5F6E", css: "bg-[#5C5F6E]" },
};

export default function RequestsPage({ searchQuery = "" }: { searchQuery?: string }) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [showCompletedModal, setShowCompletedModal] = useState(false);
  const [viewMode, setViewMode] = useState<"intake" | "priority">("intake");
  const [priorityOrder, setPriorityOrder] = useState<string[]>([]);
  const [priorityReasoning, setPriorityReasoning] = useState<Record<string, string>>({});
  const [isPrioritizing, setIsPrioritizing] = useState(false);
  const [priorityError, setPriorityError] = useState("");

  const unresolvedTickets = tickets.filter((ticket) => !isResolvedStatus(ticket.status));
  const completedTickets = tickets.filter((ticket) => isResolvedStatus(ticket.status));

  const filterFn = (t: Ticket) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      (t.reconstructed || "").toLowerCase().includes(query) ||
      (t.original || "").toLowerCase().includes(query) ||
      (t.victimName || "").toLowerCase().includes(query) ||
      (t.category || "").toLowerCase().includes(query) ||
      (t.manualLocation || "").toLowerCase().includes(query)
      || (t.report?.type || "").toLowerCase().includes(query)
      || (t.report?.conditions || []).some(condition => condition.toLowerCase().includes(query))
      || (t.report?.additionalDetails || "").toLowerCase().includes(query)
    );
  };

  const filteredUnresolvedTickets = unresolvedTickets.filter(filterFn);
  const filteredCompletedTickets = completedTickets.filter(filterFn);
  const priorityRanks = new Map(priorityOrder.map((id, index) => [id, index]));
  const displayedTickets = viewMode === "priority"
    ? [...filteredUnresolvedTickets].sort((left, right) => {
        const leftRank = priorityRanks.get(left.id);
        const rightRank = priorityRanks.get(right.id);
        if (leftRank !== undefined && rightRank !== undefined) return leftRank - rightRank;
        if (leftRank !== undefined) return -1;
        if (rightRank !== undefined) return 1;
        return right.urgency - left.urgency || new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime();
      })
    : filteredUnresolvedTickets;
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [outboundMsg, setOutboundMsg] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [processingTicketId, setProcessingTicketId] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<{ ticketId: string; message: string } | null>(null);
  const [baseCoord, setBaseCoord] = useState<{lat: number, lng: number} | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (navigator.geolocation && !baseCoord) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setBaseCoord({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => console.warn("Location permission denied"),
        { enableHighAccuracy: true }
      );
    }
  }, [baseCoord]);

  const fetchTickets = async () => {
    try {
      const r = await fetch(`/api/reconstruct?t=${Date.now()}`);
      if (!r.ok) return;
      const d = await r.json() as Ticket[];
      const s = [...d].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setTickets(s);
      setSelectedTicket(current => current ? s.find((t: Ticket) => t.id === current.id) ?? null : null);
    } catch {} finally { setIsLoading(false); }
  };
  useEffect(() => {
    void Promise.resolve().then(() => void fetchTickets());
    const interval = setInterval(fetchTickets, 3000);
    return () => clearInterval(interval);
  }, []);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [selectedTicket?.adminNotes?.length]);

  const openRequest = async (ticket: Ticket) => {
    setSelectedTicket(ticket);
    setAnalysisError(null);
    if (isResolvedStatus(ticket.status)) return;
    if (!isPendingStatus(ticket.status) && hasCompletedAnalysis(ticket)) return;
    if (processingTicketId === ticket.id) return;

    setProcessingTicketId(ticket.id);
    try {
      const response = await fetch("/api/reconstruct", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: ticket.id, action: "open" }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "AI processing failed");
      setSelectedTicket(data);
      await fetchTickets();
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "AI processing failed";
      setAnalysisError({ ticketId: ticket.id, message });
      await fetchTickets();
    } finally {
      setProcessingTicketId(null);
    }
  };

  const runPrioritization = async () => {
    setViewMode("priority");
    setIsPrioritizing(true);
    setPriorityError("");
    try {
      const response = await fetch("/api/prioritize", { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Prioritization failed");
      const prioritized = data as (Ticket & { tacticalReasoning?: string })[];
      setPriorityOrder(prioritized.map((ticket) => ticket.id));
      setPriorityReasoning(Object.fromEntries(
        prioritized
          .filter((ticket) => ticket.tacticalReasoning)
          .map((ticket) => [ticket.id, ticket.tacticalReasoning as string])
      ));
      await fetchTickets();
    } catch (error: unknown) {
      setPriorityError(error instanceof Error ? error.message : "Prioritization failed");
    } finally {
      setIsPrioritizing(false);
    }
  };

  const sendMessage = async () => {
    if (!outboundMsg.trim() || !selectedTicket) return;
    setIsUpdating(true);
    try {
      await fetch("/api/reconstruct", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: selectedTicket.id, note: outboundMsg, sender: "admin" }) });
      setOutboundMsg("");
      fetchTickets();
    } catch {} finally { setIsUpdating(false); }
  };

  const sendMarker = async (color: "green" | "yellow" | "red") => {
    if (!selectedTicket) return;
    setIsUpdating(true);
    const label = MARKER_LABELS[color].label;
    try {
      await fetch("/api/reconstruct", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: selectedTicket.id, markerColor: color, note: `[MARKER] ${label}`, sender: "system" }) });
      fetchTickets();
    } catch {} finally { setIsUpdating(false); }
  };

  const markComplete = async () => {
    if (!selectedTicket) return;
    setIsUpdating(true);
    try {
      const response = await fetch("/api/reconstruct", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: selectedTicket.id, status: "resolved" }) });
      if (response.ok) setSelectedTicket(await response.json());
      fetchTickets();
    } catch {} finally { setIsUpdating(false); }
  };

  const uc = (u: number) => u > 8 ? "var(--danger)" : u > 5 ? "var(--warning)" : "var(--mint)";

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 h-full pb-8">
      {/* LEFT: Feed */}
      <div className="xl:col-span-4 flex flex-col space-y-4">
        {/* Feed Header */}
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1">
            <button
              onClick={() => setViewMode("intake")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] font-semibold transition-colors ${viewMode === "intake" ? "bg-[var(--surface-2)] text-[var(--mint)]" : "text-[var(--text-3)] hover:text-[var(--text)]"}`}
            >
              <Inbox size={13} /> Intake
            </button>
            <button
              onClick={() => void runPrioritization()}
              disabled={isPrioritizing}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-[12px] font-semibold transition-colors disabled:opacity-60 ${viewMode === "priority" ? "bg-[var(--surface-2)] text-[var(--mint)]" : "text-[var(--text-3)] hover:text-[var(--text)]"}`}
            >
              <Zap size={13} className={isPrioritizing ? "animate-pulse" : ""} />
              {isPrioritizing ? "Analyzing..." : "Prioritize"}
            </button>
          </div>
          <span className="text-[12px] text-[var(--text-3)]">{displayedTickets.length} unresolved</span>
        </div>

        {priorityError && (
          <div className="flex items-start gap-2 rounded-lg border border-[rgba(229,71,90,0.25)] bg-[rgba(229,71,90,0.05)] p-3 text-[12px] text-[var(--danger)]">
            <AlertTriangle size={14} className="mt-0.5 shrink-0" />
            <span>{priorityError}</span>
          </div>
        )}

        {/* Ticket List */}
        <div className="space-y-2 overflow-y-auto max-h-[500px] pr-1 custom-scrollbar">
          {displayedTickets.map((t) => {
            const marker = MARKER_LABELS[t.markerColor || "none"];
            return (
              <div
                key={t.id}
                onClick={() => void openRequest(t)}
                className={`lucid-card cursor-pointer p-4 space-y-2 ${selectedTicket?.id === t.id ? "border-[var(--mint)]" : ""}`}
                style={{ borderLeftWidth: '3px', borderLeftColor: selectedTicket?.id === t.id ? 'var(--mint)' : marker.color }}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center gap-2">
                      {viewMode === "priority" && priorityRanks.has(t.id) && (
                        <span className="bc-badge bg-[var(--surface-2)] border border-[var(--border)] text-[var(--mint)]">#{(priorityRanks.get(t.id) ?? 0) + 1}</span>
                      )}
                      <span className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: uc(t.urgency) }}>{t.category || "Awaiting AI"}</span>
                    </div>
                    <p className="text-[14px] font-semibold text-[var(--text)] mt-0.5">{t.victimName || `Unit ${t.id}`}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {/* Marker dot */}
                    <div className={`w-2.5 h-2.5 rounded-full ${marker.css}`} title={marker.label} />
                    <span className="text-[11px] text-[var(--text-3)]">{new Date(t.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
                {t.manualLocation && t.manualLocation !== "Unknown Location" && (
                  <div className="flex items-center gap-1.5 text-[11px] text-[var(--text-3)]"><MapPin size={9} /> {t.manualLocation}</div>
                )}
                {t.report && (
                  <div className="flex flex-wrap gap-1.5 text-[10px]">
                    <span className="bc-badge bg-[var(--surface-2)] border border-[var(--border)]">{t.report.type}</span>
                    <span className="bc-badge bg-[var(--surface-2)] border border-[var(--border)]">{t.report.peopleAffected} affected</span>
                  </div>
                )}
                <p className="text-[13px] text-[var(--text-2)] line-clamp-2 leading-relaxed">{t.reconstructed || "Open this request to run AI analysis."}</p>
                <div className="flex items-center gap-3 pt-1.5 border-t border-[var(--border)] text-[11px] text-[var(--text-3)]">
                  <span className="font-semibold" style={{ color: uc(t.urgency) }}>{t.urgency > 0 ? `L${t.urgency}` : "Unscored"}</span>
                  <span className="flex items-center gap-1">{isActiveStatus(t.status) ? <CheckCircle size={9} className="text-[var(--mint)]" /> : <Clock size={9} />} {isPendingStatus(t.status) ? "pending" : "active"}</span>
                  {t.adminNotes.length > 0 && <MessageSquare size={9} className="text-[var(--plum)] ml-auto" />}
                </div>
              </div>
            );
          })}
          {!isLoading && displayedTickets.length === 0 && (
            <div className="bento-card border-dashed py-14 text-center">
              <p className="text-[13px] text-[var(--text-3)]">
                {unresolvedTickets.length === 0 ? "No unresolved requests" : "No matching requests"}
              </p>
            </div>
          )}
        </div>

        {/* Resolved Section */}
        <div className="border-t border-[var(--border)] pt-4 mt-2">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle size={14} className="text-[var(--text-3)]" />
            <span className="text-[15px] font-bold text-[var(--text)]">Resolved</span>
          </div>
          <button
            onClick={() => setShowCompletedModal(true)}
            className="w-full text-left p-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-2)] hover:border-[var(--mint)] transition-all cursor-pointer shadow-sm flex justify-between items-center"
          >
            <div>
              <p className="text-[14px] font-semibold text-[var(--text)]">Resolved Incidents</p>
              <p className="text-[11px] text-[var(--text-3)] mt-0.5">Archive of resolved signals</p>
            </div>
            <span className="bc-badge bg-[var(--surface-2)] border border-[var(--border)] text-[11px] font-semibold text-[var(--text-3)]">
              {filteredCompletedTickets.length} resolved
            </span>
          </button>
        </div>
      </div>

      {/* RIGHT: Detail */}
      <div className="xl:col-span-8 flex flex-col h-full">
        {selectedTicket ? (
          <div className="bento-card flex-1 flex flex-col">
            {/* Header */}
            <div className="flex justify-between items-start pb-5 mb-5 border-b border-[var(--border)]">
              <div>
                <p className="text-[12px] text-[var(--text-3)] mb-0.5">Signal #{selectedTicket.id}</p>
                <h3 className="text-lg font-bold text-[var(--text)]">{selectedTicket.victimName || "Unknown"}</h3>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className={`bc-badge border border-[var(--border)] ${isActiveStatus(selectedTicket.status) ? "text-[var(--mint)] bg-[var(--surface-2)]" : "text-[var(--warning)] bg-[var(--surface-2)]"}`}>
                    {isResolvedStatus(selectedTicket.status) ? "resolved" : isPendingStatus(selectedTicket.status) ? "pending" : "active"}
                  </span>
                  <span className="text-[11px] text-[var(--text-3)]">{new Date(selectedTicket.timestamp).toLocaleString()}</span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {/* Current marker display */}
                <div className="text-center px-4 py-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]">
                  <p className="text-[9px] text-[var(--text-3)] uppercase tracking-wider mb-1">Marker</p>
                  <div className="flex items-center gap-1.5 justify-center">
                    <div className={`w-3 h-3 rounded-full ${MARKER_LABELS[selectedTicket.markerColor || "none"].css}`} />
                    <span className="text-[12px] font-semibold" style={{ color: MARKER_LABELS[selectedTicket.markerColor || "none"].color }}>{MARKER_LABELS[selectedTicket.markerColor || "none"].label}</span>
                  </div>
                </div>
                <div className="text-center px-4 py-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]">
                  <p className="text-[9px] text-[var(--text-3)] uppercase tracking-wider mb-1">Triage</p>
                  <p className="text-xl font-light" style={{ color: uc(selectedTicket.urgency) }}>{selectedTicket.urgency > 0 ? selectedTicket.urgency : "—"}</p>
                </div>
                
                {/* Complete Button */}
                {!isResolvedStatus(selectedTicket.status) ? (
                  <button onClick={markComplete} disabled={isUpdating} className="h-full flex flex-col items-center justify-center px-4 py-2 rounded-lg border border-[var(--border)] bg-[var(--bg)] hover:bg-[var(--surface-2)] hover:border-[var(--mint)] text-[var(--text-3)] hover:text-[var(--mint)] transition-colors" title="Mark Rescue Complete">
                    <CheckCircle size={15} className="mb-1" />
                    <span className="text-[9px] uppercase tracking-wider font-bold">Close</span>
                  </button>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center px-4 py-2 rounded-lg border border-[var(--mint)] bg-[var(--surface-2)] text-[var(--mint)]" title="Rescue Completed">
                    <CheckCircle size={15} className="mb-1" />
                    <span className="text-[9px] uppercase tracking-wider font-bold">Closed</span>
                  </div>
                )}
              </div>
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 flex-1 overflow-y-auto custom-scrollbar pr-1">
              {/* Left: Signal Data */}
              <div className="space-y-4">
                {/* Broken/Raw Signal */}
                <div>
                  <p className="stat-label mb-2 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)]" /> Broken Signal (Raw)
                  </p>
                  <div className="p-3 rounded-lg bg-[var(--bg)] border border-[var(--border)] font-mono text-[14px] text-[var(--danger)] leading-relaxed">
                    &ldquo;{selectedTicket.original}&rdquo;
                  </div>
                </div>
                {/* AI Decoded */}
                <div>
                  <p className="stat-label mb-2 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--mint)]" /> AI Decoded
                  </p>
                  <div className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-[16px] text-[var(--text)] font-medium leading-snug">
                    {processingTicketId === selectedTicket.id || selectedTicket.analysisStatus === "processing"
                      ? <span className="text-[var(--mint)] animate-pulse">Analyzing emergency signal…</span>
                      : selectedTicket.reconstructed || "AI analysis will begin when this request is opened."}
                  </div>
                  {analysisError?.ticketId === selectedTicket.id && (
                    <div className="mt-2 flex items-start justify-between gap-3 rounded-lg border border-[rgba(229,71,90,0.25)] bg-[rgba(229,71,90,0.05)] p-3 text-[12px] text-[var(--danger)]">
                      <span className="flex items-start gap-2"><AlertTriangle size={14} className="mt-0.5 shrink-0" /> {analysisError.message}</span>
                      <button onClick={() => void openRequest(selectedTicket)} className="font-bold uppercase tracking-wider hover:underline">Retry</button>
                    </div>
                  )}
                  {priorityReasoning[selectedTicket.id] && (
                    <div className="mt-2 rounded-lg border border-[var(--border)] bg-[var(--bg)] p-3">
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--plum)]">Priority reasoning</p>
                      <p className="mt-1 text-[13px] font-normal leading-relaxed text-[var(--text-2)]">{priorityReasoning[selectedTicket.id]}</p>
                    </div>
                  )}
                </div>
                {/* Location */}
                <div>
                  <p className="stat-label mb-2">Location Tracker</p>
                  <div className="h-[200px] mb-3">
                    <SituationalMap tickets={[selectedTicket]} baseCoord={baseCoord} height={200} />
                  </div>
                  <div className="p-3.5 rounded-xl bg-[var(--surface-2)] border border-[var(--border)] flex items-center gap-4">
                    <div className="w-9 h-9 rounded-full bg-[var(--bg)] flex items-center justify-center border border-[var(--border)] shrink-0 shadow-sm">
                      <Crosshair size={15} className="text-[var(--text-2)]" />
                    </div>
                    <div>
                      {selectedTicket.manualLocation && selectedTicket.manualLocation.includes(",") ? (
                        <p className="text-[14px] font-bold text-[var(--text)] font-mono">{selectedTicket.manualLocation}</p>
                      ) : (
                        <>
                          <p className="text-[14px] font-bold text-[var(--text)] font-mono">{(selectedTicket.location?.lat ?? 0).toFixed(6)}, {(selectedTicket.location?.lng ?? 0).toFixed(6)}</p>
                          <p className="text-[11px] text-[var(--text-3)] mt-0.5 uppercase tracking-wider">{selectedTicket.manualLocation || "No manual location"}</p>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Color Marker Buttons */}
                <div className="pt-2 border-t border-[var(--border)] mt-4">
                  <p className="stat-label text-[var(--teal)] mb-3 flex items-center gap-1.5"><Radio size={12}/> Dispatch Status Marker</p>
                  <div className="grid grid-cols-3 gap-3">
                    {(["green", "yellow", "red"] as const).map((c) => {
                      const m = MARKER_LABELS[c];
                      const isActive = selectedTicket.markerColor === c;
                      return (
                        <button
                          key={c}
                          onClick={() => sendMarker(c)}
                          disabled={isUpdating}
                          className={`flex flex-col items-center justify-center gap-2 py-3 rounded-xl border transition-all ${
                            isActive
                              ? `border-[${m.color}] bg-[var(--surface-2)] shadow-sm`
                              : "border-[var(--border)] bg-[var(--bg)] hover:bg-[var(--surface-2)] hover:border-[var(--text-3)]"
                          }`}
                          style={{ borderColor: isActive ? m.color : undefined }}
                        >
                          <Circle size={11} fill={m.color} stroke="none" className={isActive ? "animate-pulse" : ""} />
                          <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: isActive ? m.color : "var(--text-3)" }}>
                            {c === "green" ? "Forces En Route" : m.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Right: Chat */}
              <div className="flex flex-col">
                <p className="stat-label mb-2">Communications</p>

                {/* Chat Messages */}
                <div className="flex-1 min-h-[220px] max-h-[420px] overflow-y-auto rounded-xl bg-[var(--surface-2)] border border-[var(--border)] p-4 space-y-3 custom-scrollbar shadow-inner mt-1">
                  {selectedTicket.adminNotes.length > 0 ? selectedTicket.adminNotes.map((n, i) => {
                    const isSystem = n.sender === "system";
                    const isMarker = n.text.startsWith("[MARKER]");
                    return (
                      <div key={i} className={`flex flex-col ${isSystem ? "items-center my-3" : "items-end"}`}>
                        {isMarker ? (
                          <div className="px-3 py-1 rounded-full bg-[var(--bg)] border border-[var(--border)] text-[11px] font-semibold text-[var(--text-3)] text-center uppercase tracking-wider shadow-sm">
                            {n.text.replace("[MARKER] ", "")} · {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        ) : (
                          <div className="max-w-[75%]">
                            <div className="px-4 py-2.5 rounded-2xl rounded-tr-sm bg-[var(--mint)] text-[var(--bg)] shadow-sm">
                              <p className="text-[14px] font-medium leading-relaxed">{n.text}</p>
                            </div>
                            <p className="text-[10px] text-[var(--text-3)] mt-1 text-right font-medium">{new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                          </div>
                        )}
                      </div>
                    );
                  }) : <p className="text-[12px] text-[var(--text-3)] font-medium text-center py-10 opacity-70">Awaiting transmission. Send a message or status marker.</p>}
                  <div ref={chatEndRef} />
                </div>
              </div>
            </div>
            {selectedTicket.report && (
              <div className="mt-5 pt-5 border-t border-[var(--border)]">
                <p className="stat-label mb-2">Original emergency report</p>
                <EmergencyReportDetails report={selectedTicket.report} />
              </div>
            )}

            {/* Input Bar */}
            <div className="pt-5 mt-5 border-t border-[var(--border)] pb-2">
              <div className="flex gap-3 bg-[var(--surface-2)] p-1.5 rounded-2xl border border-[var(--border)] focus-within:border-[var(--mint)] transition-colors shadow-sm">
                <input type="text" value={outboundMsg} onChange={(e) => setOutboundMsg(e.target.value)} placeholder="Transmit a message to the victim..." className="bg-transparent flex-1 py-1.5 px-3 text-[14px] font-medium outline-none text-[var(--text)] placeholder:text-[var(--text-3)]" onKeyPress={(e) => e.key === 'Enter' && sendMessage()} />
                <button onClick={sendMessage} disabled={!outboundMsg.trim() || isUpdating} className="w-10 h-10 rounded-xl bg-[var(--mint)] text-[var(--bg)] flex items-center justify-center hover:opacity-90 disabled:opacity-30 transition-opacity shadow-sm">
                  <Send size={15} className="-ml-0.5" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center bento-card border-dashed">
            <Inbox size={32} className="text-[var(--text-3)] mb-3 opacity-30" />
            <p className="text-[14px] text-[var(--text-3)]">Select a signal from the feed</p>
          </div>
        )}
      </div>

      {/* Resolved Modal */}
      <AnimatePresence>
        {showCompletedModal && (
          <div className="fixed inset-0 z-[999] flex items-center justify-center p-6 bg-[rgba(17,17,17,0.4)] backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              className="w-full max-w-[500px] bento-card border border-[var(--border)] shadow-2xl relative overflow-hidden bg-[var(--surface)] max-h-[80vh] flex flex-col"
            >
              <div className="absolute top-0 left-0 w-full h-[3px] bg-[var(--mint)]" />
              
              {/* Header */}
              <div className="flex justify-between items-center border-b border-[var(--border)] pb-4 mb-4">
                <div>
                  <h3 className="text-base font-bold text-[var(--text)] uppercase tracking-wider flex items-center gap-2">
                    <CheckCircle size={16} className="text-[var(--mint)]" /> Resolved Incidents
                  </h3>
                  <p className="text-[11px] text-[var(--text-3)] mt-0.5">Archive of resolved signals</p>
                </div>
                <button 
                  onClick={() => setShowCompletedModal(false)}
                  className="p-1.5 rounded-md hover:bg-[var(--surface-2)] text-[var(--text-3)] hover:text-[var(--text)] transition-colors cursor-pointer"
                >
                  <X size={15} />
                </button>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar space-y-2">
                {filteredCompletedTickets.map((t) => {
                  const marker = MARKER_LABELS[t.markerColor || "none"];
                  return (
                    <div
                      key={t.id}
                      onClick={() => {
                        setSelectedTicket(t);
                        setShowCompletedModal(false);
                      }}
                      className={`lucid-card cursor-pointer p-4 space-y-2 transition-all hover:bg-[var(--surface-2)] hover:border-[var(--mint)] ${selectedTicket?.id === t.id ? "border-[var(--mint)]" : ""}`}
                      style={{ borderLeftWidth: '3px', borderLeftColor: marker.color }}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-3)]">{t.category}</span>
                          <p className="text-[14px] font-semibold text-[var(--text)] mt-0.5">{t.victimName || `Unit ${t.id}`}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className={`w-2.5 h-2.5 rounded-full ${marker.css}`} title={marker.label} />
                          <span className="text-[11px] text-[var(--text-3)]">{new Date(t.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                      {t.manualLocation && t.manualLocation !== "Unknown Location" && (
                        <div className="flex items-center gap-1.5 text-[11px] text-[var(--text-3)]"><MapPin size={9} /> {t.manualLocation}</div>
                      )}
                      <p className="text-[13px] text-[var(--text-2)] line-clamp-2 leading-relaxed">{t.reconstructed}</p>
                    </div>
                  );
                })}
                {filteredCompletedTickets.length === 0 && (
                  <div className="py-20 text-center">
                    <CheckCircle size={28} className="mx-auto mb-3 text-[var(--text-3)] opacity-20" />
                    <p className="text-[13px] text-[var(--text-3)]">No resolved incidents found</p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="border-t border-[var(--border)] pt-4 mt-4 text-right">
                <button 
                  onClick={() => setShowCompletedModal(false)}
                  className="sleek-btn sleek-btn-primary px-5 py-2"
                >
                  Close Archive
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
