import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../store/auth';
import type { Role } from '../api/types';
import { LoadingSpinner } from './LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactElement;
  allowedRoles?: Role[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
}) => {
  const { user, token, isLoading, isRole } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-900">
        <LoadingSpinner message="Authenticating session..." />
      </div>
    );
  }

  // Check token
  if (!token && !localStorage.getItem('opsdesk_token')) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check roles if specified
  if (allowedRoles && allowedRoles.length > 0 && user) {
    if (!isRole(...allowedRoles)) {
      return <Navigate to="/tickets" replace />;
    }
  }

  return children;
};
