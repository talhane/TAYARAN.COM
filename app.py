from __future__ import annotations
import os, sys, json, math, io, zipfile, secrets
from html import escape as html_escape
from pathlib import Path
from datetime import date, datetime, timedelta
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from ea.content import LESSONS, EXERCISES, SUBJECTS
from ea.storage import load_progress, save_progress, export_progress
from ea import auth as auth_system
from ea.wing3d import build_wing, wing_estimates, stl_bytes
from ea.sims import projectile_plot, spring_plot, venturi_plot, moody_plot, cylinder_plot, airfoil_plot
from ea.i18n import T
from ea.style import CSS

st.set_page_config(page_title="TAYARAN.COM · Engineering Academy", page_icon="🛠️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="ea-space-decoration" aria-hidden="true"></div>', unsafe_allow_html=True)

# --- Secure sign-in gate: each account gets separate study progress. ---
def show_auth_gate():
    from ea.emailer import make_code, send_code
    st.markdown("""<div class="ea-login-hero"><div class="ea-login-orb">✦</div><div class="ea-profile-kicker">TAYARAN.COM · TRADING TERMINAL · SPACE LEARNING</div><h1>TAYARAN.COM</h1><p>Uno spazio di studio personale, protetto e multilingue.</p><div class="ea-profile-tags"><span>🔐 Account individuale</span><span>📈 Progresso personale</span><span>🌌 Space & Ocean</span></div></div>""", unsafe_allow_html=True)
    accounts = auth_system.list_accounts()
    if not accounts:
        st.warning("Primo avvio: il primo account creato diventa amministratore. Crea questo account solo tu, su un computer controllato, prima di condividere il sito con altri.")
    login_tab, register_tab = st.tabs(["🔑 Accedi", "✦ Crea account"])
    with login_tab:
        with st.form("ea_login_form"):
            email = st.text_input("Email", placeholder="nome@esempio.it")
            password = st.text_input("Password", type="password", placeholder="La tua password")
            submitted = st.form_submit_button("Entra in Engineering Academy", type="primary", use_container_width=True)
        if submitted:
            user = auth_system.authenticate(email, password)
            if user:
                code = make_code()
                ok, msg = send_code(email.strip().lower(), code, 'accesso')
                if ok:
                    st.session_state.ea_pending_login = {'email': email.strip().lower(), 'code': code, 'expires': datetime.now().timestamp()+600, 'user': user}
                    st.success('Codice di verifica inviato alla tua email. Inseriscilo qui sotto (scade in 10 minuti).')
                else:
                    st.error(msg)
            else:
                st.error("Email o password non corretti, oppure account disabilitato.")
        pending = st.session_state.get('ea_pending_login')
        if pending:
            with st.form('ea_email_otp_form'):
                otp = st.text_input('Codice di verifica email', max_chars=6, placeholder='123456')
                verify = st.form_submit_button('Verifica e accedi', type='primary', use_container_width=True)
            if verify:
                if datetime.now().timestamp() > pending['expires']:
                    st.session_state.pop('ea_pending_login', None); st.error('Codice scaduto. Accedi di nuovo per riceverne uno nuovo.')
                elif secrets.compare_digest(str(otp).strip(), pending['code']):
                    st.session_state.ea_user = pending['user']; st.session_state.pop('ea_pending_login', None); st.session_state.pop('progress', None); st.rerun()
                else:
                    st.error('Codice non corretto.')
    with register_tab:
        with st.form("ea_register_form"):
            name = st.text_input("Nome visualizzato", placeholder="Il tuo nome")
            email_new = st.text_input("La tua email", placeholder="nome@esempio.it", key="ea_reg_email")
            password_new = st.text_input("Crea una password", type="password", help="Almeno 10 caratteri, una lettera e un numero.", key="ea_reg_pw")
            password_confirm = st.text_input("Conferma password", type="password", key="ea_reg_pw2")
            rules = st.checkbox("Accetto le regole del sito e l'informativa privacy. Capisco che ogni condivisione di dati è facoltativa e revocabile.")
            submitted_reg = st.form_submit_button("Crea il mio account", type="primary", use_container_width=True)
        if submitted_reg:
            if password_new != password_confirm:
                st.error("Le due password non coincidono.")
            elif not rules:
                st.error("Devi accettare le regole e l'informativa privacy.")
            elif auth_system.account_exists(email_new):
                st.error("Esiste già un account con questa email.")
            elif not auth_system.password_ok(password_new):
                st.error("La password deve avere almeno 10 caratteri, una lettera e un numero.")
            else:
                code = make_code()
                ok, msg = send_code(email_new.strip().lower(), code, 'verifica account')
                if ok:
                    st.session_state.ea_pending_register = {'email':email_new.strip().lower(), 'password':password_new, 'name':name, 'rules':rules, 'code':code, 'expires':datetime.now().timestamp()+600}
                    st.success("Ti abbiamo inviato un codice email. Verificalo qui sotto per completare la registrazione.")
                else:
                    st.error(msg)
        pending_reg = st.session_state.get('ea_pending_register')
        if pending_reg:
            with st.form('ea_register_otp_form'):
                reg_otp = st.text_input('Codice per verificare la tua email', max_chars=6, placeholder='123456')
                verify_reg = st.form_submit_button('Verifica email e crea account', type='primary', use_container_width=True)
            if verify_reg:
                if datetime.now().timestamp() > pending_reg['expires']:
                    st.session_state.pop('ea_pending_register', None); st.error('Codice scaduto. Ricomincia la registrazione.')
                elif secrets.compare_digest(str(reg_otp).strip(), pending_reg['code']):
                    ok, result = auth_system.register(pending_reg['email'], pending_reg['password'], pending_reg['name'], pending_reg['rules'])
                    st.session_state.pop('ea_pending_register', None)
                    if ok:
                        user = auth_system.authenticate(pending_reg['email'], pending_reg['password'])
                        st.session_state.ea_user = user; st.session_state.pop('progress', None); st.success('Email verificata. Account creato!'); st.rerun()
                    else: st.error(result)
                else:
                    st.error('Codice non corretto.')
    st.caption("Le password sono conservate come hash; l'app non legge né controlla il telefono. Per l'accesso da Internet usa HTTPS e un hosting sicuro.")

if "ea_user" not in st.session_state or not st.session_state.ea_user:
    show_auth_gate()
    st.stop()
CURRENT_USER = st.session_state.ea_user
USER_EMAIL = CURRENT_USER["email"]
USER_KEY = auth_system.user_key(USER_EMAIL)

def get_progress(user_key):
    return load_progress(user_key)

if "progress" not in st.session_state:
    st.session_state.progress = get_progress(USER_KEY)
if "lang" not in st.session_state: st.session_state.lang = "it"
if "page" not in st.session_state: st.session_state.page = "dashboard"
P = st.session_state.progress
L = st.session_state.lang

def tr(it, en):
    if L == "it": return it
    if L == "ar":
        known={"📊 Home":"📊 الرئيسية","📅 Oggi":"📅 اليوم","📚 Lezioni":"📚 الدروس","✏️ Esercizi":"✏️ التمارين","🏆 Sfide":"🏆 التحديات","🎓 Esami":"🎓 الاختبارات","📈 Simulazioni":"📈 المحاكاة","🛠️ Ala 3D":"🛠️ جناح ثلاثي الأبعاد","🎒 Studente":"🎒 الطالب","🧑‍🏫 Docente":"🧑‍🏫 الأستاذ","🤖 Tutor IA":"🤖 مساعد الذكاء الاصطناعي","⚙️ Impostazioni":"⚙️ الإعدادات","Scegli una sezione":"اختر قسماً","Lezioni completate":"الدروس المكتملة","Progresso corso":"تقدم الدورة"}
        return known.get(it, en)
    if L == "ary":
        known={"📊 Home":"📊 الرئيسية","📅 Oggi":"📅 اليوم","📚 Lezioni":"📚 الدروس","✏️ Esercizi":"✏️ التمارين","🏆 Sfide":"🏆 التحديات","🎓 Esami":"🎓 الامتحانات","🤖 Tutor IA":"🤖 مساعد ذكي","⚙️ Impostazioni":"⚙️ الإعدادات","Scegli una sezione":"ختار شي قسم","Lezioni completate":"الدروس اللي كملتي"}
        return known.get(it, en)
    return en
def persist():
    save_progress(P, USER_KEY)
    st.session_state.progress = P

def mark_lesson(lesson_id):
    if lesson_id not in P.setdefault("completed_lessons", []):
        P["completed_lessons"].append(lesson_id); persist()

def sidebar():
    # Impostazioni essenziali nella barra laterale; navigazione principale in alto.
    with st.sidebar:
        st.title("🛠️ Engineering Academy")
        st.caption(tr("Impara con calma, un passo alla volta.", "Learn at your own pace, one step at a time."))
        st.session_state.lang = st.selectbox("Lingua / Language / اللغة", ["it", "en", "ar", "ary", "es", "fr", "de", "pt"], format_func=lambda x: {"it":"🇮🇹 Italiano","en":"🇬🇧 English","ar":"🇸🇦 العربية","ary":"🇲🇦 الدارجة المغربية","es":"🇪🇸 Español","fr":"🇫🇷 Français","de":"🇩🇪 Deutsch","pt":"🇵🇹 Português"}[x], index=["it", "en", "ar", "ary", "es", "fr", "de", "pt"].index(st.session_state.lang) if st.session_state.lang in ["it", "en", "ar", "ary", "es", "fr", "de", "pt"] else 0)
        st.divider()
        st.metric(tr("Lezioni completate", "Lessons completed"), f"{len(P.get('completed_lessons', []))}/{len(LESSONS)}")
        st.progress(len(P.get('completed_lessons', []))/max(1,len(LESSONS)))
        st.caption(f"👤 {CURRENT_USER.get('display_name', USER_EMAIL)} · {CURRENT_USER.get('role', 'student').upper()}")
        if st.button("Esci / Logout", use_container_width=True):
            st.session_state.pop("ea_user", None); st.session_state.pop("progress", None); st.rerun()

sidebar()
L = st.session_state.lang
pages = [
    ("dashboard", "📊 Home"), ("today", tr("📅 Oggi", "📅 Today")),
    ("subjects", "🧠 Materie"), ("subject_detail", "📘 Scheda materia"), ("lessons", tr("📚 Lezioni", "📚 Lessons")), ("exercises", tr("✏️ Esercizi", "✏️ Exercises")),
    ("challenge", tr("🏆 Sfide", "🏆 Challenges")), ("exams", tr("🎓 Esami", "🎓 Exams")),
    ("simulations", tr("📈 Simulazioni", "📈 Simulations")), ("wing", tr("🛠️ Ala 3D", "🛠️ 3D wing")),
    ("student", tr("🎒 Studente", "🎒 Student")), ("teacher", tr("🧑‍🏫 Docente", "🧑‍🏫 Teacher")),
    ("assistant", tr("🤖 Tutor IA", "🤖 AI tutor")),
    ("settings", tr("⚙️ Impostazioni", "⚙️ Settings"))]
if CURRENT_USER.get("role") == "admin":
    pages.extend([("life", "🌱 Vita personale"), ("profile", "👤 Khalid Talhane"), ("admin", "🛡️ Admin")])
pages.append(("support", "💬 Supporto / Support"))
pages.append(("plans", "✨ Piani AI / AI plans"))
labels=[x[1] for x in pages]
current=next((x[1] for x in pages if x[0]==st.session_state.page), labels[0])
with st.container(key="ea_topnav"):
    st.caption(tr("✦ MENU SPAZIALE · SEMPRE A PORTATA DI MANO", "✦ SPACE NAVIGATION · ALWAYS WITH YOU"))
    selected_label=st.radio(tr("Scegli una sezione", "Choose a section"), labels, index=labels.index(current), horizontal=True, label_visibility="collapsed", key="top_navigation")
st.session_state.page=next(x[0] for x in pages if x[1]==selected_label)
page=st.session_state.page

page = st.session_state.page
st.title({"dashboard":tr("📊 La tua accademia", "📊 Your academy"),"subjects":"🧠 Materie · Ragioneria quinta superiore","subject_detail":"📘 Laboratorio della materia","today":tr("📅 Lezione di oggi", "📅 Today's lesson"),"lessons":tr("📚 Percorso didattico", "📚 Learning path"),"exercises":tr("✏️ Allenamento numerico", "✏️ Numerical practice"),"exams":tr("🎓 Esami", "🎓 Exams"),"simulations":tr("📈 Laboratorio di simulazione", "📈 Simulation lab"),"wing":tr("🛠️ Progetto 3D: ala NACA", "🛠️ 3D project: NACA wing"),"settings":tr("⚙️ Impostazioni", "⚙️ Settings"),"student":tr("🎓 Area studente", "🎓 Student area"),"teacher":tr("🧑‍🏫 Area docente", "🧑‍🏫 Teacher area"),"assistant":tr("🤖 Assistente IA", "🤖 AI assistant"),"challenge":tr("🏆 Arena delle sfide", "🏆 Challenge arena"),"life":tr("🌱 La mia vita personale", "🌱 My personal life"),"profile":"👤 Khalid Talhane", "admin":"🛡️ Pannello amministratore", "support":"💬 Supporto TAYARAN.COM", "plans":"✨ Piani AI"}[page])
st.markdown(f'<div class="ea-hero"><div class="ea-orbit">✦　✧　◉　✧</div><h3 style="color:white;margin:0">{tr("Impara, prova, visualizza, migliora.","Learn, practise, visualise, improve.")}</h3><p style="margin:.4rem 0 0">{tr("Un laboratorio immersivo tra spazio, aerodinamica 3D e oceano di idee.", "An immersive lab between space, 3D aerodynamics and an ocean of ideas.")}</p><span class="ea-chip">🪐 {len(LESSONS)} {tr("lezioni","lessons")}</span><span class="ea-chip">🌊 {len(EXERCISES)} {tr("esercizi numerici","numerical exercises")}</span><span class="ea-chip">🚀 30+ {tr("quiz vero/falso","true/false quizzes")}</span></div>', unsafe_allow_html=True)

SCHOOL_SUBJECTS = {
 "Italiano":{"icon":"📜","theme":"linear-gradient(135deg,#2b164b,#a64b78,#f0a6ca)","topics":["Poesia: parafrasi, figure retoriche e metrica","Dante: Divina Commedia e contesto","Leopardi: pessimismo e poetica","Verismo: Verga e impersonalità","Decadentismo: Pascoli e D’Annunzio","Novecento: Ungaretti, Montale, Quasimodo","Analisi del testo e tipologia A","Tema argomentativo e tipologia B"]},
 "Economia politica":{"icon":"📈","theme":"linear-gradient(135deg,#092c43,#087e8b,#57d5c5)","topics":["Domanda, offerta ed equilibrio","Forme di mercato","PIL e crescita economica","Inflazione e disoccupazione","Politica fiscale e monetaria","Bilancio dello Stato","Commercio internazionale","Unione europea e BCE"]},
 "Diritto":{"icon":"⚖️","theme":"linear-gradient(135deg,#192c52,#4568a8,#9ec5fe)","topics":["Costituzione italiana e principi fondamentali","Organi costituzionali","Parlamento e formazione delle leggi","Governo e Presidente della Repubblica","Magistratura e Corte costituzionale","Unione europea","Pubblica amministrazione","Contratti e obbligazioni: ripasso"]},
 "Informatica":{"icon":"💻","theme":"linear-gradient(135deg,#111827,#4338ca,#22d3ee)","topics":["Basi di dati e modello relazionale","SQL: SELECT, JOIN e GROUP BY","Reti e protocolli","Sicurezza informatica","Sistemi informativi aziendali","Progettazione di un database","Algoritmi e diagrammi di flusso","Esercizi pratici e casi aziendali"]},
 "Economia aziendale":{"icon":"💼","theme":"linear-gradient(135deg,#18392d,#23865b,#b4e197)","topics":["Bilancio d’esercizio","Stato patrimoniale e conto economico","Analisi per indici","Analisi per flussi e rendiconto finanziario","Contabilità generale e scritture di assestamento","Imposte e fiscalità d’impresa","Pianificazione e controllo di gestione","Business plan e budget"]},
 "Scienze motorie":{"icon":"🏃","theme":"linear-gradient(135deg,#3d1b42,#a33b73,#f9a8d4)","topics":["Apparato cardiovascolare e respiratorio","Allenamento e principi del carico","Forza, resistenza, velocità e flessibilità","Alimentazione e idratazione","Prevenzione degli infortuni","Salute e stili di vita","Sport e fair play","Primo soccorso: concetti fondamentali"]},
 "Matematica":{"icon":"📐","theme":"linear-gradient(135deg,#14213d,#0077b6,#90e0ef)","topics":["Funzioni e dominio","Limiti e continuità","Derivate e significato geometrico","Studio di funzione","Integrali: concetti base","Probabilità e statistica","Matematica finanziaria","Esercizi guidati per la maturità"]},
 "Religione":{"icon":"🕊️","theme":"linear-gradient(135deg,#40351d,#a88b4a,#f5e6a8)","topics":["Etica e responsabilità","Libertà e coscienza","Dialogo tra culture e religioni","Persona e dignità umana","Etica del lavoro","Scienza e responsabilità","Solidarietà e cittadinanza","Discussione argomentata"]},
 "Storia":{"icon":"🏛️","theme":"linear-gradient(135deg,#422006,#a16207,#facc15)","topics":["Seconda rivoluzione industriale","Imperialismo e nazionalismi","Prima guerra mondiale","Rivoluzione russa","Fascismo e nazismo","Seconda guerra mondiale e Shoah","Guerra fredda","Italia repubblicana ed Europa"]},
 "Inglese":{"icon":"🌍","theme":"linear-gradient(135deg,#172554,#1d4ed8,#93c5fd)","topics":["Business correspondence","Company structures","Marketing and advertising","Banking and finance","Globalisation and trade","Job applications and CV","Grammar: conditionals and passive","Oral presentation practice"]}
}

def open_subject(subject):
    st.session_state.school_subject = subject
    st.session_state.page = "subject_detail"
    st.rerun()

if page == "subjects":
    st.markdown("### 🧭 Il tuo percorso · Ragioneria, quinto superiore")
    st.caption("Ogni materia ha tre aree distinte: corsi, sfide ed esercizi. Gli argomenti sono una base di ripasso: confrontali sempre con il programma del tuo docente.")
    cols=st.columns(2)
    for i,(name,data) in enumerate(SCHOOL_SUBJECTS.items()):
        with cols[i%2]:
            done=P.setdefault("school_topics_done",{}).get(name,[])
            pct=round(100*len(done)/len(data["topics"]))
            st.markdown(f'''<div style="background:{data['theme']};padding:18px;border-radius:16px;color:white;margin:6px 0;min-height:100px;box-shadow:0 8px 25px #0004"><div style="font-size:28px">{data['icon']}</div><div style="font-size:20px;font-weight:700">{name}</div><div style="opacity:.9">{len(data['topics'])} unità · corsi · sfide · esercizi</div></div>''',unsafe_allow_html=True)
            st.progress(pct/100,text=f"Progresso {pct}%")
            if st.button(f"Apri {name} →",key=f"open_subject_{i}",use_container_width=True): open_subject(name)
    st.info("📜 Per Italiano trovi anche un percorso specifico per memorizzare e recitare le poesie.")

elif page == "subject_detail":
    names=list(SCHOOL_SUBJECTS)
    chosen=st.session_state.get("school_subject", "Italiano")
    chosen=st.selectbox("Scegli materia",names,index=names.index(chosen) if chosen in names else 0,key="subject_detail_selector")
    st.session_state.school_subject=chosen
    data=SCHOOL_SUBJECTS[chosen]
    st.markdown(f'''<div style="background:{data['theme']};padding:22px;border-radius:18px;color:white;box-shadow:0 10px 30px #0004"><div style="font-size:38px">{data['icon']}</div><h2 style="color:white;margin:0">{chosen}</h2><p>Il tuo laboratorio personale · corso, sfide, esercizi e progresso</p></div>''',unsafe_allow_html=True)
    topics=data["topics"]
    completed=P.setdefault("school_topics_done",{}).setdefault(chosen,[])
    st.progress(len(completed)/len(topics),text=f"Progresso materia: {round(100*len(completed)/len(topics))}% · {len(completed)}/{len(topics)} unità")
    tcourse, tchallenges, texercises, tprogress = st.tabs(["📚 CORSI", "🏆 SFIDE", "✏️ ESERCIZI", "📈 PROGRESSO"])
    with tcourse:
        topic=st.selectbox("Unità da studiare",topics,key=f"topic_{chosen}")
        st.markdown(f"#### {data['icon']} {topic}")
        if chosen=="Italiano" and topic.startswith("Poesia"):
            st.markdown("**Metodo in 6 passaggi per imparare una poesia**")
            st.markdown("1. **Capisci:** leggi ad alta voce e scrivi in prosa il significato di ogni strofa.\n2. **Dividi:** spezza il testo in blocchi di 2–4 versi e assegna a ciascuno un'immagine mentale.\n3. **Ascolta:** leggi con ritmo e pause, registrandoti se ti aiuta.\n4. **Richiamo attivo:** copri il testo e prova a recitare; controlla solo dopo il tentativo.\n5. **Ripetizione dilazionata:** ripassa dopo 10 minuti, la sera, il giorno dopo, dopo 3 giorni e dopo una settimana.\n6. **Spiega:** presenta autore, contesto, tema, parafrasi, figure retoriche e messaggio senza leggere.")
            poem=st.text_area("Incolla qui la poesia o i versi assegnati (facoltativo)",height=130,key="poem_text")
            if poem.strip():
                st.write("**Allenamento rapido**")
                st.write("• Riassumi ogni strofa in una frase. • Evidenzia parole-chiave e immagini. • Prova a recitare senza guardare.")
                st.text_area("Scrivi la parafrasi con parole tue",key="poem_paraphrase")
                st.text_area("Autore, tema e 2 figure retoriche",key="poem_analysis")
        else:
            st.write(f"**Obiettivo:** saper definire l'argomento, spiegarlo con parole tue, applicarlo a un esempio e rispondere a domande orali.")
            st.write("**Metodo:** 1) leggi 10–15 minuti; 2) chiudi il libro e ricostruisci i concetti; 3) crea 5 parole chiave; 4) fai un esempio; 5) rispondi ad alta voce.")
        st.text_area("I miei appunti",key=f"notes_{chosen}_{topics.index(topic)}",placeholder="Scrivi definizioni, esempi, formule, date o domande da chiarire…")
        if st.button("✓ Segna unità completata",key=f"complete_{chosen}_{topics.index(topic)}"):
            if topic not in completed: completed.append(topic)
            persist(); st.success("Progresso salvato!"); st.rerun()
        if st.button("🤖 Chiedi all'AI di spiegare questa unità",key=f"ai_{chosen}_{topics.index(topic)}"):
            st.session_state.ai_prefill=f"Materia: {chosen}. Argomento: {topic}. Spiegamelo in modo semplice, crea appunti, 5 domande con risposte e una mini sfida. Rispondi nella lingua selezionata."
            st.session_state.page="assistant"; st.rerun()
    with tchallenges:
        st.markdown("### 🚀 Sfida a livelli")
        st.write("**Livello 1 · Esploratore:** spiega l'argomento in 30 secondi senza appunti.")
        st.write("**Livello 2 · Analista:** scrivi 5 parole chiave e collegale tra loro.")
        st.write("**Livello 3 · Maestro:** fai un esempio concreto e rispondi a 3 domande senza consultare il libro.")
        challenge_answer=st.text_area("La tua risposta alla sfida",key=f"challenge_answer_{chosen}")
        if st.button("Salva tentativo",key=f"challenge_save_{chosen}"):
            P.setdefault("school_challenges",[]).append({"subject":chosen,"answer":challenge_answer,"date":date.today().isoformat()}); persist(); st.success("Tentativo salvato!")
    with texercises:
        st.markdown("### ✏️ Allenamento pratico")
        st.write("1. Definisci l'argomento in massimo 3 frasi.\n2. Scrivi un esempio o un caso concreto.\n3. Crea una domanda difficile e rispondi senza appunti.\n4. Elenca un errore comune e correggilo.")
        answer=st.text_area("Svolgi qui gli esercizi",key=f"subject_exercises_{chosen}")
        if st.button("Salva esercizi",key=f"save_exercises_{chosen}"):
            P.setdefault("school_exercise_work",{})[chosen]={"answer":answer,"date":date.today().isoformat()}; persist(); st.success("Esercizi salvati!")
    with tprogress:
        st.metric("Unità completate",f"{len(completed)}/{len(topics)}")
        for topic_item in topics:
            st.write(("✅ " if topic_item in completed else "◯ ")+topic_item)

if page == "dashboard":
    done = set(P.get("completed_lessons", [])); exdone = P.get("exercise_results", {})
    c1,c2,c3,c4 = st.columns(4)
    c1.metric(tr("Progresso corso", "Course progress"), f"{round(100*len(done)/len(LESSONS))}%")
    c2.metric(tr("Lezioni", "Lessons"), f"{len(done)}/{len(LESSONS)}")
    c3.metric(tr("Esercizi provati", "Exercises attempted"), f"{len(exdone)}/{len(EXERCISES)}")
    exams = P.get("exam_history", []); c4.metric(tr("Esami svolti", "Exams taken"), len(exams))
    st.progress(len(done)/len(LESSONS))
    st.subheader(tr("Progresso per materia", "Progress by subject"))
    rows=[]
    for key, subj in SUBJECTS.items():
        subset=[x for x in LESSONS if x['subject']==key]
        n=sum(x['id'] in done for x in subset)
        rows.append({tr("Materia","Subject"):subj[L],tr("Completate","Completed"):n,tr("Totale","Total"):len(subset),tr("Progresso","Progress"):round(n/len(subset)*100)})
    # Appunti visuali per materia, al posto della tabella tradizionale.
    cols = st.columns(3)
    palettes = {"mech": "🪐", "fluid": "🌊", "aero": "🚀"}
    for i, row in enumerate(rows):
        with cols[i % 3]:
            progress_pct = row[tr("Progresso", "Progress")]
            with st.container(border=True):
                st.markdown(f"### {palettes.get(list(SUBJECTS.keys())[i], '✨')} {row[tr('Materia','Subject')]}")
                st.progress(progress_pct / 100, text=f"{progress_pct}%")
                st.caption(f"{row[tr('Completate','Completed')]} / {row[tr('Totale','Total')]} {tr('lezioni completate','lessons completed')}")
    st.subheader(tr("Riprendi da dove eri", "Pick up where you left off"))
    next_l = next((x for x in LESSONS if x['id'] not in done), LESSONS[-1])
    st.info(f"**{next_l['title'][L]}** — {next_l['subject_name'][L]}")
    if st.button(tr("Apri la prossima lezione →", "Open next lesson →"), type="primary"):
        st.session_state.selected_lesson = next_l['id']; st.session_state.page="lessons"; st.rerun()
    if exams:
        st.subheader(tr("Storico esami", "Exam history")); st.line_chart(pd.DataFrame([{"N":i+1,"Punteggio":e['score']} for i,e in enumerate(exams)]).set_index("N"))

elif page in ("today", "lessons"):
    done=set(P.get('completed_lessons', []))
    if page == "today":
        idx=(date.today().toordinal()-1)%len(LESSONS); lesson=LESSONS[idx]
        st.caption(tr("La lezione del giorno segue il calendario; puoi studiare qualsiasi lezione.", "Today's lesson follows the calendar; you can study any lesson."))
    else:
        ids=[x['id'] for x in LESSONS]
        default=ids.index(st.session_state.get('selected_lesson', ids[0])) if st.session_state.get('selected_lesson') in ids else 0
        choice=st.selectbox(tr("Scegli una lezione", "Choose a lesson"), LESSONS, index=default, format_func=lambda x:f"{'✅' if x['id'] in done else '○'} {x['id']:02d} · {x['title'][L]}")
        lesson=choice
    st.caption(f"{lesson['subject_name'][L]} · {tr('Lezione','Lesson')} {lesson['id']}/15")
    st.markdown(lesson['body'][L])
    with st.expander(tr("Formula chiave", "Key formula")):
        st.latex(lesson['formula'])
    st.markdown("---")
    if lesson['id'] in done: st.success(tr("Lezione già completata.", "Lesson already completed."))
    if st.button(tr("Segna come completata ✓", "Mark as completed ✓"), type="primary", key=f"done_{lesson['id']}"):
        mark_lesson(lesson['id']); st.success(tr("Progressi salvati!", "Progress saved!")); st.rerun()
    relevant=[e for e in EXERCISES if e['lesson_id']==lesson['id']]
    if relevant:
        st.subheader(tr("Prova subito", "Try it now"))
        ex=relevant[0]; st.write(ex['prompt'][L]); ans=st.text_input(tr("La tua risposta", "Your answer"), key=f"quick_{ex['id']}")
        if st.button(tr("Verifica", "Check"), key=f"quickcheck_{ex['id']}"):
            try:
                val=float(ans.strip().replace(',','.').replace(' ','').replace('×10^','e'))
                ok=abs(val-ex['answer']) <= max(abs(ex['answer'])*0.02, 1e-9)
            except: ok=False
            P.setdefault('exercise_results',{})[ex['id']]={'correct':bool(ok),'answer':ans}; persist()
            st.success(tr("Corretto!", "Correct!")) if ok else st.error(tr(f"Non proprio. Soluzione: {ex['answer']} {ex['unit']}",f"Not quite. Answer: {ex['answer']} {ex['unit']}"))
            st.caption(ex['solution'][L])

elif page == "exercises":
    done=P.get('exercise_results',{})
    mode=st.radio(tr("Tipo di allenamento","Practice type"),[tr("Calcoli numerici","Numerical calculations"),tr("Vero / Falso","True / False"),tr("Risposta scritta","Written answer")],horizontal=True)
    if mode == tr("Vero / Falso","True / False"):
        tf_questions = [
          ("mech", "La forza risultante è uguale alla massa moltiplicata per l'accelerazione.", "Net force equals mass multiplied by acceleration.", True, "Seconda legge di Newton: ΣF = ma."),
          ("mech", "L'energia cinetica dipende linearmente dalla velocità.", "Kinetic energy depends linearly on speed.", False, "Eₖ = ½mv²: dipende dal quadrato della velocità."),
          ("mech", "Nel SI l'unità della forza è il newton.", "In SI, force is measured in newtons.", True, "1 N = 1 kg·m/s²."),
          ("mech", "La quantità di moto è p=m/v.", "Momentum is p=m/v.", False, "La relazione corretta è p=mv."),
          ("fluid", "A parità di densità, la pressione idrostatica aumenta con la profondità.", "At constant density, hydrostatic pressure increases with depth.", True, "p=ρgh: la pressione relativa cresce con h."),
          ("fluid", "Per un fluido incomprimibile, una sezione minore comporta velocità minore.", "For incompressible flow, a smaller area means lower speed.", False, "Dalla continuità Av=costante: area minore, velocità maggiore."),
          ("fluid", "Il numero di Reynolds confronta effetti inerziali e viscosi.", "Reynolds number compares inertial and viscous effects.", True, "Re=ρvD/μ."),
          ("fluid", "La densità si misura in kg/m³.", "Density is measured in kg/m³.", True, "ρ=m/V, quindi l'unità SI è kg/m³."),
          ("fluid", "Bernoulli vale senza ipotesi in qualsiasi flusso reale.", "Bernoulli applies without assumptions to every real flow.", False, "La forma semplice richiede ipotesi come flusso ideale e stazionario."),
          ("aero", "La pressione dinamica è proporzionale al quadrato della velocità.", "Dynamic pressure is proportional to speed squared.", True, "q=½ρV²."),
          ("aero", "A parità di tutto il resto, raddoppiare V quadruplica la portanza.", "With other factors fixed, doubling V quadruples lift.", True, "L=qSCₗ e q∝V², quindi L cresce di 4 volte."),
          ("aero", "Lo stallo è sempre causato da una velocità troppo bassa e solo da quella.", "Stall is always caused only by too-low speed.", False, "È legato soprattutto al superamento dell'angolo d'attacco critico; può avvenire a diverse velocità."),
          ("aero", "L'allungamento alare è AR=b²/S.", "Aspect ratio is AR=b²/S.", True, "b è l'apertura e S l'area alare di riferimento."),
          ("aero", "La resistenza aerodinamica si misura in newton.", "Aerodynamic drag is measured in newtons.", True, "La resistenza è una forza: D=qSCᴅ."),
          ("aero", "Un modello 3D didattico basta per certificare un aereo reale.", "An educational 3D model is enough to certify a real aircraft.", False, "Servono analisi, prove, margini di sicurezza e certificazione professionale."),
        ]
        for idx,(sub,it,en,correct,why) in enumerate(tf_questions):
            with st.container(border=True):
                st.markdown(f"**{idx+1}. {SUBJECTS[sub][L]}** — {it if L=='it' else en}")
                ans=st.radio(tr("Scegli","Choose"),[tr("Vero","True"),tr("Falso","False")],horizontal=True,key=f"tf_{idx}")
                if st.button(tr("Verifica e spiega","Check and explain"),key=f"tfcheck_{idx}"):
                    istrue=ans==tr("Vero","True")
                    if istrue==correct: st.success(tr("Esatto! ","Correct! ")+ (why if L=='it' else why))
                    else: st.error(tr("Non esatto. ","Not quite. ")+ (why if L=='it' else why))
    elif mode == tr("Risposta scritta","Written answer"):
        writing = [
          ("mech","Spiega con parole tue la differenza tra velocità e accelerazione.","Explain in your own words the difference between velocity and acceleration.", ["velocità","tempo","accelerazione","variazione"]),
          ("fluid","Perché la velocità aumenta in una strozzatura di un condotto incomprimibile?","Why does speed increase in a constriction in an incompressible pipe?",["continuità","area","portata","velocità"]),
          ("fluid","Descrivi le ipotesi principali dell'equazione di Bernoulli semplice.","Describe the main assumptions of the simple Bernoulli equation.",["stazionario","viscosità","linea di corrente","perdite"]),
          ("aero","Spiega la differenza tra portanza e resistenza aerodinamica.","Explain the difference between lift and aerodynamic drag.",["portanza","resistenza","flusso","forza"]),
          ("aero","Che cos'è l'angolo d'attacco e cosa succede vicino allo stallo?","What is angle of attack and what happens near stall?",["angolo","corda","stallo","flusso"]),
          ("mech","Descrivi come applicheresti F=ma a un carrello spinto su una superficie.","Describe how you would apply F=ma to a cart pushed along a surface.",["forza","massa","accelerazione","attrito"]),
        ]
        for idx,(sub,it,en,keywords) in enumerate(writing):
            with st.container(border=True):
                st.markdown(f"**{idx+1}. {SUBJECTS[sub][L]}** — {it if L=='it' else en}")
                answer=st.text_area(tr("Scrivi la tua spiegazione","Write your explanation"),key=f"write_{idx}",height=100)
                if st.button(tr("Controlla completezza","Check completeness"),key=f"writecheck_{idx}"):
                    low=answer.lower(); found=[k for k in keywords if k in low]
                    st.progress(len(found)/len(keywords))
                    st.write(tr(f"Parole/idee individuate: {len(found)} su {len(keywords)}. Questa è una guida automatica, non una valutazione perfetta.",f"Ideas detected: {len(found)} of {len(keywords)}. This is an automatic guide, not a perfect assessment."))
                    st.caption(tr("Suggerimento per migliorare: ","Suggestion to improve: ")+", ".join(k for k in keywords if k not in found))
    else:
        subject_filter=st.selectbox(tr("Filtra per materia", "Filter by subject"), [tr("Tutte","All")]+[v[L] for v in SUBJECTS.values()])
        pool=EXERCISES if subject_filter==tr("Tutte","All") else [e for e in EXERCISES if SUBJECTS[e['subject']][L]==subject_filter]
        for ex in pool:
            with st.expander(f"{'✅' if done.get(ex['id'],{}).get('correct') else '○'} {ex['id']:02d}. {ex['title'][L]} · {SUBJECTS[ex['subject']][L]}"):
                st.markdown(ex['prompt'][L]); answer=st.text_input(tr("Risposta numerica (virgola o punto; anche 5e-4)","Numerical answer (decimal dot/comma; 5e-4 accepted)"), key=f"ans_{ex['id']}")
                a,b=st.columns([1,3])
                with a:
                    if st.button(tr("Controlla", "Check answer"), key=f"check_{ex['id']}"):
                        try:
                            value=float(answer.strip().replace(',','.').replace(' ',''))
                            ok=math.isfinite(value) and abs(value-ex['answer']) <= max(abs(ex['answer'])*0.02, 1e-9)
                        except Exception: ok=False
                        P.setdefault('exercise_results',{})[ex['id']]={'correct':bool(ok),'answer':answer}; persist()
                        if ok: st.success(tr("Risposta corretta!", "Correct answer!"))
                        else: st.error(tr(f"Risposta non corretta. Risultato atteso: {ex['answer']:g} {ex['unit']}",f"Not correct. Expected: {ex['answer']:g} {ex['unit']}"))
                with b:
                    if st.button(tr("Mostra soluzione spiegata", "Show worked solution"), key=f"sol_{ex['id']}"): st.session_state[f"show_{ex['id']}"]=True
                if st.session_state.get(f"show_{ex['id']}"): st.info(ex['solution'][L]); st.latex(ex['formula'])
    
elif page == "challenge":
    st.markdown(tr("### 🏆 Una piccola sfida al giorno, grandi progressi in un anno", "### 🏆 One small challenge a day, big progress in a year"))
    challenge=P.setdefault("challenge", {"points":0,"streak":0,"attempts":0,"history":[]})
    c1,c2,c3,c4=st.columns(4)
    c1.metric(tr("Punti", "Points"), challenge.get("points",0)); c2.metric(tr("Serie", "Streak"), challenge.get("streak",0))
    c3.metric(tr("Tentativi", "Attempts"), challenge.get("attempts",0)); c4.metric(tr("Esercizi disponibili", "Available exercises"), len(EXERCISES))
    st.progress(min(1.0, (challenge.get("points",0)%100)/100), text=tr("Prossimo livello: ogni 100 punti", "Next level: every 100 points"))
    st.write(tr("Scegli una modalità. Ogni risposta mostra la soluzione e la spiegazione; le sfide completate aggiungono punti al tuo profilo.", "Choose a mode. Each answer shows the solution and explanation; completed challenges add points to your profile."))
    challenge_mode=st.selectbox(tr("Modalità sfida", "Challenge mode"), [tr("Sprint casuale", "Random sprint"),tr("Vero o falso", "True or false"),tr("Maratona di 5 domande", "5-question marathon")])
    if st.button(tr("🎲 Genera nuova sfida", "🎲 Generate new challenge"), type="primary"):
        import random
        if challenge_mode==tr("Vero o falso", "True or false"):
            bank=[(tr("La forza risultante è F=ma.","Net force is F=ma."),True,"ΣF = ma"),(tr("L'energia cinetica è ½mv.","Kinetic energy is ½mv."),False,"Eₖ = ½mv²"),(tr("La densità è massa divisa per volume.","Density is mass divided by volume."),True,"ρ = m/V"),(tr("In un condotto incomprimibile, A₁v₁=A₂v₂.","In an incompressible pipe, A₁v₁=A₂v₂."),True,"A₁v₁ = A₂v₂"),(tr("La pressione dinamica cresce linearmente con V.","Dynamic pressure grows linearly with V."),False,"q = ½ρV²"),(tr("Il numero di Reynolds confronta inerzia e viscosità.","Reynolds number compares inertia and viscosity."),True,"Re = ρvD/μ"),(tr("La portanza si misura in newton.","Lift is measured in newtons."),True,"L = qSCₗ"),(tr("La velocità si misura in kg.","Speed is measured in kg."),False,"La velocità si misura in m/s."),(tr("La pressione è forza divisa per area.","Pressure is force divided by area."),True,"p = F/A"),(tr("Il lavoro si misura in joule.","Work is measured in joules."),True,"W = Fs (for force parallel to displacement)")]
            st.session_state.challenge_question=random.sample(bank,1)[0]
        else:
            n=5 if challenge_mode==tr("Maratona di 5 domande", "5-question marathon") else 1
            st.session_state.challenge_ids=[x['id'] for x in random.sample(EXERCISES,min(n,len(EXERCISES)))]
        st.session_state.challenge_mode=challenge_mode
    if st.session_state.get("challenge_mode")==challenge_mode:
        if challenge_mode==tr("Vero o falso", "True or false") and st.session_state.get("challenge_question"):
            q,correct,explanation=st.session_state.challenge_question
            st.markdown(f"#### {q}")
            choice=st.radio(tr("La tua risposta", "Your answer"),[tr("Vero","True"),tr("Falso","False")],horizontal=True,key="challenge_tf_answer")
            if st.button(tr("Conferma risposta", "Submit answer"),key="challenge_tf_submit"):
                ok=(choice==tr("Vero","True"))==correct
                if ok: st.success(tr("Esatto! +10 punti", "Correct! +10 points"))
                else: st.error(tr("Non esatto questa volta.", "Not quite this time."))
                st.info(tr("Spiegazione: ","Explanation: ")+explanation)
                if not st.session_state.get("challenge_tf_recorded"):
                    challenge["points"]=challenge.get("points",0)+(10 if ok else 2); challenge["attempts"]=challenge.get("attempts",0)+1; challenge["streak"]=challenge.get("streak",0)+1 if ok else 0
                    challenge.setdefault("history",[]).append({"date":str(date.today()),"mode":"true_false","correct":ok,"points":10 if ok else 2}); st.session_state.challenge_tf_recorded=True; persist()
        elif st.session_state.get("challenge_ids"):
            for eid in st.session_state.challenge_ids:
                ex=next(x for x in EXERCISES if x['id']==eid)
                with st.container(border=True):
                    st.markdown(f"**{ex['title'][L]}** · {SUBJECTS[ex['subject']][L]}")
                    st.write(ex['prompt'][L]); ans=st.text_input(tr("Risultato (usa virgola o punto)","Answer (decimal comma or dot)"),key=f"challenge_answer_{eid}")
                    if st.button(tr("Verifica e mostra passaggi", "Check and show steps"),key=f"challenge_check_{eid}"):
                        try: val=float(ans.strip().replace(',','.')); ok=math.isfinite(val) and abs(val-ex['answer'])<=max(abs(ex['answer'])*.02,1e-9)
                        except Exception: ok=False
                        st.success(tr("Corretto! +10 punti", "Correct! +10 points")) if ok else st.error(tr(f"Risposta attesa: {ex['answer']:g} {ex['unit']}",f"Expected answer: {ex['answer']:g} {ex['unit']}"))
                        st.info(ex['solution'][L]); st.latex(ex['formula'])
                        rec_key=f"challenge_recorded_{eid}"
                        if not st.session_state.get(rec_key):
                            pts=10 if ok else 2; challenge["points"]=challenge.get("points",0)+pts; challenge["attempts"]=challenge.get("attempts",0)+1; challenge["streak"]=challenge.get("streak",0)+1 if ok else 0
                            challenge.setdefault("history",[]).append({"date":str(date.today()),"exercise_id":eid,"correct":ok,"points":pts}); st.session_state[rec_key]=True; persist()
    if challenge.get("history"):
        st.subheader(tr("🗒️ Appunti delle sfide recenti", "🗒️ Recent challenge notes"))
        for item in reversed(challenge["history"][-10:]):
            with st.container(border=True):
                st.markdown(f"**🏆 {item.get('date', '')}** · {item.get('mode', item.get('exercise_id', 'Challenge'))}")
                st.write(("✅ " if item.get("correct") else "✍️ ") + str(item.get("points", 0)) + " points")

elif page == "life":
    if CURRENT_USER.get("role") != "admin": st.error("Questa sezione è privata."); st.stop()
    st.markdown(tr("### 🌱 Il tuo spazio personale è separato dallo studio tecnico", "### 🌱 Your personal space is separate from technical study"))
    st.caption(tr("Diario e pianificazione annuale dal 18 ottobre 2026. I dati vengono salvati solo nel file locale del progetto.", "Annual journal and planning starting 18 October 2026. Data is saved only in the project's local file."))
    personal=P.setdefault("personal_life",{})
    personal.setdefault("start_date","2026-10-18"); personal.setdefault("employment_status","Attualmente non lavoro")
    personal.setdefault("journal",{}); personal.setdefault("interrogazioni",[])
    st.subheader(tr("👤 Profilo personale", "👤 Personal profile"))
    c1,c2=st.columns(2)
    personal["display_name"]=c1.text_input(tr("Nome (facoltativo)","Name (optional)"),personal.get("display_name",""))
    personal["employment_status"]=c2.selectbox(tr("Situazione lavorativa", "Work status"),["Attualmente non lavoro","Cerco lavoro","Studio e cerco lavoro","Lavoro"],index=["Attualmente non lavoro","Cerco lavoro","Studio e cerco lavoro","Lavoro"].index(personal.get("employment_status","Attualmente non lavoro")) if personal.get("employment_status") in ["Attualmente non lavoro","Cerco lavoro","Studio e cerco lavoro","Lavoro"] else 0)
    annual_start=st.date_input(tr("Inizio del tuo anno personale", "Start of your personal year"), value=date.fromisoformat(personal.get("start_date","2026-10-18")))
    personal["start_date"]=annual_start.isoformat()
    st.divider(); st.subheader(tr("🏫 Orario scolastico — Ragioneria, quinta superiore", "🏫 School timetable — final year of accounting studies"))
    timetable={
      "Lunedì":["Italiano","Economia politica","Diritto","Informatica","Informatica"],
      "Martedì":["Economia aziendale","Economia aziendale","Scienze motorie","Matematica","Diritto","Religione"],
      "Mercoledì":["Economia aziendale","Economia aziendale","Economia aziendale","Informatica","Informatica"],
      "Giovedì":["Italiano","Economia politica","Storia","Matematica","Informatica"],
      "Venerdì":["Economia aziendale","Scienze motorie","Economia aziendale","Economia politica","Inglese","Inglese"],
      "Sabato":["Storia","Italiano","Italiano","Matematica","Inglese"]}
    rows=[]
    for day,subjects in timetable.items():
        finish="14:00" if day in ("Martedì","Venerdì") else "13:00"
        rows.append({"Giorno":day,"Orario":f"08:00–{finish}","Materie": " · ".join(subjects)})
    day_cols = st.columns(3)
    for i, item in enumerate(rows):
        with day_cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### 📘 {item['Giorno']}")
                st.caption("⏰ " + item["Orario"])
                st.write(item["Materie"].replace(" · ", "  ·  "))
    st.info(tr("Orario base: scuola dalle 08:00 alle 13:00; martedì e venerdì fino alle 14:00. Puoi modificare le attività nel diario e pianificare le interrogazioni qui sotto.","Base schedule: school from 08:00 to 13:00; Tuesday and Friday until 14:00. You can record activities in the journal and plan oral tests below."))
    weekday_names={0:"Lunedì",1:"Martedì",2:"Mercoledì",3:"Giovedì",4:"Venerdì",5:"Sabato",6:"Domenica"}
    today_name=weekday_names[date.today().weekday()]
    today_subjects=timetable.get(today_name,[])
    st.subheader(tr("🧠 Piano di studio adattato alla giornata", "🧠 Study plan adapted to your day"))
    if today_subjects:
        st.write(tr(f"Oggi è {today_name}. Materie scolastiche: {', '.join(today_subjects)}.",f"Today is {today_name}. School subjects: {', '.join(today_subjects)}."))
    else:
        st.write(tr("Oggi non hai materie nel tuo orario scolastico: usa la giornata per recuperare, riposare e preparare la settimana.","No school subjects are listed for today: use the day to catch up, rest, and prepare for the week."))
    later_day=today_name in ("Martedì","Venerdì")
    suggested_start="15:30" if later_day else "14:30"
    st.markdown(tr(f"- **{suggested_start}–15:15:** pranzo e pausa (se oggi vai a scuola, sposta l'orario se necessario).\n- **15:30–16:15:** ripasso della materia più difficile.\n- **16:25–17:00:** esercizi o preparazione interrogazione.\n- **Dopo le 17:00:** tempo personale, famiglia e riposo.",f"- **{suggested_start}–15:15:** lunch and break (adjust if school finishes later).\n- **15:30–16:15:** review the hardest subject.\n- **16:25–17:00:** exercises or oral-test preparation.\n- **After 17:00:** personal time, family, and rest."))
    st.divider(); st.subheader(tr("🗓️ Pianifica interrogazioni e verifiche", "🗓️ Plan oral tests and exams"))
    with st.form("personal_exam_form"):
        c1,c2=st.columns(2)
        exam_date=c1.date_input(tr("Data della verifica/interrogazione", "Test/oral exam date"),value=date.today()+timedelta(days=3))
        exam_subject=c2.selectbox(tr("Materia", "Subject"),["Italiano","Economia politica","Diritto","Informatica","Economia aziendale","Scienze motorie","Matematica","Religione","Storia","Inglese"])
        exam_topic=st.text_input(tr("Argomenti da studiare", "Topics to study"))
        exam_priority=st.select_slider(tr("Priorità", "Priority"),options=[tr("Bassa","Low"),tr("Media","Medium"),tr("Alta","High")],value=tr("Alta","High"))
        submitted=st.form_submit_button(tr("Aggiungi al piano", "Add to plan"),type="primary")
    if submitted:
        personal["interrogazioni"].append({"date":str(exam_date),"subject":exam_subject,"topic":exam_topic,"priority":exam_priority,"done":False}); persist(); st.success(tr("Verifica aggiunta al piano!", "Test added to your plan!")); st.rerun()
    if personal["interrogazioni"]:
        for i,item in enumerate(sorted(personal["interrogazioni"],key=lambda x:x["date"])):
            with st.container(border=True):
                col1,col2=st.columns([4,1]); col1.markdown(f"**{item['date']} · {item['subject']}** — {item.get('priority','Media')}\n\n{item.get('topic') or tr('Argomenti da definire','Topics to be defined')}")
                if col2.button(tr("Elimina","Delete"),key=f"delete_personal_exam_{i}"):
                    personal["interrogazioni"].remove(item); persist(); st.rerun()
    st.divider(); st.subheader(tr("📔 Diario personale annuale", "📔 Annual personal journal"))
    journal_date=st.date_input(tr("Giorno da registrare", "Day to record"),value=date.today(),key="journal_date")
    existing=personal["journal"].get(str(journal_date),{})
    with st.form("personal_journal_form"):
        mood=st.select_slider(tr("Come ti senti?", "How are you feeling?"),options=[tr("Molto male","Very low"),tr("Male","Low"),tr("Così così","Okay"),tr("Bene","Good"),tr("Molto bene","Great")],value=existing.get("mood",tr("Bene","Good")))
        activities=st.text_area(tr("Cosa hai fatto oggi?", "What did you do today?"),value=existing.get("activities",""),height=100)
        goals=st.text_area(tr("Obiettivi o cose da ricordare", "Goals or things to remember"),value=existing.get("goals",""),height=80)
        study_hours=st.number_input(tr("Ore di studio fuori scuola", "Study hours outside school"),min_value=0.0,max_value=16.0,value=float(existing.get("study_hours",0.0)),step=0.5)
        journal_submit=st.form_submit_button(tr("Salva la giornata", "Save day"),type="primary")
    if journal_submit:
        personal["journal"][str(journal_date)]={"mood":mood,"activities":activities,"goals":goals,"study_hours":study_hours,"updated_at":datetime.now().isoformat(timespec="minutes")}; persist(); st.success(tr("Giornata salvata!", "Day saved!")); st.rerun()
    st.subheader(tr("📈 Il tuo anno in numeri", "📈 Your year in numbers"))
    year_start=date.fromisoformat(personal["start_date"]); year_end=year_start+timedelta(days=365)
    year_entries={k:v for k,v in personal["journal"].items() if year_start<=date.fromisoformat(k)<=year_end}
    c1,c2,c3=st.columns(3); c1.metric(tr("Giornate registrate", "Days recorded"),len(year_entries)); c2.metric(tr("Ore di studio", "Study hours"),sum(float(v.get("study_hours",0)) for v in year_entries.values())); c3.metric(tr("Verifiche pianificate", "Planned tests"),len(personal["interrogazioni"]))
    if year_entries:
        entries=[{"Data":k,"Umore":v.get("mood",""),"Ore studio":v.get("study_hours",0),"Attività":v.get("activities",""),"Obiettivi":v.get("goals","")} for k,v in sorted(year_entries.items(),reverse=True)]
        st.markdown(tr("### 📝 Appunti del diario", "### 📝 Journal notes"))
        for entry in entries[:10]:
            with st.container(border=True):
                st.markdown(f"**📅 {entry['Data']}** · {entry['Umore']} · {entry['Ore studio']} h")
                if entry['Attività']: st.write("**" + tr("Attività", "Activities") + ":** " + str(entry['Attività']))
                if entry['Obiettivi']: st.write("**" + tr("Obiettivi", "Goals") + ":** " + str(entry['Obiettivi']))
        st.download_button(tr("Esporta diario annuale CSV", "Export annual journal CSV"),data=pd.DataFrame(entries).to_csv(index=False).encode("utf-8-sig"),file_name="diario_personale_annual.csv",mime="text/csv")
    if st.button(tr("Salva profilo personale", "Save personal profile"),type="primary",key="save_personal_profile"): persist(); st.success(tr("Profilo salvato.","Profile saved."))

elif page == "exams":
    st.write(tr("Ogni esame contiene domande numeriche casuali dal modulo selezionato. La tolleranza è ±2%.","Each exam contains random numerical questions from the selected module. Tolerance is ±2%."))
    examtype=st.selectbox(tr("Tipo di esame", "Exam type"), [tr("Meccanica","Mechanics"),tr("Fluidodinamica","Fluid dynamics"),tr("Aerodinamica","Aerodynamics"),tr("Esame finale","Final exam")])
    keymap={tr("Meccanica","Mechanics"):'mech',tr("Fluidodinamica","Fluid dynamics"):'fluid',tr("Aerodinamica","Aerodynamics"):'aero',tr("Esame finale","Final exam"):'all'}
    pool=[e for e in EXERCISES if keymap[examtype]=='all' or e['subject']==keymap[examtype]]
    if st.button(tr("Genera / rigenera esame", "Generate / regenerate exam"), type="primary"):
        import random
        st.session_state.exam_ids=[x['id'] for x in random.sample(pool,min(6 if keymap[examtype]!='all' else 12,len(pool)))]
        st.session_state.exam_type=examtype
    if st.session_state.get('exam_ids') and st.session_state.get('exam_type')==examtype:
        score=0; submitted=[]
        with st.form("exam_form"):
            for eid in st.session_state.exam_ids:
                ex=next(e for e in EXERCISES if e['id']==eid); st.markdown(f"**{ex['title'][L]}** — {ex['prompt'][L]}")
                submitted.append((ex,st.text_input(tr("Risposta", "Answer"),key=f"exam_{eid}")))
            submit=st.form_submit_button(tr("Consegna esame", "Submit exam"), type="primary")
        if submit:
            for ex,ans in submitted:
                try: val=float(ans.replace(',','.').strip()); ok=abs(val-ex['answer'])<=max(abs(ex['answer'])*.02,1e-9)
                except: ok=False
                score+=int(ok)
            pct=round(100*score/max(1,len(submitted)))
            P.setdefault('exam_history',[]).append({'date':str(date.today()),'type':examtype,'score':pct,'correct':score,'total':len(submitted)}); persist()
            st.success(tr(f"Punteggio: {score}/{len(submitted)} ({pct}%)",f"Score: {score}/{len(submitted)} ({pct}%)"))
            for ex,ans in submitted: st.write(f"**{ex['title'][L]}** — {tr('risultato','answer')}: {ex['answer']:g} {ex['unit']}. {ex['solution'][L]}")
    if P.get('exam_history'):
        st.subheader(tr("📒 Appunti e storico esami", "📒 Exam notes and history"))
        for item in reversed(P['exam_history'][-10:]):
            with st.container(border=True):
                st.markdown(f"**🎓 {item.get('type', 'Exam')}** · {item.get('date', '')}")
                st.progress(max(0, min(1, float(item.get('score', 0))/100)), text=f"{item.get('score', 0)}% · {item.get('correct', 0)}/{item.get('total', 0)}")

elif page == "student":
    st.subheader(tr("Il tuo spazio personale","Your personal learning space"))
    settings=P.setdefault("settings",{})
    settings["student_name"]=st.text_input(tr("Nome studente","Student name"),settings.get("student_name",""))
    st.caption(tr("I risultati e i progressi vengono salvati localmente in data/progress.json.","Results and progress are saved locally in data/progress.json."))
    c1,c2,c3=st.columns(3); c1.metric(tr("Lezioni completate","Lessons completed"),f"{len(P.get('completed_lessons',[]))}/{len(LESSONS)}"); c2.metric(tr("Risposte corrette","Correct answers"),sum(1 for x in P.get("exercise_results",{}).values() if x.get("correct"))); c3.metric(tr("Esami","Exams"),len(P.get("exam_history",[])))
    if st.button(tr("Salva profilo studente","Save student profile"),type="primary"): persist(); st.success(tr("Profilo salvato.","Profile saved."))
    st.info(tr("Suggerimento: completa una lezione, prova un calcolo e poi verifica il concetto con Vero/Falso.","Tip: complete a lesson, try a calculation, then check the concept with True/False."))

elif page == "teacher":
    st.subheader(tr("Area docente — panoramica didattica","Teacher area — teaching overview"))
    st.warning(tr("Questa versione usa un selettore di ruolo locale, non un sistema di autenticazione sicuro. Non inserire dati sensibili.","This version uses a local role selector, not secure authentication. Do not enter sensitive data."))
    c1,c2,c3=st.columns(3); c1.metric(tr("Studenti su questo dispositivo","Learners on this device"),1); c2.metric(tr("Esercizi disponibili","Available exercises"),len(EXERCISES)); c3.metric(tr("Quiz Vero/Falso","True/False quiz items"),15)
    st.markdown(tr("**Strumenti docente**","**Teacher tools**"))
    st.write(tr("• Visualizza il catalogo delle lezioni e degli esercizi.\n• Esporta i risultati correnti per analisi.\n• Genera un compito stampabile dal browser con Ctrl/Cmd+P.","• Review the lesson and exercise catalogue.\n• Export current results for analysis.\n• Create a printable assignment using Ctrl/Cmd+P in the browser."))
    if P.get("exercise_results"):
        rows=[]
        for eid,result in P["exercise_results"].items():
            ex=next((x for x in EXERCISES if str(x["id"])==str(eid)),None)
            if ex: rows.append({"ID":eid,tr("Titolo","Title"):ex["title"][L],tr("Materia","Subject"):SUBJECTS[ex["subject"]][L],tr("Corretto","Correct"):result.get("correct",False),tr("Risposta inviata","Submitted answer"):result.get("answer","")})
        if rows:
            st.markdown(tr("### 🗂️ Registro visuale dei risultati", "### 🗂️ Visual results notebook"))
            for item in rows:
                with st.container(border=True):
                    st.markdown(f"**{item[tr('Titolo','Title')]}** · {item[tr('Materia','Subject')]}")
                    st.write(("✅ " if item[tr('Corretto','Correct')] else "📝 ") + tr("Risposta", "Answer") + ": " + str(item[tr('Risposta inviata','Submitted answer')]))
    st.download_button(tr("Esporta registro risultati CSV","Export results CSV"),data=pd.DataFrame([{"exercise_id":k,**v} for k,v in P.get("exercise_results",{}).items()]).to_csv(index=False).encode("utf-8"),file_name="engineering_academy_results.csv",mime="text/csv")

elif page == "assistant":
    st.subheader(tr("🤖 Assistente IA per studiare e preparare le interrogazioni", "🤖 AI assistant for studying and oral exams"))
    st.markdown(tr("Scegli la modalità: chiarire un argomento tecnico oppure prepararti a un'interrogazione scolastica con spiegazione semplice, domande simulate e piano di ripasso.", "Choose a mode: understand a technical topic or prepare for a school oral exam with a simple explanation, mock questions, and a revision plan."))
    tab_eng, tab_oral = st.tabs([tr("🛠️ Tutor ingegneria", "🛠️ Engineering tutor"), tr("🎓 Prepara interrogazione", "🎓 Prepare an oral exam")])
    with tab_eng:
        question=st.text_area(tr("La tua domanda", "Your question"),placeholder=tr("Esempio: spiegami Bernoulli da zero e fammi un esempio numerico", "Example: explain Bernoulli from zero and give me a numerical example"),height=100,key="eng_tutor_question")
        if st.button(tr("Chiedi al tutor", "Ask tutor"),type="primary",key="eng_tutor_button"):
            q=question.lower()
            api_key=os.environ.get("OPENAI_API_KEY", "").strip()
            if api_key and question.strip():
                try:
                    from openai import OpenAI
                    client=OpenAI(api_key=api_key)
                    with st.spinner(tr("Il tutor IA sta preparando una spiegazione...", "AI tutor is preparing an explanation...")):
                        response=client.responses.create(model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),input=f"Sei un tutor paziente per principianti. Rispondi in { {'it':'italiano','en':'inglese','ar':'arabo standard','ary':'darija marocchina','es':'spagnolo','fr':'francese','de':'tedesco','pt':'portoghese'}.get(L,'italiano') }. Spiega i passaggi, definisci i simboli, usa unità SI e includi un esempio numerico se utile. Non presentare stime didattiche come consigli per la sicurezza reale.\nDomanda: {question}")
                    st.markdown(response.output_text)
                except Exception:
                    st.warning(tr("Servizio IA online non disponibile: controllo chiave API, connessione e quota. Mostro intanto una guida locale.", "Online AI unavailable: check API key, connection and quota. Showing a local guide instead."))
            terms={"newton":("F=ma","La forza risultante è massa × accelerazione. Esempio: 4 kg × 3 m/s² = 12 N."),"forza":("F=ma","Disegna le forze, calcola la risultante e usa a=F/m oppure F=ma."),"energia":("Eₖ=½mv²","L'energia cinetica cresce con il quadrato della velocità. Con m=2 kg e v=3 m/s: Eₖ=9 J."),"velocità":("v=s/t","La velocità media è distanza divisa per tempo. 100 m in 20 s = 5 m/s."),"reynolds":("Re=ρvD/μ","Re confronta inerzia e viscosità."),"bernoulli":("p+½ρv²+ρgz=costante","Lungo una linea di corrente ideale, i termini di pressione, velocità e quota si scambiano."),"pressione":("p=F/A","La pressione è la forza normale divisa per l'area."),"portanza":("L=½ρV²SCₗ","La portanza dipende da densità, velocità al quadrato, area e coefficiente di portanza.")}
            matches=[(k,v) for k,v in terms.items() if k in q]
            if matches:
                for term,(formula,explanation) in matches:
                    st.markdown(f"### {term.title()}"); st.latex(formula); st.info(explanation)
            elif not (api_key and question.strip()):
                st.info(tr("Prova parole come Newton, forza, energia, velocità, pressione, Reynolds, Bernoulli o portanza. Per un modello IA online configura OPENAI_API_KEY.", "Try keywords such as Newton, force, energy, speed, pressure, Reynolds, Bernoulli, or lift. For online AI, configure OPENAI_API_KEY."))
    with tab_oral:
        st.markdown(tr("### Prepariamo insieme la tua interrogazione", "### Let's prepare your oral exam together"))
        school_subjects=["Italiano","Economia politica","Diritto","Informatica","Economia aziendale","Scienze motorie","Matematica","Religione","Storia","Inglese"]
        subject=st.selectbox(tr("Materia", "Subject"),school_subjects,key="oral_subject")
        topic=st.text_input(tr("Argomento da studiare", "Topic to study"),placeholder=tr("Es. bilancio d'esercizio, Dante, funzioni, Costituzione...", "E.g. financial statements, Dante, functions, constitution..."),key="oral_topic")
        level=st.select_slider(tr("Quanto conosci già l'argomento?", "How well do you know the topic?"),options=[tr("Da zero", "From zero"),tr("Poco", "A little"),tr("Abbastanza", "Somewhat"),tr("Bene", "Well")],value=tr("Da zero", "From zero"),key="oral_level")
        oral_date=st.date_input(tr("Data dell'interrogazione (se la conosci)", "Oral exam date (if known)"),value=date.today()+timedelta(days=3),key="oral_date")
        oral_api=os.environ.get("OPENAI_API_KEY", "").strip()
        book_files = st.file_uploader("Carica pagine del libro (PDF o immagini)", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True, key="oral_book_files")
        if book_files:
            st.caption(f"{len(book_files)} file caricati per questa sessione. Il supporto completo alle immagini/OCR dipende dal formato e dal provider IA configurato.")
            for f in book_files:
                if f.name.lower().endswith('.pdf'):
                    try:
                        from pypdf import PdfReader
                        reader=PdfReader(io.BytesIO(f.getvalue()))
                        extracted="\n".join((p.extract_text() or "") for p in reader.pages[:30])
                        st.session_state['oral_book_context'] = (st.session_state.get('oral_book_context','') + "\n" + extracted)[:30000]
                    except Exception:
                        st.warning(f"Non riesco a leggere il testo da {f.name}. Prova un PDF testuale o immagini più chiare.")
        if st.button(tr("✨ Crea il mio piano e simulazione", "✨ Create my plan and mock exam"),type="primary",key="oral_prepare"):
            if not topic.strip():
                st.warning(tr("Scrivi prima l'argomento, così posso aiutarti in modo mirato.", "Enter the topic first so I can tailor the help."))
            else:
                st.markdown(f"### {subject} — {topic}")
                if oral_api:
                    try:
                        from openai import OpenAI
                        client=OpenAI(api_key=oral_api)
                        prompt=(f"Sei un tutor scolastico paziente. Rispondi nella lingua selezionata: { {'it':'italiano','en':'inglese','ar':'arabo standard','ary':'darija marocchina','es':'spagnolo','fr':'francese','de':'tedesco','pt':'portoghese'}.get(L,'italiano') }. Prepara una scheda per interrogazione. Materia: {subject}. Argomento: {topic}. Livello attuale: {level}. Data interrogazione: {oral_date}. Fornisci: 1) spiegazione semplice ma corretta; 2) concetti e parole chiave; 3) 8 domande probabili dalla facile alla difficile con risposte modello; 4) 5 flashcard domanda/risposta; 5) mini simulazione orale una domanda alla volta; 6) piano di ripasso fino alla data indicata, realistico e con pause. Non inventare il programma specifico dell'insegnante; segnala cosa verificare sul libro/appunti. Contesto estratto dal libro: {st.session_state.get('oral_book_context', 'Nessun testo estratto')[:12000]} ")
                        with st.spinner(tr("L'assistente sta preparando la scheda...", "The assistant is preparing your study sheet...")):
                            response=client.responses.create(model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),input=prompt)
                        st.markdown(response.output_text)
                    except Exception:
                        st.warning(tr("L'IA online non è disponibile in questo momento. Ecco un piano base modificabile.", "Online AI is currently unavailable. Here is an editable basic plan."))
                if not oral_api:
                    st.markdown(tr(f"""**1. Spiega l'argomento in 5 righe.** Usa il libro e gli appunti come fonte principale.

**2. Memorizza 5 parole chiave.** Per ciascuna scrivi definizione ed esempio.

**3. Ripeti ad alta voce.** Prova a parlare per 2 minuti senza leggere.

**4. Controlla ciò che non sai.** Segna i dubbi da chiedere al docente.

**5. Piano fino al {oral_date}:** oggi 20 minuti per capire; domani 20 minuti per schema e flashcard; il giorno prima 15 minuti di simulazione orale e ripasso leggero.

**Domande per allenarti:**
- Come definiresti {topic} con parole tue?
- Quali sono i concetti o passaggi principali?
- Puoi fare un esempio concreto?
- Quale errore comune bisogna evitare?
- Come collegheresti questo argomento a ciò che hai studiato prima?""", f"""**1. Explain the topic in five lines.** Use your textbook and notes as the primary source.

**2. Learn five keywords.** Write a definition and example for each.

**3. Practise aloud.** Try speaking for two minutes without reading.

**4. Check gaps.** Write down questions for your teacher.

**5. Plan until {oral_date}:** today 20 minutes to understand; tomorrow 20 minutes for an outline and flashcards; the day before, 15 minutes of oral practice and light review.

**Practice questions:**
- How would you define {topic} in your own words?
- What are its main concepts or steps?
- Can you give a concrete example?
- What common mistake should be avoided?
- How does this connect to what you studied before?"""))
                st.caption(tr("Nota: senza OPENAI_API_KEY questa è una guida locale generica, non una risposta generata da IA. Con la chiave configurata, il tutor crea una scheda personalizzata.", "Note: without OPENAI_API_KEY this is a generic local guide, not an AI-generated answer. With the key configured, the tutor creates a tailored study sheet."))

