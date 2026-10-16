import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

type RouteMapProps = {
  basecamp: { latitude: number; longitude: number; name: string };
  settlement: { coordinates: [number, number]; name: string };
  shelter?: { name: string; published_capacity: number; nearest_segment_id?: string } | null;
  shelterCoords?: [number, number] | null;
  leg1Polyline: [number, number][];
  leg2Polyline?: [number, number][] | null;
  activeStepCoords?: [number, number][] | null;
  height?: string;
};

export default function RouteMap({
  basecamp,
  settlement,
  shelter,
  shelterCoords,
  leg1Polyline,
  leg2Polyline,
  activeStepCoords,
  height = '280px',
}: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const lastFittedKey = useRef<string>('');

  useEffect(() => {
    if (!containerRef.current) return;

    if (!mapRef.current) {
      const map = L.map(containerRef.current, {
        zoomControl: false,
        attributionControl: false,
      }).setView([basecamp.latitude, basecamp.longitude], 12);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
      }).addTo(map);

      L.control.zoom({ position: 'bottomright' }).addTo(map);
      mapRef.current = map;
    }

    const map = mapRef.current;
    const layers: L.Layer[] = [];

    // Helper for circular badge icon
    const createBadgeIcon = (text: string, bgColor: string, textColor = '#ffffff') =>
      L.divIcon({
        className: 'custom-map-badge',
        html: `<div style="background-color:${bgColor};color:${textColor};padding:4px 8px;border-radius:12px;font-weight:700;font-size:11px;border:2px solid #ffffff;box-shadow:0 2px 6px rgba(0,0,0,0.4);white-space:nowrap;display:inline-block;">${text}</div>`,
        iconSize: [40, 24],
        iconAnchor: [20, 12],
      });

    // 1. Basecamp marker
    const baseMarker = L.marker([basecamp.latitude, basecamp.longitude], {
      icon: createBadgeIcon('HQ Basecamp', '#2563eb'),
    }).bindPopup(`<strong>${basecamp.name}</strong><br/>Dispatch Origin`).addTo(map);
    layers.push(baseMarker);

    // 2. Settlement destination marker
    const destMarker = L.marker(settlement.coordinates, {
      icon: createBadgeIcon(`🎯 ${settlement.name}`, '#f59e0b', '#000000'),
    }).bindPopup(`<strong>${settlement.name}</strong><br/>Rescue Target Settlement`).addTo(map);
    layers.push(destMarker);

    // 3. Shelter marker (if coordinates known or derived from leg2)
    const sCoords = shelterCoords || (leg2Polyline && leg2Polyline.length > 0 ? leg2Polyline[leg2Polyline.length - 1] : null);
    if (sCoords && shelter) {
      const shelterMarker = L.marker(sCoords, {
        icon: createBadgeIcon(`🏥 ${shelter.name}`, '#10b981'),
      }).bindPopup(`<strong>${shelter.name}</strong><br/>Relief Camp · Capacity: ${shelter.published_capacity}`).addTo(map);
      layers.push(shelterMarker);
    }

    // 4. Leg 1 route polyline (Blue / Green)
    if (leg1Polyline.length > 0) {
      const poly1 = L.polyline(leg1Polyline, {
        color: '#0284c7',
        weight: 5,
        opacity: 0.9,
      }).bindPopup('Leg 1: Basecamp to Settlement').addTo(map);
      layers.push(poly1);
    }

    // 5. Leg 2 route polyline (Purple dashed)
    if (leg2Polyline && leg2Polyline.length > 0) {
      const poly2 = L.polyline(leg2Polyline, {
        color: '#8b5cf6',
        weight: 4,
        dashArray: '6, 6',
        opacity: 0.9,
      }).bindPopup('Leg 2: Settlement to Relief Shelter').addTo(map);
      layers.push(poly2);
    }

    // 6. Active navigation step highlight
    if (activeStepCoords && activeStepCoords.length > 0) {
      const stepPoly = L.polyline(activeStepCoords, {
        color: '#22c55e',
        weight: 8,
        opacity: 1,
      }).addTo(map);
      layers.push(stepPoly);
    }

    // Fit bounds only when route endpoints or polyline actually changes
    const fitKey = `${basecamp.latitude},${basecamp.longitude}-${settlement.coordinates?.[0]},${settlement.coordinates?.[1]}-${leg1Polyline.length}-${(leg2Polyline || []).length}`;
    const allPoints: [number, number][] = [
      [basecamp.latitude, basecamp.longitude],
      settlement.coordinates,
      ...leg1Polyline,
      ...(leg2Polyline || []),
    ];

    if (allPoints.length > 0 && fitKey !== lastFittedKey.current) {
      lastFittedKey.current = fitKey;
      const bounds = L.latLngBounds(allPoints);
      map.fitBounds(bounds, { padding: [25, 25] });
    }

    return () => {
      layers.forEach(layer => layer.remove());
    };
  }, [basecamp, settlement, shelter, shelterCoords, leg1Polyline, leg2Polyline, activeStepCoords]);

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height,
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid #334155',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
      }}
    />
  );
}
