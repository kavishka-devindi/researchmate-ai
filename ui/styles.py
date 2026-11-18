"""Global look and feel. All colours are semi-transparent, so they work in light and dark mode."""
import streamlit as st

CSS = """
<style>
/* ---------- layout ---------- */
[data-testid="stMainBlockContainer"] {padding-top: 1.6rem; max-width: 1320px;}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(234,88,12,0.14);}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: linear-gradient(180deg, rgba(249,115,22,0.07), rgba(249,115,22,0) 45%);}

/* ---------- sidebar brand, promo and profile ---------- */
.rm-brand {text-align: center; padding: 0.4rem 0 1rem 0;}
.rm-brand .rm-logo {width: 58px; height: 58px; margin: 0 auto 0.3rem auto;}
.rm-brand .rm-name {font-size: 1.35rem; font-weight: 800; letter-spacing: -0.01em;}
.rm-brand .rm-tag {font-size: 0.82rem; opacity: 0.65; line-height: 1.25;}
.rm-promo {margin-top: 1rem; padding: 0.9rem 0.8rem; border-radius: 18px; text-align: center;
           background: linear-gradient(160deg, rgba(249,115,22,0.20), rgba(251,191,36,0.12));
           border: 1px solid rgba(234,88,12,0.22); font-size: 0.82rem;}
.rm-promo .big {font-size: 1.6rem;}
.rm-promo b {display: block; font-size: 0.95rem; margin: 0.1rem 0;}
.rm-profile {display: flex; align-items: center; gap: 0.7rem; margin-top: 0.9rem; padding: 0.7rem 0.4rem 0.2rem 0.4rem;
             border-top: 1px solid rgba(128,128,128,0.2);}
.rm-avatar {width: 2.4rem; height: 2.4rem; border-radius: 50%; display: flex; align-items: center;
            justify-content: center; font-weight: 700; color: #fff; background: linear-gradient(135deg, #F97316, #EA580C);}
.rm-profile .who {font-weight: 600; font-size: 0.9rem; line-height: 1.2;}
.rm-profile .role {opacity: 0.65; font-size: 0.78rem;}

/* sidebar navigation buttons (each has a key like nav_documents) */
div[class*="st-key-nav_"] button {justify-content: flex-start; text-align: left; border: none;
    background: transparent; box-shadow: none; border-radius: 12px; padding: 0.55rem 0.85rem; font-weight: 500;}
div[class*="st-key-nav_"] button:hover {background: rgba(234,88,12,0.12); color: inherit;}
div[class*="st-key-nav_"] button p {font-size: 0.95rem;}

/* ---------- page header banner ---------- */
.rm-header {display: flex; align-items: center; gap: 1rem; padding: 1.1rem 1.5rem; border-radius: 22px;
            margin-bottom: 1.1rem; border: 1px solid rgba(234,88,12,0.20);
            background: linear-gradient(120deg, rgba(249,115,22,0.16), rgba(251,191,36,0.07) 70%, rgba(251,191,36,0));}
.rm-header .rm-icon {width: 3.4rem; height: 3.4rem; border-radius: 16px; display: flex; align-items: center;
                     justify-content: center; font-size: 1.8rem; flex-shrink: 0;
                     background: linear-gradient(135deg, #F97316, #EA580C); box-shadow: 0 6px 14px rgba(234,88,12,0.30);}
.rm-header .rm-title {font-size: 1.9rem; font-weight: 800; line-height: 1.15; letter-spacing: -0.01em;}
.rm-header .rm-sub {opacity: 0.72; margin-top: 0.1rem;}

/* ---------- cards ---------- */
div[class*="st-key-card_"], div[class*="st-key-panel_"], div[class*="st-key-box_"] {
    border-radius: 18px; border: 1px solid rgba(234,88,12,0.16);
    box-shadow: 0 2px 10px rgba(120,60,10,0.06); transition: box-shadow .15s ease, border-color .15s ease;}
div[class*="st-key-card_"]:hover {box-shadow: 0 8px 22px rgba(234,88,12,0.14); border-color: rgba(234,88,12,0.38);}
div[class*="card_sel_"] {border: 2px solid #F97316 !important; background: rgba(249,115,22,0.06);}
.rm-card-title {font-weight: 700; line-height: 1.25; margin-bottom: 0.25rem; font-size: 0.98rem;}
.rm-meta {opacity: 0.72; font-size: 0.8rem; line-height: 1.55;}
.rm-chip {display: inline-block; padding: 0.1rem 0.6rem; border-radius: 999px; font-size: 0.74rem; font-weight: 600; margin-top: 0.3rem;}
.rm-chip.ok {background: rgba(34,197,94,0.20);}
.rm-chip.info {background: rgba(59,130,246,0.18);}
.rm-chip.warn {background: rgba(245,158,11,0.22);}
.rm-cover {width: 100%; aspect-ratio: 3/4; border-radius: 10px; display: flex; align-items: center; justify-content: center;
           font-size: 2rem; background: rgba(234,88,12,0.10); border: 1px solid rgba(234,88,12,0.18);}
.rm-details {width: 100%; font-size: 0.85rem; border-collapse: collapse;}
.rm-details td {padding: 0.22rem 0; vertical-align: top;}
.rm-details td:first-child {opacity: 0.65; width: 28%;}
.rm-empty {text-align: center; padding: 2.2rem 1rem; border-radius: 18px; border: 1.5px dashed rgba(234,88,12,0.35);
           background: rgba(249,115,22,0.04);}
.rm-empty .big {font-size: 2.4rem;}
.rm-empty b {display: block; font-size: 1.05rem; margin: 0.3rem 0 0.2rem 0;}
.rm-empty span {opacity: 0.7;}
.rm-count {font-weight: 700; font-size: 1.05rem; margin: 0.3rem 0 0.6rem 0;}

/* ---------- Streamlit widgets ---------- */
[data-testid="stBaseButton-primary"] {border-radius: 12px; font-weight: 600; border: none;
    background: linear-gradient(135deg, #F97316, #EA580C); box-shadow: 0 4px 12px rgba(234,88,12,0.28);}
[data-testid="stBaseButton-primary"]:hover {filter: brightness(1.06); box-shadow: 0 6px 16px rgba(234,88,12,0.38);}
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-popover"], [data-testid="stDownloadButton"] button {
    border-radius: 12px; border: 1px solid rgba(234,88,12,0.28);}
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-popover"]:hover {
    border-color: #EA580C; color: #EA580C;}
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {border-radius: 12px !important;}
[data-testid="stFileUploaderDropzone"] {border: 1.5px dashed rgba(234,88,12,0.45); border-radius: 16px;
    background: rgba(249,115,22,0.05);}
[data-testid="stChatMessage"] {border-radius: 16px; padding: 0.9rem 1rem; margin-bottom: 0.5rem;
    background: rgba(128,128,128,0.06); border: 1px solid rgba(128,128,128,0.14);}
[data-testid="stExpander"] {border-radius: 14px; border: 1px solid rgba(234,88,12,0.16);}
[data-testid="stAlert"] {border-radius: 14px;}

/* ---------- dashboard pieces carried over from the earlier version ---------- */
.hero {display: flex; justify-content: space-between; align-items: center; gap: 1rem;
       padding: 1.4rem 1.8rem; border-radius: 22px; margin-bottom: 1rem;
       background: linear-gradient(135deg, rgba(234,88,12,0.20), rgba(251,191,36,0.12));
       border: 1px solid rgba(234,88,12,0.28);}
.hero-title {font-size: 2rem; font-weight: 700; margin-bottom: 0.3rem;}
.hero p {margin: 0; opacity: 0.8; max-width: 34rem;}
.hero img {height: 120px; flex-shrink: 0;}
.stat-card {display: flex; align-items: center; gap: 0.9rem; padding: 1rem 1.1rem; border-radius: 16px;
            background: rgba(128,128,128,0.08); border: 1px solid rgba(128,128,128,0.22);}
.stat-card .icon {display: flex; align-items: center; justify-content: center; width: 2.8rem; height: 2.8rem;
                  border-radius: 14px; font-size: 1.4rem; background: rgba(234,88,12,0.16);}
.stat-card .num {font-size: 1.8rem; font-weight: 700; line-height: 1.1;}
.stat-card .lbl {opacity: 0.75; font-size: 0.85rem;}
.doc-row {display: flex; justify-content: space-between; align-items: center; padding: 0.55rem 0.1rem;
          border-bottom: 1px solid rgba(128,128,128,0.2);}
.doc-row:last-child {border-bottom: none;}
.pill {padding: 0.15rem 0.65rem; border-radius: 999px; font-size: 0.75rem; background: rgba(34,197,94,0.20);}
.activity {padding: 0.35rem 0; font-size: 0.92rem;}
.muted {opacity: 0.65; font-size: 0.8rem;}
.st-key-qa_upload button {background: rgba(234,88,12,0.15); border: 1px solid rgba(234,88,12,0.35);}
.st-key-qa_chat button {background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.35);}
.st-key-qa_summary button {background: rgba(124,58,237,0.14); border: 1px solid rgba(124,58,237,0.35);}
.st-key-qa_compare button {background: rgba(34,197,94,0.14); border: 1px solid rgba(34,197,94,0.35);}
.st-key-qa_upload button, .st-key-qa_chat button, .st-key-qa_summary button, .st-key-qa_compare button {
    min-height: 3.2rem; border-radius: 14px; font-weight: 600;}
.st-key-chip_summary button, .st-key-chip_compare button, .st-key-chip_docs button {
    border-radius: 999px; font-size: 0.85rem; padding: 0.15rem 0.9rem;}
</style>
"""


def inject_styles():
    st.markdown(CSS, unsafe_allow_html=True)


def active_nav_css(key):
    """Highlight the sidebar button of the page that is open."""
    return (
        "<style>"
        f".st-key-nav_{key} button {{background: linear-gradient(135deg, #F97316, #EA580C) !important; "
        "color: #fff !important; box-shadow: 0 4px 12px rgba(234,88,12,0.30) !important;}}"
        f".st-key-nav_{key} button p {{color: #fff !important; font-weight: 600;}}"
        "</style>"
    )