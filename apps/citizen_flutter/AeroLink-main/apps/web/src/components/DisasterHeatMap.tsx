"use client";

import React, { useEffect } from "react";
import { MapContainer, TileLayer, Circle, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default marker icons in Leaflet
import L from "leaflet";

const mockIncidents = [
  { id: 1, pos: [28.6139, 77.2090], severity: 0.8, label: "Flood Zone A" },
  { id: 2, pos: [28.6500, 77.1000], severity: 0.5, label: "Rescue Op B" },
  { id: 3, pos: [28.7000, 77.2500], severity: 0.9, label: "Power Failure C" },
  { id: 4, pos: [28.5500, 77.1500], severity: 0.4, label: "Medical Aid D" },
];

function MapSetter() {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
  }, [map]);
  return null;
}

export default function DisasterHeatMap() {
  // Center of Delhi for demo
  const center: [number, number] = [28.6139, 77.2090];

  return (
    <div className="heatmap-container relative glass-panel">
      <div className="absolute top-4 left-4 z-[1000] p-4 lucid-card bg-[var(--graphite)]/90 backdrop-blur-md">
        <h3 className="text-sm font-bold text-[var(--lavender)] uppercase tracking-widest mb-1">Live Incident Map</h3>
        <p className="text-[12px] text-[var(--thistle)]">Scanning 248 sectors in real-time</p>
      </div>

      <MapContainer 
        center={center} 
        zoom={11} 
        style={{ height: "100%", width: "100%" }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <MapSetter />
        
        {mockIncidents.map((incident) => (
          <Circle
            key={incident.id}
            center={incident.pos as [number, number]}
            radius={2000}
            pathOptions={{
              fillColor: incident.severity > 0.7 ? "#ff3d71" : "#ffaa00",
              color: "transparent",
              fillOpacity: incident.severity * 0.6,
            }}
          >
            <Popup className="custom-popup">
              <div className="p-2">
                <p className="font-bold text-gray-900">{incident.label}</p>
                <p className="text-xs text-gray-600">Severity: {incident.severity * 100}%</p>
              </div>
            </Popup>
          </Circle>
        ))}
      </MapContainer>
    </div>
  );
}
