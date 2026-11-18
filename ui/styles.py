"""Global look and feel for the workspace."""
import streamlit as st

CSS = """
<style>
/* ---------- design tokens ---------- */
:root {
    --rm-primary: #f97316;
    --rm-primary-dark: #ea580c;
    --rm-primary-soft: rgba(249,115,22,0.10);
    --rm-border: rgba(120,76,30,0.14);
    --rm-shadow: 0 8px 24px rgba(120,76,30,0.07);
}

/* ---------- layout ---------- */
[data-testid="stAppViewContainer"] {background: #fffaf3;}
[data-testid="stMainBlockContainer"] {padding-top: 2rem; max-width: 1320px;}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(234,88,12,0.15);}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: linear-gradient(180deg, #fff5e8 0%, #fffaf3 48%, #fffaf3 100%);}
[data-testid="stSidebar"] > div:first-child {padding: 1.5rem 1rem 1rem;}
h1, h2, h3, h4 {letter-spacing: -0.025em;}

/* ---------- subtle scrollbars and focus ---------- */
* {scrollbar-color: #fdba74 transparent; scrollbar-width: thin;}
*:focus-visible {outline: 2px solid rgba(249,115,22,0.55); outline-offset: 2px;}

/* ---------- sidebar brand, promo and profile ---------- */
.rm-brand {text-align: center; padding: 0.25rem 0.55rem 1.2rem 0.55rem;}
.rm-brand .rm-logo {width: 58px; height: 58px; margin: 0 auto 0.3rem auto;}
.rm-brand .rm-name {font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em;}
.rm-brand .rm-tag {font-size: 0.82rem; opacity: 0.65; line-height: 1.25;}
.rm-promo {margin-top: 1.1rem; padding: 0.9rem 0.8rem; border-radius: 14px; text-align: center;
           background: linear-gradient(160deg, rgba(249,115,22,0.16), rgba(251,191,36,0.10));
           border: 1px solid rgba(234,88,12,0.18); font-size: 0.82rem;}
.rm-promo-art {display: block; width: 100%; height: 5.2rem; margin-bottom: 0.25rem;}
.rm-promo .big {font-size: 1.6rem;}
.rm-promo b {display: block; font-size: 0.95rem; margin: 0.1rem 0;}
.rm-profile {display: flex; align-items: center; gap: 0.7rem; margin-top: 0.9rem; padding: 0.7rem 0.4rem 0.2rem 0.4rem;
             border-top: 1px solid rgba(128,128,128,0.2);}
.rm-avatar {width: 2.4rem; height: 2.4rem; border-radius: 50%; display: flex; align-items: center;
            justify-content: center; font-weight: 700; color: #fff; background: linear-gradient(135deg, #fb923c, #ea580c);}
.rm-profile .who {font-weight: 600; font-size: 0.9rem; line-height: 1.2;}
.rm-profile .role {opacity: 0.65; font-size: 0.78rem;}

/* sidebar navigation buttons (each has a key like nav_documents) */
div[class*="st-key-nav_"] button {justify-content: flex-start; text-align: left; border: none;
    background: transparent; box-shadow: none; border-radius: 10px; padding: 0.62rem 0.85rem; font-weight: 500;}
div[class*="st-key-nav_"] button:hover {background: rgba(249,115,22,0.10); color: inherit;}
div[class*="st-key-nav_"] button p {font-size: 0.95rem;}
div[class*="st-key-nav_"] button::before {content: ""; width: 1.2rem; height: 1.2rem; margin-right: 0.75rem;
    flex: 0 0 1.2rem; background: currentColor; -webkit-mask: var(--rm-nav-icon) center / contain no-repeat;
    mask: var(--rm-nav-icon) center / contain no-repeat;}

/* ---------- page header banner ---------- */
.rm-header {display: flex; align-items: center; gap: 1rem; padding: 1.25rem 1.5rem; border-radius: 18px;
            margin-bottom: 1.35rem; border: 1px solid rgba(234,88,12,0.16);
            background: linear-gradient(120deg, rgba(249,115,22,0.14), rgba(251,191,36,0.08) 70%, transparent);}
.rm-header .rm-icon {width: 3.4rem; height: 3.4rem; border-radius: 16px; display: flex; align-items: center;
                     justify-content: center; font-size: 1.8rem; flex-shrink: 0;
                     background: linear-gradient(135deg, #fb923c, #ea580c); box-shadow: 0 6px 14px rgba(234,88,12,0.25);}
.rm-inline-icon {display: block; color: currentColor;}
.rm-header .rm-title {font-size: 1.9rem; font-weight: 800; line-height: 1.15; letter-spacing: -0.01em;}
.rm-header .rm-sub {opacity: 0.72; margin-top: 0.1rem;}

/* ---------- cards ---------- */
div[class*="st-key-card_"], div[class*="st-key-panel_"], div[class*="st-key-box_"] {
    border-radius: 16px; border: 1px solid var(--rm-border); background: rgba(255,255,255,0.74);
    box-shadow: var(--rm-shadow); transition: box-shadow .15s ease, border-color .15s ease;}
div[class*="st-key-card_"]:hover {box-shadow: 0 14px 34px rgba(120,76,30,0.12); border-color: rgba(234,88,12,0.35);}
div[class*="card_sel_"] {border: 2px solid var(--rm-primary) !important; background: var(--rm-primary-soft);}
.rm-card-title {font-weight: 700; line-height: 1.25; margin-bottom: 0.25rem; font-size: 0.98rem;}
.rm-card-title {display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;}
.rm-pdf-icon {display: inline-grid; place-items: center; width: 1.5rem; height: 1.65rem; margin-right: 0.4rem;
    border-radius: 3px; color: #fff; background: #dc2626; font-size: 0.48rem; font-weight: 800;
    letter-spacing: -0.02em; vertical-align: -0.25rem;}
.rm-meta {opacity: 0.72; font-size: 0.8rem; line-height: 1.55;}
.rm-chip {display: inline-block; padding: 0.1rem 0.6rem; border-radius: 999px; font-size: 0.74rem; font-weight: 600; margin-top: 0.3rem;}
.rm-chip.ok {background: rgba(34,197,94,0.20);}
.rm-chip.info {background: rgba(59,130,246,0.18);}
.rm-chip.warn {background: rgba(245,158,11,0.22);}
.rm-cover {width: 100%; aspect-ratio: 3/4; border-radius: 10px; display: flex; align-items: center; justify-content: center;
           font-size: 2rem; background: rgba(249,115,22,0.08); border: 1px solid rgba(234,88,12,0.16);}
.rm-details {width: 100%; font-size: 0.85rem; border-collapse: collapse;}
.rm-details td {padding: 0.22rem 0; vertical-align: top;}
.rm-details td:first-child {opacity: 0.65; width: 28%;}
.rm-details td:last-child {overflow-wrap: anywhere; word-break: break-word;}
.rm-empty {text-align: center; padding: 2.2rem 1rem; border-radius: 16px; border: 1.5px dashed rgba(234,88,12,0.30);
           background: rgba(249,115,22,0.035);}
.rm-empty .big {font-size: 2.4rem;}
.rm-empty b {display: block; font-size: 1.05rem; margin: 0.3rem 0 0.2rem 0;}
.rm-empty span {opacity: 0.7;}
.rm-count {font-weight: 700; font-size: 1.05rem; margin: 0.3rem 0 0.6rem 0;}

/* ---------- Streamlit widgets ---------- */
[data-testid="stBaseButton-primary"] {border-radius: 10px; font-weight: 600; border: none;
    background: linear-gradient(135deg, #fb923c, #ea580c); box-shadow: 0 4px 12px rgba(234,88,12,0.24);}
[data-testid="stBaseButton-primary"]:hover {filter: brightness(1.06); box-shadow: 0 6px 16px rgba(234,88,12,0.34);}
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-popover"], [data-testid="stDownloadButton"] button {
    border-radius: 10px; border: 1px solid rgba(100,116,139,0.28);}
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-popover"]:hover {
    border-color: var(--rm-primary); color: var(--rm-primary);}
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {border-radius: 12px !important;}
[data-testid="stFileUploaderDropzone"] {border: 1.5px dashed rgba(234,88,12,0.40); border-radius: 14px;
    background: rgba(249,115,22,0.04);}
[data-testid="stChatMessage"] {border-radius: 16px; padding: 0.9rem 1rem; margin-bottom: 0.5rem;
    background: rgba(128,128,128,0.06); border: 1px solid rgba(128,128,128,0.14);}
[data-testid="stExpander"] {border-radius: 12px; border: 1px solid var(--rm-border);}
[data-testid="stAlert"] {border-radius: 14px;}

/* ---------- dashboard pieces carried over from the earlier version ---------- */
.hero {display: flex; justify-content: space-between; align-items: center; gap: 1rem;
       padding: 1.4rem 1.8rem; border-radius: 22px; margin-bottom: 1rem;
       background: linear-gradient(135deg, rgba(249,115,22,0.18), rgba(251,191,36,0.12));
       border: 1px solid rgba(234,88,12,0.20);}
.hero-title {font-size: 2rem; font-weight: 700; margin-bottom: 0.3rem;}
.hero p {margin: 0; opacity: 0.8; max-width: 34rem;}
.hero img {height: 120px; flex-shrink: 0;}
.stat-card {display: flex; align-items: center; gap: 0.9rem; padding: 1rem 1.1rem; border-radius: 16px;
            background: rgba(128,128,128,0.08); border: 1px solid rgba(128,128,128,0.22);}
.stat-card .icon {display: flex; align-items: center; justify-content: center; width: 2.8rem; height: 2.8rem;
                  border-radius: 14px; font-size: 1.4rem; background: rgba(249,115,22,0.14);}
.stat-card .num {font-size: 1.8rem; font-weight: 700; line-height: 1.1;}
.stat-card .lbl {opacity: 0.75; font-size: 0.85rem;}
.doc-row {display: flex; justify-content: space-between; align-items: center; padding: 0.55rem 0.1rem;
          border-bottom: 1px solid rgba(128,128,128,0.2);}
.doc-row:last-child {border-bottom: none;}
.doc-row-main {display: flex; align-items: center; gap: 0.55rem; min-width: 0;}
.doc-row-main > div:last-child {min-width: 0;}
.doc-row-main b {display: block; max-width: 16rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;}
.rm-pdf-inline {display: inline-flex; margin-right: 0.45rem; vertical-align: middle;}
.activity {display: flex; align-items: center; gap: 0.45rem; min-width: 0;}
.activity-icon {display: inline-grid; place-items: center; width: 1.55rem; height: 1.55rem; flex: 0 0 auto;
    border-radius: 8px; color: #ea580c; background: rgba(249,115,22,0.10);}
.rm-insight-banner {display: flex; align-items: center; min-height: 9.5rem; margin-top: 1rem; padding: 1rem 1.15rem;
    border: 1px solid rgba(234,88,12,0.14); border-radius: 16px; overflow: hidden;
    background: linear-gradient(120deg, rgba(255,247,237,0.96), rgba(254,215,170,0.72));}
.rm-insight-banner > div {position: relative; z-index: 1; width: 58%;}
.rm-insight-banner b {display: block; font-size: 1.05rem; margin-bottom: 0.35rem;}
.rm-insight-banner span {display: block; font-size: 0.78rem; line-height: 1.45; opacity: 0.72;}
.rm-insight-banner .rm-insight-cta {display: inline-flex; width: fit-content; margin-top: 0.65rem; padding: 0.42rem 0.75rem;
    border-radius: 999px; color: #fff; background: #ea580c; opacity: 1; font-weight: 700;}
.rm-insight-art {width: 42%; height: 8rem; margin-left: auto;}
.pill {padding: 0.15rem 0.65rem; border-radius: 999px; font-size: 0.75rem; background: rgba(34,197,94,0.20);}
.activity {padding: 0.35rem 0; font-size: 0.92rem;}
.muted {opacity: 0.65; font-size: 0.8rem;}
.st-key-qa_upload button {background: rgba(249,115,22,0.14); border: 1px solid rgba(234,88,12,0.28);}
.st-key-qa_chat button {background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.35);}
.st-key-qa_summary button {background: rgba(124,58,237,0.14); border: 1px solid rgba(124,58,237,0.35);}
.st-key-qa_compare button {background: rgba(34,197,94,0.14); border: 1px solid rgba(34,197,94,0.35);}
.st-key-qa_upload button, .st-key-qa_chat button, .st-key-qa_summary button, .st-key-qa_compare button {
    min-height: 3.2rem; border-radius: 14px; font-weight: 600;}
.st-key-chip_summary button, .st-key-chip_compare button, .st-key-chip_docs button {
    border-radius: 999px; font-size: 0.85rem; padding: 0.15rem 0.9rem;}
.rm-insight-stat {padding: 1rem 1.1rem; border: 1px solid rgba(234,88,12,0.14); border-radius: 14px;
    background: rgba(255,255,255,0.74); box-shadow: var(--rm-shadow);}
.rm-stat-value {font-size: 1.7rem; font-weight: 800; color: #c2410c;}
.rm-stat-label {font-weight: 700; margin-top: 0.25rem;}
.rm-stat-detail, .rm-history-time {font-size: 0.76rem; opacity: 0.62;}
.rm-history-row {display: flex; align-items: center; gap: 0.7rem; padding: 0.65rem 0;
    border-bottom: 1px solid rgba(120,76,30,0.10);}
.rm-history-row:last-child {border-bottom: 0;}
.rm-history-icon {display: grid; place-items: center; width: 2rem; height: 2rem; border-radius: 9px;
    color: #ea580c; background: rgba(249,115,22,0.12); flex-shrink: 0;}
.rm-history-row > div {flex: 1;}
.rm-settings-art {height: 18rem; border-radius: 18px; position: relative; overflow: hidden;
    background: linear-gradient(145deg, #ffedd5, #fed7aa 60%, #fdba74);}
.rm-settings-orb {position: absolute; width: 8rem; height: 8rem; border-radius: 50%; left: 25%; top: 20%;
    background: rgba(255,255,255,0.72); box-shadow: 5rem 2rem 0 rgba(255,255,255,0.38);}
.rm-settings-book {position: absolute; width: 8rem; height: 3rem; left: 28%; bottom: 28%;
    border-radius: 6px; background: #ea580c; transform: rotate(-8deg); box-shadow: 0 0.8rem 0 #f97316, 0 1.6rem 0 #fb923c;}
.rm-history-detail {padding: 0.2rem 0;}
.rm-history-detail-title {font-size: 1.25rem; font-weight: 800; line-height: 1.25;}
.rm-history-badge {display: inline-block; padding: 0.25rem 0.55rem; margin: 0.65rem 0;
    border-radius: 999px; color: #9a3412; background: rgba(249,115,22,0.12); font-size: 0.74rem; font-weight: 700;}
.rm-history-card {display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; padding: 0.75rem 0.8rem;
    border: 1px solid rgba(234,88,12,0.10); border-radius: 12px; background: rgba(255,255,255,0.78);}
.rm-history-card-selected {border: 1.5px solid rgba(249,115,22,0.55); background: rgba(255,237,213,0.65);}
.rm-history-card-icon {display: grid; place-items: center; width: 2.25rem; height: 2.25rem; flex: 0 0 auto;
    border-radius: 9px; color: #ea580c; background: rgba(249,115,22,0.11);}
.rm-history-card-main {min-width: 0;}
.rm-history-card-main b {display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    max-width: 24rem; font-size: 0.9rem;}
.rm-history-card-main span {display: block; margin-top: 0.18rem; color: #64748b; font-size: 0.76rem;}
div[class*="st-key-box_history_list"] button {min-height: 2rem; border-radius: 9px;}
.rm-settings-art {height: 18rem;}
.rm-settings-art svg {width: 100%; height: 100%; display: block;}
.rm-setting-row {display: flex; justify-content: space-between; align-items: center; padding: 0.8rem 0.2rem;
    border-bottom: 1px solid rgba(120,76,30,0.10);}
.rm-setting-row:last-child {border-bottom: 0;}
.rm-setting-row span {color: #64748b;}

</style>
"""


def inject_styles():
    st.markdown(CSS, unsafe_allow_html=True)


def active_nav_css(key, icons):
    """Highlight the sidebar button of the page that is open."""
    icon_css = []
    for nav_key, path in icons.items():
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='{path}' fill='none' stroke='%23000000' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'/></svg>"
        icon_css.append(
            f".st-key-nav_{nav_key} button {{--rm-nav-icon: url(\"data:image/svg+xml,{svg}\");}}"
        )
    return (
        "<style>"
        + "".join(icon_css)
        + f".st-key-nav_{key} button {{background: linear-gradient(135deg, #fb923c, #ea580c) !important; "
        + "color: #fff !important; box-shadow: 0 4px 12px rgba(234,88,12,0.24) !important;}}"
        + f".st-key-nav_{key} button p {{color: #fff !important; font-weight: 600;}}"
        "</style>"
    )