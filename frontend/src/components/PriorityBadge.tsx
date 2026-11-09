import React from 'react';
import type { Priority } from '../api/types';

interface PriorityBadgeProps {
  priority: Priority;
  className?: string;
}

const PRIORITY_CONFIG: Record<
  Priority,
  { label: string; textClass: string; bgClass: string; borderClass: string; dotClass: string }
> = {
  P1: {
    label: 'P1',
    textClass: 'text-red-400',
    bgClass: 'bg-red-950/60',
    borderClass: 'border-red-600',
    dotClass: 'bg-red-600',
  },
  P2: {
    label: 'P2',
    textClass: 'text-orange-400',
    bgClass: 'bg-orange-950/60',
    borderClass: 'border-orange-500',
    dotClass: 'bg-orange-500',
  },
  P3: {
    label: 'P3',
    textClass: 'text-blue-400',
    bgClass: 'bg-blue-950/60',
    borderClass: 'border-blue-500',
    dotClass: 'bg-blue-500',
  },
  P4: {
    label: 'P4',
    textClass: 'text-gray-300',
    bgClass: 'bg-slate-800/80',
    borderClass: 'border-gray-400',
    dotClass: 'bg-gray-400',
  },
};

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, className = '' }) => {
  const config = PRIORITY_CONFIG[priority] ?? PRIORITY_CONFIG.P4;

  return (
    <span
      data-testid={`priority-badge-${priority}`}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold border ${config.bgClass} ${config.textClass} ${config.borderClass} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotClass}`} />
      <span>{priority}</span>
    </span>
  );
};
