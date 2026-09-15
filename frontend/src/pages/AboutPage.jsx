import React from 'react';
import { Card } from '../components/Card';

export const AboutPage = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">About SIH1518 Platform</h1>
        <p className="text-xs text-slate-400 font-mono mt-0.5">
          SMART INDIA HACKATHON • ISRO SPACE TECHNOLOGY PROBLEM STATEMENT
        </p>
      </div>

      <Card title="Problem Statement Context" subtitle="ISRO — Change Detection Due to Human Activities">
        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <p>
            Rapid anthropogenic land-use modification across urban fringes, river basins, and forested tracts necessitates automated, high-precision remote-sensing intelligence.
          </p>
          <p>
            Standard image subtraction algorithms ($I_1 - I_2$) fail because they conflate seasonal phenological cycles, cloud shadows, and sensor misalignment with true human construction. The <strong>SIH1518 Platform</strong> introduces hierarchical classification, sub-pixel co-registration, and grounded AI agent reasoning to solve this challenge.
          </p>
        </div>
      </Card>

      <Card title="Hierarchical Classification Taxonomy">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3 rounded-lg bg-space-900 border border-cyan-500/20">
            <div className="font-bold text-cyan-400 font-mono mb-1">LEVEL 1: HUMAN ACTIVITY</div>
            <p className="text-slate-400">
              New buildings, road widening, bridge construction, industrial parks, quarrying/mining, and urban expansion.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-space-900 border border-emerald-500/20">
            <div className="font-bold text-emerald-400 font-mono mb-1">LEVEL 1: NATURAL / ENV</div>
            <p className="text-slate-400">
              Seasonal canopy growth/loss, water-level shifts, river meander, soil moisture changes.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-space-900 border border-rose-500/20">
            <div className="font-bold text-rose-400 font-mono mb-1">LEVEL 1: DISASTER</div>
            <p className="text-slate-400">
              Flood inundation scars, earthquake damage zones, landslide scars, and wildfire burn perimeters.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-space-900 border border-purple-500/20">
            <div className="font-bold text-purple-400 font-mono mb-1">LEVEL 1: ATMOSPHERIC</div>
            <p className="text-slate-400">
              Cumulus clouds, cirrus haze, cloud shadows, and sensor registration residuals.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AboutPage;
