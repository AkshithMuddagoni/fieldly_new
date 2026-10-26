# Fieldly: local services & equipment marketplace

One app serves **both the website and the API**. You deploy a single Render web service. No separate frontend hosting is needed.

```
backend/    FastAPI app. backend/app/web is the built website (commit it). Database: Supabase Postgres in production, SQLite locally
frontend/   React/Vite source of the website. Only needed if you want to edit the UI (Node 18+)
supabase/lockdown.sql   one-time security step for Supabase
render.yaml optional blueprint
```

## Run locally (VS Code)
Needs Python 3.10+. Terminal: Windows `run.bat` · Mac/Linux `./run.sh`, then open http://localhost:8000
Login OTP **482609**. Provider test console: `/provider-dashboard.html` (phones 9000000001 to 9000000004). API docs: `/docs`.

## Deploy on Render (existing service)
Your current backend service keeps working. After pushing, check its settings:
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python seed.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment: `DATABASE_URL` (Supabase string), `JWT_SECRET` (long random text), `ADMIN_KEY` (long random text)

The website is then at that service's URL. The separate frontend Static Site is no longer needed; you can delete it after checking.

## Supabase
Tables are created automatically on first start. Run `supabase/lockdown.sql` once in the SQL Editor to block Supabase's public REST route to your tables.

## Secrets: never commit them
Passwords and keys belong only in the Render dashboard or a local `.env` file (git-ignored). If one was ever committed or put in a README, change it at the source.

## Know the limits
- `DEMO_MODE` is on by default: login uses the dev OTP, so anyone can sign in as any phone number. Fine for a private test; set `DEMO_MODE=false` once real SMS is wired.
- Without `JWT_SECRET` the app uses a temporary one (logins reset on restart). Without `ADMIN_KEY` admin endpoints stay locked.
- Still simulated: payments, chat, live map tracking, push notifications, document upload.
- Rebuild the website after UI changes: `cd frontend && npm install && npm run build`, then commit `backend/app/web`.


render fieldly-API   ==  https://fieldly-ihsr.onrender.com/

 fieldly == supabase

postgresql://postgres.vufkdebbysbippzzzntb:SZA97WYEYVVoBVVW@aws-0-ap-south-1.pooler.supabase.com:5432/postgres