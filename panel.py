from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from datetime import datetime
import pytz, threading

app = Flask(__name__)
CORS(app)

TZ = pytz.timezone("America/Santiago")
SIGNALS = []
LOCK = threading.Lock()

def parse_iso(ts):
    if "T" in ts:
        return datetime.fromisoformat(ts.replace("Z",""))
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")

def map_duration_by_conf(conf):
    if 85 <= conf <= 90: return 1
    if 91 <= conf <= 94: return 3
    return 5

def status_for(now, entry_dt, expire_dt):
    if now < entry_dt: return "PRÓXIMA"
    if entry_dt <= now < expire_dt: return "EN CURSO"
    return "FINALIZADA"

@app.post("/api/signal")
def add_signal():
    d = request.get_json(force=True)
    pair  = d["pair"]; side = d["side"]; price = float(d["price"])
    conf  = int(d["confidence"]); mode = d.get("mode","MIXTO")
    strat = d.get("strategy","Acción del Precio")
    entry_dt  = parse_iso(d["entry"]).replace(tzinfo=None)
    expire_dt = parse_iso(d["expire"]).replace(tzinfo=None)
    duration  = int(d.get("duration") or map_duration_by_conf(conf))
    payload = {"pair":pair,"side":side,"price":price,"confidence":conf,"mode":mode,
               "strategy":strat,"entry":entry_dt,"expire":expire_dt,"duration":duration}
    with LOCK:
        for i,s in enumerate(SIGNALS):
            if s["pair"]==pair and abs((s["entry"]-entry_dt).total_seconds())<1:
                SIGNALS[i]=payload; break
        else:
            SIGNALS.append(payload)
    return jsonify(ok=True)

@app.get("/api/data")
def api_data():
    now = datetime.now(TZ).replace(tzinfo=None)
    rows=[]
    with LOCK:
        for s in SIGNALS:
            st = status_for(now,s["entry"],s["expire"])
            rows.append({
                "pair":s["pair"],"side":s["side"],"price":f"{s['price']:.5f}",
                "entry":s["entry"].strftime("%H:%M:%S"),
                "expire":s["expire"].strftime("%H:%M:%S"),
                "confidence":s["confidence"],"duration":s["duration"],
                "strategy":s["strategy"],"status":st,"mode":s["mode"]
            })
    order={"PRÓXIMA":0,"EN CURSO":1,"FINALIZADA":2}
    rows.sort(key=lambda r:(order.get(r["status"],3), r["entry"]))
    return jsonify(rows)

@app.get("/")
def index():
    html=f"""<!doctype html><html lang="es"><head><meta charset="utf-8"/>
<title>Panel de Señales IQ Option</title><meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
body{{background:#000;color:#9f9;font-family:Menlo,Consolas,monospace}}
h1{{color:#9f9}} table{{width:100%;border-collapse:collapse}}
th,td{{border:1px solid #2f2;padding:8px}} thead th{{background:#030}}
tr:nth-child(even) td{{background:#010}}
.CALL{{color:#0f0;font-weight:bold}} .PUT{{color:#f33;font-weight:bold}}
.st-prox{{color:#0af;font-weight:bold}} .st-live{{color:#ff0;font-weight:bold}}
.st-done{{color:#f55;font-weight:bold}}
</style></head><body>
<h1>📊 Panel de Señales IQ Option</h1>
<div id="clock">Reloj local: --:--:--</div>
<table><thead><tr>
<th>Par</th><th>Tipo</th><th>Precio</th><th>Entrada</th><th>Expira</th>
<th>Confianza</th><th>Duración (min)</th><th>Estrategia</th><th>Estado</th><th>Modo</th>
</tr></thead><tbody id="rows"></tbody></table>
<script>
function pad(n){{return n.toString().padStart(2,'0')}}
function tick(){{const d=new Date();document.getElementById('clock').innerText=
'Reloj local: '+pad(d.getHours())+':'+pad(d.getMinutes())+':'+pad(d.getSeconds())}}
setInterval(tick,500);tick();
function clsSide(s){{return s==='PUT'?'PUT':'CALL'}}
function clsSt(s){{return s==='PRÓXIMA'?'st-prox':(s==='EN CURSO'?'st-live':'st-done')}}
async function upd(){{const r=await fetch('/api/data');const a=await r.json();
const tb=document.getElementById('rows');tb.innerHTML='';
for(const s of a){{const tr=document.createElement('tr');tr.innerHTML=
`<td>${{s.pair}}</td><td class="${{clsSide(s.side)}}">${{s.side}}</td>
<td>${{s.price}}</td><td>${{s.entry}}</td><td>${{s.expire}}</td>
<td>${{s.confidence}}</td><td>${{s.duration}}</td>
<td>${{s.strategy}}</td><td class="${{clsSt(s.status)}}">${{s.status}}</td>
<td>${{s.mode}}</td>`;tb.appendChild(tr);}}}}
setInterval(upd,1500);upd();
</script></body></html>"""
    return Response(html, mimetype="text/html")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000, debug=False, threaded=True)
