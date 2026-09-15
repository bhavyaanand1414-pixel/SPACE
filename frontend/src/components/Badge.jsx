import React from 'react';

export const Badge = ({ children, variant = 'default', size = 'md' }) => {
  const variantStyles = {
    default: 'bg-space-800 text-slate-300 border-space-700',
    cyan: 'bg-cyan-950/60 text-cyan-400 border-cyan-500/30',
    emerald: 'bg-emerald-950/60 text-emerald-400 border-emerald-500/30',
    amber: 'bg-amber-950/60 text-amber-400 border-amber-500/30',
    rose: 'bg-rose-950/60 text-rose-400 border-rose-500/30',
    indigo: 'bg-indigo-950/60 text-indigo-400 border-indigo-500/30',
    purple: 'bg-purple-950/60 text-purple-400 border-purple-500/30',
    gray: 'bg-slate-900 text-slate-400 border-slate-700',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs font-mono',
    md: 'px-2.5 py-1 text-xs font-medium',
  };

  return (
    <span className={`inline-flex items-center rounded-full border ${variantStyles[variant] || variantStyles.default} ${sizeStyles[size] || sizeStyles.md} tracking-wide`}>
      {children}
    </span>
  );
};

export const CategoryBadge = ({ category }) => {
  switch (category) {
    case 'HUMAN':
      return <Badge variant="cyan">Human Activity</Badge>;
    case 'NATURAL':
      return <Badge variant="emerald">Natural / Env</Badge>;
    case 'DISASTER':
      return <Badge variant="rose">Disaster</Badge>;
    case 'ATMOSPHERIC':
      return <Badge variant="purple">Atmospheric</Badge>;
    default:
      return <Badge variant="gray">Unknown</Badge>;
  }
};

export const SeverityBadge = ({ severity }) => {
  switch (severity) {
    case 'CRITICAL':
      return <Badge variant="rose">CRITICAL</Badge>;
    case 'HIGH':
      return <Badge variant="amber">HIGH</Badge>;
    case 'MEDIUM':
      return <Badge variant="cyan">MEDIUM</Badge>;
    default:
      return <Badge variant="gray">LOW</Badge>;
  }
};

export default Badge;
