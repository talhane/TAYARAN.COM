CSS = r'''<style>
:root{--ea-bg:#171316;--ea-panel:#241d22;--ea-panel2:#30252c;--ea-text:#f6edf1;--ea-muted:#c8b7c0;--ea-accent:#d88ca4;--ea-accent2:#9b7bd1;--ea-border:#4a3943}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{background:#171316;color:var(--ea-text)}
.stApp{background:radial-gradient(ellipse at 8% 0%,rgba(216,140,164,.2),transparent 30%),radial-gradient(ellipse at 92% 15%,rgba(56,189,248,.15),transparent 27%),radial-gradient(ellipse at 55% 90%,rgba(20,184,166,.12),transparent 30%),linear-gradient(160deg,#12141e,#21191f 52%,#111e2a);background-size:160% 160%;animation:eaFondenteGlow 18s ease-in-out infinite alternate;color:var(--ea-text)}
@keyframes eaFondenteGlow{0%{background-position:0% 0%}100%{background-position:100% 100%}}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:#4a3943!important;border-radius:16px!important}
[data-testid="stPlotlyChart"], [data-testid="stImage"]{border-radius:16px;overflow:hidden}
hr{border-color:#4a3943!important;opacity:.85}
.block-container{padding-top:1rem;max-width:1500px;padding-bottom:3rem}
[data-testid="stHeader"]{background:rgba(23,19,22,.88)}
[data-testid="stMetric"],div[data-testid="stExpander"] details,[data-testid="stForm"],div[data-testid="stDataFrame"],div[data-testid="stTable"]{background:rgba(42,32,39,.88);border:1px solid var(--ea-border);border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,.18)}
[data-testid="stMetric"]{padding:14px}
[data-testid="stMetricLabel"],[data-testid="stMetricValue"],p,li,label,h1,h2,h3,h4{color:var(--ea-text)}
[data-testid="stCaptionContainer"],.stMarkdown small{color:var(--ea-muted)}
.stButton>button,.stDownloadButton>button{border-radius:12px;border:1px solid #e3a8bd;background:linear-gradient(110deg,#9f526e,#7957a8);color:#fff;font-weight:700;transition:transform .15s,filter .15s}
.stButton>button:hover,.stDownloadButton>button:hover{filter:brightness(1.12);transform:translateY(-1px);border-color:#f5cad9}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#21171e,#30212b 60%,#211a26);color:var(--ea-text);border-right:1px solid var(--ea-border)}
[data-testid="stSidebar"] *{color:inherit}
.ea-hero{padding:1.35rem 1.5rem;border:1px solid #775263;border-radius:22px;background:radial-gradient(circle at 82% 20%,rgba(56,189,248,.35),transparent 24%),radial-gradient(circle at 12% 90%,rgba(20,184,166,.28),transparent 28%),linear-gradient(120deg,#27151f,#453047 45%,#163044);color:#fff;margin-bottom:1rem;box-shadow:0 14px 35px rgba(0,0,0,.25)}
.ea-chip{display:inline-block;border:1px solid #dba8bc;border-radius:999px;padding:.25rem .7rem;margin:.2rem;font-size:.82rem;background:#ffffff10;color:#fff}
/* Space/ocean ambience, depth and luminous cards */
.ea-space-decoration{pointer-events:none;position:fixed;inset:0;z-index:0;opacity:.22;background-image:radial-gradient(2px 2px at 20px 30px,#fff,transparent),radial-gradient(1px 1px at 80px 110px,#9fe8ff,transparent),radial-gradient(2px 2px at 170px 70px,#fff,transparent),radial-gradient(1px 1px at 240px 190px,#e8b7ff,transparent);background-size:280px 220px;animation:eaStars 45s linear infinite}
@keyframes eaStars{from{transform:translateY(0)}to{transform:translateY(-220px)}}
[data-testid="stAppViewContainer"]>.main{position:relative;z-index:1}
[data-testid="stVerticalBlockBorderWrapper"]{background:linear-gradient(145deg,rgba(48,40,52,.9),rgba(20,38,51,.82));box-shadow:0 12px 28px rgba(0,0,0,.2),inset 0 1px 0 rgba(255,255,255,.04);transition:transform .18s,border-color .18s}
[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:#7c9cae!important}
.ea-orbit{float:right;font-size:1.35rem;letter-spacing:.35rem;color:#c4f1ff;text-shadow:0 0 18px #57c7ff;animation:eaOrbit 8s linear infinite}
@keyframes eaOrbit{to{transform:rotate(360deg)}}
/* Fixed/sticky navigation bar: remains visible while scrolling */
.st-key-ea_topnav{position:sticky;top:0;z-index:9999;background:rgba(20,24,34,.98);backdrop-filter:blur(16px);border:1px solid #4a3943;border-radius:16px;padding:.5rem .7rem;margin:0 0 1rem;box-shadow:0 10px 26px rgba(0,0,0,.32)}
.st-key-ea_topnav [data-testid="stRadio"]>label{font-size:.72rem;font-weight:800;letter-spacing:.12em;color:#e8bacb}
.st-key-ea_topnav [role="radiogroup"]{gap:.35rem;flex-wrap:wrap}
.st-key-ea_topnav [role="radiogroup"] label{background:linear-gradient(135deg,#30252c,#183244);border:1px solid #466276;border-radius:999px;padding:.35rem .65rem;transition:all .15s}
.st-key-ea_topnav [role="radiogroup"] label:has(input:checked){background:linear-gradient(110deg,#9f526e,#7957a8);border-color:#e6aec4}
input,textarea,[data-baseweb="select"]>div{background-color:#20232e!important;color:#fff!important;border-color:#536678!important}
[data-testid="stAlert"]{border-radius:14px}
/* Improve scroll offset and avoid a large empty top region. */
.st-key-ea_topnav{scroll-margin-top:0}
[data-testid="stMainBlockContainer"]{position:relative;z-index:1}
[data-testid="stFileUploader"] section{background:linear-gradient(135deg,rgba(20,184,166,.08),rgba(155,123,209,.12));border:1px dashed #64879a;border-radius:16px}
[data-testid="stTabs"] button[role="tab"]{border-radius:12px}
@media(prefers-reduced-motion:reduce){.stApp,.ea-space-decoration,.ea-orbit{animation:none!important;transition:none!important}}
@media(max-width:700px){.block-container{padding:.6rem .7rem 2rem}.ea-hero{padding:1rem;border-radius:15px}h1{font-size:1.55rem!important}[data-testid="stMetric"]{padding:8px}.st-key-ea_topnav{padding:.3rem}.st-key-ea_topnav [role="radiogroup"]{gap:.2rem}.st-key-ea_topnav [role="radiogroup"] label{padding:.25rem .45rem}}
/* Trading-terminal inspired interface: compact dark chrome, cyan highlights and clear chart surfaces. */
:root{--ea-bg:#0b0e11;--ea-panel:#131722;--ea-panel2:#1e222d;--ea-text:#d1d4dc;--ea-muted:#787b86;--ea-accent:#2962ff;--ea-accent2:#00bfa5;--ea-border:#2a2e39}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{background:#0b0e11;color:#d1d4dc}
.stApp{background:radial-gradient(ellipse at 12% 0%,rgba(41,98,255,.15),transparent 28%),radial-gradient(ellipse at 88% 35%,rgba(0,191,165,.1),transparent 27%),linear-gradient(160deg,#0b0e11,#111724 55%,#10131a);background-size:180% 180%;animation:eaFondenteGlow 24s ease-in-out infinite alternate}
.st-key-ea_topnav{position:fixed!important;top:2.7rem!important;left:50%!important;transform:translateX(-50%)!important;width:min(calc(100vw - 2rem),1460px)!important;z-index:100000!important;background:rgba(19,23,34,.98)!important;backdrop-filter:blur(18px);border:1px solid #2a2e39!important;border-radius:10px!important;padding:.45rem .65rem!important;margin:0!important;box-shadow:0 8px 26px #0009!important}
[data-testid="stMainBlockContainer"]{padding-top:7.4rem!important}
.st-key-ea_topnav [data-testid="stRadio"]>label{font-size:.68rem!important;font-weight:800;letter-spacing:.12em;color:#8b98ad!important}
.st-key-ea_topnav [role="radiogroup"]{gap:.25rem!important;flex-wrap:nowrap!important;overflow-x:auto!important;scrollbar-width:thin;padding-bottom:2px}
.st-key-ea_topnav [role="radiogroup"] label{white-space:nowrap;background:transparent!important;border:1px solid transparent!important;border-radius:7px!important;padding:.4rem .62rem!important;transition:all .16s}
.st-key-ea_topnav [role="radiogroup"] label:hover{background:#252a36!important;border-color:#3b4252!important}
.st-key-ea_topnav [role="radiogroup"] label:has(input:checked){background:#2962ff!important;border-color:#2962ff!important;color:white!important;box-shadow:0 0 18px #2962ff40}
[data-testid="stMetric"],div[data-testid="stExpander"] details,[data-testid="stForm"],div[data-testid="stDataFrame"],div[data-testid="stTable"]{background:rgba(19,23,34,.92);border:1px solid #2a2e39;border-radius:10px;box-shadow:0 6px 18px #0002}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:#2a2e39!important;border-radius:12px!important;background:linear-gradient(145deg,rgba(24,29,42,.95),rgba(16,25,34,.9));box-shadow:0 8px 24px #0003,inset 0 1px 0 #ffffff08;transition:transform .18s,border-color .18s}
[data-testid="stVerticalBlockBorderWrapper"]:hover{border-color:#2962ff!important;transform:translateY(-1px)}
.stButton>button,.stDownloadButton>button{border-radius:8px!important;border:1px solid #2962ff!important;background:linear-gradient(110deg,#2962ff,#147dbe)!important;color:#fff!important;font-weight:700;transition:transform .15s,filter .15s}
.stButton>button:hover,.stDownloadButton>button:hover{filter:brightness(1.14);transform:translateY(-1px)}
.ea-hero{border-color:#2b5685!important;background:radial-gradient(circle at 82% 20%,#2962ff40,transparent 24%),radial-gradient(circle at 12% 90%,#00bfa530,transparent 28%),linear-gradient(120deg,#131722,#172b3c 55%,#102b2b)!important;border-radius:14px!important}
.ea-profile-hero{position:relative;overflow:hidden;padding:1.5rem;border:1px solid #2962ff80;border-radius:16px;background:radial-gradient(circle at 88% 15%,#00bfa545,transparent 22%),radial-gradient(circle at 20% 120%,#2962ff50,transparent 40%),linear-gradient(125deg,#131722,#162337 55%,#102c2b);box-shadow:0 16px 40px #0005;margin-bottom:1rem}
.ea-profile-hero h1{margin:.35rem 0;color:#fff!important}.ea-profile-hero p{color:#c2cad8}.ea-profile-kicker{font-size:.7rem;letter-spacing:.16em;color:#7fb7ff;font-weight:800}.ea-profile-tags{display:flex;gap:.5rem;flex-wrap:wrap;margin-top:1rem}.ea-profile-tags span{padding:.35rem .65rem;border:1px solid #52677c;border-radius:999px;background:#101923b8;color:#d9eaff;font-size:.82rem}.ea-profile-orb{float:right;font-size:3rem;color:#8be9ff;text-shadow:0 0 25px #2962ff;animation:eaOrbit 14s linear infinite}
.ea-fixed-profile{position:fixed;right:16px;bottom:14px;z-index:100001;display:flex;align-items:center;gap:9px;padding:8px 13px 8px 8px;border:1px solid #3b5f82;border-radius:999px;background:rgba(19,23,34,.96);backdrop-filter:blur(14px);box-shadow:0 8px 26px #0009;color:#eef5ff;font-size:.78rem;max-width:240px;pointer-events:none}.ea-fixed-profile b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:160px}.ea-fixed-profile small{display:block;color:#78c8ff;font-size:.58rem;letter-spacing:.14em}.ea-avatar{display:flex;align-items:center;justify-content:center;width:36px;height:36px;flex-shrink:0;border-radius:50%;background:linear-gradient(135deg,#2962ff,#00bfa5);color:white;font-weight:900;box-shadow:0 0 18px #2962ff55}
input,textarea,[data-baseweb="select"]>div{background-color:#151a25!important;color:#fff!important;border-color:#354052!important}
[data-testid="stHeader"]{background:rgba(11,14,17,.94)}
@media(max-width:700px){.st-key-ea_topnav{top:2.4rem!important;width:calc(100vw - 1rem)!important;padding:.25rem!important}[data-testid="stMainBlockContainer"]{padding-top:9rem!important}.st-key-ea_topnav [role="radiogroup"]{flex-wrap:wrap!important;max-height:130px;overflow-y:auto}.ea-fixed-profile{right:8px;bottom:8px;max-width:190px}.ea-fixed-profile b{max-width:120px}.ea-profile-hero{padding:1rem}}

/* Secure login screen, compact terminal-style cards. */
.ea-login-hero{position:relative;overflow:hidden;padding:1.2rem 1.4rem;margin:.2rem 0 1rem;border:1px solid #2962ff70;border-radius:14px;background:radial-gradient(circle at 86% 12%,#00bfa545,transparent 23%),radial-gradient(circle at 12% 95%,#2962ff45,transparent 34%),linear-gradient(125deg,#131722,#17273a 55%,#102b2a);box-shadow:0 18px 42px #0005}
.ea-login-hero h1{color:#fff!important;margin:.25rem 0;font-size:clamp(1.7rem,4vw,2.5rem)}.ea-login-hero p{color:#c1ccdc;margin:.3rem 0}
.ea-login-orb{float:right;font-size:2.7rem;color:#79e8ff;text-shadow:0 0 24px #2962ff;animation:eaOrbit 12s linear infinite}
[data-testid="stTabs"] [role="tablist"]{gap:.25rem;border-bottom:1px solid #2a2e39}
[data-testid="stTabs"] button[role="tab"]{border-radius:8px 8px 0 0;padding:.55rem .85rem}
.ea-fixed-profile{max-width:min(240px,calc(100vw - 1rem))}

</style>'''
