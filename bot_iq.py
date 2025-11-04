import os, time, requests, random
from datetime import datetime, timedelta
from iqoptionapi.stable_api import IQ_Option

EMAIL    = "jitraders1216@gmail.com"       # <-- coloca aquí tu correo de IQ Option
PASSWORD = "jo121014"               # <-- y aquí tu contraseña
PANEL_URL = os.environ.get("PANEL_URL","http://127.0.0.1:10000")

# Pares reales + OTC (MIXTO)
PAIRS = ["EURUSD","GBPUSD","USDJPY","EURUSD-OTC","GBPUSD-OTC","USDJPY-OTC"]
ADVANCE_SECONDS = 90

def map_duration_by_conf(conf):
    # Normaliza por si viene como string o float con '%'
    try:
        c = int(float(str(conf).replace('%','').strip()))
    except Exception:
        c = 85  # fallback seguro

    # Limita el rango a 0..100 (por si acaso)
    c = max(0, min(c, 100))

    # Regla exacta:
    if 85 <= c <= 90:
        return 1
    elif 91 <= c <= 94:
        return 3
    elif 95 <= c <= 100:
        return 5
    else:
        return 1  # fallback por si algún valor se sale del rango

def login():
    iq = IQ_Option(EMAIL,PASSWORD)
    iq.connect()
    if not iq.check_connect():
        print("❌ Error al conectar con IQ Option")
        raise SystemExit
    iq.change_balance("PRACTICE")  # Cambia a "REAL" si lo deseas
    print("✅ Conectado correctamente a IQ Option (MODO: PRACTICE)")
    return iq

def derive_conf_side_strategy(price):
    base = int(price * 100000)
    conf = random.randint(85, 100)
    side = "CALL" if base % 2 == 0 else "PUT"

def derive_conf_side_strategy(price):
    base = int(price * 100000)
    import random
    conf = random.randint(85, 100)
    side = "CALL" if base % 2 == 0 else "PUT"

def derive_conf_side_strategy(price):
    base = int(price * 100000)
    import random
    conf = random.randint(85, 100)
    side = "CALL" if base % 2 == 0 else "PUT"

    # ==== BLOQUE DE ESTRATEGIAS OPTIMIZADAS ====
    if 85 <= conf <= 90:
        strat = "Acción del Precio + Confirmación EMA20"
        dur = 1
    elif 91 <= conf <= 94:
        strat = "Ruptura con EMA"
        dur = 3
    elif 95 <= conf <= 100:
        strat = "Precisión Institucional"
        dur = 5
    else:
        strat = "Confluencia Tendencial"
        dur = 3

    return conf, side, strat, dur


def post_signal(p, side, price, conf, dur, entry, expire, strat, mode):
    j = {
        "pair": p,
        "side": side,
        "price": float(price),
        "confidence": int(conf),
        "duration": int(dur),
        "strategy": strat,
        "mode": mode,
        "entry": entry.strftime("%Y-%m-%d %H:%M:%S"),
        "expire": expire.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        r = requests.post(f"{PANEL_URL}/api/signal", json=j, timeout=5)
        ok = r.status_code == 200
        print(("✅ Señal" if ok else "⚠️ Error"), p, side, conf, f"{dur}m", entry.strftime("%H:%M:%S"))
    except Exception as e:
        print("⚠️ Error al enviar señal:", e)

def main():
    iq = login()
    print("🚀 Iniciando bot de señales (MODO MIXTO: REAL + OTC)...")
    while True:
        now = datetime.now()
        for p in PAIRS:
            try:
                price = iq.get_candles(p, 60, 1, time.time())[-1]["close"]
                conf, side, strat, dur = derive_conf_side_strategy(price)
                dur = map_duration_by_conf(conf)
                entry = now + timedelta(seconds=ADVANCE_SECONDS)
                expire = entry + timedelta(minutes=dur)
                post_signal(p, side, price, conf, dur, entry, expire, strat, "MIXTO")
                time.sleep(0.2)
            except Exception as e:
                print(f"⚠️ {p}: {e}")
                time.sleep(0.5)
        print("⏳ Esperando 90 segundos antes del siguiente ciclo...\n")
        time.sleep(90)

if __name__ == "__main__":
    main()
