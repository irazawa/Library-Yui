import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE_URL = 'http://127.0.0.1:8787';
const LIBRARY_SUMMARY_URL = `${API_BASE_URL}/library/summary`;
const LIBRARY_AUDIO_URL = `${API_BASE_URL}/library/audio`;
const LIBRARY_VIDEO_URL = `${API_BASE_URL}/library/video`;
const LIBRARY_THUMBNAILS_URL = `${API_BASE_URL}/library/thumbnails`;
const JOBS_URL = `${API_BASE_URL}/jobs`;
const UPLOAD_URL = `${API_BASE_URL}/library/upload`;
const UPLOADS_URL = `${API_BASE_URL}/library/uploads`;
const LIBRARY_TAGS_URL = `${API_BASE_URL}/library/tags`;
const COLLECTIONS_URL = `${API_BASE_URL}/collections`;
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

interface VideoItem {
  name: string;
}

interface VideoListResponse {
  items: VideoItem[];
}

/** Build the per-file streaming URL for a video item name. */
function videoUrlFor(name: string): string {
  return `${LIBRARY_VIDEO_URL}/${encodeURIComponent(name)}`;
}

/** Build the per-file streaming URL for an audio item name. */
function audioUrlFor(name: string): string {
  return `${LIBRARY_AUDIO_URL}/${encodeURIComponent(name)}`;
}

/**
 * Build the best-effort thumbnail URL for a video item name.
 *
 * The backend stores thumbnails as `<video-stem>.jpg` in
 * `library/thumbnails/`, so we drop the video's file extension and append
 * `.jpg`. The returned URL is used directly in an `<img onError>` handler —
 * a 404 (no thumbnail yet, or ffmpeg disabled) simply falls back to the
 * placeholder and never surfaces an error to the user.
 */
function thumbnailUrlFor(videoName: string): string {
  const stem = videoName.replace(/\.[^./\\]+$/, '');
  return `${LIBRARY_THUMBNAILS_URL}/${encodeURIComponent(stem)}.jpg`;
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
  total: number;
}

interface CollectionItem {
  id: number;
  name: string;
}

interface CollectionListResponse {
  items: CollectionItem[];
}

interface CollectionItemsResponse {
  collection: CollectionItem;
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
 * Accepts optional `query` parameter to filter by filename substring (`?q=`).
 */
function useLibraryAudio(refreshKey: number = 0, query: string = '') {
  const [items, setItems] = useState<AudioItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const q = query.trim();
    const url = q !== '' ? `${LIBRARY_AUDIO_URL}?q=${encodeURIComponent(q)}` : LIBRARY_AUDIO_URL;
    fetch(url)
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
  }, [refreshKey, query]);

  return { items, loading };
}

/**
 * Fetch the list of MP4 files in the video library via `GET /library/video`.
 * Returns the list of video items plus a loading flag.
 * Accepts optional `query` parameter to filter by filename substring (`?q=`).
 */
function useLibraryVideo(refreshKey: number = 0, query: string = '') {
  const [items, setItems] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const q = query.trim();
    const url = q !== '' ? `${LIBRARY_VIDEO_URL}?q=${encodeURIComponent(q)}` : LIBRARY_VIDEO_URL;
    fetch(url)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as VideoListResponse;
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
  }, [refreshKey, query]);

  return { items, loading };
}

/**
 * Fetch the list of uploaded files via `GET /library/uploads`.
 * Pass a changing `refreshKey` (e.g. a counter bumped after a successful
 * upload) to force a re-fetch. Returns the list plus a loading flag.
 *
 * Supports incremental pagination: when `limit` is set, only `limit` items
 * per page are fetched; calling `loadMore()` advances `offset` by `limit`
 * and appends the next page. `hasMore` is true when the server reports a
 * `total` larger than the items currently held. When `limit` is null the
 * full list is fetched in one shot (legacy behaviour).
 */
const UPLOADS_PAGE_SIZE = 10;

/**
 * Fetch all tag names once on mount via `GET /library/tags`.
 * Best-effort: any failure yields an empty list (the dropdown simply
 * offers no tags to filter by).
 */
