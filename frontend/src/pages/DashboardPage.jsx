import React from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Layers,
  Building,
  Trees,
  Flame,
  Maximize2,
  UploadCloud,
  PlayCircle,
  FileText,
  MapPin,
} from 'lucide-react';
import { MetricCard } from '../components/MetricCard';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Table } from '../components/Table';
import { Badge } from '../components/Badge';
import { SatelliteOrbitHUD } from '../components/SatelliteOrbitHUD';

export const DashboardPage = () => {
  const recentAnalyses = [
    {
      id: 'AN-2026-0801',
      title: 'Guwahati Urban Sprawl & Infrastructure',
      location: 'Guwahati, Assam',
      dates: '2020-01-15 → 2026-01-15',
      sensor: 'Sentinel-2 MSI (10m)',
      changedArea: '5.24 km²',
      humanPercentage: '72.9%',
      status: 'Completed',
      reliability: 'HIGH',
    },
    {
      id: 'AN-2026-0802',
      title: 'Brahmaputra Flood Plain & River Course Shift',
      location: 'Kaziranga Region, Assam',
      dates: '2025-06-10 → 2025-08-20',
      sensor: 'Sentinel-1 SAR + MSI',
      changedArea: '18.60 km²',
      humanPercentage: '8.4%',
      status: 'Completed',
      reliability: 'HIGH',
    },
    {
      id: 'AN-2026-0803',
      title: 'Bengaluru Outer Ring Road Expansion',
      location: 'Bengaluru, Karnataka',
      dates: '2022-03-01 → 2026-02-15',
      sensor: 'Sentinel-2 MSI (10m)',
      changedArea: '3.15 km²',
      humanPercentage: '91.2%',
      status: 'Completed',
      reliability: 'HIGH',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner with Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Mission Dashboard</h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            ISRO SIH1518 SATELLITE INTELLIGENCE TELEMETRY & CHANGE MONITORING
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/upload">
            <Button size="sm" variant="primary" icon={UploadCloud}>
              Upload Raster Tile
            </Button>
          </Link>
          <Link to="/analysis">
            <Button size="sm" variant="secondary" icon={PlayCircle}>
              Run AI Model
            </Button>
          </Link>
        </div>
      </div>

      {/* ISRO EO Constellation Orbit & Mission Telemetry HUD */}
      <SatelliteOrbitHUD />

      {/* Required 6 Core Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Analyses"
          value={18}
          unit="runs"
          icon={Activity}
          color="indigo"
          description="Processed multi-temporal pairs"
        />
        <MetricCard
          title="Detected Changes"
          value={342}
          unit="regions"
          icon={Layers}
          color="cyan"
          change="+14.2%"
          isPositive={true}
          description="Vectorized change polygons"
        />
        <MetricCard
          title="Human Changes"
          value={218}
          unit="sites"
          icon={Building}
          color="cyan"
          description="Buildings, Roads, Infrastructure"
        />
        <MetricCard
          title="Natural Changes"
          value={84}
          unit="sites"
          icon={Trees}
          color="emerald"
          description="Vegetation, Water, Soil"
        />
        <MetricCard
          title="Disaster Changes"
          value={28}
          unit="zones"
          icon={Flame}
          color="rose"
          description="Floods, Landslides, Burn scars"
        />
        <MetricCard
          title="Affected Area"
          value="48.6"
          unit="km²"
          icon={Maximize2}
          color="amber"
          description="Geodesic surface change"
        />
      </div>

      {/* Analysis Overview & Telemetry Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card
            title="Recent Change Intelligence Analyses"
            subtitle="Verified multi-temporal satellite observations"
            headerAction={
              <Link to="/history">
                <Button variant="ghost" size="sm">
                  View All History
                </Button>
              </Link>
            }
          >
            <Table
              data={recentAnalyses}
              keyExtractor={(item) => item.id}
              columns={[
                {
                  header: 'Analysis ID / Title',
                  accessor: (item) => (
                    <div>
                      <div className="font-semibold text-white">{item.title}</div>
                      <div className="text-[11px] text-cyan-400 font-mono">{item.id}</div>
                    </div>
                  ),
                },
                {
                  header: 'Observation Dates',
                  accessor: (item) => (
                    <div className="font-mono text-xs text-slate-300">{item.dates}</div>
                  ),
                },
                {
                  header: 'Changed Area',
                  accessor: (item) => (
                    <div className="font-mono text-xs font-semibold text-amber-400">
                      {item.changedArea}
                    </div>
                  ),
                },
                {
                  header: 'Human Activity',
                  accessor: (item) => (
                    <Badge variant="cyan">{item.humanPercentage}</Badge>
                  ),
                },
                {
                  header: 'Status',
                  accessor: () => <Badge variant="emerald">COMPLETED</Badge>,
                },
              ]}
            />
          </Card>
        </div>

        {/* System & Model Information Panel */}
        <div className="space-y-6">
          <Card title="System Diagnostics" subtitle="Remote Sensing & ML Engines">
            <div className="space-y-4 text-xs font-mono">
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <span className="text-slate-400">Primary AI Architecture:</span>
                <span className="text-cyan-400 font-bold">Siamese U-Net v1.0</span>
              </div>
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <span className="text-slate-400">GIS Core Engine:</span>
                <span className="text-emerald-400 font-bold">Rasterio 1.3.9 / GDAL</span>
              </div>
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <span className="text-slate-400">Spatial Persistence:</span>
                <span className="text-indigo-400 font-bold">PostgreSQL 15 / PostGIS</span>
              </div>
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <span className="text-slate-400">AI Agent Orchestrator:</span>
                <span className="text-cyan-400 font-bold">18 Tool Handlers</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Hardware Acceleration:</span>
                <span className="text-emerald-400 font-bold">Auto (CUDA / MPS / CPU)</span>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-white/5 flex gap-2">
              <Link to="/map" className="flex-1">
                <Button variant="outline" size="sm" className="w-full" icon={MapPin}>
                  GIS Map
                </Button>
              </Link>
              <Link to="/reports" className="flex-1">
                <Button variant="secondary" size="sm" className="w-full" icon={FileText}>
                  PDF Reports
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
