export type RequestStatus = "pending" | "active" | "resolved";
export type AnalysisStatus = "pending" | "processing" | "complete" | "failed";

export function isResolvedStatus(status: string): boolean {
  return status === "resolved" || status === "completed";
}

export function isPendingStatus(status: string): boolean {
  return status === "pending";
}

export function isActiveStatus(status: string): boolean {
  return !isPendingStatus(status) && !isResolvedStatus(status);
}

export function normalizeRequestStatus(status: string): RequestStatus | null {
  if (status === "pending") return "pending";
  if (status === "active" || status === "received") return "active";
  if (status === "resolved" || status === "completed") return "resolved";
  return null;
}

export function hasCompletedAnalysis(ticket: {
  analysisStatus?: AnalysisStatus;
  reconstructed?: string;
  urgency?: number;
}): boolean {
  if (ticket.analysisStatus === "complete") return true;
  return !ticket.analysisStatus && Boolean(ticket.reconstructed?.trim()) && Number(ticket.urgency) > 0;
}