elif page == "support":
    st.subheader("💬 Supporto TAYARAN.COM")
    st.markdown("Scrivici per problemi tecnici, accesso o suggerimenti.")
    st.link_button("Invia email al supporto", "mailto:khalidtalhane875@gmail.com?subject=TAYARAN.COM%20Support")
    st.caption("Email supporto: khalidtalhane875@gmail.com")
    st.info("Il dominio TAYARAN.COM è mostrato come marchio nell'app. Per renderlo un indirizzo Internet pubblico devi registrare il dominio e configurare hosting, DNS e HTTPS.")

elif page == "plans":
    st.subheader("✨ Piani per l'assistente IA")
    st.markdown("Scegli un piano in base alle tue esigenze. I pagamenti online non sono attivi finché non configuri un gestore di pagamenti e le relative chiavi segrete.")
    c1,c2,c3=st.columns(3)
    with c1:
        st.markdown("### 🌱 Base"); st.metric("Prezzo", "Gratis"); st.write("Lezioni, esercizi e progressi personali")
    with c2:
        st.markdown("### 🚀 AI Study"); st.metric("Prezzo", "Da definire"); st.write("Tutor IA, spiegazioni e preparazione interrogazioni"); st.caption("Richiede configurazione API e provider di pagamento")
    with c3:
        st.markdown("### 🌌 Pro Studio"); st.metric("Prezzo", "Da definire"); st.write("Funzioni avanzate e strumenti di studio condiviso"); st.caption("Non acquistabile finché il pagamento non è configurato")
    st.link_button("Contatta il supporto", "mailto:khalidtalhane875@gmail.com?subject=TAYARAN.COM%20AI%20plans")

