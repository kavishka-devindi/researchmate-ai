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


def _specs():
    # imported here (not at the top) so the page modules can import this file without a loop
    from ui import classic, documents, placeholders

    return [
        ("dashboard", "Dashboard", "🏠", classic.page_dashboard),
        ("workspace", "Research Workspace", "💬", classic.page_chat),
        ("documents", "My Documents", "📁", documents.page_documents),
        ("compare", "Compare Papers", "⚖️", classic.page_compare),
        ("summary", "Summary", "📝", classic.page_summary),
        ("insights", "Research Insights", "📊", placeholders.page_insights),
        ("history", "Research History", "🕘", placeholders.page_history),
        ("settings", "Settings", "⚙️", placeholders.page_settings),
    ]


def build_pages():
    pages = {}
    for key, title, icon, fn in _specs():
        options = {"default": True} if key == "dashboard" else {"url_path": key}
        pages[key] = st.Page(fn, title=title, icon=icon, **options)
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
            if st.button(f"{page.icon}  {page.title}", key=f"nav_{key}", use_container_width=True):
                st.switch_page(page)
        st.markdown(active_nav_css(current_key), unsafe_allow_html=True)

        st.markdown(
            '<div class="rm-promo"><div class="big">🤖</div><b>Powered by AI</b>'
            "RAG · Gemini · LangGraph</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="rm-profile"><div class="rm-avatar">R</div>'
            '<div><div class="who">Researcher</div><div class="role">Local workspace</div></div></div>',
            unsafe_allow_html=True,
        )
        st.caption("Uses the Gemini free tier. Please avoid uploading private or sensitive documents.")