import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  AlertOctagon,
  BarChart3,
  Download,
  Flame,
  Globe2,
  Inbox,
  Layers,
  Link2,
  LogOut,
  PlusCircle,
  Tag,
  UserCheck,
} from 'lucide-react';
import { useAuth } from '../store/auth';

export const Nav: React.FC = () => {
  const { user, logout, isRole } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isLead = isRole('lead');
  const isAgent = isRole('agent', 'lead');
  const isEM = isRole('escalation_manager', 'lead');

  return (
    <aside className="w-[240px] flex-shrink-0 bg-slate-800 border-r border-slate-700/80 flex flex-col h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-700/80 bg-slate-850">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-600/30">
          <Flame className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="text-base font-bold text-white tracking-wide">OpsDesk</span>
          <span className="block text-[10px] text-indigo-400 font-mono uppercase tracking-wider">
            Case 360
          </span>
        </div>
      </div>

      {/* Quick Action Button */}
      {isRole('requester', 'agent', 'lead') && <div className="p-3">
        <button
          type="button"
          onClick={() => navigate('/tickets/new')}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold shadow-sm transition-all hover:shadow-indigo-600/20"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Ticket</span>
        </button>
      </div>}

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-6">
        {/* Main Queues */}
        <div>
          <div className="px-2 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Queues
          </div>
          <div className="space-y-1">
            <NavLink
              to="/tickets"
              end
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                    : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                }`
              }
            >
              <Inbox className="w-4 h-4 text-slate-400" />
              <span>All Tickets</span>
            </NavLink>

            {isAgent && (
              <>
                <NavLink
                  to="/tickets?tab=triage"
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                        : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                    }`
                  }
                >
                  <Layers className="w-4 h-4 text-slate-400" />
                  <span>Triage Queue</span>
                </NavLink>

                <NavLink
                  to="/tickets?tab=my_queue"
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                        : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                    }`
                  }
                >
                  <UserCheck className="w-4 h-4 text-slate-400" />
                  <span>My Queue</span>
                </NavLink>

                <NavLink
                  to="/tickets?tab=by_region"
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                        : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                    }`
                  }
                >
                  <Globe2 className="w-4 h-4 text-slate-400" />
                  <span>By Region</span>
                </NavLink>

                <NavLink
                  to="/tickets?tab=by_intent"
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                        : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                    }`
                  }
                >
                  <Tag className="w-4 h-4 text-slate-400" />
                  <span>By Intent</span>
                </NavLink>

                <NavLink
                  to="/tickets?tab=linked"
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                        : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                    }`
                  }
                >
                  <Link2 className="w-4 h-4 text-slate-400" />
                  <span>Linked Cases</span>
                </NavLink>
              </>
            )}

            {isEM && (
              <NavLink
                to="/tickets?tab=escalation"
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-rose-950/60 text-rose-300 border border-rose-500/50'
                      : 'text-rose-300/80 hover:bg-rose-950/30 hover:text-rose-200'
                  }`
                }
              >
                <AlertOctagon className="w-4 h-4 text-rose-400" />
                <span>Escalation Queue</span>
              </NavLink>
            )}
          </div>
        </div>

        {/* Lead Tools */}
        {isLead && (
          <div>
            <div className="px-2 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Operations Lead
            </div>
            <div className="space-y-1">
              <NavLink
                to="/insights"
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                      : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                  }`
                }
              >
                <BarChart3 className="w-4 h-4 text-slate-400" />
                <span>Insights & Themes</span>
              </NavLink>

              <NavLink
                to="/export"
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                      : 'text-slate-300 hover:bg-slate-700/60 hover:text-white'
                  }`
                }
              >
                <Download className="w-4 h-4 text-slate-400" />
                <span>Data Export</span>
              </NavLink>
            </div>
          </div>
        )}
      </nav>

      {/* User Footer with Logout */}
      <div className="p-3 border-t border-slate-700/80 bg-slate-900/60">
        <div className="flex items-center justify-between mb-2">
          <div className="min-w-0 pr-2">
            <div className="text-xs font-semibold text-slate-200 truncate">
              {user?.full_name ?? 'Guest User'}
            </div>
            <div className="text-[11px] text-slate-400 truncate font-mono">
              {user?.email ?? ''}
            </div>
          </div>
          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase bg-slate-700 text-slate-300 border border-slate-600">
            {user?.role?.replace('_', ' ') ?? 'User'}
          </span>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 px-2.5 py-1.5 text-xs text-rose-300 hover:text-rose-200 bg-rose-950/40 hover:bg-rose-950/70 border border-rose-900/60 rounded transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
};
