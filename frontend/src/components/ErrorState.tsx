import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  message = 'An unexpected error occurred while loading data.',
  onRetry,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center bg-red-950/20 rounded-lg border border-red-900/50 ${className}`}
    >
      <div className="w-12 h-12 mb-3 rounded-full bg-red-900/30 flex items-center justify-center text-red-400">
        <AlertCircle className="w-6 h-6 text-red-400" />
      </div>
      <h3 className="text-sm font-semibold text-red-200 mb-1">Failed to load</h3>
      <p className="text-xs text-red-300/80 max-w-sm mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-red-600/80 hover:bg-red-600 rounded-md transition-colors shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </button>
      )}
    </div>
  );
};
