import React from 'react';

export const Card = ({
  title,
  subtitle,
  children,
  headerAction,
  className = '',
  glow = 'none',
}) => {
  const glowStyles = {
    none: '',
    cyan: 'border-cyan-500/30 hover:shadow-glow-cyan',
    emerald: 'border-emerald-500/30 hover:shadow-glow-emerald',
    rose: 'border-rose-500/30 hover:shadow-glow-rose',
  };

  return (
    <div className={`glass-panel rounded-xl p-5 ${glowStyles[glow]} ${className}`}>
      {(title || headerAction) && (
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-white/5">
          <div>
            {title && <h3 className="text-base font-semibold text-white tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};

export default Card;
