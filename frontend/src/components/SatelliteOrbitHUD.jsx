import React, { useState, useEffect } from 'react';
import {
  Satellite,
  Radio,
  Clock,
  Compass,
  Zap,
  Activity,
  ChevronRight,
  ShieldCheck,
  Signal,
  MapPin,
  RefreshCw,
  Sliders,
} from 'lucide-react';
import { Badge } from './Badge';

const SATELLITE_CONSTELLATIONS = [
  {
    id: 'CARTOSAT-3',
    name: 'ISRO Cartosat-3',
    type: 'Very High-Res Optical',
    sensor: 'PAN (0.28m) / MX (1.12m)',
    altitudeKm: 505.4,
    velocityKmh: 27288,
    inclination: '97.5° (SSO)',
    swathKm: '16.0 km',
    downlinkBand: 'X-Band 8.2 GHz',
    status: 'ACTIVE PASS OVER INDIA',
    signalSnr: '98.6% LOCKED',
    orbitPeriodMin: 94.7,
  },
  {
    id: 'EOS-04',
    name: 'ISRO EOS-04 (RISAT-1A)',
    type: 'C-Band Radar SAR',
    sensor: 'Dual-Pol C-Band (1.0m FRS)',
    altitudeKm: 529.0,
    velocityKmh: 27140,
    inclination: '97.9° (SSO)',
    swathKm: '25.0 - 240.0 km',
    downlinkBand: 'X-Band / S-Band',
    status: 'MICROWAVE APERTURE ENGAGED',
    signalSnr: '99.1% LOCKED',
    orbitPeriodMin: 95.2,
  },
  {
    id: 'SENTINEL-2B',
    name: 'ESA / ISRO Sentinel-2B',
    type: 'Multi-Spectral MSI',
    sensor: '13 Bands (10m VNIR, 20m SWIR)',
    altitudeKm: 786.0,
    velocityKmh: 26850,
    inclination: '98.62° (SSO)',
    swathKm: '290.0 km',
    downlinkBand: 'X-Band 8.04 GHz',
    status: 'WIDE-SWATH MONITORING',
    signalSnr: '97.8% LOCKED',
    orbitPeriodMin: 100.6,
  },
];

