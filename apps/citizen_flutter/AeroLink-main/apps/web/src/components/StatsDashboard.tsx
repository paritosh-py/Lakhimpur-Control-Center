import React from "react";
import { Zap, Activity, CheckCircle2 } from "lucide-react";
import type { Ticket } from "@/lib/db";
import { isActiveStatus, isPendingStatus, isResolvedStatus } from "@/lib/ticket-status";

interface StatCardProps {
  label: string;
  value: string | number;
  sub: string;
  icon: React.ComponentType<{ size?: number; style?: React.CSSProperties; className?: string }>;
  accent: string;
}

function StatCard({ label, value, sub, icon: Icon, accent }: StatCardProps) {
  return (
    <div className="lucid-card space-y-4">
      <div className="flex justify-between items-start">
        <p className="stat-label">{label}</p>
        <Icon size={16} style={{ color: accent }} />
      </div>
      <h3 className="stat-value">{typeof value === "number" && value < 10 && value !== 0 ? `0${value}` : value}</h3>
      <p className="text-[13px] text-[var(--text-3)]">{sub}</p>
    </div>
  );
}

interface StatsDashboardProps {
  tickets: Ticket[];
}

export default function StatsDashboard({ tickets }: StatsDashboardProps) {
  const stats = {
    active: tickets.filter((ticket) => isActiveStatus(ticket.status)).length,
    pending: tickets.filter((ticket) => isPendingStatus(ticket.status)).length,
    resolved: tickets.filter((ticket) => isResolvedStatus(ticket.status)).length,
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard label="Active" value={stats.active} sub={stats.active > 0 ? "Opened requests" : "No active requests"} icon={Activity} accent="var(--teal)" />
      <StatCard label="Pending" value={stats.pending} sub={stats.pending > 0 ? "Awaiting review" : "Queue clear"} icon={Zap} accent="var(--frost)" />
      <StatCard label="Resolved" value={stats.resolved} sub="Closed requests" icon={CheckCircle2} accent="var(--plum)" />
    </div>
  );
}