elif page == "simulations":
    sim=st.selectbox(tr("Scegli una simulazione", "Choose a simulation"), [tr("Moto del proiettile","Projectile motion"),tr("Sistema massa-molla","Spring-mass system"),"Venturi", "Moody",tr("Flusso attorno a un cilindro","Flow around a cylinder"),tr("Polare di un profilo alare","Airfoil polar")])
    if sim==tr("Moto del proiettile","Projectile motion"):
        c1,c2,c3=st.columns(3); v=c1.slider(tr("Velocità iniziale (m/s)","Initial velocity (m/s)"),1,100,25); ang=c2.slider(tr("Angolo (°)","Angle (°)"),5,85,45); h=c3.slider(tr("Altezza iniziale (m)","Initial height (m)"),0,50,0)
        fig,metrics=projectile_plot(v,ang,h); st.plotly_chart(fig,use_container_width=True); st.write(metrics)
    elif sim==tr("Sistema massa-molla","Spring-mass system"):
        c1,c2,c3=st.columns(3); m=c1.slider("m (kg)",0.1,10.0,1.0); k=c2.slider("k (N/m)",1,200,25); x0=c3.slider("x₀ (m)",0.01,1.0,0.3)
        st.plotly_chart(spring_plot(m,k,x0),use_container_width=True); st.latex(r"\omega_n=\sqrt{k/m}")
    elif sim=="Venturi":
        c1,c2=st.columns(2); d1=c1.slider(tr("Diametro ingresso (cm)","Inlet diameter (cm)"),2,30,10); d2=c2.slider(tr("Diametro gola (cm)","Throat diameter (cm)"),1, min(20,d1),5); q=c1.slider(tr("Portata (L/s)","Flow rate (L/s)"),0.1,20.0,2.0); rho=c2.selectbox(tr("Fluido","Fluid"),[1000,998,1.225],format_func=lambda x:{1000:"Acqua",998:"Acqua a 20°C",1.225:"Aria"}[x] if L=="it" else {1000:"Water",998:"Water at 20°C",1.225:"Air"}[x])
        fig, vals=venturi_plot(d1/100,d2/100,q/1000,rho); st.plotly_chart(fig,use_container_width=True); st.write(vals)
    elif sim=="Moody":
        re=st.slider("Reynolds number",500,10_000_000,100000,step=500); rough=st.slider(tr("Scabrezza relativa ε/D", "Relative roughness ε/D"),0.0,0.05,0.001)
        fig, f=moody_plot(re,rough); st.plotly_chart(fig,use_container_width=True); st.metric("Fattore di attrito Darcy",f"{f:.5f}")
    elif sim==tr("Flusso attorno a un cilindro","Flow around a cylinder"):
        u=st.slider(tr("Velocità del flusso (m/s)","Flow speed (m/s)"),1,50,10); st.plotly_chart(cylinder_plot(u),use_container_width=True); st.caption(tr("Visualizzazione qualitativa del flusso potenziale ideale.","Qualitative visualization of ideal potential flow."))
    else:
        alpha=st.slider(tr("Angolo d'attacco (°)","Angle of attack (°)"),-8,18,4); st.plotly_chart(airfoil_plot(alpha),use_container_width=True); st.caption(tr("Modello semplificato: non sostituisce dati sperimentali o CFD.","Simplified model: not a substitute for experimental data or CFD."))

