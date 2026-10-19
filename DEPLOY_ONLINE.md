# Pubblicare TAYARAN / AERO SPAZIO online

Questa cartella è pronta per essere caricata su GitHub e distribuita con Streamlit Community Cloud. L'indirizzo pubblico viene assegnato soltanto dopo aver autorizzato GitHub e premuto Deploy: non è possibile creare un URL pubblico senza accedere a un account di hosting.

## Passi minimi
1. Accedi a https://github.com/new e crea un repository privato chiamato `tayaran-engineering-academy`.
2. Carica i file di questa cartella nel repository (non caricare mai `.env`, `secrets.toml`, password, chiavi API o dati reali degli studenti).
3. Apri https://share.streamlit.io/ e autorizza GitHub.
4. Seleziona il repository, branch `main`, file `app.py`, quindi Deploy.
5. Nella sezione App settings / Secrets configura i segreti SMTP e `OPENAI_API_KEY` soltanto se li utilizzi.

## Importante prima di invitare studenti
Questo progetto usa file JSON locali per account e progressi. Su hosting gratuito i file possono non essere persistenti e questo non è adatto a un servizio pubblico multiutente con dati reali. Prima di invitare studenti, migrare gli account/progressi a un database persistente con access controls, aggiungere rate limiting e protezioni anti-abuso, verificare il flusso email, predisporre backup e testare la sicurezza. Non archiviare dati sensibili nei file del repository.

## Dominio
Il deployment crea un URL `*.streamlit.app`. Un dominio personalizzato richiede possedere/registrare il dominio e configurare DNS presso un provider compatibile.
