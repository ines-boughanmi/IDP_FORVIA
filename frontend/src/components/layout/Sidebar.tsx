import { NavLink } from 'react-router-dom';

const items = [
  { to: '/dashboard', label: 'Executive Dashboard' },
  { to: '/alerts', label: 'Alert Center' },
  { to: '/suppliers', label: 'Supplier Intelligence' },
  { to: '/transactions', label: 'Transaction Investigation' },
  { to: '/analytics', label: 'Analytics Center' },
  { to: '/chatbot', label: 'AI Risk Assistant' },
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
        {items.map((item) => (
          <NavLink key={item.to} to={item.to} className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="status-pill success">Backend connected</span>
        <p>Phase 4B frontend prepared for future chatbot integration.</p>
      </div>
    </aside>
  );
}