elif page == "wing":
    st.write(tr("Genera una geometria alare parametrica NACA 4 cifre. Le stime sono esclusivamente didattiche.","Generate a parametric NACA 4-digit wing. Estimates are for educational use only."))
    c1,c2,c3=st.columns(3); naca=c1.selectbox("NACA",["0012","2412","4412","23012"]); span=c2.slider(tr("Apertura alare (m)","Wingspan (m)"),0.5,20.0,4.0); chord=c3.slider(tr("Corda (m)","Chord (m)"),0.2,3.0,1.0)
    c1,c2,c3=st.columns(3); speed=c1.slider(tr("Velocità (m/s)","Speed (m/s)"),5,100,30); alpha=c2.slider(tr("Angolo d'attacco (°)","Angle of attack (°)"),-5,15,4); rho=c3.slider(tr("Densità aria (kg/m³)","Air density (kg/m³)"),0.8,1.3,1.225)
    X,Y,Z=build_wing(naca,span,chord)
    fig=go.Figure(data=[go.Surface(x=X,y=Y,z=Z,colorscale="Viridis",showscale=False)]); fig.update_layout(scene=dict(xaxis_title="Chord (m)",yaxis_title="Span (m)",zaxis_title="Thickness (m)"),height=560,margin=dict(l=0,r=0,t=20,b=0)); st.plotly_chart(fig,use_container_width=True)
    est=wing_estimates(span,chord,speed,alpha,rho,naca)
    cols=st.columns(4)
    for col,(k,v) in zip(cols,est.items()): col.metric(k,v)
    st.warning(tr("Stime molto semplificate: non usare per progettazione reale, sicurezza o certificazione aeronautica.","Very simplified estimates: do not use for real design, safety, or aircraft certification."))
    st.download_button(tr("Scarica modello STL", "Download STL model"), data=stl_bytes(X,Y,Z), file_name=f"wing_NACA{naca}.stl", mime="model/stl")

