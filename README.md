# AI Trader — Cloud Server

Flask webhook receiver + dashboard host. Deployed to Render.com free tier.

## Endpoints

**POST (TradingView webhooks):**
- `/api/wci/webhook`
- `/api/india/webhook`
- `/api/cci/webhook`

**GET (dashboard + debugging):**
- `/` — dashboard
- `/api/health`
- `/api/wci/history` · `/api/india/history` · `/api/cci/history`
- `/api/wci/latest` · `/api/india/latest` · `/api/cci/latest`

## Deploy to Render

1. Push this folder to a GitHub repo
2. Render.com → New Web Service → connect repo
3. Build: auto-detects via `render.yaml`
4. Deploy → get permanent URL

## Local Run
```
pip install -r requirements.txt
python app.py
```
