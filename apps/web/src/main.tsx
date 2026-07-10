import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE_URL = 'http://127.0.0.1:8787';
const LIBRARY_SUMMARY_URL = `${API_BASE_URL}/library/summary`;
const JOBS_URL = `${API_BASE_URL}/jobs`;
const JOB_POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES = new Set(['completed', 'failed']);

type SummaryState = 'loading' | 'ok' | 'error';
interface LibrarySummary {
  audio: number;
  video: number;
  uploads: number;
  thumbnails: number;
}

interface JobResponse {
  id: string;
  url: string;
  status: string;
}

/**
 * Poll `GET /jobs/{id}` on an interval until the job reaches a terminal
 * status (completed/failed) or polling is cleared. Returns the latest known
 * status string, or null when no job is being tracked.
 */
function useJobStatus(jobId: string | null) {
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [jobPollError, setJobPollError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (!jobId) {
      setJobStatus(null);
      setJobPollError(null);
      return;
    }
    let cancelled = false;
    setJobStatus('pending');
    setJobPollError(null);

    const poll = async () => {
      try {
        const res = await fetch(`${JOBS_URL}/${jobId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const job = (await res.json()) as JobResponse;
        if (cancelled) return;
        setJobStatus(job.status);
        if (TERMINAL_STATUSES.has(job.status) && timerRef.current !== null) {
          window.clearInterval(timerRef.current);
          timerRef.current = null;
        }
      } catch (err) {
        if (cancelled) return;
        setJobPollError(err instanceof Error ? err.message : 'Poll failed');
      }
    };
    poll();
    timerRef.current = window.setInterval(poll, JOB_POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      if (timerRef.current !== null) {
        window.clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [jobId]);

  return { jobStatus, jobPollError };
}

function useLibrarySummary() {
  const [state, setState] = useState<SummaryState>('loading');
  const [summary, setSummary] = useState<LibrarySummary | null>(null);

  useEffect(() => {
    let cancelled = false;
    setState('loading');
    fetch(LIBRARY_SUMMARY_URL)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as LibrarySummary;
        if (cancelled) return;
        setSummary(data);
        setState('ok');
      })
      .catch(() => {
        if (cancelled) return;
        setSummary(null);
        setState('error');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { state, summary };
}

function App() {
  const { state, summary } = useLibrarySummary();
  const [url, setUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const { jobStatus, jobPollError } = useJobStatus(jobId);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed || submitting) return;
    setSubmitting(true);
    setJobId(null);
    setJobError(null);
    try {
      const res = await fetch(JOBS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: trimmed }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const job = (await res.json()) as { id: string };
      setJobId(job.id);
    } catch (err) {
      setJobError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setSubmitting(false);
    }
  }

  const dash = state === 'loading' ? '…' : '—';
  const audio = state === 'ok' && summary ? String(summary.audio) : dash;
  const video = state === 'ok' && summary ? String(summary.video) : dash;
  const uploads = state === 'ok' && summary ? String(summary.uploads) : dash;
  const sub =
    state === 'ok'
      ? 'Live counts from the backend summary API.'
      : state === 'loading'
        ? 'Contacting the backend summary API…'
        : 'Backend unreachable — showing placeholders. Start the API on port 8787.';

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Library-Yui · MVP 0</p>
        <h1>Your personal music/video library starts here.</h1>
        <p>
          This shell will become the downloader, upload manager, and collection browser.
          MVP 1 will connect the YouTube URL form to the FastAPI download queue.
        </p>
        <form className="url-form" aria-label="Audio download URL form" onSubmit={handleSubmit}>
          <input
            type="url"
            className="url-input"
            placeholder="https://www.youtube.com/watch?v=..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
            aria-label="Video URL"
          />
          <button type="submit" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Download MP3'}
          </button>
        </form>
        {jobId && (
          <p className="job-note" role="status">
            Job created: <code>{jobId}</code> — status:{' '}
            <strong className="job-status">{jobStatus ?? 'pending'}</strong>
            {jobStatus && !TERMINAL_STATUSES.has(jobStatus) && '…'}
            {jobPollError && (
              <span className="job-status-error"> (status update failed: {jobPollError})</span>
            )}
          </p>
        )}
        {jobError && (
          <p className="job-note job-note-error" role="alert">
            Could not create job: {jobError}. Is the API running on port 8787?
          </p>
        )}
        <div className="actions">
          <button type="button" className="secondary">Upload coming soon</button>
        </div>
      </section>
      <section className="library" aria-label="Library summary">
        <header className="library-head">
          <h2>Library</h2>
          <p className="library-sub">{sub}</p>
        </header>
        <div className="library-counts">
          <article className="count-card">
            <span className="count-value">{audio}</span>
            <span className="count-label">Audio</span>
          </article>
          <article className="count-card">
            <span className="count-value">{video}</span>
            <span className="count-label">Video</span>
          </article>
          <article className="count-card">
            <span className="count-value">{uploads}</span>
            <span className="count-label">Uploads</span>
          </article>
        </div>
      </section>
      <section className="cards">
        <article><h2>Audio</h2><p>MP3 downloads will appear here.</p></article>
        <article><h2>Video</h2><p>MP4 library support is planned after audio.</p></article>
        <article><h2>Collections</h2><p>Anime, Hololive, OST, mood lists, and custom tags.</p></article>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
