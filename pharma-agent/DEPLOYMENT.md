# 🚀 PharmaAgent — Deployment Guide

## Architecture

```
┌─────────────────────┐         ┌────────────────────────────┐
│   Vercel (Frontend)  │ ──────▶ │  Google Colab (Backend)     │
│   React/Vite App     │  HTTPS  │  FastAPI + SQLite + Agents  │
│   VITE_API_URL=ngrok │         │  Exposed via ngrok tunnel   │
└─────────────────────┘         └────────────────────────────┘
```

---

## Part 1: Backend on Google Colab + ngrok

### Prerequisites
- Google account (for Colab)
- Free ngrok account → [ngrok.com/signup](https://ngrok.com/signup)
- Copy your **auth token** from [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)

### Steps

1. **Upload the notebook** `PharmaAgent_Backend.ipynb` to Google Colab
2. **Run Cell 1** → Choose one upload method (GitHub clone / Google Drive / zip upload)
3. **Run Cell 2** → Installs all Python dependencies
4. **Run Cell 3** → Paste your ngrok auth token when prompted
5. **Run Cell 4** → Starts the FastAPI server + ngrok tunnel
6. **Copy the public URL** printed in the output (e.g. `https://abc123.ngrok-free.app`)
7. **(Optional) Run Cell 5** → Tests the API to confirm it works

> ⚠️ **Keep Cell 4 running!** Stopping it kills the server and tunnel.

> 💡 **ngrok free tier** gives a random URL each restart. With a [paid plan](https://ngrok.com/pricing) ($8/mo), you get a **static domain** that never changes.

---

## Part 2: Frontend on Vercel

### Prerequisites
- GitHub account with the project pushed
- Vercel account → [vercel.com](https://vercel.com)

### Steps

1. **Push to GitHub** (if not already):
   ```bash
   cd pharma-agent
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/pharma-agent.git
   git push -u origin main
   ```

2. **Import on Vercel**:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repo
   - Set **Root Directory** to `frontend`
   - Framework will auto-detect as **Vite**

3. **Add Environment Variable**:
   - Go to **Settings** → **Environment Variables**
   - Add:
     | Key | Value |
     |-----|-------|
     | `VITE_API_URL` | Your ngrok URL (e.g. `https://abc123.ngrok-free.app`) |

4. **Deploy** → Vercel builds and deploys automatically

---

## Updating the Backend URL

When the ngrok URL changes (free tier), you need to:

1. Copy the new URL from the Colab notebook output
2. Go to Vercel → **Settings** → **Environment Variables**
3. Update `VITE_API_URL` with the new URL
4. Go to **Deployments** → Click **⋮** on latest → **Redeploy**

> 💡 With a **static ngrok domain**, you set this once and never update again.

---

## Testing

After both are running, verify:

```bash
# Test backend directly
curl https://YOUR-NGROK-URL.ngrok-free.app/health

# Test chat
curl -X POST https://YOUR-NGROK-URL.ngrok-free.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'
```

Then open your Vercel URL in a browser — you should see the PharmaAgent chat interface connected to the Colab backend.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Blank page on Vercel | Check `VITE_API_URL` is set and redeploy |
| CORS errors | Backend already allows `*` origins — should work |
| Colab disconnects | Google Colab has a ~90 min idle timeout. Keep the tab active |
| ngrok says "tunnel not found" | Re-run Cell 4 in Colab and update URL in Vercel |
| Chat returns error | Check Colab logs; backend runs in rule-based mode (no Ollama) |
