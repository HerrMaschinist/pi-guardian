import type { ReactNode } from 'react';

interface Props {
  title: string;
  children: ReactNode;
}

export function Layout({ title, children }: Props) {
  return (
    <main className="layout">
      <header className="layout__header">
        <h1 className="layout__title">{title}</h1>
        <span className="layout__time">{new Date().toLocaleDateString('de-DE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</span>
      </header>
      <div className="layout__content">{children}</div>
    </main>
  );
}
