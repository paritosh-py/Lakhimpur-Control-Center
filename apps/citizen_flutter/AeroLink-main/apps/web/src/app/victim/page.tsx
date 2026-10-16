"use client";

import React, { useState, useEffect, useRef } from "react";
import { Radio, Shield, History, ArrowLeft, Clock, AlertCircle, Wifi, Activity, Cpu, Zap, CheckCircle2, ChevronRight, Circle, MessageSquare } from "lucide-react";

const MARKER_LABELS: Record<string, { label: string; color: string; description: string }> = {
  green: { label: "Forces on the way", color: "#47E5BC", description: "Help is being dispatched to your location." },
  yellow: { label: "Message read", color: "#E5C247", description: "Your message has been received and read by command." },
  red: { label: "Not read", color: "#E5475A", description: "Your message has not been read yet." },
  none: { label: "Pending", color: "#5C5F6E", description: "Awaiting admin response." },
};

export default function VictimPage() {
  const [view, setView] = useState<"monitor" | "history" | "detail">("monitor");
  const [history, setHistory] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [sig, setSig] = useState({ message: "LISTENING...", state: "IDLE", timestamp: "" });
  const [log, setLog] = useState<{ msg: string; time: string; status: string }[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const poll = async () => { try { const r = await fetch("/api/data"); const d = await r.json(); if (d.timestamp !== sig.timestamp) { setSig(d); if (d.state !== "IDLE") setLog(p => [{ msg: d.message, time: new Date(d.timestamp).toLocaleTimeString(), status: d.state }, ...p].slice(0, 5)); } } catch {} };
    const i = setInterval(poll, 1000); return () => clearInterval(i);
  }, [sig.timestamp]);

  const fetchHistory = async () => {
    const ids = localStorage.getItem("myDistressTickets"); if (!ids) return;
    try { const r = await fetch(`/api/reconstruct?ids=${ids}`); if (r.ok) { const d = await r.json(); setHistory(d.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())); if (selected) { const u = d.find((t: any) => t.id === selected.id); if (u) setSelected(u); } } } catch {}
  };

  useEffect(() => { fetchHistory(); const i = setInterval(fetchHistory, 3000); return () => clearInterval(i); }, [selected?.id]);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [selected?.adminNotes?.length]);

  return (
    <div className="min-h-screen bg-[var(--bg)] flex flex-col font-[Inter,system-ui,sans-serif] text-[var(--text)]">
      {/* Nav */}
      <nav className="bg-[var(--surface)] px-8 py-4 flex justify-between items-center sticky top-0 z-50 border-b border-[var(--border)]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[var(--mint)] flex items-center justify-center rounded-lg">
            <Cpu size={14} className="text-[var(--bg)]" />
          </div>
          <div>
            <span className="text-[15px] font-bold uppercase tracking-wide block">Field Node</span>
            <div className="flex items-center gap-1.5">
              <span className="status-dot status-dot-live" />
              <span className="text-[10px] text-[var(--text-3)] font-medium uppercase tracking-wider">ESP32</span>
            </div>
          </div>
        </div>
        <div className="flex gap-5">
          {(["monitor", "history"] as const).map((t) => (
            <button key={t} onClick={() => setView(t)} className={`text-[12px] font-semibold uppercase tracking-wider py-1 border-b-2 ${(view === t || (t === "history" && view === "detail")) ? "text-[var(--mint)] border-[var(--mint)]" : "text-[var(--text-3)] border-transparent hover:text-[var(--text)]"}`}>
              {t === "history" && <History size={11} className="inline mr-1.5" />}{t === "monitor" ? "Monitor" : "History"}
            </button>
          ))}
        </div>
      </nav>

      <main className="flex-1 p-8">
        <div className="max-w-4xl mx-auto space-y-6">

          {/* MONITOR */}
          {view === "monitor" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
              <div className="lg:col-span-8">
                <div className="bento-card p-8 space-y-8">
                  <div>
                    <p className="stat-label mb-2">System State</p>
                    <h2 className="text-4xl font-extralight text-[var(--mint)] uppercase tracking-tighter">
                      {sig.state === "IDLE" ? "LISTENING..." : sig.state === "PROCESSING" ? "DECODING..." : sig.state === "DISPATCHED" ? "UPLINKED" : sig.state}
                    </h2>
                  </div>
                  <div className="p-5 rounded-lg bg-[var(--bg)] border border-[var(--border)] space-y-3">
                    <div className="flex justify-between text-[11px] text-[var(--text-3)] pb-2 border-b border-[var(--border)]">
                      <span>Payload</span>
                      <span className="text-[var(--teal)]">RF-IOT-{sig.timestamp.slice(-4)}</span>
                    </div>
                    <p className="text-2xl font-extralight text-[var(--text)] italic">&ldquo;{sig.message}&rdquo;</p>
                    <p className="text-[11px] text-[var(--text-3)] flex items-center gap-1"><Clock size={10} /> {sig.timestamp ? new Date(sig.timestamp).toLocaleTimeString() : "--:--:--"}</p>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {[{ icon: Activity, l: "Node", v: "ESP32", c: "var(--mint)" }, { icon: Zap, l: "Triage", v: "Auto", c: "var(--warning)" }, { icon: CheckCircle2, l: "Status", v: sig.state === "DISPATCHED" ? "Verified" : "Wait", c: "var(--teal)" }].map((s, i) => (
                      <div key={i} className="lucid-card p-3 text-center">
                        <s.icon size={14} style={{ color: s.c }} className="mx-auto mb-1" />
                        <p className="text-[9px] text-[var(--text-3)] uppercase">{s.l}</p>
                        <p className="text-[12px] font-semibold">{s.v}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="lg:col-span-4 space-y-3">
                <h3 className="text-[15px] font-bold">Signal Log</h3>
                {log.map((l, i) => (
                  <div key={i} className="lucid-card p-3" style={{ borderLeftWidth: '2px', borderLeftColor: 'var(--mint)' }}>
                    <div className="flex justify-between mb-1.5">
                      <span className="text-[10px] font-semibold text-[var(--teal)] uppercase">{l.status}</span>
                      <span className="text-[10px] text-[var(--text-3)]">{l.time}</span>
                    </div>
                    <p className="text-[13px] text-[var(--text-2)] italic">&ldquo;{l.msg.slice(0, 40)}{l.msg.length > 40 ? "..." : ""}&rdquo;</p>
                  </div>
                ))}
                {log.length === 0 && <div className="py-16 text-center"><Radio size={24} className="mx-auto mb-2 text-[var(--text-3)] opacity-15" /><p className="text-[11px] text-[var(--text-3)] uppercase tracking-wider">Scanning...</p></div>}
              </div>
            </div>
          )}

          {/* HISTORY */}
          {view === "history" && (
            <div className="bento-card p-6 space-y-4">
              <h2 className="text-base font-bold border-b border-[var(--border)] pb-3">Incident Log</h2>
              {history.length > 0 ? history.map((t) => {
                const marker = MARKER_LABELS[t.markerColor || "none"];
                return (
                  <div key={t.id} onClick={() => { setSelected(t); setView("detail"); }} className="group flex items-center justify-between py-4 px-3 border-b border-[var(--border)] last:border-b-0 cursor-pointer hover:bg-[var(--surface-2)] rounded-lg">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[11px] font-semibold text-[var(--teal)] uppercase">{t.category}</span>
                        {/* Marker status */}
                        <div className="flex items-center gap-1">
                          <Circle size={8} fill={marker.color} stroke="none" />
                          <span className="text-[10px] font-semibold" style={{ color: marker.color }}>{marker.label}</span>
                        </div>
                      </div>
                      <p className="text-[16px] font-medium text-[var(--text)] truncate group-hover:text-[var(--mint)]">{t.reconstructed}</p>
                      <p className="text-[11px] text-[var(--text-3)] mt-0.5">{new Date(t.timestamp).toLocaleTimeString()}</p>
                    </div>
                    <div className="flex items-center gap-2 ml-3 shrink-0">
                      {t.adminNotes?.length > 0 && <MessageSquare size={12} className="text-[var(--plum)]" />}
                      <ChevronRight size={14} className="text-[var(--text-3)] group-hover:text-[var(--mint)]" />
                    </div>
                  </div>
                );
              }) : (
                <div className="py-16 text-center"><AlertCircle size={28} className="mx-auto mb-2 text-[var(--text-3)] opacity-15" /><p className="text-[13px] text-[var(--text-3)]">No missions</p></div>
              )}
            </div>
          )}

          {/* DETAIL */}
          {view === "detail" && selected && (() => {
            const marker = MARKER_LABELS[selected.markerColor || "none"];
            return (
              <div className="space-y-4">
                <button onClick={() => setView("history")} className="sleek-btn sleek-btn-ghost text-[12px]"><ArrowLeft size={12} /> Back</button>
                <div className="bento-card p-6 space-y-5">
                  {/* Header */}
                  <div className="flex justify-between items-start pb-4 border-b border-[var(--border)]">
                    <div>
                      <p className="text-[11px] text-[var(--teal)] font-semibold uppercase tracking-wider mb-1">Ticket: {selected.id}</p>
                      <h3 className="text-lg font-bold">{selected.category}</h3>
                    </div>
                    <div className="text-center px-4 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]">
                      <p className="text-[9px] text-[var(--text-3)] uppercase tracking-wider mb-0.5">Status</p>
                      <p className="text-sm font-semibold text-[var(--mint)]">{selected.status}</p>
                    </div>
                  </div>

                  {/* Marker Banner */}
                  <div className="p-4 rounded-lg border flex items-center gap-4" style={{ borderColor: marker.color, backgroundColor: `${marker.color}08` }}>
                    <Circle size={16} fill={marker.color} stroke="none" className="shrink-0" />
                    <div>
                      <p className="text-[15px] font-bold" style={{ color: marker.color }}>{marker.label}</p>
                      <p className="text-[13px] text-[var(--text-2)] mt-0.5">{marker.description}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    {/* Left: Signal data */}
                    <div className="space-y-4">
                      {/* Raw / Broken message */}
                      <div>
                        <p className="stat-label mb-1.5 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)]" /> Your Original Message (Broken)
                        </p>
                        <div className="p-3 rounded-lg bg-[var(--bg)] border border-[var(--border)] font-mono text-[14px] text-[var(--danger)] italic leading-relaxed">
                          &ldquo;{selected.original}&rdquo;
                        </div>
                      </div>
                      {/* Decoded */}
                      <div>
                        <p className="stat-label mb-1.5 flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[var(--mint)]" /> AI Decoded Message
                        </p>
                        <div className="p-3 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-[16px] text-[var(--text)] font-medium leading-snug">
                          {selected.reconstructed}
                        </div>
                      </div>
                    </div>

                    {/* Right: Messages from command */}
                    <div className="flex flex-col">
                      <p className="stat-label mb-1.5">Messages from Command</p>
                      <div className="flex-1 min-h-[180px] max-h-[350px] overflow-y-auto rounded-lg bg-[var(--bg)] border border-[var(--border)] p-3 space-y-2 custom-scrollbar">
                        {selected.adminNotes?.length > 0 ? selected.adminNotes.map((n: any, i: number) => {
                          const isMarker = n.text.startsWith("[MARKER]");
                          return (
                            <div key={i} className={`flex flex-col ${isMarker ? "items-center" : "items-start"}`}>
                              {isMarker ? (
                                <div className="px-3 py-1.5 rounded-full bg-[var(--surface-2)] border border-[var(--border)] text-[11px] text-[var(--text-3)] text-center">
                                  {n.text.replace("[MARKER] ", "")} · {new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </div>
                              ) : (
                                <div className="max-w-[85%]">
                                  <div className="flex items-center gap-1.5 mb-0.5">
                                    <Shield size={9} className="text-[var(--teal)]" />
                                    <span className="text-[10px] font-semibold text-[var(--teal)] uppercase tracking-wider">Command</span>
                                  </div>
                                  <div className="px-3 py-2 rounded-lg bg-[var(--surface-2)] border border-[var(--border)]">
                                    <p className="text-[14px] text-[var(--text)] leading-relaxed">{n.text}</p>
                                  </div>
                                  <p className="text-[10px] text-[var(--text-3)] mt-0.5">{new Date(n.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
                                </div>
                              )}
                            </div>
                          );
                        }) : (
                          <div className="flex items-center justify-center h-full py-8">
                            <p className="text-[12px] text-[var(--text-3)] italic">No messages from command yet</p>
                          </div>
                        )}
                        <div ref={chatEndRef} />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      </main>

      <footer className="mt-auto py-6 text-center text-[11px] text-[var(--text-3)] uppercase tracking-[4px] border-t border-[var(--border)]">
        Aerolink Field Node · Alpha-9
      </footer>
    </div>
  );
}
