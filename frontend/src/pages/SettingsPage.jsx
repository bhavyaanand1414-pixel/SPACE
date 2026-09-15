import React from 'react';
import { Card } from '../components/Card';

export const SettingsPage = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">System Settings</h1>
        <p className="text-xs text-slate-400 font-mono mt-0.5">
          INFRASTRUCTURE CONFIGURATION, POSTGIS CONNECTIONS & AI PROVIDERS
        </p>
      </div>

      <div className="space-y-6">
        <Card title="Geospatial Database & Storage" subtitle="PostGIS and raster file system paths">
          <div className="space-y-4 text-xs font-mono">
            <div>
              <label className="text-slate-400 block mb-1">PostGIS Database URL:</label>
              <input
                type="text"
                readOnly
                value="postgresql://postgres:postgres@localhost:5432/sih1518_gis"
                className="w-full p-2.5 rounded bg-space-900 border border-white/10 text-slate-300"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Raster Storage Root:</label>
              <input
                type="text"
                readOnly
                value="/Users/sunnykumar/SIH1518/data/storage"
                className="w-full p-2.5 rounded bg-space-900 border border-white/10 text-slate-300"
              />
            </div>
          </div>
        </Card>

        <Card title="AI Agent Engine Configuration" subtitle="Model inference & LLM tool provider">
          <div className="space-y-4 text-xs font-mono">
            <div>
              <label className="text-slate-400 block mb-1">LLM Orchestration Provider:</label>
              <select className="w-full p-2.5 rounded bg-space-900 border border-white/10 text-slate-200">
                <option>OpenAI (GPT-4o Tool Calling)</option>
                <option>Anthropic (Claude 3.5 Sonnet)</option>
                <option>Google Gemini (Gemini 1.5 Pro)</option>
                <option>Local Fallback Deterministic Engine</option>
              </select>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SettingsPage;
