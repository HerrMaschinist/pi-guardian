import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ensureRouterAdminSession } from './api/client';
import App from './App';
import './styles.css';

const root = createRoot(document.getElementById('root')!);

void ensureRouterAdminSession().finally(() => {
  root.render(
    <StrictMode>
      <App />
    </StrictMode>
  );
});
