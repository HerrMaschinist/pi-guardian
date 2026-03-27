import type { Page, ConnectionState } from '../types';
import { StatusBadge } from './StatusBadge';
import { routerAddress, CONFIG } from '../config';

interface Props {
  current: Page;
  onNavigate: (page: Page) => void;
  connectionState: ConnectionState;
}

const NAV_ITEMS: { page: Page; label: string; icon: string }[] = [
  { page: 'dashboard', label: 'Übersicht', icon: '◉' },
  { page: 'models', label: 'Modelle', icon: '⬡' },
  { page: 'diagnostics', label: 'Diagnose', icon: '⚙' },
  { page: 'clients', label: 'Clients', icon: '⊞' },
  { page: 'settings', label: 'Einstellungen', icon: '☰' },
  { page: 'logs', label: 'Logs', icon: '▤' },
];

export function Sidebar({ current, onNavigate, connectionState }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__logo">π</div>
        <div className="sidebar__brand-text">
          <span className="sidebar__name">PI Guardian</span>
          <span className="sidebar__sub">Model Router</span>
        </div>
      </div>

      <div className="sidebar__status">
        <StatusBadge state={connectionState} />
      </div>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.page}
            className={`sidebar__link ${current === item.page ? 'sidebar__link--active' : ''}`}
            onClick={() => onNavigate(item.page)}
          >
            <span className="sidebar__icon">{item.icon}</span>
            <span className="sidebar__label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar__footer">
        <span className="sidebar__meta">{routerAddress()}</span>
        <span className="sidebar__meta">v{CONFIG.version}</span>
      </div>
    </aside>
  );
}
