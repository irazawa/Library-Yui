import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const HEALTH_URL = 'http://127.0.0.1:8787/health';

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
        {roadmap.map(([title, text]) => (
          <article key={title}>
            <strong>{title}</strong>
            <span>{text}</span>
          </article>
        ))}
      </section>
      <footer>Next small step: add a disabled URL input form shell to the main web app.</footer>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
