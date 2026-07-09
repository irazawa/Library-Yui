import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const LIBRARY_SUMMARY_URL = 'http://127.0.0.1:8787/library/summary';

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
        <form className="url-form" aria-label="Audio download URL form (coming soon)" onSubmit={(e) => e.preventDefault()}>
          <input
            type="url"
            className="url-input"
            placeholder="https://www.youtube.com/watch?v=..."
            disabled
            aria-label="Video URL"
          />
          <button type="submit" disabled>Download MP3</button>
        </form>
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
