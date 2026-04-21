import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  buildGuardianApiUrl,
  fetchGuardianHistory,
  fetchGuardianStatus,
} from '../src/api/client';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('guardian api client', () => {
  it('joins the proxy prefix exactly once for health requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          status: 'ok',
          component: 'guardian',
          version: '0.1.0',
          checked_at: '2026-04-21T18:30:00.000Z',
          router: {
            checked_at: '2026-04-21T18:30:00.000Z',
            base_url: 'http://127.0.0.1:8071',
            health_path: '/health',
            status_path: '/status/service',
            access_state: 'reachable',
            readiness_state: 'healthy',
            severity: 'ok',
            healthy: true,
            degraded: false,
            incomplete: false,
            auth_required: false,
            reachable: true,
            health: null,
            service_status: null,
            findings: [],
            notes: [],
            probe: {
              router_base_url: 'http://127.0.0.1:8071',
            },
          },
          router_evaluation: {
            status: 'ok',
            summary: 'Router is healthy.',
            checked_at: '2026-04-21T18:30:00.000Z',
            reasons: [],
            router: {
              checked_at: '2026-04-21T18:30:00.000Z',
              base_url: 'http://127.0.0.1:8071',
              health_path: '/health',
              status_path: '/status/service',
              access_state: 'reachable',
              readiness_state: 'healthy',
              severity: 'ok',
              healthy: true,
              degraded: false,
              incomplete: false,
              auth_required: false,
              reachable: true,
              health: null,
              service_status: null,
              findings: [],
              notes: [],
              probe: {
                router_base_url: 'http://127.0.0.1:8071',
              },
            },
          },
          system: {
            checked_at: '2026-04-21T18:30:00.000Z',
            hostname: 'guardian-test',
            running_as_root: true,
            process_pid: 1234,
            process_name: 'guardian',
            notes: [],
            errors: [],
          },
          system_evaluation: {
            status: 'ok',
            summary: 'System is healthy.',
            checked_at: '2026-04-21T18:30:00.000Z',
            reasons: [],
            system: {
              checked_at: '2026-04-21T18:30:00.000Z',
              hostname: 'guardian-test',
              running_as_root: true,
              process_pid: 1234,
              process_name: 'guardian',
              notes: [],
              errors: [],
            },
          },
          evaluation: {
            status: 'ok',
            summary: 'Guardian is healthy.',
            checked_at: '2026-04-21T18:30:00.000Z',
            reasons: [],
            router: {},
            system: {},
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    vi.stubGlobal('fetch', fetchMock);

    await fetchGuardianStatus('/api/guardian');

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/guardian/health',
      expect.objectContaining({
        credentials: 'include',
      }),
    );
  });

  it('builds history urls without duplicating the prefix', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          checked_at: '2026-04-21T18:30:00.000Z',
          limit: 8,
          snapshots: [],
          transitions: [],
          alerts: [],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );

    vi.stubGlobal('fetch', fetchMock);

    await fetchGuardianHistory(8, '/api/guardian');

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/guardian/history?limit=8',
      expect.objectContaining({
        credentials: 'include',
      }),
    );
    expect(buildGuardianApiUrl('/api/guardian', '/health')).toBe('/api/guardian/health');
  });
});
