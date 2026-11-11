import streamlit as st
import pandas as pd
import requests
import json, os
from datetime import datetime, timezone

st.set_page_config(page_title="AI Crypto Trader — Demo", page_icon="📊", layout="wide")
st.title("📊 AI Crypto Trader — Demo")
st.caption("Paper trading בלבד · nessun denaro reale · dati pubblici di mercato")

STARTING_CASH = 20.0
STATE_FILE = "portfolio.json"
SYMBOLS = ["BTCEUR", "ETHEUR", "BNBEUR", "SOLEUR", "XRPEUR"]

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"cash": STARTING_CASH, "positions": {}, "trades": [], "last_update": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

@st.cache_data(ttl=45)
def get_market():
    url = "https://api.binance.com/api/v3/ticker/price"
    r = requests.get(url, timeout=12)
    r.raise_for_status()
    rows = r.json()
    return {x["symbol"]: float(x["price"]) for x in rows if x["symbol"] in SYMBOLS}

@st.cache_data(ttl=90)
def get_candles(symbol):
    url = "https://api.binance.com/api/v3/klines"
    r = requests.get(url, params={"symbol": symbol, "interval": "1h", "limit": 60}, timeout=12)
    r.raise_for_status()
    data = r.json()
    return pd.DataFrame([{"close": float(x[4]), "volume": float(x[5])} for x in data])

def signal(symbol):
    df = get_candles(symbol)
    if len(df) < 30:
        return "ATTENDI", 0
    close = df["close"]
    fast = close.rolling(7).mean().iloc[-1]
    slow = close.rolling(25).mean().iloc[-1]
    momentum = (close.iloc[-1] / close.iloc[-8] - 1) * 100
    # Regola trasparente e deterministica: non è una previsione AI né una garanzia.
    if fast > slow and momentum > 0.4:
        return "POTENZIALE ACQUISTO", momentum
    if fast < slow and momentum < -0.4:
        return "DEBOLE", momentum
    return "ATTENDI", momentum

def execute_cycle(state, prices):
    # Demo volutamente conservativa: una sola posizione, importo fisso, stop simulato.
    for sym in list(state["positions"].keys()):
        pos = state["positions"][sym]
        price = prices.get(sym)
        if price is None:
            continue
        change = (price / pos["entry"] - 1) * 100
        if change <= -3.0 or change >= 5.0:
            proceeds = pos["qty"] * price
            pnl = proceeds - pos["cost"]
            state["cash"] += proceeds
            state["trades"].append({
                "ora": datetime.now(timezone.utc).isoformat(),
                "simbolo": sym, "azione": "VENDITA DEMO",
                "prezzo": price, "pnl_eur": round(pnl, 4),
                "motivo": "stop -3%" if change <= -3.0 else "target +5%"
            })
            del state["positions"][sym]

    if not state["positions"] and state["cash"] >= 2.0:
        for sym in SYMBOLS:
            try:
                label, mom = signal(sym)
            except Exception:
                continue
            if label == "POTENZIALE ACQUISTO" and sym in prices:
                cost = 2.0
                qty = cost / prices[sym]
                state["cash"] -= cost
                state["positions"][sym] = {"entry": prices[sym], "qty": qty, "cost": cost}
                state["trades"].append({
                    "ora": datetime.now(timezone.utc).isoformat(),
                    "simbolo": sym, "azione": "ACQUISTO DEMO",
                    "prezzo": prices[sym], "pnl_eur": 0.0,
                    "motivo": f"media 7h sopra 25h; momentum {mom:.2f}%"
                })
                break
    state["last_update"] = datetime.now(timezone.utc).isoformat()
    return state

state = load_state()
col_a, col_b, col_c = st.columns(3)
try:
    prices = get_market()
    equity = state["cash"] + sum(p["qty"] * prices.get(s, p["entry"]) for s,p in state["positions"].items())
    pnl_total = equity - STARTING_CASH
    col_a.metric("Capitale iniziale", "€20,00")
    col_b.metric("Patrimonio demo", f"€{equity:.2f}", f"{pnl_total:+.2f} €")
    col_c.metric("Liquidità", f"€{state['cash']:.2f}")
    st.info("I prezzi sono pubblici e possono avere ritardi o indisponibilità. I risultati sono simulati.")
    if st.button("▶ Esegui un ciclo di analisi", type="primary"):
        state = execute_cycle(state, prices)
        save_state(state)
        st.rerun()
    st.subheader("Mercato")
    market_rows = []
    for sym in SYMBOLS:
        try:
            label, mom = signal(sym)
        except Exception:
            label, mom = "DATI NON DISPONIBILI", 0
        market_rows.append({"Asset": sym.replace("EUR",""), "Prezzo (€)": prices.get(sym), "Segnale tecnico": label, "Momentum 7h": f"{mom:+.2f}%"})
    st.dataframe(pd.DataFrame(market_rows), use_container_width=True, hide_index=True)
    st.subheader("Posizioni aperte")
    if state["positions"]:
        rows=[]
        for sym,p in state["positions"].items():
            mark=prices.get(sym,p["entry"])
            rows.append({"Asset":sym,"Ingresso":p["entry"],"Prezzo":mark,"Quantità":p["qty"],"P/L non realizzato (€)":p["qty"]*mark-p["cost"]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.write("Nessuna posizione aperta.")
    st.subheader("Storico operazioni")
    if state["trades"]:
        st.dataframe(pd.DataFrame(state["trades"]).iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.write("Ancora nessuna operazione.")
    st.caption(f"Ultimo ciclo: {state.get('last_update') or 'mai'} · UTC")
except Exception as e:
    st.error(f"Non riesco a recuperare i dati di mercato: {e}")
    st.warning("Riprova più tardi. Nessuna operazione reale viene eseguita.")

with st.expander("⚙️ Controlli e limiti"):
    st.write("""
    - Capitale simulato iniziale: 20 €.
    - Acquisto simulato: 2 € per operazione.
    - Una posizione alla volta.
    - Uscita simulata: stop -3% oppure obiettivo +5%.
    - Segnale basato su media mobile 7h/25h e momentum; non è una vera IA predittiva.
    - Il pulsante esegue un singolo ciclo: non è un servizio H24 e non lavora in background quando la pagina è inattiva.
    - Commissioni, spread, slippage, tasse e rischio di esecuzione non sono ancora modellati in modo completo.
    """)

if st.button("♻️ Azzera simulazione e riparti da 20 €"):
    state = {"cash": STARTING_CASH, "positions": {}, "trades": [], "last_update": None}
    save_state(state)
    st.rerun()