elif page == "admin":
    if CURRENT_USER.get("role") != "admin":
        st.error("Accesso non autorizzato."); st.stop()
    st.markdown("""<div class="ea-profile-hero"><div class="ea-profile-orb">◈</div><div class="ea-profile-kicker">ADMIN CONTROL CENTER</div><h1>🛡️ Pannello amministratore</h1><p>Gestisci account, accessi, consensi e progressi di studio. Le password non sono visibili né recuperabili.</p></div>""", unsafe_allow_html=True)
    accounts = auth_system.list_accounts()
    total_students = sum(1 for a in accounts if a.get('role') == 'student')
    active_accounts = sum(1 for a in accounts if not a.get('disabled'))
    a1,a2,a3 = st.columns(3); a1.metric("Account registrati", len(accounts)); a2.metric("Studenti", total_students); a3.metric("Account attivi", active_accounts)
    st.subheader("Account e livelli")
    for account in accounts:
        with st.container(border=True):
            c1,c2,c3 = st.columns([2,1,1])
            c1.markdown(f"**{account.get('display_name') or 'Studente'}**  \n{account.get('email')}")
            c2.caption("Ruolo"); c2.write("🛡️ Admin" if account.get('role') == 'admin' else '🎓 Studente')
            c3.caption("Ultimo accesso"); c3.write((account.get('last_login') or 'Mai')[:19].replace('T',' '))
            cons = account.get('consents') or {}
            st.caption("Consensi: progressi studio=" + ("sì" if cons.get('study_progress') else "no") + " · file caricati=" + ("sì" if cons.get('uploaded_files') else "no") + " · posizione=" + ("sì" if cons.get('location') else "no") + " · condivisione dispositivo=" + ("sì" if cons.get('device_sharing') else "no"))
            from ea.storage import load_progress as _load_user_progress
            user_progress = _load_user_progress(auth_system.user_key(account['email']))
            completed = len(user_progress.get('completed_lessons', [])); attempted = len(user_progress.get('exercise_results', {}))
            st.caption(f"Livello studio: {completed}/15 lezioni completate · {attempted} esercizi provati")
            if account.get('role') != 'admin':
                label = "Riattiva account" if account.get('disabled') else "Disabilita account"
                if st.button(label, key="toggle_" + auth_system.user_key(account['email'])):
                    auth_system.set_disabled(account['email'], not account.get('disabled', False)); st.rerun()
    st.info("Per privacy, il pannello mostra solo dati di account e consensi, non password, contenuti privati del telefono o file personali non condivisi. Le metriche di progresso sono isolate per account e non vengono aggregate da questo pannello in questa versione.")

