# Introduzione
- Questo custom component permette di recuperare le seguenti informazioni relative alle schede SIM dell'operatore <code>1nce</code>:
  - numero di MB (internet/dati) rimanenti; 
  - numero di MB totali previsti dal piano;
  - data di scadenza della SIM.
- Viene supportato il caso di 2 o più SIM (iccid) associate allo stesso account (username e password).
- Non è supportato il caso di 2 o più account.

# Installazione
- Creare la directory <code>custom_components</code> nella directory principale (quella che contiene il file <code>configuration.yaml</code>)
- Nella directory <code>custom_components</code>, creare la directory <code>sim_credit</code>
- Nella directory <code>1nce_account</code> copia i seguenti file:
  - <code>\_\_init.py\_\_</code>
  - <code>manifest.json</code>
- Riavviare Home Assistant
- Dopo aver riavviato Home Assistant, nel file <code>configuration.yaml</code> aggiungere le seguenti righe (e salvare):

```yaml
1nce_account:
  sim_iccids: !secret 1nce_account_sim_iccids
  username: !secret 1nce_account_username
  password: !secret 1nce_account_password
```

- Andare nel file <code>secrets.yaml</code> e aggiungere le seguenti righe (e salvare):

```yaml
1nce_username: "inserire-qui-la-username"  
1nce_password: "inserire-qui-la-password"
1nce_sim_iccids: 
  - "inserire-qui-il-iccid-della-sim-#1"
  - "inserire-qui-il-iccid-della-sim-#2" 
```

- Riavviare Home Assistant
- Dovrebbero comparire le seguenti terne di entità (una terna per ogni numero di telefono):
  - <code>1nce_account.\<iccid\>_volume</code> > MB rimasti
  - <code>1nce_account.\<iccid\>_expiry_date</code> > Data di scadenza della SIM
  - <code>1nce_account.\<iccid\>_total_volume</code> > MB totali della offerta

# Configurazione
- Di default, viene eseguito un aggiornamento dei dati ogni 15 minuti
- Si può personalizzare il periodo di aggiornamento dei dati, configurando il parametro <code>scan_interval</code> espresso in secondi:
```yaml
1nce_account:
  sim_iccids: !secret 1nce_account_sim_iccids
  username: !secret 1nce_account_username
  password: !secret 1nce_account_password
  scan_interval: 900
```

