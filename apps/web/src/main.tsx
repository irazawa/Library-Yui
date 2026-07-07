import React from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

function App() {
  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Library-Yui · MVP 0</p>
        <h1>Your personal music/video library starts here.</h1>
        <p>
          This shell will become the downloader, upload manager, and collection browser.
          MVP 1 will connect the YouTube URL form to the FastAPI download queue.
        </p>
        <div className="actions">
          <button type="button">Download form coming soon</button>
          <button type="button" className="secondary">Upload coming soon</button>
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
