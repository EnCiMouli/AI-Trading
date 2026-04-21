"""
AI Trader — Crisis Index Receiver + Dashboard Server (CLOUD DEPLOYMENT)
Optimized for Render.com free tier with external PORT binding.
Accepts TradingView webhook POSTs for WCI / IFS / CCI indices,
stores in SQLite, exposes history/latest GET endpoints,
serves the dashboard at /.
"""
import sqlite3, json, os, re
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "crisis.db")
DASH_DIR = BASE  # dashboard.html lives in same folder on cloud

app = Flask(__name__, static_folder=None)
CORS(app)

# ---- DB ----
def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    for tbl in ("wci", "ifs", "cci"):
        cur.execute(f"""CREATE TABLE IF NOT EXISTS {tbl} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            received_at TEXT,
            ticker TEXT,
            payload TEXT
        )""")
    con.commit()
    con.close()

def store(table, data):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ticker = (data or {}).get("ticker", "UNKNOWN")
    cur.execute(f"INSERT INTO {table} (received_at, ticker, payload) VALUES (?,?,?)",
                (now, ticker, json.dumps(data or {})))
    con.commit()
    con.close()
    print(f"[{now}] {table.upper()} stored | ticker={ticker} | payload={json.dumps(data)[:200]}")

def history(table, limit=100):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(f"SELECT id, received_at, ticker, payload FROM {table} ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    con.close()
    out = []
    for r in rows:
        try: p = json.loads(r[3])
        except Exception: p = {}
        p["id"] = r[0]; p["received_at"] = r[1]; p["ticker"] = r[2]
        out.append(p)
    return out

def latest_real(table):
    h = history(table, 100)
    real = [x for x in h if x.get("ticker") != "TEST"]
    return real[0] if real else (h[0] if h else {})

# ---- Webhook POST endpoints ----
@app.route("/api/wci/webhook", methods=["POST"])
def wci_hook():
    try: data = request.get_json(force=True, silent=True) or {}
    except Exception: data = {}
    store("wci", data); return "OK", 200

@app.route("/api/india/webhook", methods=["POST"])
def ifs_hook():
    try: data = request.get_json(force=True, silent=True) or {}
    except Exception: data = {}
    store("ifs", data); return "OK", 200

@app.route("/api/cci/webhook", methods=["POST"])
def cci_hook():
    try: data = request.get_json(force=True, silent=True) or {}
    except Exception: data = {}
    store("cci", data); return "OK", 200

# ---- History / Latest GET endpoints ----
@app.route("/api/wci/history", methods=["GET"])
def wci_hist(): return jsonify(history("wci"))
@app.route("/api/india/history", methods=["GET"])
def ifs_hist(): return jsonify(history("ifs"))
@app.route("/api/cci/history", methods=["GET"])
def cci_hist(): return jsonify(history("cci"))
@app.route("/api/wci/latest", methods=["GET"])
def wci_latest(): return jsonify(latest_real("wci"))
@app.route("/api/india/latest", methods=["GET"])
def ifs_latest(): return jsonify(latest_real("ifs"))
@app.route("/api/cci/latest", methods=["GET"])
def cci_latest(): return jsonify(latest_real("cci"))

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status":"ok","server":"AI Trader (Render)","db":"cloud-sqlite"})

# ---- On cloud deployment the tunnel concept does not apply; return a dummy OK ----
@app.route("/api/tunnel", methods=["GET"])
def tunnel_info():
    # On Render, this is the permanent URL itself. Browser already knows.
    return jsonify({"url": request.host_url.rstrip("/"), "status": "live"})

# ---- Test-fire endpoint ----
@app.route("/api/test-fire", methods=["POST"])
def test_fire():
    which = (request.args.get("which") or "wci").lower()
    if which not in ("wci","ifs","cci"):
        return jsonify({"error":"invalid 'which'"}), 400
    payload = {
        "ticker":"PIPE_TEST",
        ("ifs" if which=="ifs" else which): 50.0,
        "level":"ALERT","direction":"FLAT","action":"WAIT",
        "subhead":"Dashboard pipe test · delete safely",
    }
    store(which, payload)
    return jsonify({"ok":True,"inserted":payload})

# ---- Serve dashboard ----
@app.route("/")
def dash_root(): return send_from_directory(DASH_DIR, "dashboard.html")

@app.route("/<path:fname>")
def dash_files(fname):
    if any(fname.endswith(ext) for ext in (".html",".css",".js",".md",".png",".jpg",".svg",".ico")):
        if os.path.exists(os.path.join(DASH_DIR, fname)):
            return send_from_directory(DASH_DIR, fname)
    return "Not found", 404

init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
