import React, { useState, useEffect } from 'react';
import {
  Check,
  Edit3,
  Download,
  AlertTriangle,
  CheckCircle2,
  X,
  ZoomIn,
  ZoomOut,
  RefreshCw,
  Layers,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Sliders,
  Eye,
  Crosshair,
} from 'lucide-react';
import { Card } from '../components/Card';
import { Table } from '../components/Table';
import { Button } from '../components/Button';
import { Badge, CategoryBadge } from '../components/Badge';

export const ReviewPage = () => {
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [editingItem, setEditingItem] = useState(null);
  const [correctedCategory, setCorrectedCategory] = useState('HUMAN');
  const [correctedSubcategory, setCorrectedSubcategory] = useState('Building');
  const [reviewerNotes, setReviewerNotes] = useState('');
  const [exportSuccessMessage, setExportSuccessMessage] = useState(null);

  // Inspector modal states
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showMask, setShowMask] = useState(true);
  const [isFlickerActive, setIsFlickerActive] = useState(false);
  const [flickerFrame, setFlickerFrame] = useState(0); // 0 = T1, 1 = T2
  const [mouseCoord, setMouseCoord] = useState({ x: 120, y: 85 });

  const [reviewQueue, setReviewQueue] = useState([
    {
      id: 'CR-007',
      analysisId: 'AN-2026-0801',
      coordinates: '28.5355° N, 77.3910° E',
      sensor: 'Cartosat-3 (0.5m) / Sentinel-2',
      predictedCategory: 'HUMAN',
      predictedSubtype: 'Construction Site',
      confidence: 0.62,
      area_m2: 38000,
      reason: 'Low model confidence threshold (62.0% < 80.0%)',
      status: 'PENDING',
      correctedCategory: null,
      correctedSubcategory: null,
      reviewer: null,
      timestamp: '2026-01-15T12:30:00Z',
      spectral: {
        dNdvi: -0.44,
        dNdbi: +0.58,
        dNdwi: -0.05,
        sarDb: '+3.8 dB',
      },
      metrics: {
        edgeSharpness: 86,
        contextScore: 92,
        shadowRejection: 95,
      },
    },
    {
      id: 'CR-014',
      analysisId: 'AN-2026-0801',
      coordinates: '28.5120° N, 77.4192° E',
      sensor: 'Sentinel-2 MSI (10m)',
      predictedCategory: 'UNKNOWN',
      predictedSubtype: 'Unclassified Spectral Disruption',
      confidence: 0.54,
      area_m2: 15400,
      reason: 'Ambiguous category: spectral contradiction between NDVI and NDBI',
      status: 'PENDING',
      correctedCategory: null,
      correctedSubcategory: null,
      reviewer: null,
      timestamp: '2026-01-15T12:30:00Z',
      spectral: {
        dNdvi: -0.21,
        dNdbi: +0.19,
        dNdwi: +0.11,
        sarDb: '+0.4 dB',
      },
      metrics: {
        edgeSharpness: 58,
        contextScore: 61,
        shadowRejection: 74,
      },
    },
    {
      id: 'CR-021',
      analysisId: 'AN-2026-0801',
      coordinates: '28.5681° N, 77.3620° E',
      sensor: 'EOS-04 C-Band SAR / Cartosat-3',
      predictedCategory: 'NATURAL',
      predictedSubtype: 'Bare Soil Exposure',
      confidence: 0.68,
      area_m2: 42000,
      reason: 'Sub-threshold confidence near high-risk infrastructure buffer',
      status: 'PENDING',
      correctedCategory: null,
      correctedSubcategory: null,
      reviewer: null,
      timestamp: '2026-01-15T12:30:00Z',
      spectral: {
        dNdvi: -0.32,
        dNdbi: +0.12,
        dNdwi: -0.14,
        sarDb: '-1.1 dB',
      },
      metrics: {
        edgeSharpness: 72,
        contextScore: 88,
        shadowRejection: 90,
      },
    },
    {
      id: 'CR-003',
      analysisId: 'AN-2026-0801',
      coordinates: '28.4901° N, 77.4433° E',
      sensor: 'Sentinel-2 MSI (10m)',
      predictedCategory: 'NATURAL',
      predictedSubtype: 'Vegetation Shift (Seasonal)',
      confidence: 0.89,
      area_m2: 1120000,
      reason: 'Verified seasonal wetland canopy variation',
      status: 'APPROVED',
      correctedCategory: 'NATURAL',
      correctedSubcategory: 'Vegetation',
      reviewer: 'Analyst Dr. Sharma',
      timestamp: '2026-01-16T09:15:00Z',
      spectral: {
        dNdvi: +0.38,
        dNdbi: -0.28,
        dNdwi: +0.22,
        sarDb: '-2.4 dB',
      },
      metrics: {
        edgeSharpness: 91,
        contextScore: 96,
        shadowRejection: 98,
      },
    },
    {
      id: 'CR-009',
      analysisId: 'AN-2026-0801',
      coordinates: '28.5804° N, 77.3211° E',
      sensor: 'Cartosat-3 / RISAT-1A',
      predictedCategory: 'UNKNOWN',
      predictedSubtype: 'Linear Spectral Strip',
      confidence: 0.58,
      area_m2: 24000,
      reason: 'Model misclassified linear road as unknown artifact',
      status: 'CORRECTED',
      correctedCategory: 'HUMAN',
      correctedSubcategory: 'Road',
      reviewer: 'Senior Analyst Rao',
      timestamp: '2026-01-16T10:45:00Z',
      spectral: {
        dNdvi: -0.29,
        dNdbi: +0.47,
        dNdwi: -0.08,
        sarDb: '+2.1 dB',
      },
      metrics: {
        edgeSharpness: 84,
        contextScore: 89,
        shadowRejection: 93,
      },
    },
  ]);

  // Handle temporal flicker loop (2 Hz)
  useEffect(() => {
    let interval = null;
    if (isFlickerActive && editingItem) {
      interval = setInterval(() => {
        setFlickerFrame((prev) => (prev === 0 ? 1 : 0));
      }, 500);
    } else {
      setFlickerFrame(1);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isFlickerActive, editingItem]);

  // Hotkey navigation handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!editingItem) return;
      // Do not trigger if typing in notes textarea, input, or select
      if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
        if (e.key === 'Escape') setEditingItem(null);
        return;
      }

      if (e.key === 'Escape') {
        setEditingItem(null);
      } else if (e.key === 'a' || e.key === 'A') {
        handleQuickApprove(editingItem.id);
        setEditingItem(null);
      } else if (e.key === ' ') {
        e.preventDefault();
        setIsFlickerActive((prev) => !prev);
      } else if (e.key === 'ArrowLeft') {
        goToSiblingCandidate(-1);
      } else if (e.key === 'ArrowRight') {
        goToSiblingCandidate(1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [editingItem, reviewQueue]);

  const goToSiblingCandidate = (direction) => {
    if (!editingItem) return;
    const currentIndex = reviewQueue.findIndex((item) => item.id === editingItem.id);
    if (currentIndex === -1) return;
    const nextIndex = (currentIndex + direction + reviewQueue.length) % reviewQueue.length;
    handleOpenEdit(reviewQueue[nextIndex]);
  };

  const handleOpenEdit = (item) => {
    setEditingItem(item);
    setCorrectedCategory(item.correctedCategory || item.predictedCategory || 'HUMAN');
    setCorrectedSubcategory(item.correctedSubcategory || item.predictedSubtype || 'Building');
    setReviewerNotes('');
    setZoomLevel(1);
    setIsFlickerActive(false);
  };

  const handleSaveCorrection = () => {
    if (!editingItem) return;
    setReviewQueue((prev) =>
      prev.map((item) =>
        item.id === editingItem.id
          ? {
              ...item,
              status: 'CORRECTED',
              correctedCategory,
              correctedSubcategory,
              reviewer: 'ISRO GIS Analyst',
              timestamp: new Date().toISOString(),
            }
          : item
      )
    );
    setEditingItem(null);
  };

  const handleQuickApprove = (id) => {
    setReviewQueue((prev) =>
      prev.map((item) =>
        item.id === id
          ? {
              ...item,
              status: 'APPROVED',
              correctedCategory: item.predictedCategory,
              correctedSubcategory: item.predictedSubtype,
              reviewer: 'ISRO GIS Analyst',
              timestamp: new Date().toISOString(),
            }
          : item
      )
    );
    if (editingItem && editingItem.id === id) {
      setEditingItem(null);
    }
  };

  const handleExportCandidates = () => {
    const candidateCount = reviewQueue.filter((r) => r.status === 'CORRECTED' || r.status === 'APPROVED').length;
    setExportSuccessMessage(
      `Exported ${candidateCount} verified annotations to Active Learning dataset candidate store. Production models are NOT automatically retrained without explicit validation.`
    );
    setTimeout(() => setExportSuccessMessage(null), 6000);
  };

  const filteredQueue =
    activeFilter === 'ALL'
      ? reviewQueue
      : reviewQueue.filter((item) => item.status === activeFilter);

  const pendingCount = reviewQueue.filter((r) => r.status === 'PENDING').length;
  const correctedCount = reviewQueue.filter((r) => r.status === 'CORRECTED').length;
  const approvedCount = reviewQueue.filter((r) => r.status === 'APPROVED').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Human-in-the-Loop Review Queue</h1>
            <Badge variant="amber">{pendingCount} PENDING REVIEW</Badge>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            ACTIVE-LEARNING FEEDBACK & LOW-CONFIDENCE CLASSIFICATION OVERRIDES
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="primary" icon={Download} onClick={handleExportCandidates}>
            Export Active Learning Candidates
          </Button>
        </div>
      </div>

      {/* Export Success Banner */}
      {exportSuccessMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-950/80 border border-emerald-500/40 flex items-start gap-3 text-xs font-mono animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <span className="text-emerald-200">{exportSuccessMessage}</span>
        </div>
      )}

      {/* Non-Automatic Retraining Safety Card */}
      <div className="p-3.5 rounded-xl bg-space-900 border border-cyan-500/30 flex items-start gap-3 text-xs font-mono">
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-cyan-300">Active Learning Safety Policy: </span>
          <span className="text-slate-300">
            Verified human corrections are staged into the active-learning candidate dataset. Production deep learning models
            are <strong className="text-amber-400 font-bold">NOT automatically retrained</strong> without explicit validation gates and offline benchmark verification.
          </span>
        </div>
      </div>

      {/* 3 Metric Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
        <Card>
          <div className="text-slate-400 uppercase">Pending Review</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{pendingCount} Polygons</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Confidence &lt;80% or Ambiguous</div>
        </Card>
        <Card>
          <div className="text-slate-400 uppercase">Human Corrected</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">{correctedCount} Polygons</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Taxonomic overrides recorded</div>
        </Card>
        <Card>
          <div className="text-slate-400 uppercase">Analyst Approved</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{approvedCount} Polygons</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Verified as ground-truth candidate</div>
        </Card>
      </div>

      {/* Filter Tabs & Queue Table */}
      <Card title="Candidate Verification Queue" subtitle="Filter change detections by review status">
        <div className="flex flex-wrap gap-2 mb-4">
          {[
            { id: 'ALL', label: `All Items (${reviewQueue.length})` },
            { id: 'PENDING', label: `Pending Review (${pendingCount})` },
            { id: 'CORRECTED', label: `Corrected (${correctedCount})` },
            { id: 'APPROVED', label: `Approved (${approvedCount})` },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                activeFilter === tab.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan'
                  : 'bg-space-900 text-slate-400 border border-white/5 hover:border-white/20'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <Table
          data={filteredQueue}
          keyExtractor={(item) => item.id}
          columns={[
            {
              header: 'Region ID',
              accessor: (item) => (
                <div>
                  <span className="font-mono text-cyan-400 font-semibold">{item.id}</span>
                  <div className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                    <MapPin className="w-2.5 h-2.5" />
                    <span>{item.coordinates}</span>
                  </div>
                </div>
              ),
            },
            {
              header: 'Predicted Classification',
              accessor: (item) => (
                <div>
                  <div className="font-medium text-white">{item.predictedSubtype}</div>
                  <div className="text-[10px] text-slate-400 font-mono">
                    <CategoryBadge category={item.predictedCategory} />
                  </div>
                </div>
              ),
            },
            {
              header: 'Confidence',
              accessor: (item) => (
                <span className={`font-mono font-bold ${item.confidence < 0.7 ? 'text-rose-400' : 'text-amber-400'}`}>
                  {(item.confidence * 100).toFixed(1)}%
                </span>
              ),
            },
            {
              header: 'Review Trigger',
              accessor: (item) => <span className="text-xs text-slate-300 block max-w-xs">{item.reason}</span>,
            },
            {
              header: 'Status & Correction',
              accessor: (item) => (
                <div>
                  {item.status === 'PENDING' && <Badge variant="amber" size="sm">REVIEW REQUIRED</Badge>}
                  {item.status === 'APPROVED' && <Badge variant="emerald" size="sm">APPROVED</Badge>}
                  {item.status === 'CORRECTED' && (
                    <div className="space-y-0.5">
                      <Badge variant="cyan" size="sm">CORRECTED</Badge>
                      <div className="text-[10px] text-cyan-300 font-mono">
                        → {item.correctedCategory}: {item.correctedSubcategory}
                      </div>
                    </div>
                  )}
                </div>
              ),
            },
            {
              header: 'Actions',
              accessor: (item) => (
                <div className="flex items-center gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    icon={Edit3}
                    onClick={() => handleOpenEdit(item)}
                  >
                    Review / Override
                  </Button>
                  {item.status === 'PENDING' && (
                    <Button
                      variant="outline"
                      size="sm"
                      icon={Check}
                      onClick={() => handleQuickApprove(item.id)}
                    >
                      Confirm
                    </Button>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* Advanced Zoomable Satellite Chip Inspector & Human Correction Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-space-950/85 backdrop-blur-md animate-fade-in overflow-y-auto">
          <div className="w-full max-w-5xl bg-space-900/95 border border-cyan-500/40 rounded-2xl p-5 sm:p-6 shadow-2xl shadow-cyan-950/50 space-y-5 relative font-mono text-xs max-h-[95vh] overflow-y-auto">
            {/* Modal Topbar */}
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                  <Eye className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                      Human Verification & Correction
                    </h2>
                    <Badge variant="cyan">{editingItem.id}</Badge>
                    <Badge variant="outline">{editingItem.sensor}</Badge>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5 flex items-center gap-2">
                    <span>ANALYSIS {editingItem.analysisId}</span>
                    <span>•</span>
                    <span className="text-cyan-300 flex items-center gap-1">
                      <MapPin className="w-3 h-3" /> {editingItem.coordinates}
                    </span>
                  </p>
                </div>
              </div>

              {/* Prev / Next & Close */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => goToSiblingCandidate(-1)}
                  title="Previous candidate [←]"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-space-800 border border-white/5 transition"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => goToSiblingCandidate(1)}
                  title="Next candidate [→]"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-space-800 border border-white/5 transition"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setEditingItem(null)}
                  title="Close [Esc]"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-space-800 border border-white/5 transition ml-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* 🛰️ Interactive Side-by-Side Satellite Chip Inspection Canvas */}
            <div className="p-4 rounded-xl bg-space-950 border border-white/10 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 pb-2">
                <div className="flex items-center gap-2">
                  <span className="text-white font-bold tracking-wider flex items-center gap-1.5 uppercase text-[11px]">
                    <Layers className="w-3.5 h-3.5 text-cyan-400" />
                    Multi-Temporal Satellite Chip Inspection
                  </span>
                  <span className="text-slate-500">|</span>
                  <span className="text-cyan-400 font-mono text-[10px]">
                    Area: {(editingItem.area_m2 / 10000).toFixed(2)} Ha ({editingItem.area_m2.toLocaleString()} m²)
                  </span>
                </div>

                {/* Inspection Controls Toolbar */}
                <div className="flex items-center gap-2">
                  {/* Flicker Mode Toggle */}
                  <button
                    onClick={() => setIsFlickerActive((prev) => !prev)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border transition flex items-center gap-1.5 ${
                      isFlickerActive
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/50 shadow-glow-amber animate-pulse'
                        : 'bg-space-900 text-slate-300 border-white/10 hover:border-cyan-500/30'
                    }`}
                  >
                    <RefreshCw className={`w-3 h-3 ${isFlickerActive ? 'animate-spin' : ''}`} />
                    {isFlickerActive ? 'Flicker Mode [ACTIVE]' : '2Hz Flicker Mode [Space]'}
                  </button>

                  {/* Mask Overlay Toggle */}
                  <button
                    onClick={() => setShowMask((prev) => !prev)}
                    className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border transition flex items-center gap-1.5 ${
                      showMask
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50'
                        : 'bg-space-900 text-slate-400 border-white/10'
                    }`}
                  >
                    <Sliders className="w-3 h-3" />
                    AI Mask {showMask ? 'ON' : 'OFF'}
                  </button>

                  {/* Zoom Controls */}
                  <div className="flex items-center bg-space-900 rounded-lg border border-white/10 p-0.5 text-[10px]">
                    <button
                      onClick={() => setZoomLevel((z) => Math.max(1, z - 0.5))}
                      disabled={zoomLevel <= 1}
                      className="p-1 text-slate-400 hover:text-white disabled:opacity-30"
                    >
                      <ZoomOut className="w-3 h-3" />
                    </button>
                    <span className="px-1.5 font-mono text-cyan-300">{zoomLevel}x</span>
                    <button
                      onClick={() => setZoomLevel((z) => Math.min(3, z + 0.5))}
                      disabled={zoomLevel >= 3}
                      className="p-1 text-slate-400 hover:text-white disabled:opacity-30"
                    >
                      <ZoomIn className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Dual Satellite Chips Viewport */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* T1 Baseline Chip (2020) */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <span className="text-emerald-400 font-bold">T1: BASELINE (2020-03-12)</span>
                    <span>ISRO Cartosat-3 / Sentinel-2</span>
                  </div>
                  <div
                    onMouseMove={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      setMouseCoord({
                        x: Math.round(e.clientX - rect.left),
                        y: Math.round(e.clientY - rect.top),
                      });
                    }}
                    className="relative h-56 rounded-xl overflow-hidden border border-emerald-500/30 bg-gradient-to-br from-emerald-950/70 via-slate-950 to-green-950/80 select-none group"
                  >
                    {/* Simulated High-Res Baseline Satellite Ground Texture */}
                    <div
                      className="w-full h-full transition-transform duration-200 flex items-center justify-center relative"
                      style={{ transform: `scale(${zoomLevel})` }}
                    >
                      <svg className="w-full h-full opacity-60" viewBox="0 0 300 200">
                        <rect x="0" y="0" width="300" height="200" fill="#064e3b" />
                        <path d="M 0,40 Q 80,60 150,30 T 300,50 L 300,0 L 0,0 Z" fill="#047857" opacity="0.6" />
                        <path d="M 50,200 L 120,90 L 220,110 L 180,200 Z" fill="#065f46" />
                        <path d="M 20,120 L 70,110 L 90,160 L 30,170 Z" fill="#059669" opacity="0.5" />
                        <line x1="0" y1="100" x2="300" y2="100" stroke="#022c22" strokeWidth="2" strokeDasharray="4 4" />
                        <line x1="140" y1="0" x2="140" y2="200" stroke="#022c22" strokeWidth="2" strokeDasharray="4 4" />
                        <circle cx="150" cy="100" r="30" fill="#10b981" opacity="0.15" />
                      </svg>
                      <div className="absolute inset-0 bg-[radial-gradient(#10b981_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />
                    </div>

                    {/* Reticle HUD overlay */}
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-space-950/80 border border-emerald-500/30 text-[9px] text-emerald-300 font-mono">
                      PRE-DEVELOPMENT NATURAL / VEGETATION
                    </div>
                    <div className="absolute bottom-2 right-2 text-[9px] text-slate-400 font-mono bg-space-950/70 px-1.5 py-0.5 rounded border border-white/5">
                      NDVI: 0.68 | NDBI: -0.22
                    </div>
                  </div>
                </div>

                {/* T2 Post-Event Chip (2026) */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <span className="text-cyan-400 font-bold">
                      {isFlickerActive && flickerFrame === 0 ? 'T1 FLICKER FRAME' : 'T2: POST-EVENT (2026-01-15)'}
                    </span>
                    <span className="text-amber-400 font-bold">{editingItem.predictedSubtype}</span>
                  </div>
                  <div
                    onMouseMove={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      setMouseCoord({
                        x: Math.round(e.clientX - rect.left),
                        y: Math.round(e.clientY - rect.top),
                      });
                    }}
                    className={`relative h-56 rounded-xl overflow-hidden border transition-all select-none group ${
                      isFlickerActive && flickerFrame === 0
                        ? 'border-emerald-500/50 bg-gradient-to-br from-emerald-950/70 via-slate-950 to-green-950/80'
                        : 'border-cyan-500/40 bg-gradient-to-br from-slate-950 via-space-900 to-cyan-950/60'
                    }`}
                  >
                    {/* Simulated High-Res Post-Event Ground Texture */}
                    <div
                      className="w-full h-full transition-transform duration-200 flex items-center justify-center relative"
                      style={{ transform: `scale(${zoomLevel})` }}
                    >
                      {isFlickerActive && flickerFrame === 0 ? (
                        <svg className="w-full h-full opacity-60" viewBox="0 0 300 200">
                          <rect x="0" y="0" width="300" height="200" fill="#064e3b" />
                          <circle cx="150" cy="100" r="30" fill="#10b981" opacity="0.3" />
                        </svg>
                      ) : (
                        <svg className="w-full h-full opacity-85" viewBox="0 0 300 200">
                          {/* Cleared Ground / Excavation Zone */}
                          <rect x="0" y="0" width="300" height="200" fill="#1e293b" />
                          <polygon points="90,40 230,45 220,165 80,150" fill="#334155" stroke="#64748b" strokeWidth="1" />
                          {/* New Building Concrete Footprint & Shadow */}
                          <polygon points="120,65 190,68 185,130 115,125" fill="#475569" stroke="#94a3b8" strokeWidth="1.5" />
                          <polygon points="115,125 185,130 195,145 110,140" fill="#0f172a" opacity="0.8" />
                          {/* Ingress Road Corridor */}
                          <line x1="0" y1="95" x2="85" y2="100" stroke="#94a3b8" strokeWidth="4" />
                          <line x1="85" y1="100" x2="115" y2="100" stroke="#e2e8f0" strokeWidth="2" strokeDasharray="3 3" />

                          {/* AI Segmentation Mask Overlay */}
                          {showMask && (
                            <g className="animate-pulse">
                              <polygon
                                points="85,38 235,42 225,170 75,155"
                                fill="rgba(6, 182, 212, 0.25)"
                                stroke="#22d3ee"
                                strokeWidth="2"
                                strokeDasharray="4 2"
                              />
                              <circle cx="85" cy="38" r="3" fill="#22d3ee" />
                              <circle cx="235" cy="42" r="3" fill="#22d3ee" />
                              <circle cx="225" cy="170" r="3" fill="#22d3ee" />
                              <circle cx="75" cy="155" r="3" fill="#22d3ee" />
                            </g>
                          )}
                        </svg>
                      )}
                    </div>

                    {/* Coordinate Crosshairs HUD */}
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-space-950/80 border border-cyan-500/30 text-[9px] text-cyan-300 font-mono flex items-center gap-1.5">
                      <Crosshair className="w-3 h-3 text-cyan-400" />
                      <span>X:{mouseCoord.x}px Y:{mouseCoord.y}px</span>
                    </div>

                    {/* Subtype Badge */}
                    <div className="absolute bottom-2 right-2 text-[9px] text-slate-300 font-mono bg-space-950/80 px-2 py-0.5 rounded border border-cyan-500/30">
                      ΔNDBI: {editingItem.spectral?.dNdbi || '+0.58'} | SAR: {editingItem.spectral?.sarDb || '+3.8 dB'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Multi-Spectral Telemetry & Ground Corroboration Breakdown */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-[11px]">
                <div className="p-2 rounded-lg bg-space-900 border border-rose-500/20">
                  <div className="text-slate-400 text-[10px]">ΔNDVI (Vegetation)</div>
                  <div className="text-rose-400 font-bold text-sm">
                    {editingItem.spectral?.dNdvi ?? -0.44}
                  </div>
                  <div className="text-[9px] text-slate-500">Vegetation loss confirmed</div>
                </div>

                <div className="p-2 rounded-lg bg-space-900 border border-cyan-500/20">
                  <div className="text-slate-400 text-[10px]">ΔNDBI (Built-Up)</div>
                  <div className="text-cyan-400 font-bold text-sm">
                    {editingItem.spectral?.dNdbi ?? +0.58}
                  </div>
                  <div className="text-[9px] text-slate-500">Impervious surface surge</div>
                </div>

                <div className="p-2 rounded-lg bg-space-900 border border-blue-500/20">
                  <div className="text-slate-400 text-[10px]">ΔNDWI (Water/Moisture)</div>
                  <div className="text-blue-400 font-bold text-sm">
                    {editingItem.spectral?.dNdwi ?? -0.05}
                  </div>
                  <div className="text-[9px] text-slate-500">No flood inundation</div>
                </div>

                <div className="p-2 rounded-lg bg-space-900 border border-amber-500/20">
                  <div className="text-slate-400 text-[10px]">SAR Backscatter σ⁰</div>
                  <div className="text-amber-400 font-bold text-sm">
                    {editingItem.spectral?.sarDb ?? '+3.8 dB'}
                  </div>
                  <div className="text-[9px] text-slate-500">Vertical double-bounce</div>
                </div>
              </div>
            </div>

            {/* Original Prediction Reference */}
            <div className="p-3.5 rounded-xl bg-space-950 border border-white/5 space-y-1.5">
              <div className="text-slate-500 uppercase text-[10px] flex items-center justify-between">
                <span>Original Model Prediction (Read-Only)</span>
                <span className="text-cyan-400 font-mono">CONFIDENCE GAUGE</span>
              </div>
              <div className="flex flex-wrap items-center justify-between text-slate-200 gap-2">
                <span>
                  Category: <strong className="text-white">{editingItem.predictedCategory}</strong>
                </span>
                <span>
                  Subtype: <strong className="text-white">{editingItem.predictedSubtype}</strong>
                </span>
                <span>
                  Confidence: <strong className="text-amber-400">{(editingItem.confidence * 100).toFixed(1)}%</strong>
                </span>
              </div>
              <div className="text-[10px] text-slate-400">Trigger: {editingItem.reason}</div>
            </div>

            {/* Human Correction Inputs */}
            <div className="space-y-4">
              <div>
                <label className="text-slate-300 block mb-1 font-bold">Level 1 Category Override:</label>
                <select
                  value={correctedCategory}
                  onChange={(e) => setCorrectedCategory(e.target.value)}
                  className="w-full bg-space-950 border border-white/10 rounded-lg px-3 py-2 text-white"
                >
                  <option value="HUMAN">HUMAN (Anthropogenic Infrastructure & Land-Use)</option>
                  <option value="NATURAL">NATURAL (Vegetation, Riparian, Geological)</option>
                  <option value="DISASTER">DISASTER (Flood Inundation, Wildfire, Landslide)</option>
                  <option value="ATMOSPHERIC">ATMOSPHERIC (Cloud, Shadow, Haze Artifact)</option>
                  <option value="UNKNOWN">UNKNOWN (Ambiguous Spectral Contradiction)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-bold">Level 2 Subcategory Override:</label>
                <select
                  value={correctedSubcategory}
                  onChange={(e) => setCorrectedSubcategory(e.target.value)}
                  className="w-full bg-space-950 border border-white/10 rounded-lg px-3 py-2 text-white"
                >
                  {correctedCategory === 'HUMAN' && (
                    <>
                      <option value="Building">Building / Residential Complex</option>
                      <option value="Road">Road / Highway Widening</option>
                      <option value="Construction">Construction Site Groundwork</option>
                      <option value="Industrial">Industrial Tech-Park / Warehouse</option>
                      <option value="Mining">Mining & Quarrying Excavation</option>
                      <option value="Urban expansion">Urban Sprawl Boundary</option>
                    </>
                  )}
                  {correctedCategory === 'NATURAL' && (
                    <>
                      <option value="Vegetation">Vegetation Canopy Restoration</option>
                      <option value="Water">Surface Water Inundation</option>
                      <option value="River">Riparian Channel Migration</option>
                      <option value="Soil">Bare Soil Moisture Variation</option>
                    </>
                  )}
                  {correctedCategory === 'DISASTER' && (
                    <>
                      <option value="Flood">Flood Inundation Scar</option>
                      <option value="Wildfire">Wildfire Burn Scar</option>
                      <option value="Landslide">Landslide Terrain Exposure</option>
                      <option value="Cyclone">Cyclone Defoliation Path</option>
                    </>
                  )}
                  {correctedCategory === 'ATMOSPHERIC' && (
                    <>
                      <option value="Cloud">Cloud Specular Artifact</option>
                      <option value="Shadow">Shadow Projection Artifact</option>
                      <option value="Haze">Atmospheric Haze Distortion</option>
                    </>
                  )}
                  {correctedCategory === 'UNKNOWN' && (
                    <option value="Unknown">Unclassified Anomaly</option>
                  )}
                </select>
              </div>

              <div>
                <label className="text-slate-300 block mb-1 font-bold">Reviewer Verification Notes:</label>
                <textarea
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  placeholder="Enter physical corroboration justification (e.g., 'Confirmed asphalt corridor on high-res Cartosat-3 and Sentinel overlay')..."
                  className="w-full h-20 bg-space-950 border border-white/10 rounded-lg p-2.5 text-white placeholder-slate-600 resize-none"
                />
              </div>
            </div>

            {/* Analyst Hotkeys Strip & Modal Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-white/10">
              <div className="flex items-center gap-2 text-[10px] text-slate-500 font-mono flex-wrap">
                <span className="text-slate-400 font-bold">HOTKEYS:</span>
                <span className="bg-space-950 px-1.5 py-0.5 rounded border border-white/10 text-cyan-300">[A] Approve</span>
                <span className="bg-space-950 px-1.5 py-0.5 rounded border border-white/10 text-amber-300">[Space] Flicker</span>
                <span className="bg-space-950 px-1.5 py-0.5 rounded border border-white/10 text-slate-300">[←/→] Navigate</span>
                <span className="bg-space-950 px-1.5 py-0.5 rounded border border-white/10 text-slate-400">[Esc] Close</span>
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                <Button size="sm" variant="outline" onClick={() => setEditingItem(null)}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  icon={Check}
                  className="border-emerald-500/40 text-emerald-300 hover:bg-emerald-950"
                  onClick={() => handleQuickApprove(editingItem.id)}
                >
                  Confirm Prediction [A]
                </Button>
                <Button size="sm" variant="primary" icon={Check} onClick={handleSaveCorrection}>
                  Save Human Correction & Audit Trail
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewPage;
