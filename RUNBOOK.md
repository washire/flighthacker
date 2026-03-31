# FlightHacker — How to Run

## Prerequisites

| Tool | Install |
|---|---|
| Python 3.12+ | python.org/downloads |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| PostgreSQL | `brew install postgresql@16` |
| Redis | Build from source (see below — macOS 12 workaround) |
| Node 20+ | nodejs.org |

---

## Backend (local dev)

```bash
cd FlightHacker/backend

# Install Python deps
uv sync

# Start PostgreSQL and create DB (first time only)
brew services start postgresql@16
createdb flighthacker

# Start Redis (built from source)
/tmp/redis-7.2.4/src/redis-server --daemonize yes

# Start the server
uv run uvicorn main:app --reload --port 8000
```

Test: `curl http://localhost:8000/health`

---

## Backend (production — Railway)

Set these environment variables in Railway dashboard:

```
DATABASE_URL=<Railway provides this automatically>
REDIS_URL=<Railway provides this automatically>
ENVIRONMENT=production
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
DEV_AUTH_BYPASS=false
```

Railway runs: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## Mobile

```bash
cd FlightHacker/mobile
npm install
npx expo start
```

Scan QR code with iPhone camera → opens in Expo Go.

**Point at Railway backend:**
Edit `mobile/.env`:
```
EXPO_PUBLIC_API_URL=https://your-app.up.railway.app
```

**Build APK:**
```bash
npm run build:apk
```

---

## Troubleshooting

- **PostgreSQL not starting** — run `brew services restart postgresql@16`
- **Redis connection error** — run `/tmp/redis-7.2.4/src/redis-server --daemonize yes`
- **flights module error** — run `uv sync` inside backend/
- **Mobile: network error on device** — use LAN IP not localhost in `.env`
