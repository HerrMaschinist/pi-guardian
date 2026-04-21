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

- `VITE_GUARDIAN_API_PREFIX` - frontend API prefix, default `/api/guardian`
- `VITE_GUARDIAN_API_TARGET` - Vite dev-server proxy target, default `http://127.0.0.1:8000`
- `VITE_GUARDIAN_REFRESH_INTERVAL_MS` - auto-refresh interval, default `20000`
- `VITE_GUARDIAN_HISTORY_LIMIT` - number of history entries fetched per refresh, default `8`

The frontend talks to the Guardian backend through the configured prefix. In development Vite proxies that prefix to the configured target.

## Development

```bash
cd ui
npm install
npm run dev
```

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
- The dashboard is designed for a later reverse-proxy deployment as well as local development.