elif page == "profile":
    if CURRENT_USER.get("role") != "admin": st.error("Questa sezione è privata."); st.stop()
    st.markdown(f"""<div class="ea-profile-hero"><div class="ea-profile-orb">✦</div><div class="ea-profile-kicker">PERSONAL SPACE · ENGINEERING ACADEMY</div><h1>👤 {html_escape(CURRENT_USER.get("display_name", "Khalid Talhane"))}</h1><p>Il tuo spazio personale per studiare, progettare e crescere.</p><div class="ea-profile-tags"><span>🚀 Aerospace</span><span>🌊 Fluid dynamics</span><span>🪐 Mechanics</span></div></div>""", unsafe_allow_html=True)
    prof = P.setdefault("profile", {})
    p1, p2 = st.columns(2)
    with p1:
        prof["display_name"] = st.text_input(tr("Nome visualizzato", "Display name"), value=prof.get("display_name", "Khalid Talhane"), key="profile_display_name")
        prof["goal"] = st.text_area(tr("Il mio obiettivo", "My goal"), value=prof.get("goal", "Imparare meccanica, fluidodinamica e aerodinamica passo dopo passo."), key="profile_goal")
    with p2:
        prof["favorite_theme"] = st.selectbox(tr("Tema preferito", "Favourite theme"), ["Space / Spazio", "Ocean / Oceano", "Fondente / Chocolate"], index=["Space / Spazio", "Ocean / Oceano", "Fondente / Chocolate"].index(prof.get("favorite_theme", "Space / Spazio")) if prof.get("favorite_theme", "Space / Spazio") in ["Space / Spazio", "Ocean / Oceano", "Fondente / Chocolate"] else 0, key="profile_theme")
        st.metric(tr("Lezioni completate", "Lessons completed"), f"{len(P.get('completed_lessons', []))}/{len(LESSONS)}")
        st.metric(tr("Esercizi svolti", "Exercises attempted"), len(P.get("exercise_results", {})))
    if st.button(tr("Salva il mio profilo", "Save my profile"), type="primary", key="save_profile"):
        persist(); st.success(tr("Profilo salvato!", "Profile saved!")); st.rerun()

