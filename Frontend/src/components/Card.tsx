import type { ReactNode } from "react";

export function Card({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <section className="card">
      {title ? <div className="cardTitle">{title}</div> : null}
      {children}
    </section>
  );
}
