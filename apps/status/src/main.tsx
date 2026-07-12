import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const HEALTH_URL = 'http://127.0.0.1:8787/health';
const JOBS_URL = 'http://127.0.0.1:8787/jobs';
const GITHUB_URL = 'https://github.com/irazawa/Library-Yui';

type JobStatus = 'pending' | 'downloading' | 'completed' | 'failed';
interface JobItem {
  id: string;
  url: string;
  status: JobStatus;
}

function countByStatus(items: JobItem[]): Record<JobStatus, number> {
  const base: Record<JobStatus, number> = {
    pending: 0,
    downloading: 0,
    completed: 0,
    failed: 0,
  };
  for (const item of items) {
    if (item.status in base) base[item.status] += 1;
  }
  return base;
}

function useJobs(intervalMs = 5000) {
  const [items, setItems] = useState<JobItem[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const res = await fetch(JOBS_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json().catch(() => ({}));
        if (cancelled) return;
        const next = Array.isArray(data?.items) ? (data.items as JobItem[]) : [];
        setItems(next);
        setError('');
      } catch (err) {
        if (cancelled) return;
        const msg = err instanceof Error ? err.message : 'unreachable';
        setError(msg);
      }
    }

    poll();
    const timer = window.setInterval(poll, intervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [intervalMs]);

  return { items, error };
}

function JobsCard() {
  const { items, error } = useJobs();
  const counts = countByStatus(items);
  const total = items.length;
  const active = counts.pending + counts.downloading;

  return (
    <article className="jobs-card">
      <strong>Jobs</strong>
      {error ? (
        <span className="jobs-error">Failed to load: {error}</span>
      ) : (
        <>
          <span className="jobs-total">
            {total} total · {active} active
          </span>
          <ul className="jobs-breakdown">
            <li><span className="jobs-dot" data-status="pending" /> Pending: {counts.pending}</li>
            <li><span className="jobs-dot" data-status="downloading" /> Downloading: {counts.downloading}</li>
            <li><span className="jobs-dot" data-status="completed" /> Completed: {counts.completed}</li>
            <li><span className="jobs-dot" data-status="failed" /> Failed: {counts.failed}</li>
          </ul>
        </>
      )}
    </article>
  );
}

const roadmap = [
  ['MVP 0', 'Scaffold repo, API, web shell, status dashboard'],
  ['MVP 1', 'Audio download jobs and library list'],
  ['MVP 2', 'User uploads and metadata'],
  ['MVP 3', 'Collections, tags, and search'],
];

type HealthState = 'loading' | 'ok' | 'down';

function useApiHealth() {
  const [state, setState] = useState<HealthState>('loading');
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    let cancelled = false;
    setState('loading');
    fetch(HEALTH_URL)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json().catch(() => ({}));
        if (cancelled) return;
        setState('ok');
        setMessage(typeof data?.status === 'string' ? data.status : 'healthy');
      })
      .catch((err) => {
        if (cancelled) return;
        setState('down');
        setMessage(err?.message ? String(err.message) : 'unreachable');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { state, message };
}

function HealthCard() {
  const { state, message } = useApiHealth();
  const label =
    state === 'loading' ? 'Checking…' : state === 'ok' ? 'Online' : 'Offline';
  return (
    <article className={`health health-${state}`}>
      <strong>API Health</strong>
      <span className="health-dot" data-state={state} />
      <span>{label}</span>
      {message ? <span className="health-msg">{message}</span> : null}
      <a
        className="health-url"
        href={HEALTH_URL}
        target="_blank"
        rel="noreferrer"
      >
        {HEALTH_URL}
      </a>
    </article>
  );
}

function GithubCard() {
  return (
    <a className="github-card" href={GITHUB_URL} target="_blank" rel="noreferrer">
      <strong>GitHub Repository</strong>
      <span className="github-repo">irazawa/Library-Yui</span>
      <span className="github-cta">View source →</span>
    </a>
  );
}

function App() {
  return (
    <main className="dashboard">
      <header>
        <p className="eyebrow">Progress Dashboard · Port 5175</p>
        <h1>Library-Yui Build Status</h1>
        <p>Slow, real progress tracker for the personal media library project.</p>
      </header>
      <section className="grid">
        <HealthCard />
        <JobsCard />
        <GithubCard />
        {roadmap.map(([title, text]) => (
          <article key={title}>
            <strong>{title}</strong>
            <span>{text}</span>
          </article>
        ))}
      </section>
      <footer>Next small step: port core MP3 download logic from the legacy Downloader.py into an app/downloader.py module behind a feature flag.</footer>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
