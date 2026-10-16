"use client";

import React, { useState, useEffect } from "react";
import { Radio, Shield, Clock, Cpu, RefreshCcw, Zap, CheckCircle2 } from "lucide-react";
import EmergencyReportDetails from "@/components/EmergencyReportDetails";
import type { EmergencyReport } from "@/lib/emergency-report";

interface MonitoredSignal {
  message: string;
  state: string;
  timestamp: string;
  victimName: string;
  report?: EmergencyReport;
}

export default function MonitorPage() {
  const [sig, setSig] = useState<MonitoredSignal>({ message: "LISTENING...", state: "IDLE", timestamp: "", victimName: "" });
  const [log, setLog] = useState<{ msg: string; time: string; status: string; name: string }[]>([]);

  useEffect(() => {
    const poll = async () => {
      try {
        const r = await fetch("/api/data"); if (!r.ok) return; const d = await r.json();
        if (d.timestamp !== sig.timestamp) { setSig(d); if (d.state !== "IDLE") setLog(p => [{ msg: d.message, time: new Date(d.timestamp).toLocaleTimeString(), status: d.state, name: d.victimName || "Unknown" }, ...p].slice(0, 10)); }
      } catch {}
    };
    const i = setInterval(poll, 1000); return () => clearInterval(i);
  }, [sig.timestamp]);

  const label = sig.state === "IDLE" ? "LISTENING" : sig.state === "NEW_SIGNAL" ? "LOGGED" : sig.state === "PROCESSING" ? "DECODING" : sig.state === "DISPATCHED" ? "UPLINKED" : sig.state;

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] font-[Inter,system-ui,sans-serif]">
      {/* Nav */}
      <nav className="border-b border-[var(--border)] px-8 py-4 flex justify-between items-center sticky top-0 z-50 bg-[var(--bg)]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[var(--mint)] flex items-center justify-center">
            <Cpu size={14} className="text-[var(--bg)]" />
          </div>
          <div>
            <h1 className="text-[14px] font-bold uppercase tracking-[3px]">Intelligence Node</h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="status-dot status-dot-live" />
              <span className="text-[10px] font-medium text-[var(--mint)] uppercase tracking-wider">Sync Active</span>
            </div>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          <div className="text-right hidden sm:block">
            <p className="text-[10px] text-[var(--text-3)] uppercase tracking-wider">Endpoint</p>
            <p className="text-[12px] text-[var(--frost)] font-mono">/api/data</p>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[var(--surface)] border border-[var(--border)]">
            <span className="status-dot status-dot-live" />
            <span className="text-[11px] font-semibold uppercase tracking-wider">Live</span>
          </div>
        </div>
      </nav>

      <main className="p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-6xl mx-auto">
          {/* Main */}
          <div className="lg:col-span-8">
            <div className="bento-card p-8 min-h-[420px] flex flex-col justify-center space-y-8">
              <div>
                <p className="stat-label mb-2">Intake Status</p>
                <h2 className="text-6xl font-extralight text-[var(--mint)] uppercase tracking-tighter leading-none">{label}</h2>
              </div>

              <div className="p-6 rounded-xl bg-[var(--bg)] border border-[var(--border)] space-y-4" style={{ borderLeftWidth: '3px', borderLeftColor: 'var(--mint)' }}>
                <div className="flex justify-between items-center pb-2 border-b border-[var(--border)]">
                  <span className="text-[11px] text-[var(--text-3)] uppercase tracking-wider italic">
                    {sig.victimName ? `${sig.victimName} · Payload` : "Awaiting Interrupt"}
                  </span>
                  <span className="text-[10px] text-[var(--mint)] font-mono">AES</span>
                </div>
                <p className="text-3xl font-extralight text-[var(--text)] leading-tight italic">
                  &ldquo;{sig.message || "Waiting..."}&rdquo;
                </p>
                <div className="flex justify-between items-center pt-2 text-[11px] text-[var(--text-3)]">
                  <span className="flex items-center gap-1.5"><Clock size={11} /> {sig.timestamp ? new Date(sig.timestamp).toLocaleTimeString() : "--:--:--"}</span>
                  <span className="flex items-center gap-1 text-[var(--teal)]"><Zap size={10} /> Validated</span>
                </div>
              </div>
              {sig.report && <EmergencyReportDetails report={sig.report} />}

              <div className="grid grid-cols-4 gap-3">
                {[
                  { icon: Radio, label: "Source", val: "ESP32", c: "var(--mint)" },
                  { icon: Shield, label: "Security", val: "AES-256", c: "var(--frost)" },
                  { icon: Zap, label: "Protocol", val: "CodeRed", c: "var(--warning)" },
                  { icon: CheckCircle2, label: "Dispatch", val: "Auto", c: "var(--mint)" },
                ].map((s, i) => (
                  <div key={i} className="lucid-card p-3 text-center">
                    <s.icon size={14} style={{ color: s.c }} className="mx-auto mb-1.5" />
                    <p className="text-[9px] text-[var(--text-3)] uppercase tracking-wider">{s.label}</p>
                    <p className="text-[12px] font-semibold text-[var(--text)]">{s.val}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Waterfall */}
          <div className="lg:col-span-4 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-[15px] font-bold text-[var(--text)]">Signal Log</h3>
              <RefreshCcw size={10} className="text-[var(--text-3)]" />
            </div>
            <div className="space-y-2 max-h-[550px] overflow-y-auto pr-1 custom-scrollbar">
              {log.map((l, i) => (
                <div key={i} className="lucid-card p-3.5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="bc-badge bg-[var(--surface-2)] border border-[var(--border)]" style={{ color: l.status === "DISPATCHED" ? 'var(--mint)' : 'var(--teal)' }}>{l.status}</span>
                    <span className="text-[10px] text-[var(--text-3)] font-mono">{l.time}</span>
                  </div>
                  <p className="text-[12px] font-semibold text-[var(--frost)] uppercase tracking-wider mb-1">{l.name}</p>
                  <p className="text-[13px] text-[var(--text-2)] italic border-l-2 border-[var(--plum)] pl-2.5">
                    &ldquo;{l.msg.slice(0, 70)}{l.msg.length > 70 ? '...' : ''}&rdquo;
                  </p>
                </div>
              ))}
              {log.length === 0 && (
                <div className="py-28 text-center">
                  <Radio size={28} className="mx-auto mb-3 text-[var(--text-3)] opacity-15" />
                  <p className="text-[11px] text-[var(--text-3)] uppercase tracking-[3px]">Scanning</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
