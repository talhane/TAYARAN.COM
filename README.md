# Engineering Academy

App didattica Python + Streamlit in italiano/inglese: meccanica, fluidodinamica, aerodinamica, lezioni, 60 esercizi numerici, vero/falso, soluzioni spiegate, esami, simulazioni Plotly, ala NACA 3D, sfide a punti, tutor (regole integrate e provider IA opzionale), aree studente/docente e spazio personale separato.

## Avvio
- Windows: doppio clic su `run.bat`
- macOS/Linux: `bash run.sh`
- Manuale: `pip install -r requirements.txt` e `streamlit run app.py`

Richiede Python 3.10+. L'app apre `http://localhost:8501`.

## Novità
- Menu principale in alto e interfaccia responsive per computer e cellulare.
- Arena sfide: sprint casuali, quiz vero/falso, maratona di cinque domande, punti, serie e storico.
- Area personale distinta dal corso tecnico: stato lavorativo, orario scolastico inserito dall'utente, piano suggerito, pianificazione interrogazioni e diario giornaliero annuale a partire dal 18 ottobre 2026, esportabile in CSV.
- I dati si salvano in `data/progress.json`; per scegliere un'altra cartella usa `EA_DATA_DIR`.

Le aree studente/docente sono viste locali e non rappresentano autenticazione sicura multiutente. Per risposte IA online serve configurare `OPENAI_API_KEY`; senza chiave il tutor integrato fornisce spiegazioni basilari. Le stime alari sono didattiche e non per progettazione reale.

## Test
`python tests/test_core.py`

## Account, accesso e amministrazione

- Al primo avvio, crea il primo account da una macchina fidata: il primo account diventa amministratore. Non esporre il sito a Internet prima di aver creato l'account amministratore.
- Gli studenti si registrano con la propria email e una password di almeno 10 caratteri contenente lettere e numeri. Le password sono salvate come hash PBKDF2, non in chiaro.
- Ogni account ha un file separato per i progressi di studio. L'admin può vedere email, ruolo, ultimo accesso, stato account, consensi e conteggio del progresso; non può vedere le password.
- La password si cambia in Impostazioni → Sicurezza account. Il recupero via email e la verifica email richiedono una configurazione SMTP esterna e non sono attivi per impostazione predefinita.
- Le opzioni di consenso non concedono accesso generale al telefono. Non è implementato alcun controllo remoto, lettura di messaggi o accesso automatico a foto/posizione. Ogni eventuale funzione futura deve chiedere un permesso specifico e revocabile.
- Prima di pubblicare su Internet, usare HTTPS, proteggere la cartella dati, configurare backup e un processo sicuro per il primo account amministratore. Il sistema di account locale è pensato per una prima versione personale/didattica, non è una certificazione di sicurezza per un servizio pubblico.

## TAYARAN.COM: email verification and deployment

- Branding/support contact: `TAYARAN.COM` / `khalidtalhane875@gmail.com`.
- The login flow sends a 6-digit email verification code after the password check. Configure these environment variables before using email verification:
  - `EA_SMTP_HOST`
  - `EA_SMTP_PORT` (usually `587`)
  - `EA_SMTP_USER`
  - `EA_SMTP_PASSWORD` (use an app password/secret, never commit it)
  - `EA_SMTP_FROM`
- If SMTP is not configured, email-code login intentionally fails closed. The first admin account must be created on a trusted machine and SMTP configured before relying on login.
- Language selector includes Italian, English, Arabic, Moroccan Darija, Spanish, French, German and Portuguese. The AI tutor uses the selected language when an AI API is configured; static interface translations are currently partial.
- The AI pricing page is informational only. No payments are processed until a payment provider (e.g. Stripe), server-side checkout, webhook verification, and secrets are configured.
- `TAYARAN.COM` is branding only in this project. To publish at that URL, register/control the domain, deploy to a hosting provider, configure DNS and HTTPS, and use persistent secure storage. This local Streamlit app does not make the domain live by itself.
- Do not put SMTP, OpenAI, or payment secrets in source code or commit them to version control.
