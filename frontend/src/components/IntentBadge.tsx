import React from 'react';
import type { Intent } from '../api/types';

interface IntentBadgeProps {
  intent: Intent;
  className?: string;
}

const INTENT_CONFIG: Record<
  Intent,
  { label: string; bg: string; text: string; border: string }
> = {
  refund: {
    label: 'Refund',
    bg: 'bg-emerald-950/60',
    text: 'text-emerald-300',
    border: 'border-emerald-600/40',
  },
  cancellation: {
    label: 'Cancellation',
    bg: 'bg-rose-950/60',
    text: 'text-rose-300',
    border: 'border-rose-600/40',
  },
  amendment: {
    label: 'Amendment',
    bg: 'bg-amber-950/60',
    text: 'text-amber-300',
    border: 'border-amber-600/40',
  },
  voucher: {
    label: 'Voucher',
    bg: 'bg-purple-950/60',
    text: 'text-purple-300',
    border: 'border-purple-600/40',
  },
  inventory_sync: {
    label: 'Inventory Sync',
    bg: 'bg-cyan-950/60',
    text: 'text-cyan-300',
    border: 'border-cyan-600/40',
  },
  payment: {
    label: 'Payment',
    bg: 'bg-blue-950/60',
    text: 'text-blue-300',
    border: 'border-blue-600/40',
  },
  special_request: {
    label: 'Special Request',
    bg: 'bg-fuchsia-950/60',
    text: 'text-fuchsia-300',
    border: 'border-fuchsia-600/40',
  },
  supplier_issue: {
    label: 'Supplier Issue',
    bg: 'bg-orange-950/60',
    text: 'text-orange-300',
    border: 'border-orange-600/40',
  },
  other: {
    label: 'Other',
    bg: 'bg-slate-800/80',
    text: 'text-slate-300',
    border: 'border-slate-600/40',
  },
};

export const IntentBadge: React.FC<IntentBadgeProps> = ({ intent, className = '' }) => {
  const config = INTENT_CONFIG[intent] ?? INTENT_CONFIG.other;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${config.bg} ${config.text} ${config.border} ${className}`}
    >
      {config.label}
    </span>
  );
};
