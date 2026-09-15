import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Satellite, 
  ShieldCheck, 
  Bell, 
  Activity, 
  Clock, 
  Plus, 
  Menu, 
  X, 
  CheckCircle2, 
  AlertTriangle,
  LayoutDashboard,
  UploadCloud,
  Layers,
  Map as MapIcon,
  Bot,
  Search,
  Sparkles
} from 'lucide-react';
import { checkHealth } from '../services/api';

export const Navbar = () => {
  const navigate = useNavigate();

  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking' | 'online' | 'offline'
  const [latencyMs, setLatencyMs] = useState(null);
  const [utcTime, setUtcTime] = useState('');
  const [istTime, setIstTime] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const [notifications] = useState([
    {
      id: 1,
      type: 'warning',
      title: 'Low Confidence Detection',
      desc: 'Region #CR-004 flagged for HITL review (74% conf).',
      time: '2m ago'
    },
    {
      id: 2,
      type: 'alert',
      title: 'Flood Inundation Warning',
      desc: 'Significant water-level delta detected in Sector B.',
      time: '12m ago'
    },
    {
      id: 3,
      type: 'success',
      title: 'Pipeline Co-registration Complete',
      desc: '2D FFT alignment verified (<0.04 px error).',
      time: '25m ago'
    }
  ]);

  useEffect(() => {
    const updateClocks = () => {
      const now = new Date();
      const utcString = now.toUTCString().slice(17, 25) + ' UTC';
      const istString = now.toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }) + ' IST';

      setUtcTime(utcString);
      setIstTime(istString);
    };

    updateClocks();
    const clockTimer = setInterval(updateClocks, 1000);
    return () => clearInterval(clockTimer);
  }, []);

  useEffect(() => {
    const verifyBackendWithLatency = async () => {
      const startTime = performance.now();
      try {
        const data = await checkHealth();
        const endTime = performance.now();
        const roundTripTime = Math.round(endTime - startTime);

        if (data && data.status === 'ok') {
          setBackendStatus('online');
          setLatencyMs(roundTripTime);
        } else {
          setBackendStatus('offline');
          setLatencyMs(null);
        }
      } catch {
        setBackendStatus('offline');
        setLatencyMs(null);
      }
    };

    verifyBackendWithLatency();
    const healthInterval = setInterval(verifyBackendWithLatency, 15000);
    return () => clearInterval(healthInterval);
  }, []);

  const mobileNavItems = [
    { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { label: 'Semantic Search', to: '/search', icon: Search },
    { label: 'Discovery', to: '/discovery', icon: Sparkles },
    { label: 'Upload Imagery', to: '/upload', icon: UploadCloud },
    { label: 'Change Results', to: '/results', icon: Layers },
    { label: 'Interactive GIS Map', to: '/map', icon: MapIcon },
    { label: 'AI Agent Portal', to: '/agent', icon: Bot },
  ];

  return (
    <header className="sticky top-0 z-50 w-full glass-panel border-b border-white/5 px-4 sm:px-6 py-2.5">
      <div className="flex items-center justify-between gap-4">
        
        {/* Left Section: Logo & ISRO Mission Badge */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-indigo-600 p-0.5 shadow-glow-cyan">
              <div className="w-full h-full bg-space-950 rounded-[7px] flex items-center justify-center group-hover:bg-transparent transition-colors">
                <Satellite className="w-5 h-5 text-cyan-400 group-hover:text-white transition-colors" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base text-white tracking-tight">SIH1518</span>
                <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  MoD / DGIS
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono hidden sm:block">
                SEMANTIC RETRIEVAL & CHANGE ANALYSIS
              </p>
            </div>
          </Link>
        </div>

        {/* Center Section: Dual Mission Clocks (UTC & IST) */}
        <div className="hidden lg:flex items-center gap-3 px-3 py-1.5 rounded-lg bg-space-900 border border-white/5 text-xs font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-cyan-300 font-semibold">{utcTime || '00:00:00 UTC'}</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300">{istTime || '00:00:00 IST'}</span>
        </div>

        {/* Right Section: Telemetry, Notifications, Actions */}
        <div className="flex items-center gap-3">
          
          {/* Real-Time API Health & Latency Telemetry */}
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-space-900 border border-white/5 text-xs font-mono">
            <div
              className={`w-2 h-2 rounded-full ${
                backendStatus === 'online'
                  ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                  : backendStatus === 'checking'
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-rose-500 shadow-[0_0_8px_#f43f5e]'
              }`}
            />
            <span className="text-slate-400 text-[11px]">API:</span>
            <span
              className={`font-semibold text-[11px] ${
                backendStatus === 'online'
                  ? 'text-emerald-400'
                  : backendStatus === 'checking'
                  ? 'text-amber-400'
                  : 'text-rose-400'
              }`}
            >
              {backendStatus.toUpperCase()}
            </span>
            {latencyMs !== null && (
              <span className="text-[10px] text-slate-500 flex items-center gap-1 border-l border-white/10 pl-1.5">
                <Activity className="w-3 h-3 text-cyan-400" />
                {latencyMs}ms
              </span>
            )}
          </div>

          {/* Review Queue & Alert Notification Bell */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 rounded-lg bg-space-900 hover:bg-space-800 border border-white/5 text-slate-300 hover:text-white transition-colors"
              aria-label="Open Notifications"
            >
              <Bell className="w-4 h-4" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-cyan-500 text-[10px] font-bold text-space-950 flex items-center justify-center ring-2 ring-space-950 animate-pulse">
                  {notifications.length}
                </span>
              )}
            </button>

            {/* Notification Dropdown Flyout */}
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 rounded-xl bg-space-900 border border-white/10 shadow-2xl p-3 z-50">
                <div className="flex items-center justify-between pb-2 border-b border-white/10 mb-2">
                  <span className="text-xs font-mono font-bold text-slate-200">ACTIVE TELEMETRY ALERTS</span>
                  <span className="text-[10px] text-cyan-400 font-mono">{notifications.length} Active</span>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {notifications.map((n) => (
                    <div 
                      key={n.id} 
                      className="p-2 rounded-lg bg-space-950/60 border border-white/5 hover:border-cyan-500/30 transition-all cursor-pointer"
                    >
                      <div className="flex items-center gap-1.5 mb-1">
                        {n.type === 'warning' && <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />}
                        {n.type === 'alert' && <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />}
                        {n.type === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                        <span className="text-xs font-semibold text-slate-200">{n.title}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-tight">{n.desc}</p>
                      <span className="text-[9px] text-slate-500 font-mono mt-1 block">{n.time}</span>
                    </div>
                  ))}
                </div>
                <Link
                  to="/review"
                  onClick={() => setShowNotifications(false)}
                  className="block text-center text-xs font-mono text-cyan-400 hover:text-cyan-300 pt-2.5 mt-2 border-t border-white/5"
                >
                  View Review Queue &rarr;
                </Link>
              </div>
            )}
          </div>

          {/* Quick Action: New Analysis */}
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-space-950 font-semibold text-xs transition-all shadow-glow-cyan active:scale-95"
          >
            <Plus className="w-4 h-4 text-space-950" />
            <span className="hidden sm:inline">New Analysis</span>
          </button>

          {/* ISRO Official Shield */}
          <div className="hidden xl:flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-950/40 border border-indigo-500/30 text-indigo-300 text-xs font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span>ISRO SPACE TECH</span>
          </div>
        </div>
      </div>

      {/* Mobile Drawer (When hamburger menu is active) */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-3 pt-3 border-t border-white/10 space-y-2 pb-2">
          {mobileNavItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-300 hover:text-cyan-400 hover:bg-white/5"
            >
              <item.icon className="w-4 h-4 text-cyan-400" />
              <span>{item.label}</span>
            </Link>
          ))}
          <div className="pt-2 px-3 flex items-center justify-between text-xs font-mono text-slate-400 border-t border-white/5">
            <span>{utcTime}</span>
            <span>{istTime}</span>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
