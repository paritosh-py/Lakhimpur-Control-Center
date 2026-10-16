"use client";

import React, { useEffect, useState } from "react";
import { Map, Overlay, ZoomControl } from "pigeon-maps";
import { MapPin, Navigation, Maximize2, Minimize2, ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import type { Ticket } from "@/lib/db";

export function parseCoordinates(manualLocation: string | undefined): [number, number] | null {
  if (!manualLocation) return null;
  const parts = manualLocation.split(",");
  if (parts.length >= 2) {
    const lat = parseFloat(parts[0].trim());
    const lng = parseFloat(parts[1].trim());
    if (!isNaN(lat) && !isNaN(lng)) return [lat, lng];
  }
  return null;
}

function validCoordinates(lat: number, lng: number): [number, number] | null {
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  if (Math.abs(lat) > 90 || Math.abs(lng) > 180) return null;
  return [lat, lng];
}

export function getTicketCoordinates(ticket: Ticket): [number, number] | null {
  if (ticket.report) {
    const reportCoordinates = validCoordinates(ticket.report.latitude, ticket.report.longitude);
    if (reportCoordinates) return reportCoordinates;
  }

  const manualCoordinates = parseCoordinates(ticket.manualLocation);
  if (manualCoordinates) return manualCoordinates;

  return ticket.location
    ? validCoordinates(ticket.location.lat, ticket.location.lng)
    : null;
}

export function calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

export default function SituationalMap({ tickets, baseCoord, height = 320 }: { tickets: Ticket[]; baseCoord: {lat: number, lng: number} | null; height?: number }) {
  const [mounted, setMounted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const centerPoints = tickets.map(getTicketCoordinates).filter(Boolean) as [number, number][];
  const defaultCenter: [number, number] = baseCoord ? [baseCoord.lat, baseCoord.lng] : (centerPoints[0] || [18.5204, 73.8567]);

  const [center, setCenter] = useState<[number, number]>(defaultCenter);
  const [zoom, setZoom] = useState(13);
  const [prevTicketId, setPrevTicketId] = useState<string | null>(null);
  const [prevBaseCoord, setPrevBaseCoord] = useState<{lat: number, lng: number} | null>(null);

  // Sync center state with selected ticket coordinates during render-phase
  if (tickets.length === 1 && tickets[0].id !== prevTicketId) {
    setPrevTicketId(tickets[0].id);
    const coords = getTicketCoordinates(tickets[0]);
    if (coords) {
      setCenter(coords);
    }
  }

  // Sync center state with base coordinates when base coordinates become available
  if (baseCoord && baseCoord !== prevBaseCoord) {
    setPrevBaseCoord(baseCoord);
    if (center[0] === 18.5204) {
      setCenter([baseCoord.lat, baseCoord.lng]);
    }
  }

  useEffect(() => {
    Promise.resolve().then(() => setMounted(true));
  }, []);

  if (!mounted) return <div className="animate-pulse bg-[var(--surface-2)] rounded-2xl w-full h-full" style={{ height: `${height}px` }} />;

  const mapStyle = isFullscreen ? { position: "fixed" as const, top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999, height: "100vh" } : { height: `${height}px` };

  const panStep = Math.max(0.002, 0.4 / zoom);
  const pan = (dLat: number, dLng: number) => setCenter([center[0] + dLat, center[1] + dLng]);

  return (
    <div className="w-full rounded-2xl overflow-hidden border border-[var(--border)] relative bg-[var(--bg)] shadow-sm" style={mapStyle}>
      <Map 
        height={isFullscreen ? window.innerHeight : height} 
        center={center} 
        zoom={zoom} 
        onBoundsChanged={({ center, zoom }) => { setCenter(center); setZoom(zoom); }}
        minZoom={5}
      >
        <ZoomControl style={{ top: 10, left: 10 }} />
        
        {/* Base Station Overlay */}
        {baseCoord && (
          <Overlay anchor={[baseCoord.lat, baseCoord.lng]} offset={[16, 32]}>
            <div className="flex flex-col items-center drop-shadow-md">
              <div className="bg-[var(--plum)] p-1.5 rounded-full text-[var(--bg)] border-2 border-[var(--bg)]">
                <Navigation size={14} fill="currentColor" />
              </div>
              <span className="text-[11px] font-bold mt-1 bg-[var(--bg)] px-1.5 py-0.5 rounded shadow text-[var(--plum)] uppercase tracking-wider">Command</span>
            </div>
          </Overlay>
        )}

        {/* Dynamic Victim Overlays */}
        {tickets.map(t => {
           const coords = getTicketCoordinates(t);
           if (!coords) return null;
           
           const isCritical = t.urgency > 7;
           const color = isCritical ? "var(--danger)" : "var(--mint)";
           
           return (
             <Overlay key={t.id} anchor={coords} offset={[14, 28]}>
                <div className="flex flex-col items-center group cursor-pointer drop-shadow-md">
                  <MapPin size={28} color={color} fill={color} stroke="var(--bg)" className={`${isCritical ? 'animate-bounce' : ''}`} />
                  <div className="hidden group-hover:block absolute top-[28px] z-50 bg-[var(--bg)] p-2.5 text-[12px] rounded-lg shadow-lg border border-[var(--border)] whitespace-nowrap min-w-[120px]">
                     <p className="font-bold text-[14px] text-[var(--text)] mb-0.5">{t.victimName}</p>
                     <p className="text-[var(--text-3)] mb-1.5 border-b border-[var(--border)] pb-1.5">{t.category}</p>
                     {baseCoord ? (
                       <p className="text-[11px] font-semibold text-[var(--teal)] uppercase">
                         {calculateDistance(baseCoord.lat, baseCoord.lng, coords[0], coords[1]).toFixed(2)} km away
                       </p>
                     ) : null}
                  </div>
                </div>
             </Overlay>
           );
        })}
      </Map>

      {/* Directional Pad */}
      <div className="absolute bottom-4 left-4 flex flex-col items-center z-50 bg-[var(--bg)] rounded-xl shadow-lg border border-[var(--border)] overflow-hidden">
        <button onClick={() => pan(panStep, 0)} className="p-2 hover:bg-[var(--surface-2)] text-[var(--text-3)] hover:text-[var(--text)] transition-colors"><ChevronUp size={16} /></button>
        <div className="flex border-y border-[var(--border)] w-full">
          <button onClick={() => pan(0, -panStep)} className="p-2 flex-1 border-r border-[var(--border)] hover:bg-[var(--surface-2)] text-[var(--text-3)] hover:text-[var(--text)] transition-colors"><ChevronLeft size={16} /></button>
          <button onClick={() => pan(0, panStep)} className="p-2 flex-1 hover:bg-[var(--surface-2)] text-[var(--text-3)] hover:text-[var(--text)] transition-colors"><ChevronRight size={16} /></button>
        </div>
        <button onClick={() => pan(-panStep, 0)} className="p-2 hover:bg-[var(--surface-2)] text-[var(--text-3)] hover:text-[var(--text)] transition-colors"><ChevronDown size={16} /></button>
      </div>

      {/* Fullscreen Toggle Button */}
      <button 
        onClick={() => setIsFullscreen(!isFullscreen)} 
        className="absolute bottom-4 right-4 bg-[var(--bg)] p-2.5 rounded-lg shadow-lg border border-[var(--border)] hover:bg-[var(--surface-2)] z-50 text-[var(--teal)] hover:text-[var(--text)] transition-colors flex items-center justify-center"
        title={isFullscreen ? "Exit Fullscreen" : "View Big Map"}
      >
        {isFullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
      </button>
    </div>
  );
}
