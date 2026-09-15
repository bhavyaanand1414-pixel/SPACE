import React from 'react';
import { AlertTriangle, Database, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export const LoadingSpinner = ({
  message = 'Processing...',
  size = 'md',
}) => {
  const sizeMap = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 gap-3">
      <div
        className={`${sizeMap[size] || sizeMap.md} rounded-full border-cyan-400 border-t-transparent animate-spin`}
      />
      {message && <p className="text-xs font-mono text-cyan-400 tracking-wide">{message}</p>}
    </div>
  );
};

export const SkeletonLoader = ({
  lines = 3,
  className = '',
}) => {
  return (
    <div className={`space-y-2.5 animate-pulse ${className}`}>
      {Array.from({ length: lines }).map((_, idx) => (
        <div
          key={idx}
          className="h-4 bg-white/5 rounded"
          style={{ width: `${100 - (idx % 3) * 15}%` }}
        />
      ))}
    </div>
  );
};

export const ErrorState = ({ title = 'Telemetry Connection Interrupted', message, onRetry }) => {
  return (
    <div className="glass-panel border-rose-500/30 rounded-xl p-8 text-center max-w-md mx-auto my-8">
      <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center mx-auto mb-4">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h4 className="text-base font-semibold text-white mb-1.5">{title}</h4>
      <p className="text-xs text-slate-400 mb-5 leading-relaxed">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" icon={RefreshCw} onClick={onRetry}>
          Retry Connection
        </Button>
      )}
    </div>
  );
};

export const EmptyState = ({ title, description, actionText, onAction, icon }) => {
  return (
    <div className="glass-panel rounded-xl p-12 text-center max-w-lg mx-auto my-8 border-dashed border-white/10">
      <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mx-auto mb-4">
        {icon || <Database className="w-6 h-6" />}
      </div>
      <h4 className="text-base font-semibold text-white mb-1.5">{title}</h4>
      <p className="text-xs text-slate-400 mb-6 leading-relaxed">{description}</p>
      {actionText && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  );
};

export default {
  LoadingSpinner,
  SkeletonLoader,
  ErrorState,
  EmptyState,
};
