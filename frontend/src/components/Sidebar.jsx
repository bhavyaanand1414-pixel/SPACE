import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  UploadCloud,
  Layers,
  Map as MapIcon,
  LineChart,
  FileText,
  History,
  Bot,
  CheckSquare,
  Cpu,
  Settings,
  Info,
  PlayCircle,
  Search,
  Sparkles,
} from 'lucide-react';

export const Sidebar = () => {
  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/search', icon: Search, label: 'Semantic Search' },
    { to: '/discovery', icon: Sparkles, label: 'Discovery' },
    { to: '/upload', icon: UploadCloud, label: 'Upload Imagery' },
    { to: '/analysis', icon: PlayCircle, label: 'Run Analysis' },
    { to: '/results', icon: Layers, label: 'Change Results' },
    { to: '/map', icon: MapIcon, label: 'Interactive GIS Map' },
    { to: '/timeline', icon: LineChart, label: 'Time-Series' },
    { to: '/reports', icon: FileText, label: 'PDF Reports' },
    { to: '/history', icon: History, label: 'Analysis History' },
    { to: '/agent', icon: Bot, label: 'AI Agent Portal' },
    { to: '/review', icon: CheckSquare, label: 'Human Review Queue' },
    { to: '/models', icon: Cpu, label: 'Model Benchmarks' },
    { to: '/settings', icon: Settings, label: 'Settings' },
    { to: '/about', icon: Info, label: 'About SIH1518' },
  ];

  return (
    <aside className="w-64 shrink-0 glass-panel border-r border-white/5 p-4 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-61px)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-[10px] font-mono uppercase font-bold tracking-widest text-cyan-400/70">
          Navigation Modules
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.15)] font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]'
                }`
              }
            >
              <item.icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="pt-4 border-t border-white/5">
        <div className="p-3 rounded-lg bg-space-900 border border-white/5">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
            <span>PIPELINE ENGINE</span>
            <span className="text-emerald-400">READY</span>
          </div>
          <p className="text-[10px] text-slate-400">Siamese U-Net v1.0.0 (Optical MSI / SAR-C)</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
