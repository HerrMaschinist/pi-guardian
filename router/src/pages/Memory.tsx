import { useEffect } from 'react';
import { Card } from '../components/Card';
import { Layout } from '../components/Layout';
import {
  fetchMemoryRuns,
  fetchMemoryIncidents,
  fetchMemoryKnowledge,
  fetchMemoryFeedback,
} from '../api/client';
import { useApiCall } from '../hooks/useApi';
import type {
  MemoryRunSummary,
  MemoryIncidentRead,
  MemoryKnowledgeEntryRead,
  MemoryFeedbackEntryRead,
} from '../types';

function formatDate(value?: string | null): string {
  if (!value) return '–';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString('de-DE');
}

function RunTable({ runs }: { runs: MemoryRunSummary[] }) {
  if (runs.length === 0) {
    return <p className="text--muted">Noch keine gespeicherten Agentenläufe vorhanden.</p>;
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>Run</th>
          <th>Agent</th>
          <th>Modell</th>
          <th>Status</th>
          <th>Start</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <tr key={run.run_id}>
            <td><code>{run.run_id.slice(0, 8)}</code></td>
            <td>{run.agent_name}</td>
            <td>{run.used_model || '–'}</td>
            <td>{run.success ? 'Erfolgreich' : 'Fehler'}</td>
            <td>{formatDate(run.started_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function IncidentTable({ incidents }: { incidents: MemoryIncidentRead[] }) {
  if (incidents.length === 0) {
    return <p className="text--muted">Noch keine Incidents gespeichert.</p>;
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Titel</th>
          <th>Severity</th>
          <th>Status</th>
          <th>Findings</th>
        </tr>
      </thead>
      <tbody>
        {incidents.map((incident) => (
          <tr key={incident.id}>
            <td><code>{incident.id}</code></td>
            <td>{incident.title}</td>
            <td>{incident.severity}</td>
            <td>{incident.status}</td>
            <td>{incident.findings.length}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function KnowledgeTable({ entries }: { entries: MemoryKnowledgeEntryRead[] }) {
  if (entries.length === 0) {
    return <p className="text--muted">Noch keine Knowledge-Entries gespeichert.</p>;
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Titel</th>
          <th>Bestätigt</th>
          <th>Confidence</th>
          <th>Updated</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.id}>
            <td><code>{entry.id}</code></td>
            <td>{entry.title}</td>
            <td>{entry.confirmed ? 'Ja' : 'Nein'}</td>
            <td>{entry.confidence}</td>
            <td>{formatDate(entry.updated_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function FeedbackTable({ entries }: { entries: MemoryFeedbackEntryRead[] }) {
  if (entries.length === 0) {
    return <p className="text--muted">Noch kein Feedback gespeichert.</p>;
  }

  return (
    <table className="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Verdict</th>
          <th>Run</th>
          <th>Incident</th>
          <th>Created</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry) => (
          <tr key={entry.id}>
            <td><code>{entry.id}</code></td>
            <td>{entry.verdict}</td>
            <td>{entry.related_run_id || '–'}</td>
            <td>{entry.related_incident_id || '–'}</td>
            <td>{formatDate(entry.created_at)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function Memory() {
  const {
    data: runData,
    loading: runLoading,
    error: runError,
    execute: loadRuns,
  } = useApiCall<MemoryRunSummary[]>();
  const {
    data: incidentData,
    loading: incidentLoading,
    error: incidentError,
    execute: loadIncidents,
  } = useApiCall<MemoryIncidentRead[]>();
  const {
    data: knowledgeData,
    loading: knowledgeLoading,
    error: knowledgeError,
    execute: loadKnowledge,
  } = useApiCall<MemoryKnowledgeEntryRead[]>();
  const {
    data: feedbackData,
    loading: feedbackLoading,
    error: feedbackError,
    execute: loadFeedback,
  } = useApiCall<MemoryFeedbackEntryRead[]>();

  useEffect(() => {
    loadRuns(fetchMemoryRuns).catch(() => {});
    loadIncidents(fetchMemoryIncidents).catch(() => {});
    loadKnowledge(fetchMemoryKnowledge).catch(() => {});
    loadFeedback(fetchMemoryFeedback).catch(() => {});
  }, [loadRuns, loadIncidents, loadKnowledge, loadFeedback]);

  return (
    <Layout title="Memory & Knowledge">
      <div className="grid grid--2">
        <Card title="Agentenläufe" tag={runLoading ? 'LÄDT' : 'LIVE'}>
          {runError && <div className="alert alert--error">{runError}</div>}
          {!runError && <RunTable runs={runData || []} />}
        </Card>

        <Card title="Incidents" tag={incidentLoading ? 'LÄDT' : 'LIVE'}>
          {incidentError && <div className="alert alert--error">{incidentError}</div>}
          {!incidentError && <IncidentTable incidents={incidentData || []} />}
        </Card>
      </div>

      <div className="grid grid--2" style={{ marginTop: '1.5rem' }}>
        <Card title="Knowledge" tag={knowledgeLoading ? 'LÄDT' : 'LIVE'}>
          {knowledgeError && <div className="alert alert--error">{knowledgeError}</div>}
          {!knowledgeError && <KnowledgeTable entries={knowledgeData || []} />}
        </Card>

        <Card title="Feedback" tag={feedbackLoading ? 'LÄDT' : 'LIVE'}>
          {feedbackError && <div className="alert alert--error">{feedbackError}</div>}
          {!feedbackError && <FeedbackTable entries={feedbackData || []} />}
        </Card>
      </div>
    </Layout>
  );
}
