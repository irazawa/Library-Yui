import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE_URL = 'http://127.0.0.1:8787';
const LIBRARY_SUMMARY_URL = `${API_BASE_URL}/library/summary`;
const JOBS_URL = `${API_BASE_URL}/jobs`;

type SummaryState = 'loading' | 'ok' | 'error';
interface LibrarySummary {
  audio: number;
  video: number;
  uploads: number;
  thumbnails: number;
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
            Job created: <code>{jobId}</code> (pending)
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
