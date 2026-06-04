import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

export function Topbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  return (
    <header className="topbar">
      <div>
        <p className="topbar-kicker">Enterprise Business API Layer</p>
        <h2 className="topbar-title">Executive monitoring and investigation suite</h2>
      </div>

      <div className="topbar-actions">
        <div className="user-badge">
          <span className="user-name">{user?.username || 'Unknown user'}</span>
          <span className="user-role">{user?.role || 'user'}</span>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            logout();
            navigate('/login');
          }}
        >
          Logout
        </button>
      </div>
    </header>
  );
}
