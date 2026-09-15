import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Map as MapIcon,
  FileText,
  Trees,
  Droplets,
  Building2,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  X,
  Zap,
} from 'lucide-react';
import { Card } from '../components/Card';
import { Table } from '../components/Table';
import { Button } from '../components/Button';
import { Badge, CategoryBadge, SeverityBadge } from '../components/Badge';

export const ResultsPage = () => {
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('ALL');
  const [activeExplainRegion, setActiveExplainRegion] = useState(null);

  const spectralIndices = [
    {
      name: 'NDVI',
      title: 'Normalized Difference Vegetation Index',
      icon: Trees,
      isAvailable: true,
      formula: '(NIR - Red) / (NIR + Red)',
      requiredBands: 'B8 (NIR), B4 (Red)',
      t1Mean: 0.5842,
      t2Mean: 0.3120,
      deltaMean: -0.2722,
      significancePct: '18.4% area drop',
      interpretation: 'Significant vegetation loss & canopy clearing corroborates urban development',
      badgeColor: 'emerald',
    },
    {
      name: 'NDWI',
      title: 'Normalized Difference Water Index',
      icon: Droplets,
      isAvailable: true,
      formula: '(Green - NIR) / (Green + NIR)',
      requiredBands: 'B3 (Green), B8 (NIR)',
      t1Mean: -0.2140,
      t2Mean: -0.1980,
      deltaMean: +0.0160,
      significancePct: 'Stable (<1% shift)',
      interpretation: 'Stable Brahmaputra river channel boundaries with minor silt bank erosion',
      badgeColor: 'cyan',
    },
    {
      name: 'NDBI',
      title: 'Normalized Difference Built-Up Index',
      icon: Building2,
      isAvailable: true,
      formula: '(SWIR1 - NIR) / (SWIR1 + NIR)',
      requiredBands: 'B11 (SWIR1), B8 (NIR)',
      t1Mean: -0.1420,
      t2Mean: +0.2680,
      deltaMean: +0.4100,
      significancePct: '32.6% area surge',
      interpretation: 'Substantial new built-up construction & structural pavement expansion',
      badgeColor: 'amber',
    },
  ];

  const changeRegions = [
    {
      id: 'CR-001',
      category: 'HUMAN',
      subtype: 'New Building Complex',
      area_km2: 0.45,
      area_m2: 450000,
      confidence: 0.96,
      severity: 'MEDIUM',
      centroid: '26.152°N, 91.734°E',
      dates: '2020 → 2026',
      evidence: 'Persistent structural built-up response (NDBI +0.42, NDVI -0.28)',
      spectral: { deltaNdbi: '+0.420', deltaNdvi: '-0.280', deltaBrightness: '+0.245' },
      geometric: { rectangularity: '0.78', elongation: '1.35x', compactness: '0.82' },
      ruleFired: 'HIGH_RECTANGULARITY_BUILTUP_EXPANSION',
      narrative: 'High geometric rectangularity (0.78) and strong positive built-up index response (ΔNDBI: +0.420) confirm new permanent structural construction over previously cleared soil.',
    },
    {
      id: 'CR-002',
      category: 'HUMAN',
      subtype: 'Road Construction / Widening',
      area_km2: 0.88,
      area_m2: 880000,
      confidence: 0.93,
      severity: 'HIGH',
      centroid: '26.178°N, 91.782°E',
      dates: '2020 → 2026',
      evidence: 'Linear asphalt spectral continuum (Elongation 4.8, NDBI +0.35)',
      spectral: { deltaNdbi: '+0.350', deltaNdvi: '-0.310', deltaBrightness: '+0.180' },
      geometric: { rectangularity: '0.62', elongation: '4.80x', compactness: '0.24' },
      ruleFired: 'HIGH_ELONGATION_LINEAR_CORRIDOR',
      narrative: 'Linear transport corridor with high elongation aspect ratio (4.80x) and asphalt spectral profile indicates highway widening and bypass road development.',
    },
    {
      id: 'CR-003',
      category: 'NATURAL',
      subtype: 'Vegetation Shift (Seasonal)',
      area_km2: 1.12,
      area_m2: 1120000,
      confidence: 0.89,
      severity: 'LOW',
      centroid: '26.210°N, 91.650°E',
      dates: '2020 → 2026',
      evidence: 'Cyclic canopy NDVI oscillation (-0.25)',
      spectral: { deltaNdbi: '-0.050', deltaNdvi: '-0.250', deltaBrightness: '+0.060' },
      geometric: { rectangularity: '0.38', elongation: '1.80x', compactness: '0.45' },
      ruleFired: 'NATURAL_CANOPY_VARIANCE',
      narrative: 'Seasonal agricultural and wetland vegetation canopy fluctuation without permanent man-made structural geometries.',
    },
    {
      id: 'CR-004',
      category: 'DISASTER',
      subtype: 'Flood Inundation Scar',
      area_km2: 2.49,
      area_m2: 2490000,
      confidence: 0.94,
      severity: 'HIGH',
      centroid: '26.245°N, 91.810°E',
      dates: '2020 → 2026',
      evidence: 'High NDWI absorption (+0.35) & sediment deposition',
      spectral: { deltaNdbi: '-0.220', deltaNdvi: '-0.380', deltaBrightness: '-0.410' },
      geometric: { rectangularity: '0.29', elongation: '2.40x', compactness: '0.31' },
      ruleFired: 'DISASTER_FLOOD_WATER_SURGE',
      narrative: 'Potential flood inundation: Acute water index surge (ΔNDWI: +0.350) and low radiometric albedo indicate post-monsoon river overflow extent.',
    },
    {
      id: 'CR-005',
      category: 'ATMOSPHERIC',
      subtype: 'Cloud Shadow Artifact',
      area_km2: 0.30,
      area_m2: 300000,
      confidence: 0.97,
      severity: 'LOW',
      centroid: '26.110°N, 91.700°E',
      dates: '2020 → 2026',
      evidence: 'Matched cumulus projection with low spectral albedo',
      spectral: { deltaNdbi: '0.000', deltaNdvi: '0.000', deltaBrightness: '-0.520' },
      geometric: { rectangularity: '0.45', elongation: '1.20x', compactness: '0.68' },
      ruleFired: 'ATMOSPHERIC_SPECULAR_VARIANCE',
      narrative: 'Transient atmospheric shadow projection with acute specular albedo drop and absence of permanent terrain change.',
    },
  ];

  const filteredRegions = selectedCategoryFilter === 'ALL'
    ? changeRegions
    : changeRegions.filter((r) => r.category === selectedCategoryFilter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Analysis Results</h1>
            <Badge variant="cyan">AN-2026-0801</Badge>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            GUWAHATI URBAN SPRAWL & DYNAMICS (SENTINEL-2 MSI • 2020-01-15 → 2026-01-15)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/map">
            <Button size="sm" variant="outline" icon={MapIcon}>
              View on GIS Map
            </Button>
          </Link>
          <Link to="/reports">
            <Button size="sm" variant="primary" icon={FileText}>
              Generate PDF Report
            </Button>
          </Link>
        </div>
      </div>

      {/* 4 System & Reliability Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <div className="text-xs font-mono text-slate-400 uppercase">Model Confidence</div>
          <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">94.2%</div>
          <div className="text-[11px] text-slate-500 mt-1">System Indicator: Siamese U-Net</div>
        </Card>
        <Card>
          <div className="text-xs font-mono text-cyan-400 uppercase">Image Quality Score</div>
          <div className="text-2xl font-bold text-cyan-400 font-mono mt-1">88 / 100</div>
          <div className="text-[11px] text-cyan-500/80 mt-1">Data Quality Matrix: PASS</div>
        </Card>
        <Card>
          <div className="text-xs font-mono text-slate-400 uppercase">Registration Quality</div>
          <div className="text-2xl font-bold text-slate-300 font-mono mt-1">96.4%</div>
          <div className="text-[11px] text-slate-500 mt-1">Co-Registration Error: &lt;0.05 px</div>
        </Card>
        <Card>
          <div className="text-xs font-mono text-amber-400 uppercase">Overall Reliability</div>
          <div className="text-2xl font-bold text-amber-400 font-mono mt-1">HIGH (93.1%)</div>
          <div className="text-[11px] text-amber-500/80 mt-1">Weighted System Composite</div>
        </Card>
      </div>

      {/* Multi-Spectral Supporting Index Cards (Phase 13) */}
      <Card
        title="Multi-Spectral Supporting Index Analysis"
        subtitle="NDVI, NDWI, and NDBI multi-temporal physical verification"
        glow="cyan"
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 font-mono text-xs">
          {spectralIndices.map((idx) => {
            const Icon = idx.icon;
            return (
              <div
                key={idx.name}
                className="p-4 rounded-xl bg-space-900 border border-white/10 space-y-3 relative overflow-hidden"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-space-800 border border-white/5 text-cyan-400">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-white">{idx.name}</div>
                      <div className="text-[10px] text-slate-400">{idx.title}</div>
                    </div>
                  </div>
                  {idx.isAvailable ? (
                    <Badge variant="emerald" size="sm">
                      <CheckCircle2 className="w-3 h-3 mr-1 inline" /> VERIFIED
                    </Badge>
                  ) : (
                    <Badge variant="amber" size="sm">
                      <AlertTriangle className="w-3 h-3 mr-1 inline" /> BYPASSED
                    </Badge>
                  )}
                </div>

                <div className="text-[11px] text-slate-400 bg-space-950 p-2 rounded border border-white/5 space-y-1">
                  <div>Formula: <span className="text-slate-300">{idx.formula}</span></div>
                  <div>Required Bands: <span className="text-cyan-300">{idx.requiredBands}</span></div>
                </div>

                {idx.isAvailable && (
                  <div className="grid grid-cols-3 gap-2 text-center text-[11px]">
                    <div className="p-2 rounded bg-space-950 border border-white/5">
                      <span className="text-slate-500 block text-[10px]">T1 (2020)</span>
                      <span className="text-slate-200 font-bold">{idx.t1Mean.toFixed(3)}</span>
                    </div>
                    <div className="p-2 rounded bg-space-950 border border-white/5">
                      <span className="text-slate-500 block text-[10px]">T2 (2026)</span>
                      <span className="text-slate-200 font-bold">{idx.t2Mean.toFixed(3)}</span>
                    </div>
                    <div className="p-2 rounded bg-space-950 border border-white/5">
                      <span className="text-slate-500 block text-[10px]">DELTA Δ</span>
                      <span
                        className={`font-bold ${
                          idx.deltaMean > 0 ? 'text-amber-400' : 'text-rose-400'
                        }`}
                      >
                        {idx.deltaMean > 0 ? `+${idx.deltaMean.toFixed(3)}` : idx.deltaMean.toFixed(3)}
                      </span>
                    </div>
                  </div>
                )}

                <div className="p-2.5 rounded bg-space-950/80 border border-cyan-500/20 text-[11px] text-slate-300 leading-relaxed">
                  <span className="text-cyan-400 font-bold block text-[10px] uppercase">
                    Physical Evidence Interpretation:
                  </span>
                  {idx.interpretation}
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Category Breakdown Filters */}
      <Card title="Categorical Change Breakdown" subtitle="Filter localized polygons by Level 1 Taxonomy">
        <div className="flex flex-wrap gap-2">
          {[
            { id: 'ALL', label: 'All Detections (42)' },
            { id: 'HUMAN', label: 'Human Activity (30 sites • 3.82 km²)' },
            { id: 'NATURAL', label: 'Natural / Env (8 sites • 1.12 km²)' },
            { id: 'DISASTER', label: 'Disaster (0 sites)' },
            { id: 'ATMOSPHERIC', label: 'Atmospheric (4 sites • 0.30 km²)' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategoryFilter(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                selectedCategoryFilter === cat.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan'
                  : 'bg-space-900 text-slate-400 border border-white/5 hover:border-white/20'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </Card>

      {/* Change Regions Table with Explainability Action */}
      <Card title="Localized Change Polygons" subtitle="Click 'Why Detected?' to inspect grounded ML & GIS explanation">
        <Table
          data={filteredRegions}
          keyExtractor={(item) => item.id}
          columns={[
            {
              header: 'Region ID',
              accessor: (item) => <span className="font-mono text-cyan-400 font-semibold">{item.id}</span>,
            },
            {
              header: 'Category',
              accessor: (item) => <CategoryBadge category={item.category} />,
            },
            {
              header: 'Subtype / Label',
              accessor: (item) => <span className="font-medium text-white">{item.subtype}</span>,
            },
            {
              header: 'Affected Area',
              accessor: (item) => (
                <span className="font-mono text-amber-400 font-semibold">{item.area_km2} km²</span>
              ),
            },
            {
              header: 'Confidence',
              accessor: (item) => (
                <span className="font-mono text-emerald-400">{(item.confidence * 100).toFixed(1)}%</span>
              ),
            },
            {
              header: 'Severity',
              accessor: (item) => <SeverityBadge severity={item.severity} />,
            },
            {
              header: 'Centroid (Lat, Lon)',
              accessor: (item) => <span className="font-mono text-xs text-slate-400">{item.centroid}</span>,
            },
            {
              header: 'Diagnostics',
              accessor: (item) => (
                <Button
                  size="sm"
                  variant="outline"
                  icon={HelpCircle}
                  onClick={() => setActiveExplainRegion(item)}
                >
                  Why Detected?
                </Button>
              ),
            },
          ]}
        />
      </Card>

      {/* 'Why was this detected?' Grounded Explainability Modal */}
      {activeExplainRegion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-space-950/80 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-space-900 border border-cyan-500/40 rounded-2xl p-6 shadow-2xl space-y-5 relative">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-white/10 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-white tracking-tight">Why was this detected?</h2>
                  <Badge variant="cyan">{activeExplainRegion.id}</Badge>
                  <CategoryBadge category={activeExplainRegion.category} />
                </div>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  GROUNDED EXPLAINABLE AI (XAI) DIAGNOSTIC REPORT • {activeExplainRegion.subtype}
                </p>
              </div>
              <button
                onClick={() => setActiveExplainRegion(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-space-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 4 Visual Crops Matrix */}
            <div className="space-y-2">
              <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                Visual Evidence Crop Matrix (Pre-Event, Post-Event, Change Mask, Difference Saliency)
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-2.5 rounded-xl bg-space-950 border border-white/10 text-center space-y-1.5">
                  <div className="text-[10px] font-mono text-slate-400 font-bold">T1 (2020-01-15)</div>
                  <div className="w-full h-28 rounded-lg bg-space-800 border border-white/5 flex items-center justify-center overflow-hidden">
                    <div className="w-16 h-16 rounded bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-[10px] text-emerald-400 font-mono">
                      Vegetation
                    </div>
                  </div>
                  <div className="text-[9px] text-slate-500 font-mono">Baseline Surface</div>
                </div>

                <div className="p-2.5 rounded-xl bg-space-950 border border-white/10 text-center space-y-1.5">
                  <div className="text-[10px] font-mono text-cyan-400 font-bold">T2 (2026-01-15)</div>
                  <div className="w-full h-28 rounded-lg bg-space-800 border border-white/5 flex items-center justify-center overflow-hidden">
                    <div className="w-16 h-16 rounded bg-cyan-950/60 border border-cyan-500/50 flex items-center justify-center text-[10px] text-cyan-300 font-mono">
                      Structural
                    </div>
                  </div>
                  <div className="text-[9px] text-cyan-500/80 font-mono">Comparison Target</div>
                </div>

                <div className="p-2.5 rounded-xl bg-space-950 border border-white/10 text-center space-y-1.5">
                  <div className="text-[10px] font-mono text-amber-400 font-bold">Change Mask</div>
                  <div className="w-full h-28 rounded-lg bg-space-950 border border-white/5 flex items-center justify-center overflow-hidden">
                    <div className="w-16 h-16 rounded bg-white text-black font-bold flex items-center justify-center text-[10px] font-mono">
                      MASK
                    </div>
                  </div>
                  <div className="text-[9px] text-slate-500 font-mono">Binary Delineation</div>
                </div>

                <div className="p-2.5 rounded-xl bg-space-950 border border-white/10 text-center space-y-1.5">
                  <div className="text-[10px] font-mono text-rose-400 font-bold">Saliency Heatmap</div>
                  <div className="w-full h-28 rounded-lg bg-space-800 border border-white/5 flex items-center justify-center overflow-hidden relative">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-rose-500/80 via-amber-400/80 to-blue-500/40 blur-sm flex items-center justify-center text-[9px] text-white font-bold">
                      ACTIVATION
                    </div>
                  </div>
                  <div className="text-[9px] text-slate-500 font-mono">Spectral Saliency</div>
                </div>
              </div>
            </div>

            {/* Grounded Explanation Narrative */}
            <div className="p-4 rounded-xl bg-space-950 border border-cyan-500/30 space-y-2">
              <div className="flex items-center gap-2 text-xs font-mono font-bold text-cyan-400 uppercase">
                <Zap className="w-4 h-4" /> Physical GIS & Remote Sensing Explanation
              </div>
              <p className="text-xs text-slate-200 leading-relaxed font-mono">
                {activeExplainRegion.narrative}
              </p>
              <div className="text-[10px] font-mono text-slate-400 pt-1 border-t border-white/5">
                Decision Rule Executed: <span className="text-cyan-300">{activeExplainRegion.ruleFired}</span>
              </div>
            </div>

            {/* Metrics Radar & System Reliability Bundle */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-xs">
              {/* Spectral & Shape Evidence */}
              <div className="p-4 rounded-xl bg-space-950 border border-white/10 space-y-2">
                <div className="font-bold text-white uppercase text-[11px]">Spectral & Geometric Evidence</div>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="p-2 rounded bg-space-900 border border-white/5">
                    <span className="text-slate-500 block text-[9px]">Δ NDBI (Built-Up)</span>
                    <span className="text-amber-400 font-bold">{activeExplainRegion.spectral.deltaNdbi}</span>
                  </div>
                  <div className="p-2 rounded bg-space-900 border border-white/5">
                    <span className="text-slate-500 block text-[9px]">Δ NDVI (Canopy)</span>
                    <span className="text-rose-400 font-bold">{activeExplainRegion.spectral.deltaNdvi}</span>
                  </div>
                  <div className="p-2 rounded bg-space-900 border border-white/5">
                    <span className="text-slate-500 block text-[9px]">Rectangularity</span>
                    <span className="text-cyan-300 font-bold">{activeExplainRegion.geometric.rectangularity}</span>
                  </div>
                  <div className="p-2 rounded bg-space-900 border border-white/5">
                    <span className="text-slate-500 block text-[9px]">Elongation Ratio</span>
                    <span className="text-cyan-300 font-bold">{activeExplainRegion.geometric.elongation}</span>
                  </div>
                </div>
              </div>

              {/* System Reliability Indicators */}
              <div className="p-4 rounded-xl bg-space-950 border border-white/10 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white uppercase text-[11px]">System Reliability Indicators</span>
                  <Badge variant="emerald" size="sm">HIGH (93.4%)</Badge>
                </div>
                <div className="space-y-1.5 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Model Confidence:</span>
                    <span className="text-emerald-400 font-bold">{(activeExplainRegion.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Data Quality Score:</span>
                    <span className="text-cyan-300 font-bold">88.0%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Registration Fit:</span>
                    <span className="text-slate-200 font-bold">96.4%</span>
                  </div>
                  <div className="pt-2 border-t border-white/5 text-[9px] text-slate-500">
                    Formula: 0.40*ModelConf + 0.35*RegQual + 0.25*ImgQual
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-end pt-2">
              <Button size="sm" variant="primary" onClick={() => setActiveExplainRegion(null)}>
                Close Diagnostic Panel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsPage;
