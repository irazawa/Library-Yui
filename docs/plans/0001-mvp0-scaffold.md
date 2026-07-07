# MVP 0 Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a runnable skeleton for Library-Yui with backend API, main web shell, status dashboard, documentation, and storage folders.

**Architecture:** Monorepo with FastAPI backend and two Vite React apps. Downloader logic is intentionally deferred until MVP 1 so MVP 0 remains small and verifiable.

**Tech Stack:** FastAPI, Python, React, TypeScript, Vite, SQLite-ready folder layout.

## Global Constraints

- Keep MVP 0 simple: no database migrations, no yt-dlp integration, no auth.
- Ports are fixed: API `8787`, Web `5174`, Status `5175`.
- Commits must be real changes, not empty/fake activity.

---

### Task 1: Repository Skeleton

**Files:**
- Create: `README.md`, `.gitignore`, `docs/ROADMAP.md`, `docs/PROGRESS.md`, `docs/ARCHITECTURE.md`
- Create: `library/audio/.gitkeep`, `library/video/.gitkeep`, `library/uploads/.gitkeep`, `library/thumbnails/.gitkeep`

**Interfaces:**
- Produces repo documentation and stable folder layout.

- [x] Write docs and storage folders.
- [x] Commit with `chore: scaffold repository structure`.

### Task 2: FastAPI Health API

**Files:**
- Create: `apps/api/main.py`, `apps/api/app/routes/health.py`, `apps/api/app/__init__.py`, `apps/api/app/routes/__init__.py`, `apps/api/requirements.txt`

**Interfaces:**
- Produces `GET /health` returning `{ "status": "ok", "service": "library-yui-api" }`.

- [x] Add health endpoint.
- [x] Verify with FastAPI TestClient.
- [x] Commit with `feat: add api health endpoint`.

### Task 3: Frontend Shells

**Files:**
- Create React/Vite app files under `apps/web/` and `apps/status/`.

**Interfaces:**
- Produces main web app on port `5174`.
- Produces status dashboard app on port `5175`.

- [x] Add visible placeholder UI.
- [x] Verify TypeScript builds.
- [x] Commit with `feat: add frontend shells`.

### Task 4: Developer Scripts and Remote Push

**Files:**
- Create: `scripts/dev.sh`, `scripts/slow_update.py`

**Interfaces:**
- Produces developer helper scripts and initial GitHub push.

- [x] Add helper scripts.
- [x] Verify git status and remote.
- [x] Push `main` to `origin`.
