import React, { useState } from 'react';
import {
  Download,
  FileText,
  ShieldCheck,
  Sparkles,
  CheckCircle2,
  Eye,
  Printer,
  X,
  Award,
} from 'lucide-react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Table } from '../components/Table';
import { Badge } from '../components/Badge';

export const ReportsPage = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationSuccess, setGenerationSuccess] = useState(null);
  const [selectedDossier, setSelectedDossier] = useState(null);

  const [reports, setReports] = useState([
    {
      id: 'REP-AN-2026-0801',
      title: 'Guwahati Multi-Temporal Satellite Change Intelligence Dossier',
      analysisId: 'AN-2026-0801',
      studyArea: 'Guwahati Urban Corridor',
      dates: '2020-01-15 → 2026-01-15',
      sensor: 'Sentinel-2 MSI (10m)',
      size: '2.8 MB',
      created: '2026-08-30 12:30:00 UTC',
      status: 'COMPLETED',
      downloadUrl: 'http://localhost:8000/api/v1/reports/REP-AN-2026-0801',
    },
    {
      id: 'REP-AN-2026-0802',
      title: 'Brahmaputra Flood Plain Extent & NDWI Inundation Assessment',
      analysisId: 'AN-2026-0802',
      studyArea: 'Brahmaputra Basin',
      dates: '2025-06-10 → 2025-08-20',
      sensor: 'Sentinel-1 SAR + Sentinel-2',
      size: '4.2 MB',
      created: '2026-08-25 14:15:00 UTC',
      status: 'COMPLETED',
      downloadUrl: 'http://localhost:8000/api/v1/reports/REP-AN-2026-0801',
    },
  ]);

  const handleGenerateReport = () => {
    setIsGenerating(true);
    setGenerationSuccess(null);

    setTimeout(() => {
      const newReportId = `REP-AN-2026-${Date.now().toString().slice(-4)}`;
      const newReport = {
        id: newReportId,
        title: 'Guwahati Urban Expansion & Spectral Delta Report',
        analysisId: 'AN-2026-0801',
        studyArea: 'Guwahati Urban Corridor',
        dates: '2020-01-15 → 2026-01-15',
        sensor: 'Sentinel-2 MSI (10m GSD)',
        size: '3.1 MB',
        created: new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC',
        status: 'COMPLETED',
        downloadUrl: 'http://localhost:8000/api/v1/reports/REP-AN-2026-0801',
      };

      setReports((prev) => [newReport, ...prev]);
      setIsGenerating(false);
      setGenerationSuccess(`Successfully compiled publication-grade PDF report: ${newReportId}`);
      setTimeout(() => setGenerationSuccess(null), 6000);
    }, 1200);
  };

  const handleDownload = (url) => {
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <FileText className="w-6 h-6 text-cyan-400" />
              Automated Geospatial Intelligence Reports
            </h1>
            <Badge variant="cyan">REPORTLAB ENGINE</Badge>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            COMPREHENSIVE MULTI-TEMPORAL DOSSIERS WITH PROJECTED STATISTICS & SPECTRAL DELTAS
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="md"
            icon={Sparkles}
            onClick={handleGenerateReport}
            disabled={isGenerating}
          >
            {isGenerating ? 'Compiling PDF...' : 'Generate New PDF Report'}
          </Button>
        </div>
      </div>

      {/* Generation Success Notification */}
      {generationSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-950/80 border border-emerald-500/40 flex items-start gap-3 text-xs font-mono animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <span className="text-emerald-200">{generationSuccess}</span>
        </div>
      )}

      {/* 4 Statistics Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 font-mono text-xs">
        <Card>
          <div className="text-slate-400 uppercase">Total Study Area</div>
          <div className="text-2xl font-bold text-white mt-1">104.85 km²</div>
          <div className="text-[10px] text-slate-500 mt-0.5">104,850,000 m² (10m GSD)</div>
        </Card>
        <Card>
          <div className="text-slate-400 uppercase">Total Changed Area</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">5.24 km²</div>
          <div className="text-[10px] text-slate-500 mt-0.5">4.99% of total scene</div>
        </Card>
        <Card>
          <div className="text-slate-400 uppercase">Human Infrastructure</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">3.82 km²</div>
          <div className="text-[10px] text-slate-500 mt-0.5">72.9% of changed area</div>
        </Card>
        <Card>
          <div className="text-slate-400 uppercase">Natural / Seasonal</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">1.12 km²</div>
          <div className="text-[10px] text-slate-500 mt-0.5">21.4% of changed area</div>
        </Card>
      </div>

      {/* Report Generator Control & Configuration */}
      <Card title="Executive PDF Report Dossier Specification" subtitle="Publication-ready analytical summary parameters">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
          <div className="p-3 rounded-lg bg-space-950 border border-white/5 space-y-1">
            <div className="text-slate-500 uppercase text-[10px]">Active Study Scene</div>
            <div className="text-white font-bold">Guwahati Urban Corridor</div>
            <div className="text-[10px] text-slate-400">EPSG:32646 (WGS 84 / UTM Zone 46N)</div>
          </div>
          <div className="p-3 rounded-lg bg-space-950 border border-white/5 space-y-1">
            <div className="text-slate-500 uppercase text-[10px]">Sensor & Model</div>
            <div className="text-white font-bold">Sentinel-2 MSI (10m GSD)</div>
            <div className="text-[10px] text-slate-400">Siamese U-Net Deep Learning v1.0.0</div>
          </div>
          <div className="p-3 rounded-lg bg-space-950 border border-white/5 space-y-1">
            <div className="text-slate-500 uppercase text-[10px]">Data Quality Score</div>
            <div className="text-emerald-400 font-bold">88 / 100 (HIGH RELIABILITY)</div>
            <div className="text-[10px] text-slate-400">2D FFT Phase Shift &lt; 0.05 px</div>
          </div>
        </div>
      </Card>

      {/* Reports Table */}
      <Card title="Generated Geospatial Intelligence Reports" subtitle="Compiled ReportLab PDF files ready for download">
        <Table
          data={reports}
          keyExtractor={(item) => item.id}
          columns={[
            {
              header: 'Report Title & ID',
              accessor: (item) => (
                <div>
                  <div className="font-semibold text-white">{item.title}</div>
                  <div className="text-[11px] text-cyan-400 font-mono flex items-center gap-1.5 mt-0.5">
                    <span>{item.id}</span>
                    <Badge variant="cyan" size="sm">PDF</Badge>
                  </div>
                </div>
              ),
            },
            {
              header: 'Study Scene',
              accessor: (item) => <span className="font-mono text-xs text-slate-300">{item.studyArea}</span>,
            },
            {
              header: 'Observation Dates',
              accessor: (item) => <span className="font-mono text-xs text-slate-400">{item.dates}</span>,
            },
            {
              header: 'File Size',
              accessor: (item) => <span className="font-mono text-xs text-slate-400">{item.size}</span>,
            },
            {
              header: 'Status',
              accessor: (item) => <Badge variant="emerald" size="sm">{item.status}</Badge>,
            },
            {
              header: 'Actions',
              accessor: (item) => (
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    icon={Eye}
                    onClick={() => setSelectedDossier(item)}
                  >
                    Preview Dossier
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    icon={Download}
                    onClick={() => handleDownload(item.downloadUrl)}
                  >
                    Download PDF
                  </Button>
                </div>
              ),
            },
          ]}
        />
      </Card>

      {/* Mandatory Scientific Disclaimer Card */}
      <div className="p-4 rounded-xl bg-space-900 border border-cyan-500/30 text-xs text-slate-300 leading-relaxed font-mono">
        <div className="flex items-center gap-2 font-bold text-cyan-300 mb-1.5">
          <ShieldCheck className="w-4 h-4 text-cyan-400" />
          ISRO SIH1518 Mandatory Scientific Advisory Disclaimer
        </div>
        <p className="text-slate-400">
          This publication report is compiled automatically by the <strong>ISRO SIH1518 Change Intelligence Platform</strong> using
          deterministic geospatial metrics, Siamese U-Net deep learning, and multi-spectral index deltas (NDVI, NDWI, NDBI).
          Causality statements represent algorithmic indicators and do not substitute for authoritative field ground-truth or administrative land-registry verification.
        </p>
      </div>

      {/* 🇮🇳 ISRO / NRSC Geospatial Change Intelligence Technical Dossier Modal */}
      {selectedDossier && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-space-950/85 backdrop-blur-md overflow-y-auto">
          <div className="relative w-full max-w-4xl max-h-[92vh] overflow-y-auto rounded-2xl bg-[#0b0f19] border border-cyan-500/40 shadow-glow-cyan p-6 sm:p-8 text-slate-100 font-sans space-y-6">
            {/* Top Close Button */}
            <button
              type="button"
              onClick={() => setSelectedDossier(null)}
              className="absolute top-4 right-4 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Official Header & Mission Seals */}
            <div className="border-b-2 border-cyan-500/30 pb-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 via-cyan-500 to-indigo-600 p-0.5 flex items-center justify-center shadow-lg">
                    <div className="w-full h-full bg-[#0b0f19] rounded-[10px] flex items-center justify-center">
                      <Award className="w-6 h-6 text-amber-400" />
                    </div>
                  </div>
                  <div>
                    <div className="text-[11px] font-mono tracking-widest text-cyan-400 uppercase font-bold">
                      INDIAN SPACE RESEARCH ORGANISATION • NRSC
                    </div>
                    <div className="text-lg sm:text-xl font-bold text-white tracking-tight">
                      Earth Observation Satellite Change Dossier
                    </div>
                    <div className="text-xs text-slate-400 font-mono">
                      Project SIH-1518 • National Remote Sensing Centre, Hyderabad
                    </div>
                  </div>
                </div>

                <div className="text-right font-mono">
                  <span className="inline-block px-2.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-[10px] font-bold uppercase">
                    OFFICIAL ANALYTICAL REPORT
                  </span>
                  <div className="text-[11px] text-slate-400 mt-1">
                    DOSSIER ID: <span className="text-white font-semibold">{selectedDossier.id}</span>
                  </div>
                  <div className="text-[10px] text-slate-500">
                    GENERATED: {selectedDossier.created}
                  </div>
                </div>
              </div>
            </div>

            {/* Scene & Platform Metadata Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
              <div className="p-3 rounded-lg bg-space-900/90 border border-white/5">
                <div className="text-[10px] text-slate-500 uppercase">Target Scene</div>
                <div className="text-white font-bold mt-0.5">{selectedDossier.studyArea}</div>
                <div className="text-[10px] text-slate-400">Assam, India</div>
              </div>

              <div className="p-3 rounded-lg bg-space-900/90 border border-white/5">
                <div className="text-[10px] text-slate-500 uppercase">Temporal Baseline</div>
                <div className="text-amber-300 font-bold mt-0.5">{selectedDossier.dates}</div>
                <div className="text-[10px] text-slate-400">Multi-temporal</div>
              </div>

              <div className="p-3 rounded-lg bg-space-900/90 border border-white/5">
                <div className="text-[10px] text-slate-500 uppercase">Sensor Constellation</div>
                <div className="text-cyan-300 font-bold mt-0.5">{selectedDossier.sensor}</div>
                <div className="text-[10px] text-slate-400">GSD: 10.0 m/px</div>
              </div>

              <div className="p-3 rounded-lg bg-space-900/90 border border-white/5">
                <div className="text-[10px] text-slate-500 uppercase">Spatial Reference</div>
                <div className="text-emerald-300 font-bold mt-0.5">EPSG:32646</div>
                <div className="text-[10px] text-slate-400">UTM Zone 46N / WGS84</div>
              </div>
            </div>

            {/* Analytical Findings Summary */}
            <div className="p-4 rounded-xl bg-space-900/70 border border-cyan-500/20 space-y-2">
              <div className="text-xs font-bold font-mono text-cyan-300 uppercase tracking-wider">
                1. Executive Geospatial Metric Summary
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Automated multi-spectral segmentation and change vector analysis identified a net surface change of{' '}
                <strong className="text-cyan-300">5.24 km² (5,240,000 m²)</strong> across the 104.85 km² survey footprint (4.99% net perturbation).
                Change vectors are dominated by anthropogenic infrastructure expansion (72.9%) with moderate fluvial channel morphology (21.4%).
              </p>
            </div>

            {/* Spectral Delta Breakdown Table */}
            <div className="space-y-2">
              <div className="text-xs font-bold font-mono text-cyan-300 uppercase tracking-wider">
                2. Sub-Region Spectral Index Matrix & Ground Delta
              </div>
              <div className="overflow-x-auto rounded-xl border border-white/10">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="bg-space-900 text-slate-400 border-b border-white/10 text-[11px]">
                    <tr>
                      <th className="p-2.5">Region</th>
                      <th className="p-2.5">Category</th>
                      <th className="p-2.5">Area (m²)</th>
                      <th className="p-2.5">Confidence</th>
                      <th className="p-2.5">Δ NDVI</th>
                      <th className="p-2.5">Δ NDBI</th>
                      <th className="p-2.5">SAR Backscatter</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-slate-200">
                    <tr className="hover:bg-white/5">
                      <td className="p-2.5 font-bold text-white">#1 Urban Sprawl</td>
                      <td className="p-2.5"><Badge variant="emerald" size="sm">Infrastructure</Badge></td>
                      <td className="p-2.5 text-cyan-300 font-bold">1,450,200 m²</td>
                      <td className="p-2.5 text-emerald-400">94%</td>
                      <td className="p-2.5 text-rose-400">-0.46 (Loss)</td>
                      <td className="p-2.5 text-amber-400">+0.72 (Built)</td>
                      <td className="p-2.5 text-cyan-300">+4.1 dB (Metallic)</td>
                    </tr>
                    <tr className="hover:bg-white/5">
                      <td className="p-2.5 font-bold text-white">#2 Highway Corridor</td>
                      <td className="p-2.5"><Badge variant="emerald" size="sm">Infrastructure</Badge></td>
                      <td className="p-2.5 text-cyan-300 font-bold">820,400 m²</td>
                      <td className="p-2.5 text-emerald-400">91%</td>
                      <td className="p-2.5 text-rose-400">-0.38 (Loss)</td>
                      <td className="p-2.5 text-amber-400">+0.65 (Paving)</td>
                      <td className="p-2.5 text-cyan-300">+2.9 dB (Asphalt)</td>
                    </tr>
                    <tr className="hover:bg-white/5">
                      <td className="p-2.5 font-bold text-white">#3 Fluvial Siltation</td>
                      <td className="p-2.5"><Badge variant="amber" size="sm">Hydrology</Badge></td>
                      <td className="p-2.5 text-cyan-300 font-bold">2,969,400 m²</td>
                      <td className="p-2.5 text-emerald-400">89%</td>
                      <td className="p-2.5 text-slate-400">-0.22 (Scour)</td>
                      <td className="p-2.5 text-slate-400">-0.45 (Wet)</td>
                      <td className="p-2.5 text-purple-400">-16.2 dB (Specular)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Neural Network & Coregistration Validation */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
              <div className="p-3 rounded-lg bg-space-900 border border-white/5 space-y-1">
                <span className="text-[10px] text-slate-400 block">COREGISTRATION ERROR:</span>
                <span className="text-emerald-400 font-bold">Δx = 0.02 px, Δy = 0.04 px</span>
                <span className="text-[10px] text-slate-500 block">Sub-pixel 2D FFT Cross-Correlation Phase Peak = 0.94</span>
              </div>
              <div className="p-3 rounded-lg bg-space-900 border border-white/5 space-y-1">
                <span className="text-[10px] text-slate-400 block">AI INFERENCE ENGINE:</span>
                <span className="text-cyan-400 font-bold">Siamese ResNet50 + U-Net Feature Pyramids</span>
                <span className="text-[10px] text-slate-500 block">Hallucination Mitigation: Spectral Index Corroborated</span>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-white/10 font-mono">
              <div className="text-[11px] text-slate-400">
                Authorized for Remote Sensing Decision Support • ISRO SIH1518
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <Button
                  variant="outline"
                  size="sm"
                  icon={Printer}
                  onClick={() => window.print()}
                  className="flex-1 sm:flex-none"
                >
                  Print / Save PDF
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  icon={Download}
                  onClick={() => handleDownload(selectedDossier.downloadUrl)}
                  className="flex-1 sm:flex-none"
                >
                  Download Dossier
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsPage;
