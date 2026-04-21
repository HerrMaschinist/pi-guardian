import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import GuardianDashboardView from '../src/components/GuardianDashboardView.vue';
import type { GuardianDashboardPayload } from '../src/types';

const mockedApi = vi.hoisted(() => ({
  fetchGuardianStatus: vi.fn(),
  fetchGuardianHistory: vi.fn(),
}));

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    fetchGuardianStatus: mockedApi.fetchGuardianStatus,
    fetchGuardianHistory: mockedApi.fetchGuardianHistory,
  };
});

const successPayload: GuardianDashboardPayload = {
  status: {
    status: 'warn',
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
      health: {
        status: 'ok',
        service: 'pi-guardian-router',
        version: '1.0.0',
      },
      service_status: {
        service: 'pi-guardian-router',
        active: true,
        uptime: '1h',
        pid: 1234,
        memory_usage: '128MB',
        cpu_percent: 12.5,
      },
      findings: [],
      notes: ['Router probe completed successfully.'],
      probe: {
        checked_at: '2026-04-21T18:30:00.000Z',
        status: 'ok',
        action: 'none',
        reachable: true,
        service_active: true,
        health: {
          status: 'ok',
          service: 'pi-guardian-router',
          version: '1.0.0',
        },
        service_status: {
          service: 'pi-guardian-router',
          active: true,
          uptime: '1h',
          pid: 1234,
          memory_usage: '128MB',
          cpu_percent: 12.5,
        },
        findings: [],
        errors: [],
        router_base_url: 'http://127.0.0.1:8071',
        health_path: '/health',
        status_path: '/status/service',
      },
    },
    router_evaluation: {
      status: 'ok',
      summary: 'Router is healthy.',
      checked_at: '2026-04-21T18:30:00.000Z',
      reasons: [
        {
          code: 'router_state_healthy',
          summary: 'Router health and readout are consistent.',
          severity: 'ok',
          source: 'router',
        },
      ],
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
        health: { status: 'ok' },
        service_status: { service: 'pi-guardian-router', active: true },
        findings: [],
        notes: ['Router probe completed successfully.'],
        probe: {
          reachable: true,
        },
      },
    },
    system: {
      checked_at: '2026-04-21T18:30:00.000Z',
      hostname: 'guardian-test',
      running_as_root: false,
      process_pid: 2222,
      process_name: 'guardian',
      process_uptime_seconds: 123.4,
      cpu_count: 4,
      cpu_usage_percent: 12.3,
      load_avg_1m: 0.25,
      load_avg_5m: 0.2,
      load_avg_15m: 0.15,
      cpu_load_ratio_1m: 0.06,
      memory_total_bytes: 4 * 1024 * 1024 * 1024,
      memory_available_bytes: 3 * 1024 * 1024 * 1024,
      memory_used_bytes: 1 * 1024 * 1024 * 1024,
      memory_usage_percent: 25,
      disk_mountpoint: '/',
      disk_total_bytes: 64 * 1024 * 1024 * 1024,
      disk_free_bytes: 48 * 1024 * 1024 * 1024,
      disk_used_bytes: 16 * 1024 * 1024 * 1024,
      disk_usage_percent: 25,
      temperature_c: 49.4,
      temperature_source: '/sys/class/thermal/thermal_zone0/temp',
      notes: ['Guardian is not running as root.'],
      errors: [],
    },
    system_evaluation: {
      status: 'warn',
      summary: 'Local system state needs attention.',
      checked_at: '2026-04-21T18:30:00.000Z',
      reasons: [
        {
          code: 'system_not_running_as_root',
          summary: 'Guardian is not running as root.',
          severity: 'warn',
          source: 'system',
        },
      ],
      system: {
        checked_at: '2026-04-21T18:30:00.000Z',
        hostname: 'guardian-test',
        running_as_root: false,
        process_pid: 2222,
        process_name: 'guardian',
        notes: ['Guardian is not running as root.'],
        errors: [],
      },
    },
    evaluation: {
      status: 'warn',
      summary: 'Guardian needs attention.',
      checked_at: '2026-04-21T18:30:00.000Z',
      reasons: [
        {
          code: 'system_warn',
          summary: 'System evaluation returned warn.',
          severity: 'warn',
          source: 'system',
        },
      ],
      router: {} as never,
      system: {} as never,
    },
    persistence: {
      ok: true,
      database_path: '/tmp/guardian.sqlite3',
      stored_at: '2026-04-21T18:30:00.000Z',
      snapshot_id: 7,
      transition_id: 3,
      changed: true,
      previous_status: 'ok',
      current_status: 'warn',
      error: null,
    },
    policy: {
      outcome: 'observe',
      relevance: 'warn',
      checked_at: '2026-04-21T18:30:00.000Z',
      summary: 'Warning observed and tracked.',
      reasons: [
        {
          code: 'policy_warning_observe',
          summary: 'Warning is observable but not yet escalated.',
          severity: 'warn',
          source: 'external',
        },
      ],
      visibility: {
        auth_limited: false,
        privilege_limited: true,
        data_limited: false,
        reduced_confidence: true,
        notes: ['guardian is not running as root'],
      },
      changed: true,
      transition_relevant: true,
      candidate_alert: true,
      candidate_action: false,
      deferred: false,
      confidence: 0.84,
      current_status: 'warn',
      previous_status: 'ok',
      snapshot_id: 7,
      transition_id: 3,
      persistence_ok: true,
      context: {
        current_status: 'warn',
      },
    },
    alerting: {
      outcome: 'suppress',
      alert_kind: 'visibility',
      should_send: false,
      sent: false,
      suppressed: true,
      summary: 'Visibility-limited warning suppressed: WARN via observe',
      reason_codes: ['policy_warning_observe'],
      alert_key: 'visibility|warn|observe',
      dedupe_key: 'dedupe-key',
      cooldown_seconds: 900,
      cooldown_remaining_seconds: null,
      policy_outcome: 'observe',
      current_status: 'warn',
      previous_status: 'ok',
      changed: true,
      transition_relevant: true,
      telegram_ready: false,
      telegram_ready_reason: 'telegram bot token and chat id are not configured',
      policy_visibility: {
        auth_limited: false,
        privilege_limited: true,
        data_limited: false,
        reduced_confidence: true,
        notes: ['guardian is not running as root'],
      },
      message_text: 'PI Guardian\nStatus: WARN',
      send_result: null,
      error: null,
      context: {
        snapshot_id: 7,
        transition_id: 3,
        persistence_ok: true,
      },
    },
  },
  history: {
    checked_at: '2026-04-21T18:31:00.000Z',
    limit: 8,
    snapshots: [
      {
        id: 7,
        checked_at: '2026-04-21T18:30:00.000Z',
        guardian_status: 'warn',
        router_status: 'ok',
        system_status: 'warn',
        overview_summary: 'Guardian needs attention.',
        router_summary: 'Router is healthy.',
        system_summary: 'Local system state needs attention.',
        overview_reason_codes: ['system_warn'],
        router_reason_codes: ['router_state_healthy'],
        system_reason_codes: ['system_not_running_as_root'],
        router_access_state: 'reachable',
        router_readiness_state: 'healthy',
        router_reachable: true,
        router_auth_required: false,
        system_running_as_root: false,
        system_cpu_usage_percent: 12.3,
        system_memory_usage_percent: 25,
        system_disk_usage_percent: 25,
        system_temperature_c: 49.4,
        evidence: {},
        stored_at: '2026-04-21T18:30:00.000Z',
      },
    ],
    transitions: [
      {
        id: 3,
        created_at: '2026-04-21T18:30:00.000Z',
        previous_snapshot_id: 6,
        current_snapshot_id: 7,
        from_status: 'ok',
        to_status: 'warn',
        reason_codes: ['system_warn'],
        summary: 'ok -> warn',
        evidence: {},
      },
    ],
    alerts: [
      {
        id: 11,
        checked_at: '2026-04-21T18:30:00.000Z',
        sent_at: null,
        alert_key: 'visibility|warn|observe',
        dedupe_key: 'dedupe-key',
        alert_kind: 'visibility',
        outcome: 'suppress',
        should_send: false,
        sent: false,
        suppressed_reason: 'visibility-limited state is suppressed',
        current_status: 'warn',
        previous_status: 'ok',
        policy_outcome: 'observe',
        changed: true,
        transition_relevant: true,
        cooldown_seconds: 900,
        cooldown_remaining_seconds: null,
        telegram_ready: false,
        telegram_ready_reason: 'telegram bot token and chat id are not configured',
        telegram_chat_id: null,
        telegram_message_id: null,
        telegram_error: null,
        reason_codes: ['policy_warning_observe'],
        summary: 'Visibility-limited warning suppressed: WARN via observe',
        message_text: 'PI Guardian\nStatus: WARN',
        evidence: {},
      },
    ],
  },
};

