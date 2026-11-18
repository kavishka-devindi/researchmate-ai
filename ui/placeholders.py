"""Secondary workspace pages with the same visual language as the main flows."""
from html import escape as esc
import streamlit as st

from src.history import load_history, time_ago
from src.vector_store import stored_documents
from ui.components import empty_state, icon_markup, page_header
from ui.nav import goto


KIND_LABELS = {
    "question": "Question",
    "summary": "Summary",
    "comparison": "Comparison",
    "upload": "Upload",
}


def page_insights():
    docs = stored_documents()
    history = load_history()
    page_header("chart", "Research Insights", "Discover patterns and activity across your research library.")
    if not docs:
        empty_state("chart", "Insights will appear here", "Upload and process research papers to start building your library.")
        return
    stats = [
        ("Documents", len(docs), "Papers currently indexed"),
        ("Pages", sum(d["Pages"] for d in docs), "Pages with searchable text"),
        ("Sections", sum(d["Chunks"] for d in docs), "Indexed research sections"),
        ("Activities", len(history), "Saved research actions"),
    ]
    for col, (label, value, detail) in zip(st.columns(4), stats):
        col.markdown(
            f'<div class="rm-insight-stat"><div class="rm-stat-value">{value}</div>'
            f'<div class="rm-stat-label">{label}</div><div class="rm-stat-detail">{detail}</div></div>',
            unsafe_allow_html=True,
        )
    left, right = st.columns([1.2, 0.8])
    with left:
        with st.container(border=True, key="box_insights_activity"):
            st.markdown("#### Research activity")
            if history:
                for item in reversed(history[-8:]):
                    label = KIND_LABELS.get(item["kind"], "Activity")
                    st.markdown(
                        f'<div class="rm-history-row"><span class="rm-history-icon">{icon_markup("spark", "1rem")}</span>'
                        f'<div><b>{label}</b><div class="rm-meta">{item["text"]}</div></div>'
                        f'<span class="rm-history-time">{time_ago(item["time"])}</span></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Your research activity will appear here.")
    with right:
        with st.container(border=True, key="box_insights_next"):
            st.markdown("#### Build your research picture")
            st.write("Analyze documents to extract titles, authors, methods, topics and publication details.")
            if st.button("Open My Documents", type="primary", key="insights_docs"):
                goto("documents")


def page_history():
    history = load_history()
    page_header("history", "Research History", "Continue where you left off.")
    if not history:
        empty_state("history", "No research history yet", "Questions, summaries and comparisons will appear here as you work.")
        return
    search_col, type_col = st.columns([3, 1])
    query = search_col.text_input("Search history", placeholder="Search conversations, papers or analyses...",
                                  label_visibility="collapsed")
    kind = type_col.selectbox("Type", ["All types"] + list(KIND_LABELS.values()), label_visibility="collapsed")
    kind_key = next((key for key, value in KIND_LABELS.items() if value == kind), None)
    filtered = [
        item for item in reversed(history)
        if (not query.strip() or query.lower() in item["text"].lower())
        and (not kind_key or item["kind"] == kind_key)
    ]
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        with st.container(border=True, key="box_history_list"):
            st.markdown(f"#### Recent activity ({len(filtered)})")
            for index, item in enumerate(filtered):
                selected = st.session_state.get("history_selected") == index
                label = KIND_LABELS.get(item["kind"], "Activity")
                icon = {"question": "chat", "summary": "document", "comparison": "scale", "upload": "document"}[item["kind"]] if item["kind"] in {"question","summary","comparison","upload"} else "history"
                st.markdown(
                    f'<div class="rm-history-card {"rm-history-card-selected" if selected else ""}">'
                    f'<div class="rm-history-card-icon">{icon_markup(icon, "1.15rem")}</div>'
                    f'<div class="rm-history-card-main"><b>{esc(item["text"])}</b>'
                    f'<span>{esc(label)} · {time_ago(item["time"])}</span></div></div>',
                    unsafe_allow_html=True,
                )
                if st.button("Open", key=f"history_{index}", use_container_width=True,
                             type="primary" if selected else "secondary"):
                    st.session_state.history_selected = index
                    st.rerun()
    with right:
        selected_index = st.session_state.get("history_selected", 0)
        selected = filtered[selected_index] if filtered and selected_index < len(filtered) else filtered[0] if filtered else None
        with st.container(border=True, key="box_history_detail"):
            if selected:
                label = KIND_LABELS.get(selected["kind"], "Activity")
                st.markdown(
                    f'<div class="rm-history-detail"><div class="rm-history-detail-title">'
                    f'{selected["text"]}</div><span class="rm-history-badge">{label}</span></div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"Recorded {time_ago(selected['time'])}")
                st.write("")
                if selected["kind"] == "question" and st.button("Resume in Workspace", type="primary", key="resume_history"):
                    st.session_state.pending_question = selected["text"]
                    goto("workspace")
            else:
                st.caption("Select an activity to view its details.")


def page_settings():
    page_header("settings", "Settings", "Customize your research assistant.")
    settings = st.session_state.setdefault(
        "settings",
        {"smart": True, "show_steps": True, "compact": False},
    )
    settings.setdefault("smart", True)
    settings.setdefault("show_steps", True)

    tabs = st.tabs(["General", "AI Model", "Retrieval & Documents", "Privacy & Data"])
    with tabs[0]:
        left, right = st.columns([0.85, 1.15], gap="large")
        with left:
            st.markdown(
                '<div class="rm-settings-art">'
                '<svg viewBox="0 0 360 260" xmlns="http://www.w3.org/2000/svg" aria-label="Research assistant illustration">'
                '<circle cx="180" cy="136" r="96" fill="#FFF7ED" opacity=".72"/>'
                '<ellipse cx="180" cy="226" rx="125" ry="10" fill="#7C2D12" opacity=".10"/>'
                '<rect x="112" y="82" width="136" height="92" rx="38" fill="#FFF7ED" stroke="#F97316" stroke-width="7"/>'
                '<rect x="132" y="104" width="96" height="50" rx="20" fill="#1F2937"/>'
                '<circle cx="158" cy="129" r="7" fill="#FFF7ED"/><circle cx="202" cy="129" r="7" fill="#FFF7ED"/>'
                '<path d="M166 145q14 10 28 0" fill="none" stroke="#F97316" stroke-width="5" stroke-linecap="round"/>'
                '<path d="M180 82V58" stroke="#EA580C" stroke-width="7" stroke-linecap="round"/>'
                '<circle cx="180" cy="48" r="11" fill="#F59E0B"/><circle cx="180" cy="48" r="5" fill="#FFF7ED"/>'
                '<path d="M112 126q-30 8-25 44 4 34 40 23" fill="#FB923C" stroke="#EA580C" stroke-width="6"/>'
                '<path d="M248 126q30 8 25 44-4 34-40 23" fill="#FB923C" stroke="#EA580C" stroke-width="6"/>'
                '<rect x="70" y="177" width="220" height="42" rx="20" fill="#FFF7ED" stroke="#EA580C" stroke-width="7"/>'
                '<path d="M96 176v-28h168v28" fill="#F97316" stroke="#EA580C" stroke-width="7"/>'
                '<rect x="84" y="154" width="192" height="22" rx="8" fill="#FDBA74"/>'
                '<rect x="142" y="145" width="76" height="21" rx="8" fill="#EA580C"/>'
                '<circle cx="82" cy="66" r="18" fill="#FED7AA"/><circle cx="278" cy="92" r="14" fill="#FDBA74"/>'
                '</svg></div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### Your Research Assistant")
            st.caption("Powered by AI. Built for researchers.")
        with right:
            with st.container(border=True, key="box_settings_general"):
                st.markdown("#### General preferences")
                mode = st.radio(
                    "Answer mode",
                    ["Smart assistant", "Quick answer"],
                    index=0 if settings["smart"] else 1,
                    horizontal=True,
                )
                settings["smart"] = mode == "Smart assistant"
                settings["show_steps"] = st.toggle(
                    "Show how answers were found",
                    value=settings["show_steps"],
                )
                st.caption("These settings are used by Research Workspace.")
    with tabs[1]:
        st.info("The active model is configured through the application environment.")
    with tabs[2]:
        st.info("Document retrieval settings are managed by the indexing pipeline.")
    with tabs[3]:
        with st.container(border=True, key="box_settings_privacy"):
            st.markdown("#### Privacy and data")
            st.caption("Your documents and history are stored in this local workspace.")
