import { useState } from 'react';
import RouteMap from './RouteMap';

type Step = {
  step_number: number;
  leg: 'rescue' | 'evacuation';
  instruction: string;
  road_name: string;
  distance_m: number;
  duration_sec: number;
  probability_unusable: number;
  risk_level: string;
  coordinates: [number, number][];
};

type NavigationModeProps = {
  mission: any;
  task?: any;
  onUpdateStatus?: (status: string, note?: string) => Promise<void>;
  onExit: () => void;
};

export default function NavigationMode({ mission, task, onUpdateStatus, onExit }: NavigationModeProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [reportingBlockage, setReportingBlockage] = useState(false);
  const [blockageNote, setBlockageNote] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const steps: Step[] = mission.navigation_steps || [];
  const currentStep = steps[currentStepIndex] || steps[0];

  const handleNextStep = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(i => i + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(i => i - 1);
    }
  };

  const handleStatusClick = async (status: string) => {
    if (!onUpdateStatus) return;
    setIsUpdating(true);
    try {
      await onUpdateStatus(status);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleReportBlockage = async () => {
    if (!onUpdateStatus || !blockageNote.trim()) return;
    setIsUpdating(true);
    try {
      await onUpdateStatus('blocked', blockageNote);
      setReportingBlockage(false);
      setBlockageNote('');
    } finally {
      setIsUpdating(false);
    }
  };

  const leg1Polyline: [number, number][] = mission.leg1_routes?.recommended?.polyline || [];
  const leg2Polyline: [number, number][] = mission.leg2_route?.polyline || [];

  return (
    <div className="nav-mode-container">
      {/* Sticky Top HUD (Google Maps style) */}
      <header className="nav-hud">
        <div className="nav-hud-top">
          <button className="nav-exit-btn" onClick={onExit} aria-label="Exit navigation">
            ✕ Exit
          </button>
          <div className="nav-hud-leg-badge">
            {currentStep?.leg === 'rescue' ? '🚨 OUTBOUND RESCUE' : '🏥 EVACUATION TO SHELTER'}
          </div>
          <div className="nav-hud-step-counter">
            Step {currentStepIndex + 1} / {steps.length}
          </div>
        </div>

        <div className="nav-instruction-box">
          <div className="nav-maneuver-icon">
            {currentStep?.road_name === 'Destination' || currentStep?.road_name === 'Relief Shelter' ? '📍' : '⬆️'}
          </div>
          <div className="nav-instruction-content">
            <h2 className="nav-instruction-title">{currentStep?.instruction || 'Proceed on route'}</h2>
            <div className="nav-instruction-meta">
              <span>{currentStep?.road_name}</span>
              {currentStep?.distance_m > 0 && <span> · {currentStep.distance_m} m</span>}
              {currentStep?.risk_level === 'HIGH' && (
                <span className="nav-risk-tag high">⚠️ High Flood Risk ({(currentStep.probability_unusable * 100).toFixed(0)}%)</span>
              )}
            </div>
          </div>
        </div>

        {/* Next / Previous step quick controls */}
        <div className="nav-step-stepper">
          <button onClick={handlePrevStep} disabled={currentStepIndex === 0} className="nav-stepper-btn">
            ◀ Previous
          </button>
          <button onClick={handleNextStep} disabled={currentStepIndex === steps.length - 1} className="nav-stepper-btn primary">
            Next Maneuver ▶
          </button>
        </div>
      </header>

      {/* Map View tracking active step */}
      <div className="nav-map-section">
        <RouteMap
          basecamp={mission.basecamp}
          settlement={mission.settlement}
          shelter={mission.shelter}
          leg1Polyline={leg1Polyline}
          leg2Polyline={leg2Polyline}
          activeStepCoords={currentStep?.coordinates}
          height="240px"
        />
      </div>

      {/* Action Deck for Emergency Team */}
      <section className="nav-action-deck">
        <h3 className="nav-deck-title">Quick Mission Actions</h3>
        <div className="nav-action-buttons">
          {(!task || task.status === 'assigned' || task.status === 'accepted') && (
            <button
              className="nav-action-btn primary"
              disabled={isUpdating}
              onClick={() => handleStatusClick('en_route')}
            >
              🚀 Depart Basecamp (En Route)
            </button>
          )}

          {task?.status === 'en_route' && (
            <button
              className="nav-action-btn success"
              disabled={isUpdating}
              onClick={() => handleStatusClick('arrived')}
            >
              🎯 Arrived at Settlement
            </button>
          )}

          {task?.status === 'arrived' && (
            <button
              className="nav-action-btn primary"
              disabled={isUpdating}
              onClick={() => handleStatusClick('en_route')}
            >
              🏥 Proceed to Relief Camp
            </button>
          )}

          {(task?.status === 'arrived' || task?.status === 'en_route') && (
            <button
              className="nav-action-btn complete"
              disabled={isUpdating}
              onClick={() => handleStatusClick('completed')}
            >
              ✅ Mission Completed
            </button>
          )}

          <button
            className="nav-action-btn danger"
            onClick={() => setReportingBlockage(b => !b)}
          >
            🛑 Report Road Blocked
          </button>
        </div>

        {reportingBlockage && (
          <div className="nav-blockage-modal">
            <h4>Report Road Obstruction / Flood Blockage</h4>
            <p>Tell the command center about the blockage at this location:</p>
            <textarea
              rows={3}
              value={blockageNote}
              onChange={e => setBlockageNote(e.target.value)}
              placeholder="e.g. Water over road 2 feet deep near culvert, impassable for trucks"
            />
            <div className="nav-blockage-actions">
              <button
                className="nav-action-btn danger"
                disabled={isUpdating || !blockageNote.trim()}
                onClick={handleReportBlockage}
              >
                Send Blockage Report
              </button>
              <button className="nav-action-btn secondary" onClick={() => setReportingBlockage(false)}>
                Cancel
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Upcoming Turns List */}
      <section className="nav-steps-list">
        <h3>Upcoming Route Steps</h3>
        <ol className="nav-steps-timeline">
          {steps.map((s, idx) => (
            <li
              key={idx}
              className={`nav-step-item ${idx === currentStepIndex ? 'active' : idx < currentStepIndex ? 'completed' : ''}`}
              onClick={() => setCurrentStepIndex(idx)}
            >
              <span className="nav-step-badge">{idx + 1}</span>
              <div className="nav-step-details">
                <strong>{s.instruction}</strong>
                <small>
                  {s.road_name} {s.distance_m > 0 ? `· ${s.distance_m} m` : ''}
                </small>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
