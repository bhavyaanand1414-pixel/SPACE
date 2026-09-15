import React from 'react';
import { Link } from 'react-router-dom';
import {
  Satellite,
  Layers,
  Shield,
  ArrowRight,
} from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { SatelliteOrbitHUD } from '../components/SatelliteOrbitHUD';

export const LandingPage = () => {
  return (
    <div className="space-y-16 py-6">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-cyan-400 text-xs font-mono mb-2">
          <Satellite className="w-3.5 h-3.5 animate-pulse" />
          <span>SMART INDIA HACKATHON — PROBLEM STATEMENT SIH1518 (ISRO)</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-tight">
          AI-Powered Multi-Temporal <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400">
            Satellite Change Intelligence
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Autonomous multi-temporal remote sensing platform distinguishing human infrastructure activities from natural cycles, disasters, and atmospheric artifacts.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link to="/dashboard">
            <Button size="lg" variant="primary" icon={ArrowRight} iconPosition="right">
              Open Intelligence Dashboard
            </Button>
          </Link>
          <Link to="/upload">
            <Button size="lg" variant="secondary" icon={Layers}>
              Upload GeoTIFF Tiles
            </Button>
          </Link>
        </div>
      </section>

      {/* Real-time Constellation Orbit & Mission Telemetry HUD */}
      <section className="max-w-6xl mx-auto">
        <SatelliteOrbitHUD />
      </section>

      {/* Core Capabilities Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card
          title="Hierarchical Classification"
          subtitle="Beyond Naive Differencing"
          glow="cyan"
        >
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Categorizes ground dynamics into Level 1 major classes (Human, Natural, Disaster, Atmospheric, Unknown) and Level 2 granular subtypes with spectral index corroboration.
          </p>
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="cyan">New Buildings</Badge>
            <Badge variant="emerald">Vegetation Shift</Badge>
            <Badge variant="rose">Flood Scars</Badge>
            <Badge variant="purple">Cloud Shadows</Badge>
          </div>
        </Card>

        <Card
          title="Sub-Pixel GIS Co-Registration"
          subtitle="GDAL / Rasterio / PostGIS"
          glow="emerald"
        >
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Automated CRS standardization, reprojection, and phase-correlation image alignment to prevent misalignment artifacts from being falsely labeled as human change.
          </p>
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="emerald">UTM Reprojection</Badge>
            <Badge variant="emerald">Geodesic Areas</Badge>
            <Badge variant="emerald">PostGIS Vectors</Badge>
          </div>
        </Card>

        <Card
          title="Grounded AI Agent"
          subtitle="Tool-Calling Orchestration"
          glow="rose"
        >
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Multi-modal conversational agent connected directly to verified PostGIS queries and ML masks. The LLM explains real detections without hallucinating data.
          </p>
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="indigo">18 Tools</Badge>
            <Badge variant="indigo">Fact Grounded</Badge>
            <Badge variant="indigo">PDF Reports</Badge>
          </div>
        </Card>
      </section>

      {/* Scientific Principle Alert */}
      <section className="glass-panel border-cyan-500/30 rounded-xl p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-cyan-400" />
              ISRO Scientific Principle & Multi-Sensor Readiness
            </h3>
            <p className="text-xs text-slate-300 max-w-2xl">
              Optical Sentinel-2 MSI, Landsat-8/9, and Sentinel-1 SAR imagery compatibility. Every observation calculates temporal differences, data quality scores, and multi-factor reliability indicators.
            </p>
          </div>
          <Link to="/about" className="shrink-0">
            <Button variant="outline" size="sm">
              Read Technical Spec
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
