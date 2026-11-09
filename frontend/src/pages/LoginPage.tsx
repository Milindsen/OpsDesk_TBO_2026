import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle, Flame, Lock, Mail } from 'lucide-react';
import { useAuth } from '../store/auth';

const DEMO_USERS = [
  { role: 'Operations Lead', email: 'lead@opsdesk.com', desc: 'Full access: Queues, Insights, Export' },
  { role: 'Support Agent', email: 'agent@opsdesk.com', desc: 'Queues, Case 360, Triage, Assign' },
  { role: 'Escalation Manager', email: 'em@opsdesk.com', desc: 'Escalation queue, priority resolution' },
  { role: 'Travel Requester', email: 'requester@agency.com', desc: 'Agency ticket submissions' },
];

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('lead@opsdesk.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/tickets';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Email is required');
      return;
    }
    setError(null);
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const axiosErr = err as any;
        setError(axiosErr.response?.data?.detail || 'Invalid email or password. Please try again.');
      } else {
        setError('Connection failed. Ensure the OpsDesk backend is running on port 8000.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('password123');
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center items-center p-4">
      {/* Container */}
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-600 shadow-xl shadow-indigo-600/30 mb-4">
            <Flame className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">OpsDesk</h1>
          <p className="text-sm text-slate-400 mt-1">High-Throughput Operations Management</p>
        </div>

        {/* Card */}
        <div className="bg-slate-800 border border-slate-700/80 rounded-xl p-6 shadow-2xl">
          {error && (
            <div className="mb-5 flex items-start gap-2.5 p-3 rounded-lg bg-red-950/60 border border-red-700/60 text-xs text-red-200">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Work Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="agent@opsdesk.com"
                  required
                  className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label htmlFor="pass" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  id="pass"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full mt-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm rounded-lg transition-colors shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <span>Sign in to Workspace</span>
              )}
            </button>
          </form>

          {/* Quick Demo Logins */}
          <div className="mt-6 pt-5 border-t border-slate-700/80">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
              Quick Switch Role (Demo)
            </div>
            <div className="grid grid-cols-2 gap-2">
              {DEMO_USERS.map((u) => (
                <button
                  key={u.role}
                  type="button"
                  onClick={() => handleQuickLogin(u.email)}
                  className={`text-left p-2 rounded border text-xs transition-colors ${
                    email === u.email
                      ? 'bg-indigo-950/80 border-indigo-600 text-indigo-300'
                      : 'bg-slate-900/60 border-slate-700 text-slate-300 hover:border-slate-600'
                  }`}
                >
                  <div className="font-semibold text-slate-200">{u.role}</div>
                  <div className="text-[10px] text-slate-400 truncate">{u.email}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer info */}
        <p className="text-center text-xs text-slate-500 mt-6">
          OpsDesk Case 360 • Multi-Agency Operations Platform
        </p>
      </div>
    </div>
  );
};
