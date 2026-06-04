import { useState, type FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { ApiError } from '@/services/apiClient';

type LocationState = {
  from?: { pathname?: string };
};

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('adminpass');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(username, password);
      const state = location.state as LocationState | null;
      navigate(state?.from?.pathname || '/dashboard', { replace: true });
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError('Unable to login. Please verify your credentials.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-panel">
        <div className="login-copy">
          <span className="status-pill success">Phase 4B</span>
          <h1>Enterprise P2P Intelligence Center</h1>
          <p>
            Monitor executive KPIs, investigate suppliers and transactions, and prepare the platform for future chatbot-guided analysis.
          </p>
          <ul className="login-features">
            <li>JWT authentication and route protection</li>
            <li>Executive dashboard with analytics</li>
            <li>Supplier and transaction investigation views</li>
          </ul>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <h2>Sign in</h2>
          <label>
            Username
            <input className="input" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          <label>
            Password
            <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
          </label>
          {error && <div className="form-error">{error}</div>}
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Login'}
          </button>
          <p className="login-hint">Default admin credentials are available in the backend seed data.</p>
        </form>
      </div>
    </div>
  );
}
