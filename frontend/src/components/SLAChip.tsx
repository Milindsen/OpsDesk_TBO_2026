import React from 'react';
import type { SLAStatus } from '../api/types';

interface SLAChipProps {
  status: SLAStatus;
  className?: string;
  showIcon?: boolean;
}

export const SLAChip: React.FC<SLAChipProps> = ({ status, className = '', showIcon = true }) => {
  if (status === 'breached') {
    return (
      <span
        data-testid="sla-chip-breached"
        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-950/80 text-red-400 border border-red-700/60 animate-pulse ${className}`}
      >
        {showIcon && <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-ping inline-block" />}
        🔴 Breached
      </span>
    );
  }

  if (status === 'at_risk') {
    return (
      <span
        data-testid="sla-chip-at-risk"
        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/70 text-amber-300 border border-amber-600/50 ${className}`}
      >
        {showIcon && <span className="text-[11px] leading-none">⚠</span>}
        At Risk
      </span>
    );
  }

  return (
    <span
      data-testid="sla-chip-ok"
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/70 text-emerald-300 border border-emerald-600/50 ${className}`}
    >
      {showIcon && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 inline-block" />}
      On Track
    </span>
  );
};
