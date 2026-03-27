import type { ReactNode } from 'react';

interface Props {
  title: string;
  tag?: string;
  children: ReactNode;
  className?: string;
}

export function Card({ title, tag, children, className = '' }: Props) {
  return (
    <section className={`card ${className}`}>
      <div className="card__header">
        <h3 className="card__title">{title}</h3>
        {tag && <span className="card__tag">{tag}</span>}
      </div>
      <div className="card__body">{children}</div>
    </section>
  );
}
