import React, { useState } from 'react';
import { PlayCircle, CheckCircle2, Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { Badge } from '../components/Badge';

export const AnalysisPage = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);

  const stages = [
    { name: 'Raster Read & Validation', desc: 'Verify CRS, spatial overlap, bit depth' },
    { name: 'Reprojection & Resampling', desc: 'Harmonize grids to target UTM projection' },
    { name: 'Sub-Pixel Co-Registration', desc: 'Phase correlation alignment optimization' },
    { name: 'AI Siamese U-Net Inference', desc: 'Deep feature difference extraction' },
    { name: 'Spectral Index Analysis', desc: 'Corroborate with NDBI, NDVI, NDWI' },
    { name: 'Hierarchical Classification', desc: 'Categorize into Human, Natural, Disaster' },
    { name: 'PostGIS Vectorization', desc: 'Douglas-Peucker polygon & geodesic area calc' },
    { name: 'Intelligence Synthesis', desc: 'Generate statistics & reliability score' },
  ];

  const handleStartAnalysis = () => {
    setIsProcessing(true);
    setCurrentStageIndex(0);

    let stage = 0;
    const interval = setInterval(() => {
      stage += 1;
      if (stage >= stages.length) {
        clearInterval(interval);
        setIsProcessing(false);
        setCurrentStageIndex(stages.length);
      } else {
        setCurrentStageIndex(stage);
      }
    }, 800);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Run Change Detection Analysis</h1>
        <p className="text-xs text-slate-400 font-mono mt-0.5">
          AI-ORCHESTRATED MULTI-TEMPORAL PROCESSING PIPELINE
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Analysis Parameters" className="md:col-span-1">
          <div className="space-y-4 text-xs font-mono">
            <div>
              <label className="text-slate-400 block mb-1">Target Pair:</label>
              <div className="p-2 rounded bg-space-900 border border-white/5 text-cyan-400">
                Guwahati (2020 → 2026)
              </div>
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Inference Architecture:</label>
              <select className="w-full p-2 rounded bg-space-900 border border-white/10 text-slate-200">
                <option>Siamese U-Net v1.0 (Recommended)</option>
                <option>Spectral Difference Baseline</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Confidence Threshold:</label>
              <input
                type="range"
                min="0.5"
                max="0.95"
                step="0.05"
                defaultValue="0.65"
                className="w-full accent-cyan-400"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>0.50 (Sensitive)</span>
                <span>0.65 (Standard)</span>
                <span>0.95 (Strict)</span>
              </div>
            </div>

            <Button
              variant="primary"
              size="md"
              className="w-full mt-4"
              icon={PlayCircle}
              isLoading={isProcessing}
              disabled={isProcessing}
              onClick={handleStartAnalysis}
            >
              {isProcessing ? 'Processing Pipeline...' : 'Launch Intelligence Pipeline'}
            </Button>
          </div>
        </Card>

        {/* Pipeline Stage Tracker */}
        <Card title="Pipeline Orchestration Pipeline" className="md:col-span-2">
          <div className="space-y-3">
            {stages.map((stage, idx) => {
              const isCompleted = currentStageIndex > idx;
              const isCurrent = currentStageIndex === idx && isProcessing;
              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border flex items-center justify-between transition-all ${
                    isCompleted
                      ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                      : isCurrent
                      ? 'bg-cyan-950/40 border-cyan-500 text-cyan-300 shadow-glow-cyan animate-pulse'
                      : 'bg-space-900/50 border-white/5 text-slate-500'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : isCurrent ? (
                      <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin shrink-0" />
                    ) : (
                      <Clock className="w-4 h-4 text-slate-600 shrink-0" />
                    )}
                    <div>
                      <div className="text-xs font-semibold font-mono">{stage.name}</div>
                      <div className="text-[10px] text-slate-400">{stage.desc}</div>
                    </div>
                  </div>
                  <Badge variant={isCompleted ? 'emerald' : isCurrent ? 'cyan' : 'gray'} size="sm">
                    {isCompleted ? 'DONE' : isCurrent ? 'RUNNING' : 'PENDING'}
                  </Badge>
                </div>
              );
            })}
          </div>

          {currentStageIndex === stages.length && (
            <div className="mt-6 p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 flex items-center justify-between">
              <div>
                <div className="text-sm font-bold text-white">Analysis Successfully Executed</div>
                <div className="text-xs text-slate-300">42 change regions localized and classified in PostGIS.</div>
              </div>
              <Link to="/results">
                <Button variant="primary" size="sm" icon={ArrowRight} iconPosition="right">
                  View Results
                </Button>
              </Link>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default AnalysisPage;
