import { useEffect, useState } from 'react';
import './reports.css';

export type CitizenReport = {
  id: string;
  context: string;
  device_id: string;
  message_id: string;
  sender_name?: string | null;
  sender_phone?: string | null;
  incident_type: string;
  settlement_id?: string | null;
  settlement_name?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  people_affected?: number;
  severity_level: string;
  water_depth_cm?: number | null;
  water_trend?: string | null;
  road_status?: string | null;
  description: string;
  conditions: string[];
  gemini_triage: {
    urgency: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
    urgency_score: number;
    primary_hazard: string;
    summary: string;
    recommended_action: string;
    extracted_needs: string[];
    road_closure_asserted: boolean;
    road_closure_details?: string | null;
    rationale?: string;
    triage_source?: string;
  };
  urgency: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'new' | 'verified' | 'actioned' | 'dismissed' | 'closed' | 'resolved';
  timestamp: string;
  received_at: string;
  device_total_reports: number;
  is_repeat_device: boolean;
};

export type ReportStats = {
  total: number;
  critical: number;
  high: number;
  road_blocked: number;
  closed?: number;
  active?: number;
  unique_devices: number;
  repeat_reports: number;
};

interface ReportsPageProps {
  context: string | null;
  onLocate: (lat: number, lon: number, reportId: string) => void;
  onAssign: (settlementId: string) => void;
}

const formatTime = (iso: string) => {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      timeZone: 'Asia/Kolkata',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }) + ' IST';
  } catch {
    return iso;
  }
};

