import { useState } from 'react';

const POWERBI_URL =
  'https://app.powerbi.com/reportEmbed?reportId=a3b6aa0f-43e0-45a7-882f-82fdc64055b4&autoAuth=true&ctid=5047bca2-da88-442e-a09a-d9b8af692adc';

export function PowerBIPage() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  return (
    <div className="page-stack">
      {/* ─── Header ────────────────────────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <p className="page-kicker">Power BI · Business Intelligence</p>
          <h1>Contract Monitoring Dashboard</h1>
          <p>
            Live Power BI report — contract tracking, supplier performance, and
            procurement KPIs.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {/* Status badge */}
          <span className={`status-pill ${isLoaded && !hasError ? 'success' : hasError ? 'error' : 'warning'}`}>
            {isLoaded && !hasError ? 'Report loaded' : hasError ? 'Load error' : 'Loading…'}
          </span>

          {/* Open in Power BI button */}
          <a
            href="https://app.powerbi.com/groups/me/reports/a3b6aa0f-43e0-45a7-882f-82fdc64055b4"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '7px',
              fontSize: '13px',
              padding: '8px 16px',
              borderRadius: '10px',
              textDecoration: 'none',
            }}
          >
            {/* Power BI icon */}
            <svg
              width="15"
              height="15"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            Open in Power BI
          </a>
        </div>
      </div>

      {/* ─── Embed container ───────────────────────────────────────────────── */}
      <div
        className="section-card"
        style={{ padding: 0, overflow: 'hidden', position: 'relative' }}
      >
        {/* Loading skeleton */}
        {!isLoaded && !hasError && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '16px',
              background: 'var(--panel)',
              zIndex: 1,
            }}
          >
            {/* Animated bars */}
            <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-end', height: '40px' }}>
              {[0.5, 0.75, 1, 0.65, 0.85, 0.55, 0.9].map((h, i) => (
                <div
                  key={i}
                  style={{
                    width: '8px',
                    height: `${h * 40}px`,
                    borderRadius: '4px',
                    background: 'var(--blue)',
                    opacity: 0.4,
                    animation: `bar-pulse 1.4s ease-in-out ${i * 0.12}s infinite`,
                  }}
                />
              ))}
            </div>
            <style>{`
              @keyframes bar-pulse {
                0%, 100% { opacity: 0.2; transform: scaleY(0.8); }
                50%       { opacity: 0.7; transform: scaleY(1.1); }
              }
            `}</style>
            <p style={{ color: 'var(--muted)', fontSize: '14px' }}>
              Loading Power BI report…
            </p>
          </div>
        )}

        {/* Error state */}
        {hasError && (
          <div
            style={{
              padding: '48px 32px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '14px',
              textAlign: 'center',
            }}
          >
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--red)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <p style={{ color: 'var(--text)', fontWeight: 600 }}>Could not load the report</p>
            <p style={{ color: 'var(--muted)', fontSize: '13px', maxWidth: '380px' }}>
              The Power BI report may require a Microsoft 365 account with access to this
              workspace. Try opening it directly in Power BI.
            </p>
            <a
              href="https://app.powerbi.com/groups/me/reports/a3b6aa0f-43e0-45a7-882f-82fdc64055b4"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-primary"
              style={{ textDecoration: 'none', borderRadius: '10px', fontSize: '13px' }}
            >
              Open in Power BI ↗
            </a>
          </div>
        )}

        {/* The actual iframe */}
        <iframe
          title="Contract Monitoring Dashboard — Power BI"
          src={POWERBI_URL}
          frameBorder="0"
          allowFullScreen
          onLoad={() => setIsLoaded(true)}
          onError={() => { setIsLoaded(true); setHasError(true); }}
          style={{
            display: 'block',
            width: '100%',
            height: 'calc(100vh - 220px)',
            minHeight: '540px',
            border: 'none',
            opacity: isLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease',
          }}
        />
      </div>
    </div>
  );
}

export default PowerBIPage;
