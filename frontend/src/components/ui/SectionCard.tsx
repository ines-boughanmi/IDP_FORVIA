import type { ReactNode } from 'react';

export function SectionCard({ title, description, children }: { title?: string; description?: string; children: ReactNode }) {
  return (
    <section className="section-card">
      {(title || description) && (
        <div className="section-header">
          <div>
            {title && <h3>{title}</h3>}
            {description && <p>{description}</p>}
          </div>
        </div>
      )}
      {children}
    </section>
  );
}
