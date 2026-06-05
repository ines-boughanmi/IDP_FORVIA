import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/dashboard',    label: 'Executive Dashboard' },
  { to: '/alerts',       label: 'Alert Center' },
  { to: '/suppliers',    label: 'Supplier Intelligence' },
  { to: '/transactions', label: 'Transaction Investigation' },
  { to: '/analytics',    label: 'Analytics Center' },
  { to: '/chatbot',      label: 'AI Risk Assistant' },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <div className="brand-mark">SP</div>
        <div>
          <p className="brand-eyebrow">SAP / Forvia</p>
          <h1 className="brand-title">P2P Intelligence</h1>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
          >
            {item.label}
          </NavLink>
        ))}

        {/* ── Power BI dashboard button ────────────────────────────── */}
        <div style={{ padding: '8px 0 4px', borderTop: '1px solid var(--border)', marginTop: '8px' }}>
          <NavLink
            to="/powerbi"
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: isActive
                ? 'rgba(33,198,100,0.15)'
                : 'rgba(33,198,100,0.07)',
              border: `1px solid ${isActive ? 'rgba(33,198,100,0.45)' : 'rgba(33,198,100,0.2)'}`,
              borderRadius: '10px',
              color: '#21c664',
              fontWeight: 600,
              padding: '9px 14px',
              marginTop: '2px',
              transition: 'background 0.15s, border-color 0.15s',
            })}
          >
            {/* Power BI bar-chart icon */}
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ flexShrink: 0 }}
            >
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6"  y1="20" x2="6"  y2="14" />
            </svg>
            Power BI Dashboard
          </NavLink>
        </div>
      </nav>

      <div className="sidebar-footer">
        <span className="status-pill success">Backend connected</span>
        <p>Phase 4B frontend prepared for future chatbot integration.</p>
      </div>
    </aside>
  );
}
