"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Radio, MapPin, Gauge, Cpu, AlertTriangle } from "lucide-react";

interface ReconstructedMessage {
  id: string; original: string; reconstructed: string; urgency: number;
  category: string; entities: string[]; confidence: number; timestamp: Date;
}

export default function IntelligenceModule() {
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState<ReconstructedMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleReconstruct = async () => {
    if (!inputText.trim()) return;
    setIsProcessing(true); setError(null);
    try {
      const response = await fetch("/api/intelligence", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: inputText }) });
      const data = await response.json();
      if (data.error) { setError(data.error); }
      else { setMessages([{ ...data, id: Math.random().toString(36).substr(2, 9), timestamp: new Date() }, ...messages]); setInputText(""); }
    } catch { setError("Connection failed."); }
    finally { setIsProcessing(false); }
  };

  const urgencyColor = (u: number) => u >= 8 ? "var(--danger)" : u >= 5 ? "var(--warning)" : "var(--mint)";

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 h-full pb-8">
      {/* Decoder */}
      <div className="xl:col-span-4">
        <div className="bento-card h-full flex flex-col space-y-4">
          <div className="flex items-center gap-2 mb-1">
            <Radio size={15} className="text-[var(--mint)]" />
            <h2 className="text-[15px] font-bold text-[var(--text)]">Signal Decoder</h2>
          </div>
          <textarea value={inputText} onChange={(e) => setInputText(e.target.value)} placeholder="Paste raw fragmented signal..." className="bc-input flex-1 w-full p-3 text-[14px] resize-none min-h-[120px] rounded-lg" />
          {error && <p className="text-[13px] text-[var(--danger)]">{error}</p>}
          <button onClick={handleReconstruct} disabled={isProcessing} className="sleek-btn sleek-btn-primary w-full py-3">
            <Cpu size={13} /> {isProcessing ? "Decrypting..." : "Analyze"}
          </button>
          <div className="flex flex-wrap gap-2 pt-1">
            {["H..lp flo..d 2f", "Med..cal blee..ng", "W..ter ri..ng"].map((p, i) => (
              <button key={p} onClick={() => setInputText(p)} className="text-[12px] px-3 py-1.5 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] hover:text-[var(--mint)] hover:border-[var(--border-hover)]">
                Sample {i + 1}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Feed */}
      <div className="xl:col-span-8 flex flex-col space-y-3">
        <div className="flex justify-between items-center">
          <h2 className="text-[15px] font-bold text-[var(--text)]">Intelligence Feed</h2>
          <span className="text-[12px] text-[var(--mint)]">{messages.length} signals</span>
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto pr-1 custom-scrollbar">
          <AnimatePresence initial={false}>
            {messages.length === 0 ? (
              <div className="bento-card py-20 text-center border-dashed">
                <p className="text-[14px] text-[var(--text-3)]">No signals decoded yet</p>
              </div>
            ) : (
              messages.sort((a, b) => b.urgency - a.urgency).map((msg) => (
                <motion.div key={msg.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="lucid-card" style={{ borderLeftWidth: '3px', borderLeftColor: urgencyColor(msg.urgency) }}>
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2">
                      <span className="bc-badge bg-[var(--surface-2)] border border-[var(--border)]" style={{ color: urgencyColor(msg.urgency) }}>{msg.category}</span>
                      <span className="text-[12px] text-[var(--text-3)]">{msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <span className="text-[12px] font-semibold" style={{ color: urgencyColor(msg.urgency) }}>{msg.urgency}/10</span>
                  </div>
                  <p className="text-[16px] font-medium text-[var(--text)] leading-snug mb-3">{msg.reconstructed}</p>
                  <div className="flex flex-wrap gap-3 border-t border-[var(--border)] pt-3 text-[11px] text-[var(--text-3)]">
                    {(msg.entities || []).map((e, i) => (<span key={i} className="flex items-center gap-1"><MapPin size={8} /> {e}</span>))}
                    <span className="ml-auto">Confidence: {((msg.confidence ?? 0.9) * 100).toFixed(0)}%</span>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
