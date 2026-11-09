import React from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { QueuePage } from './pages/QueuePage';
import { CreateTicketPage } from './pages/CreateTicketPage';
import { TicketDetailPage } from './pages/TicketDetailPage';
import { InsightsPage } from './pages/InsightsPage';
import { ExportPage } from './pages/ExportPage';
import { ProtectedRoute } from './components/ProtectedRoute';

export const App: React.FC = () => {
  return (
    <Routes>
      {/* Public Route */}
      <Route path="/login" element={<LoginPage />} />

      {/* Root redirect */}
      <Route path="/" element={<Navigate to="/tickets" replace />} />

      {/* Protected Ticket Routes */}
      <Route
        path="/tickets"
        element={
          <ProtectedRoute>
            <QueuePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tickets/new"
        element={
          <ProtectedRoute allowedRoles={['requester', 'agent', 'lead']}>
            <CreateTicketPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tickets/:id"
        element={
          <ProtectedRoute>
            <TicketDetailPage />
          </ProtectedRoute>
        }
      />

      {/* Protected Lead Only Routes */}
      <Route
        path="/insights"
        element={
          <ProtectedRoute allowedRoles={['lead']}>
            <InsightsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/export"
        element={
          <ProtectedRoute allowedRoles={['lead']}>
            <ExportPage />
          </ProtectedRoute>
        }
      />

      {/* Catch-all route */}
      <Route path="*" element={<Navigate to="/tickets" replace />} />
    </Routes>
  );
};

export default App;
