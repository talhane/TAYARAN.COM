"""SMTP email verification. Configure EA_SMTP_HOST/PORT/USER/PASSWORD/FROM in environment."""
import os, smtplib, secrets
from email.message import EmailMessage

def smtp_configured():
    return all(os.environ.get(k) for k in ('EA_SMTP_HOST','EA_SMTP_USER','EA_SMTP_PASSWORD','EA_SMTP_FROM'))

def make_code():
    return f'{secrets.randbelow(1_000_000):06d}'

def send_code(recipient, code, purpose='accesso'):
    if not smtp_configured():
        return False, 'Verifica email non configurata: imposta EA_SMTP_HOST, EA_SMTP_PORT, EA_SMTP_USER, EA_SMTP_PASSWORD ed EA_SMTP_FROM.'
    msg=EmailMessage()
    msg['Subject']='TAYARAN.COM — codice di verifica'
    msg['From']=os.environ['EA_SMTP_FROM']; msg['To']=recipient
    msg.set_content(f'Il tuo codice di verifica per {purpose} su TAYARAN.COM è: {code}\n\nScade dopo 10 minuti. Se non hai richiesto questo codice, ignora questa email.')
    try:
        host=os.environ['EA_SMTP_HOST']; port=int(os.environ.get('EA_SMTP_PORT','587'))
        with smtplib.SMTP(host,port,timeout=15) as server:
            server.starttls(); server.login(os.environ['EA_SMTP_USER'],os.environ['EA_SMTP_PASSWORD']); server.send_message(msg)
        return True, 'Codice inviato.'
    except Exception:
        return False, 'Invio email non riuscito. Controlla le impostazioni SMTP e riprova.'