export function ReportsPage({ context, onLocate, onAssign }: ReportsPageProps) {
  const currentContext = context || 'live';
  const [reports, setReports] = useState<CitizenReport[]>([]);
  const [stats, setStats] = useState<ReportStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('active');
  const [filterUrgency, setFilterUrgency] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [repeatOnly, setRepeatOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedDevices, setExpandedDevices] = useState<Record<string, CitizenReport[]>>({});
  const [loadingDevice, setLoadingDevice] = useState<string | null>(null);

  const fetchReports = async () => {
    try {
      const [listRes, statsRes] = await Promise.all([
        fetch(`/api/reports?context=${encodeURIComponent(currentContext)}`),
        fetch(`/api/reports/stats?context=${encodeURIComponent(currentContext)}`),
      ]);
      if (!listRes.ok || !statsRes.ok) throw new Error('Failed to load reports');
      const listData = await listRes.json();
      const statsData = await statsRes.json();
      setReports(listData.reports || []);
      setStats(statsData);
      setError('');
    } catch (e: any) {
      setError(e.message || 'Unable to reach reports service');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
    const interval = setInterval(fetchReports, 5000);
    return () => clearInterval(interval);
  }, [currentContext]);

  const toggleDeviceHistory = async (deviceId: string) => {
    if (expandedDevices[deviceId]) {
      const updated = { ...expandedDevices };
      delete updated[deviceId];
      setExpandedDevices(updated);
      return;
    }
    setLoadingDevice(deviceId);
    try {
      const res = await fetch(`/api/reports/devices/${encodeURIComponent(deviceId)}?context=${encodeURIComponent(currentContext)}`);
      if (res.ok) {
        const data = await res.json();
        setExpandedDevices(prev => ({ ...prev, [deviceId]: data.reports || [] }));
      }
    } catch (e) {
      console.error('Failed to load device history', e);
    } finally {
      setLoadingDevice(null);
    }
  };

  const updateStatus = async (reportId: string, status: string) => {
    // Optimistic state update for instant UI responsiveness
    setReports(prev =>
      prev.map(r => (r.id === reportId ? { ...r, status: status as any } : r))
    );
    try {
      const res = await fetch(`/api/reports/${encodeURIComponent(reportId)}/status?context=${encodeURIComponent(currentContext)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (res.ok) {
        fetchReports();
      }
    } catch (e) {
      console.error('Status update failed', e);
      fetchReports();
    }
  };

  // Filter reports
  const filtered = reports.filter(r => {
    if (filterStatus === 'active' && (r.status === 'closed' || r.status === 'resolved')) return false;
    if (filterStatus === 'closed' && (r.status !== 'closed' && r.status !== 'resolved')) return false;
    if (filterStatus !== 'all' && filterStatus !== 'active' && filterStatus !== 'closed' && r.status !== filterStatus) return false;
    if (filterUrgency !== 'all' && r.gemini_triage.urgency !== filterUrgency) return false;
    if (filterType !== 'all' && r.incident_type !== filterType) return false;
    if (repeatOnly && !r.is_repeat_device) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        (r.sender_name && r.sender_name.toLowerCase().includes(q)) ||
        (r.sender_phone && r.sender_phone.includes(q)) ||
        (r.device_id && r.device_id.toLowerCase().includes(q)) ||
        (r.settlement_name && r.settlement_name.toLowerCase().includes(q)) ||
        (r.description && r.description.toLowerCase().includes(q)) ||
        (r.gemini_triage.summary && r.gemini_triage.summary.toLowerCase().includes(q));
      if (!match) return false;
    }
    return true;
  });

  return (
    <section className="reports-page">
      <div className="reports-header-row">
        <div>
          <h2>Ground & Citizen Reports</h2>
          <p>
            Real-time field reports from Lakhimpur district · AI prioritized via Gemini · Device frequency tracking
          </p>
        </div>
        <div>
          <button onClick={fetchReports} disabled={loading}>
            {loading ? 'Refreshing…' : '↻ Refresh Reports'}
          </button>
        </div>
      </div>

      {error && <div className="live-error">{error}</div>}

      {/* KPI Cards Strip */}
      <div className="reports-kpi-grid">
        <div className="kpi-card">
          <span className="kpi-label">Total Reports</span>
          <span className="kpi-value">{stats?.total ?? reports.length}</span>
        </div>
        <div className="kpi-card kpi-active">
          <span className="kpi-label">Active Open</span>
          <span className="kpi-value">
            {stats?.active ?? reports.filter(r => r.status !== 'closed' && r.status !== 'resolved').length}
          </span>
        </div>
        <div className="kpi-card kpi-critical">
          <span className="kpi-label">Critical Emergencies</span>
          <span className="kpi-value">{stats?.critical ?? 0}</span>
        </div>
        <div className="kpi-card kpi-high">
          <span className="kpi-label">High Urgency</span>
          <span className="kpi-value">{stats?.high ?? 0}</span>
        </div>
        <div className="kpi-card kpi-roads">
          <span className="kpi-label">Road Closures</span>
          <span className="kpi-value">{stats?.road_blocked ?? 0}</span>
        </div>
        <div className="kpi-card kpi-closed">
          <span className="kpi-label">Closed / Resolved</span>
          <span className="kpi-value">
            {stats?.closed ?? reports.filter(r => r.status === 'closed' || r.status === 'resolved').length}
          </span>
        </div>
        <div className="kpi-card kpi-repeat">
          <span className="kpi-label">Repeat Senders Alert</span>
          <span className="kpi-value">{stats?.repeat_reports ?? 0}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="reports-filter-bar">
        <div className="reports-search-box">
          <input
            type="text"
            placeholder="Search reports, sender, phone, village, or keywords…"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="reports-filter-selects">
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
            <option value="active">Active Requests Only</option>
            <option value="all">All Statuses (Active & Closed)</option>
            <option value="closed">✓ Closed / Resolved Only</option>
            <option value="new">New Only</option>
            <option value="verified">Verified Only</option>
            <option value="actioned">Actioned Only</option>
            <option value="dismissed">Dismissed Only</option>
          </select>
          <select value={filterUrgency} onChange={e => setFilterUrgency(e.target.value)}>
            <option value="all">All Urgencies</option>
            <option value="CRITICAL">🔴 Critical Only</option>
            <option value="HIGH">🟠 High Only</option>
            <option value="MEDIUM">🔵 Medium</option>
            <option value="LOW">⚪ Low</option>
          </select>
          <select value={filterType} onChange={e => setFilterType(e.target.value)}>
            <option value="all">All Incidents</option>
            <option value="rescue_sos">Rescue SOS</option>
            <option value="road_closure">Road Blockage</option>
            <option value="flood_rising">Water Rising</option>
            <option value="medical">Medical Need</option>
            <option value="general">General</option>
          </select>
          <button
            style={{
              background: repeatOnly ? '#f9e9ed' : '#ffffff',
              borderColor: repeatOnly ? '#a33453' : '#b8b6aa',
              color: repeatOnly ? '#8c2945' : '#34413b',
              fontSize: '15px',
              padding: '6px 12px',
            }}
            onClick={() => setRepeatOnly(v => !v)}
          >
            {repeatOnly ? '✓ Repeat Devices Only' : 'Repeat Devices Only'}
          </button>
        </div>
      </div>

      {/* Reports Feed */}
      <div className="report-cards-list">
        {filtered.length === 0 ? (
          <div className="reports-empty">
            <h3>No reports match the current filters</h3>
            <p>
              When citizen or field apps post reports to <code>/api/reports</code>, they appear here live with Gemini AI triage and repeat device alerts.
            </p>
          </div>
        ) : (
          filtered.map(r => {
            const isClosed = r.status === 'closed' || r.status === 'resolved';
            const urgency = r.gemini_triage.urgency || r.urgency || 'MEDIUM';
            const urgencyClass = `urgency-${urgency.toLowerCase()}`;
            const isCritical = urgency === 'CRITICAL';
            const hasCoords = r.latitude != null && r.longitude != null;

            return (
              <div key={r.id} className={`report-card ${urgencyClass} ${isClosed ? 'status-closed' : ''}`}>
                {/* Header Row */}
                <div className="report-card-top">
                  <div className="report-badges">
                    {isClosed ? (
                      <span className="closed-status-badge">
                        ✓ CLOSED / RESOLVED
                      </span>
                    ) : (
                      <span className={`urgency-badge ${urgency.toLowerCase()}`}>
                        {isCritical ? '🚨 ' : ''}
                        {urgency}
                      </span>
                    )}
                    <span className="ai-score-pill">
                      AI Priority: {r.gemini_triage.urgency_score ?? 50}/100
                    </span>
                    <span className="incident-type-chip">
                      {r.incident_type.replaceAll('_', ' ')}
                    </span>
                    {r.is_repeat_device && (
                      <button
                        className="repeat-device-alert"
                        onClick={() => toggleDeviceHistory(r.device_id)}
                        title="Click to view full message history from this device"
                      >
                        ⚠️ {r.device_total_reports} reports from this device
                      </button>
                    )}
                  </div>
                  <span className="report-timestamp">
                    {formatTime(r.received_at || r.timestamp)}
                  </span>
                </div>

                {/* Gemini AI Triage Callout Box */}
                <div className="report-gemini-box">
                  <div className="gemini-box-header">
                    <span>
                      ✨ GEMINI DISASTER TRIAGE{' '}
                      {r.gemini_triage.triage_source === 'rule_heuristic' && '(Offline Heuristic)'}
                    </span>
                    {r.gemini_triage.road_closure_asserted && (
                      <span className="road-alert-tag">⛔ ROAD CLOSURE ASSERTED</span>
                    )}
                  </div>
                  <p className="gemini-summary-text">
                    {r.gemini_triage.summary || r.description}
                  </p>
                  {r.gemini_triage.recommended_action && (
                    <div className="gemini-action-rec">
                      <strong>Recommended Action:</strong>
                      <span>{r.gemini_triage.recommended_action}</span>
                    </div>
                  )}
                  {r.gemini_triage.extracted_needs && r.gemini_triage.extracted_needs.length > 0 && (
                    <div className="gemini-needs-tags">
                      {r.gemini_triage.extracted_needs.map(need => (
                        <span key={need} className="need-tag">
                          {need}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Metadata Grid */}
                <div className="report-meta-grid">
                  <div className="report-meta-item">
                    <strong>Location</strong>
                    <span>
                      {r.settlement_name || 'Lakhimpur District'}
                      {hasCoords ? ` (${r.latitude?.toFixed(4)}, ${r.longitude?.toFixed(4)})` : ''}
                    </span>
                  </div>
                  <div className="report-meta-item">
                    <strong>Sender & Device</strong>
                    <span>
                      {r.sender_name || 'Anonymous citizen'} · {r.device_id}
                      {r.sender_phone ? ` · Ph: ${r.sender_phone}` : ''}
                    </span>
                  </div>
                  <div className="report-meta-item">
                    <strong>Conditions & Depth</strong>
                    <span>
                      {r.water_depth_cm != null ? `${r.water_depth_cm} cm water` : 'Water depth unstated'}{' '}
                      {r.water_trend ? `(${r.water_trend})` : ''} · {r.people_affected || 0} affected
                    </span>
                  </div>
                  <div className="report-meta-item">
                    <strong>Road Status</strong>
                    <span className={r.road_status === 'blocked' ? 'road-alert-tag' : ''}>
                      {r.road_status ? r.road_status.replaceAll('_', ' ') : 'Not reported'}
                    </span>
                  </div>
                </div>

                {/* Raw Citizen Message */}
                {r.description && (
                  <div className="report-raw-message">
                    "{r.description}"
                  </div>
                )}

                {/* Card Action Controls */}
                <div className="report-card-actions">
                  <div className="report-action-buttons">
                    {!isClosed ? (
                      <button
                        className="btn-close-report"
                        onClick={() => updateStatus(r.id, 'closed')}
                        title="Mark request as resolved and closed"
                      >
                        ✓ Close Request
                      </button>
                    ) : (
                      <button
                        className="btn-reopen-report"
                        onClick={() => updateStatus(r.id, 'new')}
                        title="Reopen request for response"
                      >
                        ↺ Reopen Request
                      </button>
                    )}
                    {hasCoords && (
                      <button
                        className="btn-locate"
                        onClick={() => onLocate(r.latitude!, r.longitude!, r.id)}
                      >
                        📍 Locate on Map
                      </button>
                    )}
                    {r.settlement_id && !isClosed && (
                      <button
                        className="btn-dispatch"
                        onClick={() => onAssign(r.settlement_id!)}
                      >
                        🚑 Dispatch Team Here
                      </button>
                    )}
                    <button
                      style={{ fontSize: '14px', padding: '7px 12px', minHeight: '34px' }}
                      onClick={() => toggleDeviceHistory(r.device_id)}
                    >
                      {expandedDevices[r.device_id] ? 'Hide Device History' : `Device History (${r.device_total_reports})`}
                    </button>
                  </div>

                  <div className="report-status-control">
                    <span style={{ fontSize: '14px', color: '#59665e' }}>Status:</span>
                    <select
                      value={r.status}
                      onChange={e => updateStatus(r.id, e.target.value)}
                    >
                      <option value="new">New</option>
                      <option value="verified">Verified</option>
                      <option value="actioned">Actioned</option>
                      <option value="closed">Closed / Resolved</option>
                      <option value="dismissed">Dismissed</option>
                    </select>
                  </div>
                </div>

                {/* Collapsible Device History */}
                {expandedDevices[r.device_id] && (
                  <div className="device-history-collapse">
                    <strong style={{ color: '#8c2945', fontSize: '14px' }}>
                      Device Timeline for {r.device_id} ({expandedDevices[r.device_id].length} reports)
                    </strong>
                    {expandedDevices[r.device_id].map(hist => (
                      <div key={hist.id} className="history-item">
                        <div className="history-item-top">
                          <span>
                            <strong>{hist.incident_type}</strong> · {hist.gemini_triage?.urgency || hist.urgency}
                          </span>
                          <span>{formatTime(hist.received_at || hist.timestamp)}</span>
                        </div>
                        <p style={{ margin: '4px 0', color: '#34413b' }}>{hist.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
