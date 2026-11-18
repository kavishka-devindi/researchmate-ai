"""Pages that are built in later steps. They say so honestly and show no fake data."""
import streamlit as st

from ui.components import page_header, empty_state


def _coming(icon, title, subtitle, items):
    page_header(icon, title, subtitle)
    empty_state("🚧", "This page is built in the next step", "Nothing on this page is simulated.")
    st.markdown("**What it will show**")
    for item in items:
        st.markdown(f"- {item}")


def page_insights():
    _coming("📊", "Research Insights", "Discover patterns, trends and gaps across your research library.", [
        "Topics, methods, keywords and publication years, taken from your analysed papers",
        "Charts for topic distribution, publication trends and methodologies",
        "Research gaps the papers mention themselves",
    ])


def page_history():
    _coming("🕘", "Research History", "Continue where you left off.", [
        "Your past conversations, summaries and comparisons, with search and filters",
        "Resume a conversation, rename it, pin it, export it or delete it",
    ])


def page_settings():
    _coming("⚙️", "Settings", "Customize your research assistant.", [
        "Answer style and source options (these control the real assistant)",
        "Retrieval settings such as how many passages are used",
        "Privacy tools: clear history, delete stored documents",
    ])