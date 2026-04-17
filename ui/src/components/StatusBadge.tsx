import type { ConnectionState } from '../types';

const LABELS: Record<ConnectionState, string> = {
  connected: 'Verbunden',
  disconnected: 'Nicht erreichbar',
  checking: 'Prüfe…',
  error: 'Fehler',
};

const CLASSES: Record<ConnectionState, string> = {
  connected: 'badge badge--ok',
  disconnected: 'badge badge--fail',
  checking: 'badge badge--warn',
  error: 'badge badge--fail',
};

interface Props {
  state: ConnectionState;
  label?: string;
}

export function StatusBadge({ state, label }: Props) {
  return (
    <span className={CLASSES[state]}>
      <span className="badge__dot" />
      {label ?? LABELS[state]}
    </span>
  );
}
