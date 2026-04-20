# 🚀 PharmaAgent — Deployment Guide

## Architecture

```
┌─────────────────────┐         ┌────────────────────────────┐
│   Vercel (Frontend)  │ ──────▶ │   Render (Backend)          │
│   React/Vite App     │  HTTPS  │   FastAPI + SQLite + Agents │
│   VITE_API_URL=Render│         │   Persistent Disk Sync      │
└─────────────────────┘         └────────────────────────────┘
```

---

## Part 1: Backend on Render

### Prerequisites
- GitHub account with the project pushed.
- Render account → [render.com](https://render.com)

### Steps

1. **Create New Web Service**:
   - Connect your GitHub repo.
   - Select the repository.
   - Set **Name** to `pharma-agent-backend`.
   - Set **Root Directory** to `backend`.
   - **Environment**: `Python`.
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 10000`

2. **Configure Storage (Critical for SQLite)**:
   - Go to **Advanced** → **Disk**.
   - Add a disk:
     - **Name**: `pharma-agent-data`
     - **Mount Path**: `/opt/render/project/src`
     - **Size**: 1GB (Free tier)

3. **Deploy**: Render will build using your `render.yaml` and `build.sh`.
4. **Copy the URL**: (e.g. `https://pharma-agent-backend.onrender.com`)

---

## Part 2: Frontend on Vercel

### Prerequisites
- Vercel account → [vercel.com](https://vercel.com)

### Steps

1. **Import Project**:
   - Go to [vercel.com/new](https://vercel.com/new) and import your repo.
   - Set **Root Directory** to `frontend`.

2. **Set Environment Variables**:
   - Go to **Settings** → **Environment Variables**.
   - Add:
     | Key | Value |
     |-----|-------|
     | `VITE_API_URL` | Your Render URL (or ngrok URL if testing locally) |

3. **Deploy**: Vercel will build and host your React application.

---

## Part 3: Local Testing with ngrok (Optional)

If you are developing locally and want to expose your local backend to your Vercel frontend:

1. **Start Local Backend**: `uvicorn app.main:app --reload`
2. **Start ngrok**: `ngrok http 8000`
3. **Update Vercel**: Paste the ngrok URL into the `VITE_API_URL` environment variable and redeploy.

---

## 🛠️ Maintenance & Updates

### Schema Changes
Since this project uses SQLite without Alembic, when changing the database schema:
1. Commit and push the updated `pharma_agent.db` from your local machine.
2. Render will update the persistent file upon the next deploy.

### Troubleshooting

| Issue | Solution |
|-------|----------|
| 404 on API calls | Ensure `VITE_API_URL` in Vercel ends without a trailing slash |
| DB Resetting | Verify the Disk is correctly mounted in Render dashboard |
| Build Failures | Check `backend/build.sh` logs for missing components |
