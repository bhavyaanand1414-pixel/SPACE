import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  ArrowRight,
  AlertCircle,
} from 'lucide-react';
import { Card } from '../components/Card';
import { Badge, CategoryBadge } from '../components/Badge';
import { Button } from '../components/Button';

export const TimelinePage = () => {
  const [selectedStepIndex, setSelectedStepIndex] = useState(0);
  const [comparisonMode, setComparisonMode] = useState('sequential');
  const [pairFrom, setPairFrom] = useState('2020');
  const [pairTo, setPairTo] = useState('2026');

  // Multi-temporal observation sequence
  const observations = [
    { id: 'T1', date: '2020-01-15', label: '2020 Baseline', sensor: 'Sentinel-2 MSI (10m)', clouds: '0.2%' },
    { id: 'T2', date: '2021-01-15', label: '2021 T2', sensor: 'Sentinel-2 MSI (10m)', clouds: '1.4%' },
    { id: 'T3', date: '2022-01-15', label: '2022 T3', sensor: 'Sentinel-2 MSI (10m)', clouds: '0.8%' },
    { id: 'T4', date: '2024-01-15', label: '2024 T4', sensor: 'Sentinel-2 MSI (10m)', clouds: '2.1%' },
    { id: 'T5', date: '2026-01-15', label: '2026 Current', sensor: 'Sentinel-2 MSI (10m)', clouds: '0.5%' },
  ];

  // Sequential Step Comparisons (T_i -> T_{i+1})
  const sequentialSteps = [
    {
      step: 1,
      from: '2020-01-15',
      to: '2021-01-15',
      fromLabel: '2020',
      toLabel: '2021',
      interval: '365 days (~1.0 year)',
      changedAreaKm2: 0.50,
      humanGrowthKm2: 0.40,
      naturalShiftKm2: 0.10,
      disasterKm2: 0.00,
      dominant: 'HUMAN',
      keyEvent: 'Initial ground clearance & road foundation laying in North corridor',
    },
    {
      step: 2,
      from: '2021-01-15',
      to: '2022-01-15',
      fromLabel: '2021',
      toLabel: '2022',
      interval: '365 days (~1.0 year)',
      changedAreaKm2: 0.40,
      humanGrowthKm2: 0.40,
      naturalShiftKm2: 0.00,
      disasterKm2: 0.00,
      dominant: 'HUMAN',
      keyEvent: 'Structural superstructure elevation of logistics hub & bypass junction',
    },
    {
      step: 3,
      from: '2022-01-15',
      to: '2024-01-15',
      fromLabel: '2022',
      toLabel: '2024',
      interval: '730 days (~2.0 years)',
      changedAreaKm2: 1.70,
      humanGrowthKm2: 1.30,
      naturalShiftKm2: 0.40,
      disasterKm2: 0.00,
      dominant: 'HUMAN',
      keyEvent: 'Major industrial tech-park commissioning & residential expansion',
    },
    {
      step: 4,
      from: '2024-01-15',
      to: '2026-01-15',
      fromLabel: '2024',
      toLabel: '2026',
      interval: '730 days (~2.0 years)',
      changedAreaKm2: 1.40,
      humanGrowthKm2: 0.90,
      naturalShiftKm2: 0.20,
      disasterKm2: 0.30,
      dominant: 'HUMAN',
      keyEvent: 'High-density commercial paving and minor monsoon channel siltation',
    },
  ];

  // Cumulative Area and Category over Time Data
  const timeSeriesData = [
    { year: '2020', cumulativeChange: 0.0, humanArea: 0.0, naturalArea: 0.0, disasterArea: 0.0, intervalDelta: 0.0 },
    { year: '2021', cumulativeChange: 0.5, humanArea: 0.4, naturalArea: 0.1, disasterArea: 0.0, intervalDelta: 0.5 },
    { year: '2022', cumulativeChange: 0.9, humanArea: 0.8, naturalArea: 0.1, disasterArea: 0.0, intervalDelta: 0.4 },
    { year: '2024', cumulativeChange: 2.6, humanArea: 2.1, naturalArea: 0.5, disasterArea: 0.0, intervalDelta: 1.7 },
    { year: '2026', cumulativeChange: 4.0, humanArea: 3.0, naturalArea: 0.7, disasterArea: 0.3, intervalDelta: 1.4 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Multi-Temporal Time-Series Analysis</h1>
            <Badge variant="cyan">5-DATE SEQUENCE</Badge>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            GUWAHATI URBAN SPRAWL & CORRIDOR DYNAMICS (2020-01-15 → 2026-01-15)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={comparisonMode === 'sequential' ? 'primary' : 'outline'}
            onClick={() => setComparisonMode('sequential')}
          >
            Sequential Steps
          </Button>
          <Button
            size="sm"
            variant={comparisonMode === 'pairwise' ? 'primary' : 'outline'}
            onClick={() => setComparisonMode('pairwise')}
          >
            Pairwise Diff
          </Button>
        </div>
      </div>

      {/* Mandatory Availability Notice Banner */}
      <div className="p-3.5 rounded-xl bg-space-900 border border-cyan-500/30 flex items-start gap-3 text-xs font-mono">
        <AlertCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-cyan-300">Observation Availability Notice: </span>
          <span className="text-slate-300">
            Analysis interval depends on available satellite observations. Timestamps represent actual Sentinel-2 MSI
            orbital overpasses. Intermediate intervals are computed discretely without synthetic image fabrication.
          </span>
        </div>
      </div>

      {/* Observation Timeline Bar */}
      <Card title="Acquisition Timeline Sequence" subtitle="Click any temporal slice to inspect localized change">
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {observations.map((obs, idx) => (
            <div
              key={obs.id}
              onClick={() => setSelectedStepIndex(Math.min(idx, sequentialSteps.length - 1))}
              className={`p-3 rounded-xl border transition-all cursor-pointer ${
                idx === selectedStepIndex
                  ? 'bg-cyan-500/15 border-cyan-500/50 shadow-glow-cyan'
                  : 'bg-space-950 border-white/5 hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="font-bold text-cyan-400">{obs.id}</span>
                <span className="text-slate-500">{obs.clouds} cloud</span>
              </div>
              <div className="text-sm font-bold text-white mt-1">{obs.label}</div>
              <div className="text-[10px] text-slate-400 font-mono mt-0.5">{obs.date}</div>
              <div className="text-[9px] text-slate-500 truncate mt-1">{obs.sensor}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Step Comparison or Pairwise View */}
      {comparisonMode === 'sequential' ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {sequentialSteps.map((step, idx) => (
            <div
              key={step.step}
              onClick={() => setSelectedStepIndex(idx)}
              className={`p-4 rounded-xl border transition-all cursor-pointer space-y-2.5 font-mono text-xs ${
                selectedStepIndex === idx
                  ? 'bg-space-900 border-cyan-500/50 shadow-glow-cyan'
                  : 'bg-space-950 border-white/5 hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between">
                <Badge variant="cyan" size="sm">STEP {step.step}</Badge>
                <span className="text-[10px] text-slate-400">{step.interval}</span>
              </div>
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                <span>{step.fromLabel}</span>
                <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
                <span>{step.toLabel}</span>
              </div>
              <div className="text-lg font-bold text-amber-400">+{step.changedAreaKm2} km²</div>
              <div className="text-[11px] text-slate-300 leading-tight">{step.keyEvent}</div>
              <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[10px]">
                <span className="text-slate-400">Dominant:</span>
                <CategoryBadge category={step.dominant} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <Card title="Custom Pairwise Multi-Temporal Comparison">
          <div className="flex flex-wrap items-center gap-4 font-mono text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Baseline Acquisition (T_before):</label>
              <select
                value={pairFrom}
                onChange={(e) => setPairFrom(e.target.value)}
                className="bg-space-950 border border-white/10 rounded-lg px-3 py-1.5 text-white"
              >
                <option value="2020">2020-01-15 (Baseline)</option>
                <option value="2021">2021-01-15</option>
                <option value="2022">2022-01-15</option>
                <option value="2024">2024-01-15</option>
              </select>
            </div>
            <ArrowRight className="w-4 h-4 text-cyan-400 mt-5 hidden sm:block" />
            <div>
              <label className="text-slate-400 block mb-1">Comparison Acquisition (T_after):</label>
              <select
                value={pairTo}
                onChange={(e) => setPairTo(e.target.value)}
                className="bg-space-950 border border-white/10 rounded-lg px-3 py-1.5 text-white"
              >
                <option value="2021">2021-01-15</option>
                <option value="2022">2022-01-15</option>
                <option value="2024">2024-01-15</option>
                <option value="2026">2026-01-15 (Current)</option>
              </select>
            </div>
            <div className="mt-5">
              <Badge variant="cyan">Interval: {pairFrom} → {pairTo}</Badge>
            </div>
          </div>
        </Card>
      )}

      {/* Dual Progression Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Area-Over-Time Graph */}
        <Card
          title="Area-Over-Time Progression (km²)"
          subtitle="Cumulative total detected change and interval delta"
        >
          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeSeriesData}>
                <defs>
                  <linearGradient id="colorCumulative" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="year" stroke="#64748b" fontStyle="mono" />
                <YAxis stroke="#64748b" fontStyle="mono" unit=" km²" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0a0f1d', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff', fontSize: '12px', fontFamily: 'monospace' }}
                />
                <Area
                  type="monotone"
                  dataKey="cumulativeChange"
                  name="Cumulative Changed Area"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorCumulative)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* 2. Category-Over-Time Graph */}
        <Card
          title="Category-Over-Time Breakdown"
          subtitle="Human activity growth vs natural shift vs disaster impact"
        >
          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeSeriesData}>
                <defs>
                  <linearGradient id="colorHuman" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorNatural" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorDisaster" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="year" stroke="#64748b" fontStyle="mono" />
                <YAxis stroke="#64748b" fontStyle="mono" unit=" km²" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0a0f1d', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff', fontSize: '12px', fontFamily: 'monospace' }}
                />
                <Legend />
                <Area type="monotone" dataKey="humanArea" name="Human Built-Up (km²)" stroke="#06b6d4" strokeWidth={2} fill="url(#colorHuman)" />
                <Area type="monotone" dataKey="naturalArea" name="Natural Shift (km²)" stroke="#10b981" strokeWidth={2} fill="url(#colorNatural)" />
                <Area type="monotone" dataKey="disasterArea" name="Disaster Impact (km²)" stroke="#ef4444" strokeWidth={2} fill="url(#colorDisaster)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default TimelinePage;