beforeEach(() => {
  mockedApi.fetchGuardianStatus.mockReset();
  mockedApi.fetchGuardianHistory.mockReset();
});

describe('GuardianDashboardView', () => {
  it('renders a healthy dashboard payload', async () => {
    mockedApi.fetchGuardianStatus.mockResolvedValue(successPayload.status);
    mockedApi.fetchGuardianHistory.mockResolvedValue(successPayload.history);

    const wrapper = mount(GuardianDashboardView, {
      props: {
        refreshIntervalMs: 0,
        historyLimit: 8,
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Guardian needs attention.');
    expect(wrapper.text()).toContain('Router');
    expect(wrapper.text()).toContain('System');
    expect(wrapper.text()).toContain('Policy');
    expect(wrapper.text()).toContain('Alerting');
    expect(wrapper.text()).toContain('Verlauf');
    expect(wrapper.text()).toContain('observe');
    expect(wrapper.text()).toContain('suppress');
    expect(wrapper.text()).toContain('guardian-test');

    wrapper.unmount();
  });

  it('renders API error state without crashing', async () => {
    mockedApi.fetchGuardianStatus.mockRejectedValue(new Error('Guardian backend not reachable'));
    mockedApi.fetchGuardianHistory.mockRejectedValue(new Error('History backend not reachable'));

    const wrapper = mount(GuardianDashboardView, {
      props: {
        refreshIntervalMs: 0,
        historyLimit: 8,
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Teilweise eingeschränkte Datenlage');
    expect(wrapper.text()).toContain('Guardian backend not reachable');
    expect(wrapper.text()).toContain('History backend not reachable');

    wrapper.unmount();
  });
});
