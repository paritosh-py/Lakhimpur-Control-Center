import { CalendarClock, MapPin, Users } from "lucide-react";
import type { EmergencyReport } from "@/lib/emergency-report";

function conditionLabel(value: string) {
  const spaced = value.replace(/[_-]+/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export default function EmergencyReportDetails({ report, compact = false }: { report: EmergencyReport; compact?: boolean }) {
  return (
    <div className={`rounded-xl border border-[var(--border)] bg-[var(--surface-2)] ${compact ? "p-3" : "p-4"}`}>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <span className="bc-badge bg-[var(--surface)] border border-[var(--border)] text-[var(--danger)]">
          {report.type}
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-[var(--text-3)]">
          <CalendarClock size={11} /> {new Date(report.timestamp).toLocaleString()}
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3">
          <p className="stat-label mb-1">Coordinates</p>
          <p className="flex items-center gap-1.5 text-[13px] font-mono text-[var(--text)]">
            <MapPin size={12} className="text-[var(--teal)]" /> {report.latitude}, {report.longitude}
          </p>
        </div>
        <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3">
          <p className="stat-label mb-1">People affected</p>
          <p className="flex items-center gap-1.5 text-[14px] font-bold text-[var(--text)]">
            <Users size={12} className="text-[var(--warning)]" /> {report.peopleAffected}
          </p>
        </div>
      </div>
      <div className="mt-3">
        <p className="stat-label mb-2">Reported conditions</p>
        <div className="flex flex-wrap gap-1.5">
          {report.conditions.length ? report.conditions.map(condition => (
            <span key={condition} className="bc-badge bg-[var(--surface)] border border-[var(--border)] text-[var(--text-2)]">
              {conditionLabel(condition)}
            </span>
          )) : <span className="text-[12px] text-[var(--text-3)]">None reported</span>}
        </div>
      </div>
      <div className="mt-3">
        <p className="stat-label mb-1.5">Additional details</p>
        <p className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 text-[13px] leading-relaxed text-[var(--text-2)] whitespace-pre-wrap">
          {report.additionalDetails || "No additional details supplied."}
        </p>
      </div>
    </div>
  );
}