export const SatelliteOrbitHUD = ({ isCompact = false }) => {
  const [selectedSat, setSelectedSat] = useState(SATELLITE_CONSTELLATIONS[0]);
  const [orbitProgress, setOrbitProgress] = useState(38); // 0 - 100 along track
  const [countdownSecs, setCountdownSecs] = useState(864); // 14 mins 24s
  const [sspCoord, setSspCoord] = useState({ lat: 21.48, lon: 78.96 }); // Sub-Satellite Point

  // Smooth orbital simulation tick
  useEffect(() => {
    const interval = setInterval(() => {
      setOrbitProgress((prev) => {
        const next = prev >= 100 ? 0 : +(prev + 0.35).toFixed(2);
        // Interpolate traversing sub-satellite coordinates diagonally across India & Bay of Bengal
        const lat = +(35.5 - (next / 100) * 30.0).toFixed(4);
        const lon = +(68.0 + (next / 100) * 28.0).toFixed(4);
        setSspCoord({ lat, lon });
        return next;
      });

      setCountdownSecs((prev) => (prev <= 1 ? 950 : prev - 1));
    }, 400);

    return () => clearInterval(interval);
  }, []);

  const formatCountdown = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `T - 00:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Trajectory points on the subcontinent map (SVG path)
  // Maps 0-100% progress along a curved orbital line from Kashmir (top-left) to Bay of Bengal (bottom-right)
  const satX = 70 + (orbitProgress / 100) * 220;
  const satY = 30 + (orbitProgress / 100) * 140;

  return (
    <div className="glass-panel border border-cyan-500/30 rounded-2xl p-4 sm:p-5 font-mono text-xs relative overflow-hidden shadow-2xl shadow-cyan-950/40 space-y-4">
      {/* Background ambient grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#06b6d4_1px,transparent_1px)] [background-size:24px_24px] opacity-10 pointer-events-none" />

      {/* Top Banner & Constellation Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 relative z-10 border-b border-white/10 pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-glow-cyan">
            <Satellite className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-white font-bold tracking-wide text-sm sm:text-base">
                ISRO EO Constellation Orbit & Telemetry HUD
              </span>
              <Badge variant="cyan">REAL-TIME TELEMETRY</Badge>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              AUTONOMOUS SUN-SYNCHRONOUS ORBIT TRACKER • HIGH-PRECISION SWATH ACQUISITION
            </p>
          </div>
        </div>

        {/* Constellation Switcher Pills */}
        <div className="flex items-center gap-1.5 bg-space-950/90 p-1 rounded-xl border border-white/10">
          {SATELLITE_CONSTELLATIONS.map((sat) => (
            <button
              key={sat.id}
              onClick={() => setSelectedSat(sat)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition flex items-center gap-1.5 ${
                selectedSat.id === sat.id
                  ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/50 shadow-glow-cyan'
                  : 'text-slate-400 hover:text-white hover:bg-space-900'
              }`}
            >
              <Radio className={`w-3 h-3 ${selectedSat.id === sat.id ? 'text-cyan-400 animate-pulse' : ''}`} />
              <span>{sat.id}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Visual Ground Track (Left/Center) + Physics Telemetry (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 relative z-10">
        
        {/* 🛰️ Orbital Ground-Track Canvas Simulation (7 cols) */}
        <div className="lg:col-span-7 bg-space-950/80 rounded-xl p-3.5 border border-white/10 relative overflow-hidden flex flex-col justify-between h-56 sm:h-64">
          
          {/* Canvas Header & Status */}
          <div className="flex items-center justify-between z-10 text-[11px]">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-emerald-400 font-bold">{selectedSat.status}</span>
            </div>
            <div className="text-cyan-400 font-mono text-[10px] flex items-center gap-1 bg-space-900/90 px-2 py-0.5 rounded border border-cyan-500/30">
              <Signal className="w-3 h-3 text-cyan-400" />
              <span>{selectedSat.signalSnr}</span>
            </div>
          </div>

          {/* SVG Subcontinent Orbital Map */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <svg className="w-full h-full opacity-80" viewBox="0 0 360 200">
              {/* Latitude / Longitude Graticule lines */}
              <line x1="20" y1="50" x2="340" y2="50" stroke="#334155" strokeWidth="0.5" strokeDasharray="3 3" />
              <line x1="20" y1="100" x2="340" y2="100" stroke="#334155" strokeWidth="0.5" strokeDasharray="3 3" />
              <line x1="20" y1="150" x2="340" y2="150" stroke="#334155" strokeWidth="0.5" strokeDasharray="3 3" />
              <line x1="90" y1="10" x2="90" y2="190" stroke="#334155" strokeWidth="0.5" strokeDasharray="3 3" />
              <line x1="180" y1="10" x2="180" y2="190" stroke="#334155" strokeWidth="0.5" strokeDasharray="3 3" />
              <line x1="270" y1="10" x2="270" y2="190" stroke="#334155" strokeWidth="0.5" strokeDasharray="3 3" />

              {/* Simplified India & Surrounding Landmass Contour */}
              <path
                d="M 120,30 L 150,32 L 195,50 L 220,45 L 240,65 L 255,85 L 230,90 L 205,80 L 190,105 L 175,135 L 155,175 L 140,140 L 115,115 L 105,75 Z"
                fill="#0f172a"
                stroke="#38bdf8"
                strokeWidth="1"
                strokeOpacity="0.4"
              />

              {/* Target Scene Coordinates: Guwahati (AN-2026-0801) */}
              <circle cx="230" cy="85" r="4" fill="#06b6d4" className="animate-ping" />
              <circle cx="230" cy="85" r="2.5" fill="#22d3ee" />
              <text x="238" y="88" fill="#67e8f9" fontSize="8" fontFamily="monospace">
                GUWAHATI SCENE
              </text>

              {/* Target Scene: Bengaluru (AN-2026-0803) */}
              <circle cx="150" cy="148" r="2" fill="#10b981" />
              <text x="156" y="151" fill="#6ee7b7" fontSize="7" fontFamily="monospace">
                BENGALURU ORR
              </text>

              {/* Sun-Synchronous Orbital Trajectory Arc */}
              <path
                d="M 70,30 Q 180,100 290,170"
                fill="none"
                stroke="#06b6d4"
                strokeWidth="1.5"
                strokeDasharray="5 3"
                opacity="0.7"
              />

              {/* Swath Observation Scanner Cone */}
              <polygon
                points={`${satX},${satY} ${satX - 25},${satY + 30} ${satX + 25},${satY + 30}`}
                fill="rgba(6, 182, 212, 0.15)"
                stroke="rgba(6, 182, 212, 0.4)"
                strokeWidth="0.5"
              />

              {/* Satellite Position Icon */}
              <g transform={`translate(${satX}, ${satY})`}>
                {/* Solar Panels */}
                <rect x="-14" y="-3" width="8" height="6" fill="#0284c7" stroke="#38bdf8" strokeWidth="0.5" />
                <rect x="6" y="-3" width="8" height="6" fill="#0284c7" stroke="#38bdf8" strokeWidth="0.5" />
                {/* Main Body Bus */}
                <rect x="-4" y="-4" width="8" height="8" fill="#e0f2fe" stroke="#0284c7" strokeWidth="1" />
                {/* Optical / SAR Dish */}
                <circle cx="0" cy="0" r="2" fill="#f59e0b" />
                {/* Pulse Ring */}
                <circle cx="0" cy="0" r="8" fill="none" stroke="#22d3ee" strokeWidth="0.75" opacity="0.6" className="animate-pulse" />
              </g>
            </svg>
          </div>

          {/* Canvas Bottom Coordinates Bar */}
          <div className="z-10 flex items-center justify-between text-[10px] text-slate-300 font-mono bg-space-900/90 p-1.5 rounded-lg border border-white/5 backdrop-blur-md">
            <div className="flex items-center gap-1 text-cyan-300">
              <MapPin className="w-3 h-3 text-cyan-400" />
              <span>SSP: <strong>{sspCoord.lat}° N, {sspCoord.lon}° E</strong></span>
            </div>
            <div className="text-slate-400">
              GROUND TRACK: <strong className="text-white">{orbitProgress.toFixed(1)}%</strong>
            </div>
          </div>
        </div>

        {/* 📊 Live Mission Physics Telemetry (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          {/* Next Pass Target Countdown Card */}
          <div className="p-3.5 rounded-xl bg-gradient-to-r from-space-950 via-space-900 to-cyan-950/40 border border-cyan-500/40 space-y-1.5">
            <div className="flex items-center justify-between text-slate-400 text-[10px]">
              <span className="flex items-center gap-1.5 uppercase font-bold text-cyan-300">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                Next Target Revisit Window
              </span>
              <span className="text-amber-400 font-bold">GUWAHATI SCENE</span>
            </div>
            <div className="text-xl sm:text-2xl font-bold text-white font-mono tracking-wider flex items-center gap-2">
              <span className="text-cyan-400">{formatCountdown(countdownSecs)}</span>
              <span className="text-[10px] text-slate-400 font-normal">EST. PASS</span>
            </div>
            <div className="text-[10px] text-slate-400">
              Expected Swath Overlap: <strong>94.2%</strong> • Solar Zenith: <strong>32.8°</strong>
            </div>
          </div>

          {/* 4 Core Orbital Physics Metrics */}
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            {/* Altitude */}
            <div className="p-2.5 rounded-xl bg-space-950 border border-white/5 space-y-0.5">
              <div className="text-slate-400 text-[10px]">ORBITAL ALTITUDE</div>
              <div className="text-sm font-bold text-emerald-400">{selectedSat.altitudeKm} km</div>
              <div className="text-[9px] text-slate-500">{selectedSat.inclination}</div>
            </div>

            {/* Velocity */}
            <div className="p-2.5 rounded-xl bg-space-950 border border-white/5 space-y-0.5">
              <div className="text-slate-400 text-[10px]">VELOCITY</div>
              <div className="text-sm font-bold text-cyan-400">
                {selectedSat.velocityKmh.toLocaleString()} km/h
              </div>
              <div className="text-[9px] text-slate-500">{(selectedSat.velocityKmh / 3600).toFixed(2)} km/s</div>
            </div>

            {/* Swath Width */}
            <div className="p-2.5 rounded-xl bg-space-950 border border-white/5 space-y-0.5">
              <div className="text-slate-400 text-[10px]">SWATH WIDTH</div>
              <div className="text-sm font-bold text-amber-400">{selectedSat.swathKm}</div>
              <div className="text-[9px] text-slate-500">{selectedSat.sensor}</div>
            </div>

            {/* Downlink Carrier */}
            <div className="p-2.5 rounded-xl bg-space-950 border border-white/5 space-y-0.5">
              <div className="text-slate-400 text-[10px]">DOWNLINK CARRIER</div>
              <div className="text-sm font-bold text-purple-400">{selectedSat.downlinkBand}</div>
              <div className="text-[9px] text-slate-500">{selectedSat.orbitPeriodMin} min period</div>
            </div>
          </div>

          {/* Quick Mission Readiness Pill */}
          <div className="p-2 rounded-lg bg-cyan-950/30 border border-cyan-500/20 text-[10px] text-slate-300 flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-cyan-300 font-bold">
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              NRSC / ISRO Data Acquisition Pipeline:
            </span>
            <span className="text-emerald-400 font-bold">NOMINAL 100%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SatelliteOrbitHUD;
