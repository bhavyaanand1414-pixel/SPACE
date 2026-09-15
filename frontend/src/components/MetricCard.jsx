import React from 'react';

export const MetricCard = ({
  title,
  value,
  unit,
  change,
  isPositive,
  icon: Icon,
  color = 'cyan',
  description,
}) => {
  const colorMap = {
    cyan: {
      bg: 'bg-cyan-950/40 border-cyan-500/30 text-cyan-400',
      iconBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
      glow: 'hover:border-cyan-500/40 hover:shadow-glow-cyan',
    },
    emerald: {
      bg: 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400',
      iconBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      glow: 'hover:border-emerald-500/40 hover:shadow-glow-emerald',
    },
    amber: {
      bg: 'bg-amber-950/40 border-amber-500/30 text-amber-400',
      iconBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      glow: 'hover:border-amber-500/40',
    },
    rose: {
      bg: 'bg-rose-950/40 border-rose-500/30 text-rose-400',
      iconBg: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
      glow: 'hover:border-rose-500/40 hover:shadow-glow-rose',
    },
    indigo: {
      bg: 'bg-indigo-950/40 border-indigo-500/30 text-indigo-400',
      iconBg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
      glow: 'hover:border-indigo-500/40',
    },
  };

  const scheme = colorMap[color] || colorMap.cyan;

  return (
    <div className={`glass-panel rounded-xl p-5 border transition-all duration-300 ${scheme.glow}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 font-mono">
          {title}
        </span>
        {Icon && (
          <div className={`p-2.5 rounded-lg border ${scheme.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl lg:text-3xl font-bold tracking-tight text-white font-mono">
          {value}
        </span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>

      {(change || description) && (
        <div className="mt-2 flex items-center justify-between text-xs">
          {change && (
            <span
              className={`font-mono font-medium ${
                isPositive ? 'text-emerald-400' : 'text-rose-400'
              }`}
            >
              {isPositive ? '▲' : '▼'} {change}
            </span>
          )}
          {description && <span className="text-slate-400 truncate">{description}</span>}
        </div>
      )}
    </div>
  );
};

export default MetricCard;
