"""Page registry and the custom sidebar (brand, navigation, promo card, profile)."""
import streamlit as st

from ui.components import esc
from ui.styles import active_nav_css

APP_NAME = "ResearchMate AI"
TAGLINE = "Research Smarter.<br>Discover More."

LOGO_SVG = (
    "<svg class='rm-logo' viewBox='0 0 64 64' xmlns='http://www.w3.org/2000/svg'>"
    "<path d='M32 22 C24 16 14 16 6 19 V50 C14 47 24 47 32 53 Z' fill='#F97316'/>"
    "<path d='M32 22 C40 16 50 16 58 19 V50 C50 47 40 47 32 53 Z' fill='#EA580C'/>"
    "<path d='M32 22 V53' stroke='#FFF0DD' stroke-width='2'/>"
    "<path d='M32 3 L35 10 L42 12 L35 14 L32 21 L29 14 L22 12 L29 10 Z' fill='#FBBF24'/>"
    "</svg>"
)

NAV_ICONS = {
    "dashboard": "M3 11.5 12 4l9 7.5v8a1.5 1.5 0 0 1-1.5 1.5H15v-6H9v6H4.5A1.5 1.5 0 0 1 3 19.5z",
    "workspace": "M4 5.5h16A2.5 2.5 0 0 1 22.5 8v7A2.5 2.5 0 0 1 20 17.5H11l-4.5 3v-3H4A2.5 2.5 0 0 1 1.5 15V8A2.5 2.5 0 0 1 4 5.5z",
    "documents": "M5 2.5h9l5 5v14H5a2 2 0 0 1-2-2v-15a2 2 0 0 1 2-2zm9 0v5h5M7 12h10M7 16h7",
    "compare": "M6 4v16M18 4v16M3 7h6M15 7h6M3 17h6M15 17h6M4 4h4l-2 3zM16 20h4l-2-3z",
    "summary": "M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm4 5h6M7 12h10M7 16h7",
    "insights": "M4 20V10M10 20V5M16 20v-8M22 20H2",
    "history": "M12 5a7 7 0 1 1-6.2 3.75M5 5v4h4M12 8v4l3 2",
    "settings": "M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7zm0-6 1 2.1a7.7 7.7 0 0 1 2 .8l2.2-0.7 1.7 1.7-.7 2.2a7.7 7.7 0 0 1 .8 2L21 11v2l-2.1 1a7.7 7.7 0 0 1-.8 2l.7 2.2-1.7 1.7-2.2-.7a7.7 7.7 0 0 1-2 .8L12 22l-2-1-1-2.1a7.7 7.7 0 0 1-2-.8l-2.2.7-1.7-1.7.7-2.2a7.7 7.7 0 0 1-.8-2L1 13v-2l2.1-1a7.7 7.7 0 0 1 .8-2l-.7-2.2 1.7-1.7 2.2.7a7.7 7.7 0 0 1 2-.8L10 2.5z",
}

AI_ART = (
    "<svg class='rm-promo-art' viewBox='0 0 180 110' xmlns='http://www.w3.org/2000/svg' "
    "aria-label='AI research assistant illustration'>"
    "<circle cx='45' cy='46' r='31' fill='#FDBA74' opacity='.45'/>"
    "<circle cx='137' cy='38' r='25' fill='#FED7AA'/>"
    "<rect x='47' y='34' width='82' height='52' rx='22' fill='#FFF7ED' stroke='#EA580C' stroke-width='3'/>"
    "<circle cx='72' cy='58' r='6' fill='#EA580C'/><circle cx='104' cy='58' r='6' fill='#EA580C'/>"
    "<path d='M78 72q10 8 20 0' fill='none' stroke='#EA580C' stroke-width='3' stroke-linecap='round'/>"
    "<path d='M88 34V22' stroke='#EA580C' stroke-width='3' stroke-linecap='round'/>"
    "<circle cx='88' cy='17' r='5' fill='#F59E0B'/><path d='M28 92h124' stroke='#F97316' stroke-width='8' stroke-linecap='round'/>"
    "</svg>"
)


def _specs():
    # imported here (not at the top) so the page modules can import this file without a loop
    from ui import classic, documents, placeholders

    return [
        ("dashboard", "Dashboard", classic.page_dashboard),
        ("workspace", "Research Workspace", classic.page_chat),
        ("documents", "My Documents", documents.page_documents),
        ("compare", "Compare Papers", classic.page_compare),
        ("summary", "Summary", classic.page_summary),
        ("insights", "Research Insights", placeholders.page_insights),
        ("history", "Research History", placeholders.page_history),
        ("settings", "Settings", placeholders.page_settings),
    ]


def build_pages():
    pages = {}
    for key, title, fn in _specs():
        options = {"default": True} if key == "dashboard" else {"url_path": key}
        pages[key] = st.Page(fn, title=title, **options)
    st.session_state["_pages"] = pages
    return pages


def goto(key):
    """Jump to a page by its key, for example goto('documents')."""
    st.switch_page(st.session_state["_pages"][key])


def render_sidebar(pages, current_title):
    with st.sidebar:
        st.markdown(
            f'<div class="rm-brand">{LOGO_SVG}<div class="rm-name">{esc(APP_NAME)}</div>'
            f'<div class="rm-tag">{TAGLINE}</div></div>',
            unsafe_allow_html=True,
        )
        current_key = "dashboard"
        for key, page in pages.items():
            if page.title == current_title:
                current_key = key
            if st.button(page.title, key=f"nav_{key}", use_container_width=True):
                st.switch_page(page)
        st.markdown(active_nav_css(current_key, NAV_ICONS), unsafe_allow_html=True)

        st.markdown(
            f'<div class="rm-promo">{AI_ART}<b>Powered by AI</b>'
            "RAG · Gemini · LangGraph</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="rm-profile"><div class="rm-avatar">R</div>'
            '<div><div class="who">Researcher</div><div class="role">Local workspace</div></div></div>',
            unsafe_allow_html=True,
        )