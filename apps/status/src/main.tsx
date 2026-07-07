import React from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const roadmap = [
  ['MVP 0', 'Scaffold repo, API, web shell, status dashboard'],
  ['MVP 1', 'Audio download jobs and library list'],
  ['MVP 2', 'User uploads and metadata'],
  ['MVP 3', 'Collections, tags, and search'],
];

function App() {
  return (
    <main className="dashboard">
      <header>
        <p className="eyebrow">Progress Dashboard · Port 5175</p>
        <h1>Library-Yui Build Status</h1>
        <p>Slow, real progress tracker for the personal media library project.</p>
      </header>
      <section className="grid">
        {roadmap.map(([title, text]) => (
          <article key={title}>
            <strong>{title}</strong>
            <span>{text}</span>
          </article>
        ))}
      </section>
      <footer>Next small step: connect the dashboard to API health status.</footer>
    </main>
  );
}

createRoot(document.getElementById('root')!).render(<App />);
