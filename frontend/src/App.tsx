import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardPage from '@/pages/DashboardPage';
import CreateKBPage from '@/pages/CreateKBPage';
import KBDetailPage from '@/pages/KBDetailPage';
import ProfilePage from '@/pages/ProfilePage';

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;
  return <>{children}</>;
}

function GuestGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (isAuthenticated) return null;
  return <>{children}</>;
}

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Auth Pages - Guest Only */}
        <Route path="/login" element={<GuestGuard><LoginPage /></GuestGuard>} />
        <Route path="/register" element={<GuestGuard><RegisterPage /></GuestGuard>} />

        {/* Protected Pages */}
        <Route path="/dashboard" element={<AuthGuard><DashboardPage /></AuthGuard>} />
        <Route path="/kb/create" element={<AuthGuard><CreateKBPage /></AuthGuard>} />
        <Route path="/kb/:id" element={<AuthGuard><KBDetailPage /></AuthGuard>} />
        <Route path="/profile" element={<AuthGuard><ProfilePage /></AuthGuard>} />

        {/* Default Redirect */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  );
}
