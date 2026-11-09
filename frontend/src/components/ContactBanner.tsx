import React from 'react';
import { AlertTriangle } from 'lucide-react';
import type { Intent } from '../api/types';

interface ContactBannerProps {
  contactCount: number;
  intent?: Intent | string;
  agencyName?: string;
  className?: string;
}

function getOrdinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

export const ContactBanner: React.FC<ContactBannerProps> = ({
  contactCount,
  intent = 'inquiry',
  agencyName = 'Agency',
  className = '',
}) => {
  if (contactCount <= 1) {
    return null;
  }

  const ordinal = getOrdinal(contactCount);
  const formattedIntent = intent.replace(/_/g, ' ');

  return (
    <div
      data-testid="contact-banner"
      className={`flex items-center gap-3 px-4 py-2.5 bg-amber-950/70 border border-amber-500/60 rounded-md text-amber-200 shadow-sm animate-pulse-fast ${className}`}
    >
      <div className="flex-shrink-0 text-amber-400">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <div className="flex-1 text-sm font-medium">
        <span className="font-semibold text-amber-100">⚠ {ordinal} contact</span>
        {' '}about <span className="underline decoration-amber-400/60">{formattedIntent}</span> from{' '}
        <span className="font-semibold text-amber-100">{agencyName}</span>
      </div>
      <span className="text-xs px-2 py-0.5 rounded bg-amber-900/60 border border-amber-600/50 text-amber-300 font-mono font-semibold">
        Repeat Contact
      </span>
    </div>
  );
};
