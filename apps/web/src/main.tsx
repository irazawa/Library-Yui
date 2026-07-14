import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE_URL = 'http://127.0.0.1:8787';
const LIBRARY_SUMMARY_URL = `${API_BASE_URL}/library/summary`;
const LIBRARY_AUDIO_URL = `${API_BASE_URL}/library/audio`;
const JOBS_URL = `${API_BASE_URL}/jobs`;
const UPLOAD_URL = `${API_BASE_URL}/library/upload`;
const UPLOADS_URL = `${API_BASE_URL}/library/uploads`;
const JOB_POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES = new Set(['completed', 'failed']);

type SummaryState = 'loading' | 'ok' | 'error';
interface LibrarySummary {
  audio: number;
  video: number;
  uploads: number;
  thumbnails: number;
}

interface AudioItem {
  name: string;
}

interface AudioListResponse {
  items: AudioItem[];
}

interface JobResponse {
  id: string;
  url: string;
  status: string;
}

interface UploadItem {
  id: number;
  filename: string;
  path: string;
  size: number;
  content_type: string | null;
  uploaded_at: string;
}

interface UploadListResponse {
  items: UploadItem[];
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

/**
 * Fetch the list of MP3 files in the audio library via `GET /library/audio`.
 * Returns the list of audio items plus a loading flag.
 */
function useLibraryAudio() {
  const [items, setItems] = useState<AudioItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(LIBRARY_AUDIO_URL)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as AudioListResponse;
        if (cancelled) return;
        setItems(data.items);
      })
      .catch(() => {
        if (cancelled) return;
        setItems([]);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { items, loading };
}

/**
 * Fetch the list of uploaded files via `GET /library/uploads`.
 * Pass a changing `refreshKey` (e.g. a counter bumped after a successful
 * upload) to force a re-fetch. Returns the list plus a loading flag.
 */
function useLibraryUploads(refreshKey: number) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(UPLOADS_URL)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as UploadListResponse;
        if (cancelled) return;
        setItems(data.items);
      })
      .catch(() => {
        if (cancelled) return;
        setItems([]);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return { items, loading };
}

function App() {
  const { state, summary } = useLibrarySummary();
  const { items: audioItems, loading: audioLoading } = useLibraryAudio();
  const [url, setUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const { jobStatus, jobPollError } = useJobStatus(jobId);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadNote, setUploadNote] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadsRefreshKey, setUploadsRefreshKey] = useState(0);
  const { items: uploadItems, loading: uploadsLoading } = useLibraryUploads(uploadsRefreshKey);

  async function handleFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || uploading) return;
    setUploading(true);
    setUploadNote(null);
    setUploadError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(UPLOAD_URL, { method: 'POST', body: form });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const saved = (await res.json()) as { filename: string };
      setUploadNote(`Uploaded: ${saved.filename}`);
      setUploadsRefreshKey((k) => k + 1);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
      // Allow re-selecting the same file to trigger onChange again.
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

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

  const formatBytes = (bytes: number) => {
    if (!Number.isFinite(bytes) || bytes < 0) return '—';
    if (bytes < 1024) return `${bytes} B`;
    const units = ['KB', 'MB', 'GB'];
    let value = bytes / 1024;
    let unit = 0;
    while (value >= 1024 && unit < units.length - 1) {
      value /= 1024;
      unit += 1;
    }
    return `${value.toFixed(value >= 100 ? 0 : 1)} ${units[unit]}`;
  };

  const formatUploadedAt = (iso: string) => {
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      return d.toLocaleString();
    } catch {
      return iso;
    }
  };

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
          <input
            ref={fileInputRef}
            type="file"
            className="upload-input"
            onChange={handleFileSelected}
            aria-label="Upload a file to the library"
            style={{ display: 'none' }}
          />
          <button
            type="button"
            className="secondary"
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
          >
            {uploading ? 'Uploading…' : 'Upload a file'}
          </button>
        </div>
        {uploadNote && (
          <p className="job-note" role="status">
            {uploadNote}
          </p>
        )}
        {uploadError && (
          <p className="job-note job-note-error" role="alert">
            Upload failed: {uploadError}. Is the API running on port 8787?
          </p>
        )}
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
        <article>
          <h2>Audio</h2>
          {audioLoading ? (
            <p>Loading audio library…</p>
          ) : audioItems.length === 0 ? (
            <p>MP3 downloads will appear here.</p>
          ) : (
            <ul className="audio-list">
              {audioItems.map((item) => (
                <li key={item.name} className="audio-item">
                  {item.name}
                </li>
              ))}
            </ul>
          )}
        </article>
        <article><h2>Video</h2><p>MP4 library support is planned after audio.</p></article>
        <article>
          <h2>Uploads</h2>
          {uploadsLoading ? (
            <p>Loading uploads…</p>
          ) : uploadItems.length === 0 ? (
            <p>Uploaded files will appear here.</p>
          ) : (
            <ul className="audio-list">
              {uploadItems.map((item) => (
                <li key={item.id} className="upload-item">
                  <span className="upload-name">{item.filename}</span>
                  <span className="upload-meta">
                    {formatBytes(item.size)}
                    {item.content_type ? ` · ${item.content_type}` : ''}
                    {' · '}
                    {formatUploadedAt(item.uploaded_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </article>
        <article><h2>Collections</h2><p>Anime, Hololive, OST, mood lists, and custom tags.</p></article>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
