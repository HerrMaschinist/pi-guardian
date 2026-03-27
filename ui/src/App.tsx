import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Models } from './pages/Models';
import { Diagnostics } from './pages/Diagnostics';
import { Clients } from './pages/Clients';
import { Settings } from './pages/Settings';
import { Logs } from './pages/Logs';
import { useHealthCheck } from './hooks/useApi';
import type { Page } from './types';

export default function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const health = useHealthCheck(15_000);

  function renderPage() {
    switch (page) {
      case 'dashboard':
        return (
          <Dashboard
            connectionState={health.state}
            lastCheck={health.lastCheck}
            healthError={health.error}
            onRefresh={health.refresh}
          />
        );
      case 'models':
        return <Models />;
      case 'diagnostics':
        return (
          <Diagnostics
            connectionState={health.state}
            onRefresh={health.refresh}
          />
        );
      case 'clients':
        return <Clients />;
      case 'settings':
        return <Settings />;
      case 'logs':
        return <Logs />;
      default:
        return <Dashboard connectionState={health.state} lastCheck={health.lastCheck} healthError={health.error} onRefresh={health.refresh} />;
    }
  }

  return (
    <div className="app">
      <Sidebar
        current={page}
        onNavigate={setPage}
        connectionState={health.state}
      />
      {renderPage()}
    </div>
  );
}
