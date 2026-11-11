import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(page_title="AI Crypto Trader Demo", page_icon="📊")
st.title("📊 AI Crypto Trader — Demo")
st.caption("Paper trading | nessun denaro reale | dati pubblici di mercato")

STARTING_CASH = 20.0
STATE_FILE = "portfolio.json"
COINS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana"
}

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"cash": STARTING_CASH, "positions": {}, "history": []}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

@st.cache_data(ttl=60)
def get_market_data():
    ids = ",".join(COINS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    
    prices = {}
    changes = {}
    for sym, cg_id in COINS.items():
        if cg_id in data:
            prices[sym] = float(data[cg_id].get("usd", 0.0))
            changes[sym] = float(data[cg_id].get("usd_24h_change", 0.0))
    return prices, changes

def classify_signal(change_24h):
    if change_24h >= 2.5:
        return "POTENZIALE RIALZO", "green"
    elif change_24h <= -2.5:
        return "DEBOLE", "red"
    return "ATTESA", "gray"

def execute_simulation(state, prices, changes):
    trades = []
    # Gestione posizioni aperte
    for sym in list(state["positions"].keys()):
        pos = state["positions"][sym]
        curr_p = prices.get(sym)
        if not curr_p:
            continue
        entry_p = pos["entry_price"]
        pnl_pct = ((curr_p - entry_p) / entry_p) * 100
        
        # Stop loss a -1% o Take profit a +2%
        if pnl_pct <= -1.0 or pnl_pct >= 2.0:
            proceeds = pos["qty"] * curr_p
            state["cash"] += proceeds
            trades.append(f"Chiusa posizione {sym}: PnL {pnl_pct:+.2f}%")
            state["history"].append({
                "action": "SELL",
                "symbol": sym,
                "price": curr_p,
                "pnl_pct": pnl_pct
            })
            del state["positions"][sym]
            
    # Apertura nuove posizioni se c'è liquidità (max 2 posizioni)
    if len(state["positions"]) < 2 and state["cash"] >= 2.0:
        for sym, chg in changes.items():
            if sym not in state["positions"] and chg >= 2.5:
                curr_p = prices.get(sym)
                if curr_p and curr_p > 0:
                    invest = min(2.0, state["cash"])
                    qty = invest / curr_p
                    state["cash"] -= invest
                    state["positions"][sym] = {
                        "qty": qty,
                        "entry_price": curr_p
                    }
                    trades.append(f"Aperta posizione {sym} a {curr_p:.2f} $")
                    state["history"].append({
                        "action": "BUY",
                        "symbol": sym,
                        "price": curr_p
                    })
                    break
    save_state(state)
    return trades

state = load_state()

col_btn, _ = st.columns([1, 2])
with col_btn:
    refresh = st.button("🔄 Analizza mercato ed Esegui")

try:
    prices, changes = get_market_data()
    
    # Valore portafoglio
    pos_val = sum(pos["qty"] * prices.get(sym, pos["entry_price"]) for sym, pos in state["positions"].items())
    total_val = state["cash"] + pos_val
    delta = total_val - STARTING_CASH
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Capitale Totale", f"{total_val:.2f} $", f"{delta:+.2f} $")
    m2.metric("Liquidità Residua", f"{state['cash']:.2f} $")
    m3.metric("Posizioni Aperte", f"{len(state['positions'])} / 2")
    
    if refresh:
        results = execute_simulation(state, prices, changes)
        if results:
            for r in results:
                st.info(r)
        else:
            st.write("Nessuna operazione necessaria in questo ciclo.")
            
    st.subheader("Mercati monitorati")
    market_rows = []
    for sym in COINS:
        p = prices.get(sym, 0.0)
        c = changes.get(sym, 0.0)
        sig, _ = classify_signal(c)
        market_rows.append({"Asset": sym, "Prezzo ($)": f"{p:.2f}", "Var. 24h": f"{c:+.2f}%", "Segnale": sig})
    st.dataframe(pd.DataFrame(market_rows), use_container_width=True)
    
    st.subheader("Posizioni correnti")
    if state["positions"]:
        pos_rows = []
        for sym, d in state["positions"].items():
            curr = prices.get(sym, d["entry_price"])
            pnl = ((curr - d["entry_price"]) / d["entry_price"]) * 100
            pos_rows.append({
                "Asset": sym,
                "Prezzo Carico ($)": f"{d['entry_price']:.2f}",
                "Prezzo Attuale ($)": f"{curr:.2f}",
                "PnL": f"{pnl:+.2f}%"
            })
        st.dataframe(pd.DataFrame(pos_rows), use_container_width=True)
    else:
        st.write("Nessuna posizione aperta al momento.")
        
except Exception as e:
    st.error(f"Errore nel recupero dati: {e}")
    st.warning("Riprova tra poco.")

with st.expander("⚙️ Controlli e Regole"):
    st.markdown("""
    - **Capitale iniziale:** 20.00 $
    - **Importo ordine:** 2.00 $
    - **Posizioni contemporanee massime:** 2
    - **Stop loss:** -1.0% | **Take profit:** +2.0%
    - **Trigger acquisto:** Variazione 24h >= +2.5%
    """)

if st.button("♻️ Azzera simulazione e riparti da 20 $"):
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    st.rerun()