function useLibraryTags() {
  const [tags, setTags] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetch(LIBRARY_TAGS_URL)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as { tags: string[] };
        if (cancelled) return;
        setTags(Array.isArray(data?.tags) ? data.tags : []);
      })
      .catch(() => {
        if (cancelled) return;
        setTags([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return tags;
}

/**
 * Fetch the list of collections via `GET /collections` on mount and
 * whenever `refreshKey` changes (bumped after a successful create).
 * Best-effort: any failure yields an empty list (the card shows its
 * empty-state text instead of an error). Returns the items plus a
 * loading flag.
 */
function useCollections(refreshKey: number = 0) {
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(COLLECTIONS_URL)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as CollectionListResponse;
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

/**
 * Fetch the items inside a collection via `GET /collections/{name}/items`.
 * Active only when `name` is non-null. Returns items, loading, and error states.
 */
function useCollectionItems(name: string | null, refreshKey: number = 0) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!name) {
      setItems([]);
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(`${COLLECTIONS_URL}/${encodeURIComponent(name)}/items`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as CollectionItemsResponse;
        if (cancelled) return;
        setItems(data.items);
      })
      .catch((err) => {
        if (cancelled) return;
        setItems([]);
        setError(err instanceof Error ? err.message : 'Failed to load items');
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [name, refreshKey]);

  return { items, loading, error };
}

interface CollectionRowProps {
  collection: CollectionItem;
  isExpanded: boolean;
  onToggle: () => void;
  formatBytes: (bytes: number) => string;
  onDeleteCollection: (name: string) => void;
  onRenameCollection: (oldName: string, newName: string) => void;
  onError?: (msg: string) => void;
}

function CollectionRow({
  collection,
  isExpanded,
  onToggle,
  formatBytes,
  onDeleteCollection,
  onRenameCollection,
  onError,
}: CollectionRowProps) {
  const [itemsRefreshKey, setItemsRefreshKey] = useState(0);
  const { items, loading, error } = useCollectionItems(
    isExpanded ? collection.name : null,
    itemsRefreshKey,
  );
  const [removingId, setRemovingId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [renameValue, setRenameValue] = useState(collection.name);
  const [renaming, setRenaming] = useState(false);

  async function handleRenameCollection() {
    const newName = renameValue.trim();
    if (!newName || newName === collection.name || renaming) return;
    setRenaming(true);
    try {
      const res = await fetch(
        `${COLLECTIONS_URL}/${encodeURIComponent(collection.name)}/rename`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ new_name: newName }),
        },
      );
      if (!res.ok) {
        if (res.status === 409) throw new Error('A collection with that name already exists');
        throw new Error(`HTTP ${res.status}`);
      }
      const updated = (await res.json()) as CollectionItem;
      setIsEditing(false);
      onRenameCollection(collection.name, updated.name);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Rename collection failed';
      onError?.(msg);
    } finally {
      setRenaming(false);
    }
  }

  async function handleDeleteCollection() {
    if (deleting) return;
    setDeleting(true);
    try {
      const res = await fetch(`${COLLECTIONS_URL}/${encodeURIComponent(collection.name)}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      onDeleteCollection(collection.name);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Delete collection failed';
      onError?.(msg);
    } finally {
      setDeleting(false);
    }
  }

  async function handleRemoveItem(metadataId: number) {
    if (removingId !== null) return;
    setRemovingId(metadataId);
    try {
      const res = await fetch(
        `${COLLECTIONS_URL}/${encodeURIComponent(collection.name)}/items/${metadataId}`,
        { method: 'DELETE' },
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setItemsRefreshKey((k) => k + 1);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Remove item failed';
      onError?.(msg);
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <li className={`collection-item ${isExpanded ? 'collection-item-expanded' : ''}`}>
      <div
        className="collection-item-header"
        onClick={onToggle}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle();
          }
        }}
      >
        <button
          type="button"
          className="collection-toggle"
          aria-label={isExpanded ? `Collapse collection ${collection.name}` : `Expand collection ${collection.name}`}
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
        >
          {isExpanded ? '▼' : '▶'}
        </button>
        {isEditing ? (
          <form
            className="collection-rename-form"
            onSubmit={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleRenameCollection();
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <input
              type="text"
              className="collection-rename-input"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              disabled={renaming}
              autoFocus
              aria-label={`Rename collection ${collection.name}`}
            />
            <button
              type="submit"
              className="collection-rename-save"
              disabled={renaming || renameValue.trim() === '' || renameValue.trim() === collection.name}
            >
              {renaming ? '…' : 'Save'}
            </button>
            <button
              type="button"
              className="collection-rename-cancel"
              disabled={renaming}
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(false);
                setRenameValue(collection.name);
              }}
            >
              Cancel
            </button>
          </form>
        ) : (
          <>
            <span className="collection-name">{collection.name}</span>
            <button
              type="button"
              className="collection-rename-btn"
              aria-label={`Rename collection ${collection.name}`}
              onClick={(e) => {
                e.stopPropagation();
                setIsEditing(true);
                setRenameValue(collection.name);
              }}
            >
              ✎
            </button>
            <button
              type="button"
              className="collection-delete"
              disabled={deleting}
              aria-label={`Delete collection ${collection.name}`}
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteCollection();
              }}
            >
              ✕
            </button>
          </>
        )}
      </div>
      {isExpanded && (
        <div className="collection-items-container">
          {loading ? (
            <p className="collection-items-note">Loading items…</p>
          ) : error ? (
            <p className="collection-items-note collection-items-error">{error}</p>
          ) : items.length === 0 ? (
            <p className="collection-items-note">No items in this collection.</p>
          ) : (
            <ul className="collection-sub-list">
              {items.map((item) => (
                <li key={item.id} className="collection-sub-item">
                  <span className="collection-sub-item-name">{item.filename}</span>
                  <span className="collection-sub-item-meta">{formatBytes(item.size)}</span>
                  <button
                    type="button"
                    className="collection-sub-item-remove"
                    disabled={removingId === item.id}
                    onClick={() => handleRemoveItem(item.id)}
                    aria-label={`Remove ${item.filename} from ${collection.name}`}
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </li>
  );
}

function useLibraryUploads(refreshKey: number, tag: string = '') {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [offset, setOffset] = useState(0);

  // Initial / refresh fetch: load the first page (or the whole list when
  // the server has fewer items than one page).
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setOffset(0);
    const params = new URLSearchParams({ limit: String(UPLOADS_PAGE_SIZE), offset: '0' });
    if (tag !== '') params.set('tag', tag);
    fetch(`${UPLOADS_URL}?${params.toString()}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as UploadListResponse;
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
      })
      .catch(() => {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey, tag]);

  const hasMore = items.length < total;

  function loadMore() {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    const nextOffset = offset + UPLOADS_PAGE_SIZE;
    const params = new URLSearchParams({
      limit: String(UPLOADS_PAGE_SIZE),
      offset: String(nextOffset),
    });
    if (tag !== '') params.set('tag', tag);
    fetch(`${UPLOADS_URL}?${params.toString()}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as UploadListResponse;
        setItems((prev) => [...prev, ...data.items]);
        setTotal(data.total);
        setOffset(nextOffset);
      })
      .catch(() => {
        // Best-effort: leave the already-loaded items in place.
      })
      .finally(() => {
        setLoadingMore(false);
      });
  }

  return { items, total, loading, loadingMore, hasMore, loadMore };
}

/**
 * Per-upload tag editor: renders the metadata row's current tags as
 * removable chips and a small input + "Add tag" button that calls
 * `POST /library/metadata/{id}/tags`; removing a chip calls
 * `DELETE /library/metadata/{id}/tags/{tag}`. Both responses return the
 * full sorted tag list, which is bubbled up via `onTagsChange`.
 */
interface TagEditorProps {
  metadataId: number;
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  onError: (msg: string) => void;
}

function TagEditor({ metadataId, tags, onTagsChange, onError }: TagEditorProps) {
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);

  async function handleAdd(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const tag = value.trim();
    if (!tag || busy) return;
    setBusy(true);
    try {
      const res = await fetch(`${API_BASE_URL}/library/metadata/${metadataId}/tags`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tag }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as { tags: string[] };
      onTagsChange(data.tags);
      setValue('');
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Add tag failed');
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove(tag: string) {
    if (busy) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/library/metadata/${metadataId}/tags/${encodeURIComponent(tag)}`,
        { method: 'DELETE' },
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as { tags: string[] };
      onTagsChange(data.tags);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Remove tag failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="tag-editor">
      {tags.length > 0 && (
        <ul className="tag-chips">
          {tags.map((tag) => (
            <li key={tag} className="tag-chip">
              <span className="tag-chip-name">{tag}</span>
              <button
                type="button"
                className="tag-chip-remove"
                disabled={busy}
                onClick={() => handleRemove(tag)}
                aria-label={`Remove tag ${tag}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
      <form className="tag-form" onSubmit={handleAdd}>
        <input
          type="text"
          className="tag-input"
          placeholder="Add a tag…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={busy}
          aria-label={`Add tag to upload ${metadataId}`}
        />
        <button type="submit" className="tag-add" disabled={busy || value.trim() === ''}>
          {busy ? '…' : 'Add tag'}
        </button>
      </form>
    </div>
  );
}

/**
 * Per-upload "Add to collection" control: a dropdown of existing
 * collections plus a button that calls `POST /collections/{name}/items`
 * with the item's `metadata_id`. Hidden entirely when no collections
 * exist yet. Errors surface via the shared error banner callback.
 */
interface AddToCollectionControlProps {
  metadataId: number;
  collections: CollectionItem[];
  onError: (msg: string) => void;
}

function AddToCollectionControl({ metadataId, collections, onError }: AddToCollectionControlProps) {
  const [selected, setSelected] = useState('');
  const [busy, setBusy] = useState(false);
  const [added, setAdded] = useState('');

  if (collections.length === 0) return null;

  async function handleAdd() {
    const name = selected.trim();
    if (!name || busy) return;
    setBusy(true);
    setAdded('');
    try {
      const res = await fetch(`${COLLECTIONS_URL}/${encodeURIComponent(name)}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metadata_id: metadataId }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setAdded(name);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Add to collection failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="collection-add">
      <select
        className="collection-add-select"
        value={selected}
        onChange={(e) => {
          setSelected(e.target.value);
          setAdded('');
        }}
        disabled={busy}
        aria-label={`Choose collection for upload ${metadataId}`}
      >
        <option value="">Add to collection…</option>
        {collections.map((col) => (
          <option key={col.id} value={col.name}>
            {col.name}
          </option>
        ))}
      </select>
      <button
        type="button"
        className="collection-add-button"
        onClick={handleAdd}
        disabled={busy || selected === ''}
      >
        {busy ? '…' : 'Add'}
      </button>
      {added !== '' && <span className="collection-add-done">Added to {added}</span>}
    </div>
  );
}

/**
 * Persistent bottom-docked audio player bar. Plays the currently selected
 * audio item via `GET /library/audio/{name}` with a play/pause toggle and
 * a close button. Autoplays whenever the selected track changes.
 */
interface AudioPlayerBarProps {
  track: AudioItem;
  onClose: () => void;
}

function AudioPlayerBar({ track, onClose }: AudioPlayerBarProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);

  // Load + autoplay whenever the selected track changes.
  useEffect(() => {
    const el = audioRef.current;
    if (!el) return;
    el.src = audioUrlFor(track.name);
    el.play().catch(() => {
      // Autoplay may be blocked by the browser — the user can press play.
      setPlaying(false);
    });
  }, [track.name]);

  function togglePlay() {
    const el = audioRef.current;
    if (!el) return;
    if (el.paused) {
      el.play().catch(() => setPlaying(false));
    } else {
      el.pause();
    }
  }

  return (
    <div className="player-bar" role="region" aria-label="Audio player">
      <button
        type="button"
        className="player-toggle"
        onClick={togglePlay}
        aria-label={playing ? `Pause ${track.name}` : `Play ${track.name}`}
      >
        {playing ? '⏸' : '▶'}
      </button>
      <span className="player-title" title={track.name}>
        {track.name}
      </span>
      <audio
        ref={audioRef}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
      />
      <button
        type="button"
        className="player-close"
        onClick={onClose}
        aria-label="Close audio player"
      >
        ✕
      </button>
    </div>
  );
}

function App() {
  const { state, summary } = useLibrarySummary();
  const [audioRefreshKey, setAudioRefreshKey] = useState(0);
  const [audioQuery, setAudioQuery] = useState('');
  const { items: audioItems, loading: audioLoading } = useLibraryAudio(audioRefreshKey, audioQuery);
  const [videoRefreshKey, setVideoRefreshKey] = useState(0);
  const [videoQuery, setVideoQuery] = useState('');
  const { items: videoItems, loading: videoLoading } = useLibraryVideo(videoRefreshKey, videoQuery);
  const [collectionsRefreshKey, setCollectionsRefreshKey] = useState(0);
  const { items: collectionItems, loading: collectionsLoading } =
    useCollections(collectionsRefreshKey);
  const [expandedCollection, setExpandedCollection] = useState<string | null>(null);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [creatingCollection, setCreatingCollection] = useState(false);
  const [activeVideo, setActiveVideo] = useState<VideoItem | null>(null);
  const [activeAudio, setActiveAudio] = useState<AudioItem | null>(null);
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
  // Tag-based quick filter: fetched once on mount; selecting a tag re-fetches
  // the uploads list server-side via `?tag=` on `GET /library/uploads`.
  const availableTags = useLibraryTags();
  const [uploadsTagFilter, setUploadsTagFilter] = useState('');
  const {
    items: uploadItems,
    total: uploadTotal,
    loading: uploadsLoading,
    loadingMore: uploadsLoadingMore,
    hasMore: uploadsHasMore,
    loadMore: uploadsLoadMore,
  } = useLibraryUploads(uploadsRefreshKey, uploadsTagFilter);
  const [uploadsFilter, setUploadsFilter] = useState('');
  // Per-upload tags map (metadataId -> tag list). Lazily fetched for each
  // upload item via `GET /library/metadata/{id}` once the uploads list is
  // loaded; updated in place by the TagEditor's onTagsChange callback.
  const [uploadTags, setUploadTags] = useState<Record<number, string[]>>({});
  useEffect(() => {
    if (uploadItems.length === 0) return;
    let cancelled = false;
    Promise.all(
      uploadItems.map(async (it) => {
        try {
          const res = await fetch(`${API_BASE_URL}/library/metadata/${it.id}`);
          if (!res.ok) return null;
          const data = (await res.json()) as { tags: string[] };
          return [it.id, data.tags] as const;
        } catch {
          return null;
        }
      }),
    ).then((results) => {
      if (cancelled) return;
      const next: Record<number, string[]> = {};
      for (const r of results) {
        if (r) next[r[0]] = r[1];
      }
      setUploadTags(next);
    });
    return () => {
      cancelled = true;
    };
  }, [uploadItems]);
  // Global dismissible error banner. Surfacing already-caught local failures
  // (upload/download/poll) at the top of the page so the user always notices
  // them even when scrolled past the inline error notes.
  const [notice, setNotice] = useState<string | null>(null);
  // Mirror the polling hook's error into the global banner without changing
  // the hook's API.
  useEffect(() => {
    if (jobPollError) setNotice(`Job status update failed: ${jobPollError}`);
  }, [jobPollError]);
  const filterNeedle = uploadsFilter.trim().toLowerCase();
  const visibleUploadItems =
    filterNeedle === ''
      ? uploadItems
      : uploadItems.filter((it) => it.filename.toLowerCase().includes(filterNeedle));

  async function handleDeleteAudio(name: string) {
    try {
      const res = await fetch(`${LIBRARY_AUDIO_URL}/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (activeAudio?.name === name) {
        setActiveAudio(null);
      }
      setAudioRefreshKey((k) => k + 1);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Delete audio failed';
      setNotice(`Could not delete audio item "${name}": ${msg}`);
    }
  }

  async function handleDeleteVideo(name: string) {
    try {
      const res = await fetch(`${LIBRARY_VIDEO_URL}/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (activeVideo?.name === name) {
        setActiveVideo(null);
      }
      setVideoRefreshKey((k) => k + 1);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Delete video failed';
      setNotice(`Could not delete video item "${name}": ${msg}`);
    }
  }

  async function handleCreateCollection(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const name = newCollectionName.trim();
    if (!name || creatingCollection) return;
    setCreatingCollection(true);
    try {
      const res = await fetch(COLLECTIONS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      if (res.status === 409) {
        setNotice(`Collection "${name}" already exists.`);
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setNewCollectionName('');
      setCollectionsRefreshKey((k) => k + 1);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Create collection failed';
      setNotice(`Create collection failed: ${msg}`);
    } finally {
      setCreatingCollection(false);
    }
  }

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
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setUploadError(msg);
      setNotice(`Upload failed: ${msg}`);
    } finally {
      setUploading(false);
      // Allow re-selecting the same file to trigger onChange again.
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  useEffect(() => {
    if (jobStatus === 'completed') {
      setAudioRefreshKey((k) => k + 1);
      setVideoRefreshKey((k) => k + 1);
    }
  }, [jobStatus]);

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
      const startRes = await fetch(`${JOBS_URL}/${job.id}/start`, { method: 'POST' });
      if (!startRes.ok) throw new Error(`HTTP ${startRes.status}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Request failed';
      setJobError(msg);
      setNotice(`Could not create job: ${msg}`);
    } finally {
      setSubmitting(false);
    }
  }

  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const importFileInputRef = useRef<HTMLInputElement | null>(null);

  async function handleExportLibrary() {
    if (exporting) return;
    setExporting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/library/export`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const exportUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = exportUrl;
      a.download = `library-export-${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(exportUrl);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Export failed';
      setNotice(`Export library failed: ${msg}`);
    } finally {
      setExporting(false);
    }
  }

  async function handleImportSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || importing) return;
    setImporting(true);
    try {
      const text = await file.text();
      let payload: unknown;
      try {
        payload = JSON.parse(text);
      } catch {
        throw new Error('Invalid JSON file format');
      }
      const res = await fetch(`${API_BASE_URL}/library/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as {
        imported_metadata: number;
        imported_tags: number;
        imported_collections: number;
        imported_jobs: number;
      };
      setNotice(
        `Import complete: ${data.imported_metadata} metadata, ${data.imported_tags} tags, ${data.imported_collections} collections, ${data.imported_jobs} jobs restored.`,
      );
      setCollectionsRefreshKey((k) => k + 1);
      setUploadsRefreshKey((k) => k + 1);
      setAudioRefreshKey((k) => k + 1);
      setVideoRefreshKey((k) => k + 1);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Import failed';
      setNotice(`Import library failed: ${msg}`);
    } finally {
      setImporting(false);
      if (importFileInputRef.current) importFileInputRef.current.value = '';
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
      {notice && (
        <div className="notice-banner" role="alert">
          <span className="notice-text">{notice}</span>
          <button
            type="button"
            className="notice-close"
            aria-label="Dismiss notice"
            onClick={() => setNotice(null)}
          >
            ✕
          </button>
        </div>
      )}
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
          <button
            type="button"
            className="secondary"
            onClick={handleExportLibrary}
            disabled={exporting}
            aria-label="Export library metadata JSON"
          >
            {exporting ? 'Exporting…' : 'Export JSON'}
          </button>
          <input
            ref={importFileInputRef}
            type="file"
            accept=".json,application/json"
            onChange={handleImportSelected}
            aria-label="Import library metadata JSON file"
            style={{ display: 'none' }}
          />
          <button
            type="button"
            className="secondary"
            onClick={() => importFileInputRef.current?.click()}
            disabled={importing}
            aria-label="Import library metadata JSON"
          >
            {importing ? 'Importing…' : 'Import JSON'}
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
          <input
            type="search"
            className="audio-filter"
            placeholder="Search audio…"
            value={audioQuery}
            onChange={(e) => setAudioQuery(e.target.value)}
            aria-label="Filter audio by filename"
          />
          {audioLoading ? (
            <p>Loading audio library…</p>
          ) : audioItems.length === 0 ? (
            <p className="audio-empty">
              {audioQuery.trim() !== ''
                ? `No audio matching "${audioQuery}".`
                : 'MP3 downloads will appear here.'}
            </p>
          ) : (
            <ul className="audio-list">
              {audioItems.map((item) => (
                <li key={item.name} className="audio-item audio-item-playable">
                  <button
                    type="button"
                    className="audio-play"
                    onClick={() => setActiveAudio(item)}
                    aria-label={`Play ${item.name}`}
                  >
                    ▶
                  </button>
                  <span className="audio-name">{item.name}</span>
                  <button
                    type="button"
                    className="audio-delete"
                    onClick={() => handleDeleteAudio(item.name)}
                    aria-label={`Delete ${item.name}`}
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>
        <article>
          <h2>Video</h2>
          <input
            type="search"
            className="video-filter"
            placeholder="Search video…"
            value={videoQuery}
            onChange={(e) => setVideoQuery(e.target.value)}
            aria-label="Filter video by filename"
          />
          {videoLoading ? (
            <p>Loading video library…</p>
          ) : videoItems.length === 0 ? (
            <p className="video-empty">
              {videoQuery.trim() !== ''
                ? `No video matching "${videoQuery}".`
                : 'MP4 downloads will appear here.'}
            </p>
          ) : (
            <ul className="audio-list">
              {videoItems.map((item) => (
                <li key={item.name} className="video-item">
                  <span className="video-thumb-wrap">
                    <span className="video-thumb-placeholder" aria-hidden="true">▶</span>
                    <img
                      className="video-thumb"
                      src={thumbnailUrlFor(item.name)}
                      alt=""
                      loading="lazy"
                      onError={(e) => {
                        // Thumbnail missing/unavailable — hide the broken
                        // image so the placeholder behind it shows through.
                        (e.currentTarget as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </span>
                  <button
                    type="button"
                    className="video-play"
                    onClick={() => setActiveVideo(item)}
                    aria-label={`Play ${item.name}`}
                  >
                    ▶
                  </button>
                  <span className="video-name">{item.name}</span>
                  <button
                    type="button"
                    className="video-delete"
                    onClick={() => handleDeleteVideo(item.name)}
                    aria-label={`Delete ${item.name}`}
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </article>
        <article>
          <h2>Uploads</h2>
          {uploadsLoading ? (
            <p>Loading uploads…</p>
          ) : uploadItems.length === 0 && uploadsTagFilter === '' ? (
            <p>Uploaded files will appear here.</p>
          ) : (
            <>
              {(availableTags ?? []).length > 0 && (
                <select
                  className="uploads-tag-filter"
                  value={uploadsTagFilter}
                  onChange={(e) => setUploadsTagFilter(e.target.value)}
                  aria-label="Filter uploads by tag"
                >
                  <option value="">All tags</option>
                  {(availableTags ?? []).map((tag) => (
                    <option key={tag} value={tag}>
                      {tag}
                    </option>
                  ))}
                </select>
              )}
              <input
                type="search"
                className="uploads-filter"
                placeholder="Filter by filename…"
                value={uploadsFilter}
                onChange={(e) => setUploadsFilter(e.target.value)}
                aria-label="Filter uploads by filename"
              />
              {visibleUploadItems.length === 0 ? (
                <p className="uploads-empty">
                  {filterNeedle !== ''
                    ? `No uploads match "${uploadsFilter}".`
                    : `No uploads tagged "${uploadsTagFilter}".`}
                </p>
              ) : (
                <ul className="audio-list">
                  {visibleUploadItems.map((item) => (
                    <li key={item.id} className="upload-item">
                      <span className="upload-name">{item.filename}</span>
                      <span className="upload-meta">
                        {formatBytes(item.size)}
                        {item.content_type ? ` · ${item.content_type}` : ''}
                        {' · '}
                        {formatUploadedAt(item.uploaded_at)}
                      </span>
                      <TagEditor
                        metadataId={item.id}
                        tags={uploadTags[item.id] ?? []}
                        onTagsChange={(tags) =>
                          setUploadTags((prev) => ({ ...prev, [item.id]: tags }))
                        }
                        onError={(msg) => setNotice(`Tag edit failed: ${msg}`)}
                      />
                      <AddToCollectionControl
                        metadataId={item.id}
                        collections={collectionItems}
                        onError={(msg) => setNotice(`Add to collection failed: ${msg}`)}
                      />
                    </li>
                  ))}
                </ul>
              )}
              {/* "Load more" pagination control. Only meaningful when no
                  client-side filename filter is active (the filter applies
                  over the already-loaded page, not the full backend set). */}
              {filterNeedle === '' && uploadsHasMore && (
                <div className="uploads-pagination">
                  <span className="uploads-count">
                    {uploadItems.length} of {uploadTotal}
                  </span>
                  <button
                    type="button"
                    className="uploads-load-more"
                    onClick={uploadsLoadMore}
                    disabled={uploadsLoadingMore}
                  >
                    {uploadsLoadingMore ? 'Loading…' : 'Load more'}
                  </button>
                </div>
              )}
            </>
          )}
        </article>
        <article>
          <h2>Collections</h2>
          <form className="collection-form" onSubmit={handleCreateCollection}>
            <input
              type="text"
              className="collection-input"
              placeholder="New collection name…"
              value={newCollectionName}
              onChange={(e) => setNewCollectionName(e.target.value)}
              disabled={creatingCollection}
              aria-label="New collection name"
            />
            <button
              type="submit"
              className="collection-create"
              disabled={creatingCollection || newCollectionName.trim() === ''}
            >
              {creatingCollection ? 'Creating…' : 'Create'}
            </button>
          </form>
          {collectionsLoading ? (
            <p>Loading collections…</p>
          ) : collectionItems.length === 0 ? (
            <p>No collections yet. Anime, Hololive, OST, and mood lists will live here.</p>
          ) : (
            <ul className="audio-list">
              {collectionItems.map((col) => (
                <CollectionRow
                  key={col.id}
                  collection={col}
                  isExpanded={expandedCollection === col.name}
                  onToggle={() =>
                    setExpandedCollection((prev) => (prev === col.name ? null : col.name))
                  }
                  formatBytes={formatBytes}
                  onDeleteCollection={(name) => {
                    if (expandedCollection === name) {
                      setExpandedCollection(null);
                    }
                    setCollectionsRefreshKey((k) => k + 1);
                  }}
                  onRenameCollection={(oldName, newName) => {
                    if (expandedCollection === oldName) {
                      setExpandedCollection(newName);
                    }
                    setCollectionsRefreshKey((k) => k + 1);
                  }}
                  onError={(msg) => setNotice(`Collection action failed: ${msg}`)}
                />
              ))}
            </ul>
          )}
        </article>
      </section>
      {activeVideo && (
        <div
          className="video-modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-label={`Video preview: ${activeVideo.name}`}
          onClick={(e) => {
            if (e.target === e.currentTarget) setActiveVideo(null);
          }}
        >
          <div className="video-modal">
            <div className="video-modal-head">
              <span className="video-modal-title">{activeVideo.name}</span>
              <button
                type="button"
                className="video-modal-close"
                onClick={() => setActiveVideo(null)}
                aria-label="Close video preview"
              >
                ✕
              </button>
            </div>
            <video
              className="video-modal-player"
              src={videoUrlFor(activeVideo.name)}
              controls
              autoPlay
              playsInline
            >
              Your browser does not support embedded video playback.
            </video>
          </div>
        </div>
      )}
      {activeAudio && <AudioPlayerBar track={activeAudio} onClose={() => setActiveAudio(null)} />}
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