elif page == "settings":
    P.setdefault('settings',{})
    s=P['settings']; s['name']=st.text_input(tr("Il tuo nome", "Your name"),value=s.get('name',''))
    s['pace']=st.select_slider(tr("Ritmo di studio", "Study pace"),options=[tr("Leggero","Light"),tr("Regolare","Regular"),tr("Intenso","Intensive")],value=s.get('pace',tr("Regolare","Regular")))
    if st.button(tr("Salva impostazioni", "Save settings"),type="primary"): persist(); st.success(tr("Salvato.","Saved."))
    st.divider(); st.subheader("🔐 Sicurezza account")
    with st.form("change_password_form"):
        old_pw = st.text_input("Password attuale", type="password")
        new_pw = st.text_input("Nuova password (minimo 10 caratteri, lettera e numero)", type="password")
        confirm_pw = st.text_input("Conferma nuova password", type="password")
        change_submit = st.form_submit_button("Cambia password", type="primary")
    if change_submit:
        if new_pw != confirm_pw: st.error("Le password nuove non coincidono.")
        else:
            changed, msg = auth_system.change_password(USER_EMAIL, old_pw, new_pw)
            st.success(msg) if changed else st.error(msg)
    st.subheader("Consensi facoltativi")
    current_account = auth_system.account_record(USER_EMAIL)
    consents = current_account.get("consents", {})
    with st.form("privacy_consents_form"):
        share_progress = st.checkbox("Condividi i miei progressi di studio con l'amministratore", value=consents.get('study_progress', True))
        share_files = st.checkbox("Autorizzo l'uso dei file che carico per le funzioni di studio dell'app", value=consents.get('uploaded_files', False))
        share_location = st.checkbox("Autorizzo la condivisione della mia posizione (solo se una funzione dedicata sarà implementata)", value=consents.get('location', False))
        share_device = st.checkbox("Richiedo funzioni di condivisione dispositivo con conferma esplicita per ogni sessione (non abilita accesso completo al telefono)", value=consents.get('device_sharing', False))
        save_consents = st.form_submit_button("Salva i miei consensi")
    if save_consents:
        auth_system.update_consents(USER_EMAIL, {'study_progress':share_progress,'uploaded_files':share_files,'location':share_location,'device_sharing':share_device})
        st.success("Preferenze privacy salvate. Puoi modificarle di nuovo in qualsiasi momento."); st.rerun()
    st.divider(); st.subheader(tr("Backup e dati", "Backup and data"))
    st.download_button(tr("Esporta progressi JSON", "Export progress JSON"),data=export_progress(P),file_name="engineering_academy_progress.json",mime="application/json")
    st.caption(tr("I progressi sono salvati automaticamente. EA_DATA_DIR consente di scegliere la cartella dati.","Progress is autosaved. EA_DATA_DIR lets you choose the data folder."))
    with st.expander(tr("Guida computer e cellulare", "Desktop and mobile guide")):
        tdesk,tmob=st.tabs([tr("💻 Computer", "💻 Desktop"),tr("📱 Cellulare", "📱 Mobile")])
        with tdesk: st.write(tr("Usa il menu fisso in alto per tutte le sezioni. Massimizza il browser per un laboratorio più ampio.","Use the fixed top menu for all sections. Maximise the browser for a wider lab."))
        with tmob: st.write(tr("Su cellulare apri lo stesso indirizzo locale dalla rete del computer oppure ospita l'app su un server accessibile. Il layout si adatta agli schermi piccoli; alcuni grafici si leggono meglio in orizzontale.","On mobile, open the same local address over your computer's network or host the app on an accessible server. The layout adapts to small screens; some charts are easier to read in landscape."))
    if st.button(tr("Azzera tutti i progressi", "Reset all progress")):
        P.clear(); P.update({'completed_lessons':[],'exercise_results':{},'exam_history':[],'settings':{}}); persist(); st.success(tr("Progressi azzerati.","Progress reset.")); st.rerun()

