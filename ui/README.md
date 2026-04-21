# PI Guardian UI

Read-only Vue 3 dashboard for the Guardian control layer.

## What this UI shows

- Guardian overall status
- Router state
- Local system state
- Policy decision
- Alerting decision
- Recent snapshots, transitions, and alerts

The UI is intentionally read-only. It does not send commands, trigger recovery, or change router state.

## Configuration

The app reads these environment variables from `ui/.env`:

- `VITE_GUARDIAN_API_PREFIX` - frontend API base path used by the browser, default `/api/guardian`
- `VITE_GUARDIAN_API_TARGET` - Vite dev-server proxy target, default `http://127.0.0.1:8010`
- `VITE_GUARDIAN_REFRESH_INTERVAL_MS` - auto-refresh interval, default `20000`
- `VITE_GUARDIAN_HISTORY_LIMIT` - number of history entries fetched per refresh, default `8`

The frontend talks to the Guardian backend through the configured base path. In development Vite proxies that prefix to the configured target.
The default local target is `http://127.0.0.1:8010` so the UI does not collide with the unrelated `8000` service that is present in this environment.

## Development

```bash
cd ui
npm install
npm run dev
```

The Vite dev server listens on `http://127.0.0.1:5173` by default.

## Build

```bash
cd ui
npm run build
```

## Tests

```bash
cd ui
npm run test
```

## Notes

- The UI expects the Guardian FastAPI backend to expose `GET /health` and `GET /history`.
- The Vite dev proxy maps `/api/guardian/*` to the backend root, so `GET /api/guardian/health` becomes `GET /health` on the FastAPI app.
- The dashboard is designed for a later reverse-proxy deployment as well as local development.
