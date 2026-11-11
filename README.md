# AI Crypto Trader — Demo

Dashboard web per paper trading: usa solo prezzi pubblici e simula operazioni con un capitale virtuale di 20 €.

## Avvio locale
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pubblicazione cloud da smartphone
1. Crea un account GitHub e un repository pubblico chiamato `ai-crypto-trader-demo`.
2. Carica `app.py`, `requirements.txt` e `README.md` nel repository.
3. Apri https://share.streamlit.io/ e accedi con GitHub.
4. Seleziona il repository, branch `main`, file principale `app.py`.
5. Premi Deploy. Apri il link generato dal browser del telefono.

## Importante
- È solo una demo: non effettua ordini e non richiede API key.
- Il pulsante avvia un singolo ciclo di analisi; non è un bot H24.
- Streamlit Community Cloud può sospendere le app inattive; per automazione continua servirebbe un servizio cloud sempre attivo e un processo separato.
- Non usare denaro reale sulla base dei risultati della demo. Una simulazione non prova che una strategia sarà profittevole.
- I dati di mercato provengono dall'endpoint pubblico Binance; l'accessibilità può variare.