# Mini-profilo fisso nell'angolo, sempre visibile mentre si scorre la pagina.
_profile_name = html_escape(str(P.get("profile", {}).get("display_name", CURRENT_USER.get("display_name", "Khalid Talhane")) or CURRENT_USER.get("display_name", "Khalid Talhane")))
st.markdown(f'<div class="ea-fixed-profile"><span class="ea-avatar">{html_escape(str(CURRENT_USER.get("display_name", "KT")[:2].upper()))}</span><span><b>{_profile_name}</b><small>✦ TAYARAN.COM</small></span></div>', unsafe_allow_html=True)

# Assistente universale: disponibile in tutte le pagine, anche per pagine fotografate o PDF del libro.
with st.expander(tr("🤖 AI STUDIO HUB · chiedi aiuto in qualsiasi pagina", "🤖 AI STUDY HUB · get help on every page"), expanded=False):
    st.markdown(tr("Carica pagine del libro, appunti o immagini e chiedi una spiegazione, un riassunto, una traduzione, flashcard o una simulazione d'interrogazione.", "Upload textbook pages, notes or images and ask for an explanation, summary, translation, flashcards or an oral-exam simulation."))
    ai_col1, ai_col2 = st.columns([1, 1])
    with ai_col1:
        ai_language = st.selectbox(tr("Lingua della risposta", "Answer language"), ["Italiano", "English", "Español", "Français", "العربية", "Deutsch", "Português", "Qualsiasi: segui la mia domanda"], key="global_ai_language")
        ai_task = st.selectbox(tr("Cosa vuoi ottenere?", "What do you want?"), [tr("Spiegazione semplice", "Simple explanation"), tr("Riassunto e appunti", "Summary and notes"), tr("Domande e risposte per interrogazione", "Oral-exam questions and answers"), tr("Flashcard", "Flashcards"), tr("Traduzione", "Translation"), tr("Quiz per verificare se ho capito", "Quiz to check my understanding")], key="global_ai_task")
    with ai_col2:
        ai_files = st.file_uploader(tr("Pagine del libro (PDF, PNG, JPG, JPEG)", "Book pages (PDF, PNG, JPG, JPEG)"), type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True, key="global_ai_files")
        ai_question = st.text_area(tr("La tua richiesta", "Your request"), placeholder=tr("Es. spiegami questa pagina come se partissi da zero e poi fammi 5 domande.", "E.g. explain this page from scratch and then ask me five questions."), height=95, key="global_ai_question")
    if st.button(tr("✨ Studia con l'IA", "✨ Study with AI"), type="primary", key="global_ai_submit"):
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not ai_question.strip() and not ai_files:
            st.warning(tr("Scrivi una domanda o carica almeno un file.", "Write a question or upload at least one file."))
        elif not api_key:
            st.error(tr("Per analizzare file e generare risposte personalizzate serve configurare OPENAI_API_KEY. Puoi comunque usare il Tutor IA nella sezione Assistente per le guide locali.", "To analyse files and generate tailored answers, configure OPENAI_API_KEY. You can still use the AI Tutor section for local guidance."))
        else:
            try:
                from openai import OpenAI
                import base64
                client = OpenAI(api_key=api_key)
                lang_instruction = "Rispondi nella lingua: " + ai_language + "." if ai_language != "Qualsiasi: segui la mia domanda" else "Rispondi nella lingua usata nella domanda."
                task_instruction = "Compito richiesto: " + ai_task + "."
                content = [{"type": "input_text", "text": "Sei un tutor paziente e preciso. Aiuta a studiare, spiega termini e passaggi, separa i fatti dalle ipotesi e non inventare parti illeggibili del libro. Se una pagina non è chiara, dillo. Usa titoli, appunti organizzati ed esempi. " + lang_instruction + " " + task_instruction + "\nPagina/sezione corrente: " + page + "\nRichiesta: " + (ai_question.strip() or "Analizza i file caricati e crea appunti utili per studiare.")}]
                extracted = []
                for uploaded in (ai_files or []):
                    raw = uploaded.getvalue()
                    if uploaded.name.lower().endswith(".pdf"):
                        try:
                            from pypdf import PdfReader
                            reader = PdfReader(io.BytesIO(raw))
                            txt = "\n".join((pg.extract_text() or "") for pg in reader.pages[:20])
                            if txt.strip(): extracted.append("Testo estratto da " + uploaded.name + ":\n" + txt[:24000])
                            else: content.append({"type":"input_text", "text":"Il PDF " + uploaded.name + " non contiene testo estraibile; se possibile usa immagini delle pagine o un PDF con OCR."})
                        except Exception as exc:
                            content.append({"type":"input_text", "text":"Non sono riuscito a leggere il PDF " + uploaded.name + ": " + str(exc)})
                    elif uploaded.type in ("image/png", "image/jpeg"):
                        data_url = "data:" + uploaded.type + ";base64," + base64.b64encode(raw).decode("ascii")
                        content.append({"type":"input_image", "image_url":data_url, "detail":"high"})
                if extracted:
                    content.append({"type":"input_text", "text":"\n\n".join(extracted)})
                with st.spinner(tr("Sto leggendo il materiale e preparando gli appunti...", "Reading the material and preparing study notes...")):
                    response = client.responses.create(model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"), input=[{"role":"user", "content":content}])
                st.markdown(response.output_text)
            except Exception as exc:
                st.error(tr("L'assistente IA non è riuscito a completare la richiesta. Controlla connessione, chiave API e formato dei file.", "The AI assistant could not complete the request. Check connection, API key and file formats."))
                st.caption(str(exc)[:500])

st.markdown("---")
st.caption("Engineering Academy · Python + Streamlit · " + tr("Contenuti a scopo didattico.","Educational content only."))
