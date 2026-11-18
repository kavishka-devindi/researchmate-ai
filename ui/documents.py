"""My Documents: upload, search, filter, preview, analyse and delete documents."""
import os
import zlib
from datetime import datetime, timedelta
from functools import partial

import streamlit as st

from src.analysis import all_analyses, analyze_document, remove_analysis, AnalysisError, NOT_STATED
from src.history import add_entry
from src.pdf_processing import extract_pages, chunk_pages, PDFError
from src.storage import save_pdf, read_pdf, uploaded_at, delete_pdf, render_pages
from src.vector_store import add_chunks, delete_document, stored_documents, VectorStoreError
from ui.components import esc, page_header, empty_state, status_chip

SORT_OPTIONS = ["Newest first", "Oldest first", "Name (A-Z)", "Most pages"]
DATE_OPTIONS = ["All dates", "Last 7 days", "Last 30 days"]
STATUS_OPTIONS = ["All status", "Analyzed", "Processed only"]


# ---------- small helpers ----------
@st.cache_data(show_spinner=False, max_entries=64)
def _cover(name, stamp):
    images = render_pages(name, 0, 1, 280)
    return images[0] if images else None


def _key(name):
    return zlib.crc32(name.encode("utf-8"))


def _flash(kind, message):
    st.session_state.doc_flash = (kind, message)


def _records():
    analyses = all_analyses()
    records = []
    for d in stored_documents():
        name = d["File"]
        a = analyses.get(name)
        stamp = uploaded_at(name)
        records.append({
            "name": name,
            "key": _key(name),
            "title": a["title"] if a else os.path.splitext(name)[0],
            "authors": a["authors"] if a and a["authors"] != NOT_STATED else None,
            "year": a["year"] if a and a["year"] != NOT_STATED else None,
            "pages": d["Pages"],
            "stamp": stamp,
            "date": datetime.fromtimestamp(stamp).strftime("%b %d, %Y") if stamp else "Date unknown",
            "analysis": a,
        })
    return records


def _apply_filters(records, query, date_filter, status_filter, sort):
    q = query.strip().lower()
    if q:
        def haystack(r):
            a = r["analysis"] or {}
            return " ".join([r["name"], r["title"], r["authors"] or "", " ".join(a.get("keywords", []))]).lower()
        records = [r for r in records if q in haystack(r)]
    if date_filter != "All dates":
        days = 7 if date_filter == "Last 7 days" else 30
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        records = [r for r in records if r["stamp"] and r["stamp"] >= cutoff]
    if status_filter == "Analyzed":
        records = [r for r in records if r["analysis"]]
    elif status_filter == "Processed only":
        records = [r for r in records if not r["analysis"]]
    if sort == "Newest first":
        records = sorted(records, key=lambda r: r["stamp"] or 0, reverse=True)
    elif sort == "Oldest first":
        records = sorted(records, key=lambda r: r["stamp"] or 0)
    elif sort == "Name (A-Z)":
        records = sorted(records, key=lambda r: r["title"].lower())
    else:
        records = sorted(records, key=lambda r: r["pages"], reverse=True)
    return records


def _chip(rec):
    return status_chip("Analyzed ✓", "info") if rec["analysis"] else status_chip("Processed ✓", "ok")


# ---------- actions ----------
def _toggle(name):
    selected = st.session_state.setdefault("selected_docs", [])
    if st.session_state.get(f"chk_{_key(name)}"):
        if name not in selected:
            selected.append(name)
        st.session_state.preview_doc = name
    elif name in selected:
        selected.remove(name)


def _analyze(name):
    try:
        with st.spinner(f"Analysing {name}..."):
            analyze_document(name)
        _flash("success", f"{name}: analysis complete.")
    except AnalysisError as e:
        _flash("error", str(e))
    st.rerun()


def _delete(name):
    delete_document(name)
    delete_pdf(name)
    remove_analysis(name)
    selected = st.session_state.get("selected_docs", [])
    if name in selected:
        selected.remove(name)
    if st.session_state.get("preview_doc") == name:
        st.session_state.preview_doc = None
    _flash("success", f"{name} was removed.")
    st.rerun()


@st.dialog("Document preview", width="large")
def _preview_dialog(name):
    images = render_pages(name, 0, 4, 720)
    if not images:
        st.info("The original PDF is not stored for this document. Upload it again to enable previews.")
        return
    st.caption("Showing the first pages.")
    for i, png in enumerate(images, start=1):
        st.image(png, caption=f"Page {i}", width="stretch")


# ---------- upload ----------
def _upload_section():
    with st.container(border=True, key="box_upload"):
        st.markdown("##### ☁️ Upload research papers")
        files = st.file_uploader(
            "Upload research papers", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed"
        )
        st.caption("Drag and drop PDF files here. Supports multiple files.")
        analyze_after = st.checkbox(
            "Also analyse new papers (title, authors, methods). Uses 1 AI request per paper.", value=False
        )
        if st.button("Process documents", type="primary"):
            if not files:
                st.warning("Please upload at least one PDF first.")
                return
            report = []
            with st.spinner("Reading and indexing documents..."):
                for f in files:
                    try:
                        data = f.getvalue()
                        pages = extract_pages(data, f.name)
                        added = add_chunks(chunk_pages(pages))
                        save_pdf(f.name, data)          # keep a copy for preview and download
                        if added:
                            report.append(("success", f"{f.name}: ready ({added} sections indexed)."))
                            add_entry("upload", f.name)
                        else:
                            report.append(("info", f"{f.name}: already indexed (preview copy saved)."))
                        if analyze_after:
                            analyze_document(f.name)
                    except (PDFError, VectorStoreError, AnalysisError) as e:
                        report.append(("error", f"{f.name}: {e}"))
            st.session_state.doc_report = report
            st.rerun()


# ---------- cards ----------
def _grid_card(rec, selected):
    k = rec["key"]
    with st.container(border=True, key=f"card_sel_{k}" if selected else f"card_{k}"):
        st.checkbox("Select", value=selected, key=f"chk_{k}", on_change=_toggle, args=(rec["name"],),
                    label_visibility="collapsed")
        img_col, text_col = st.columns([2, 3])
        with img_col:
            cover = _cover(rec["name"], rec["stamp"])
            if cover:
                st.image(cover, width="stretch")
            else:
                st.markdown('<div class="rm-cover">📄</div>', unsafe_allow_html=True)
        with text_col:
            meta = []
            if rec["authors"]:
                meta.append(esc(rec["authors"]) + (f" ({esc(rec['year'])})" if rec["year"] else ""))
            meta.append(f"📅 {rec['date']}")
            meta.append(f"📄 {rec['pages']} pages")
            st.markdown(
                f'<div class="rm-card-title">{esc(rec["title"])}</div>'
                + "".join(f'<div class="rm-meta">{m}</div>' for m in meta)
                + _chip(rec),
                unsafe_allow_html=True,
            )
        b1, b2, b3 = st.columns(3)
        if b1.button("👁", key=f"pv_{k}", help="Preview", use_container_width=True):
            st.session_state.preview_doc = rec["name"]
            _preview_dialog(rec["name"])
        has_pdf = uploaded_at(rec["name"]) is not None
        b2.download_button("⬇", data=partial(read_pdf, rec["name"]), file_name=rec["name"],
                           mime="application/pdf", key=f"dl_{k}", help="Download" if has_pdf else "No PDF copy stored",
                           disabled=not has_pdf, use_container_width=True)
        with b3.popover("⋮", use_container_width=True):
            if not rec["analysis"]:
                if st.button("🔬 Analyse", key=f"an_{k}", use_container_width=True):
                    _analyze(rec["name"])
            sure = st.checkbox("Confirm delete", key=f"cd_{k}")
            if st.button("🗑 Delete", key=f"del_{k}", disabled=not sure, use_container_width=True):
                _delete(rec["name"])


def _list_row(rec, selected):
    k = rec["key"]
    with st.container(border=True, key=f"card_sel_{k}" if selected else f"card_{k}"):
        c_chk, c_title, c_pages, c_date, c_status, c_act = st.columns([0.5, 4, 1.2, 1.6, 1.6, 1.2])
        c_chk.checkbox("Select", value=selected, key=f"chk_{k}", on_change=_toggle, args=(rec["name"],),
                       label_visibility="collapsed")
        sub = (esc(rec["authors"]) if rec["authors"] else esc(rec["name"]))
        c_title.markdown(f'<div class="rm-card-title">{esc(rec["title"])}</div><div class="rm-meta">{sub}</div>',
                         unsafe_allow_html=True)
        c_pages.markdown(f'<div class="rm-meta">📄 {rec["pages"]} pages</div>', unsafe_allow_html=True)
        c_date.markdown(f'<div class="rm-meta">📅 {rec["date"]}</div>', unsafe_allow_html=True)
        c_status.markdown(_chip(rec), unsafe_allow_html=True)
        if c_act.button("👁", key=f"pv_{k}", help="Preview", use_container_width=True):
            st.session_state.preview_doc = rec["name"]
            _preview_dialog(rec["name"])


# ---------- preview panel ----------
def _preview_panel(rec):
    with st.container(border=True, key="panel_preview"):
        st.markdown("##### Document preview")
        if rec is None:
            st.caption("Select a document to see its details here.")
            return
        cover = _cover(rec["name"], rec["stamp"])
        if cover:
            st.image(cover, width="stretch")
        else:
            st.markdown('<div class="rm-cover">📄</div>', unsafe_allow_html=True)
        a = rec["analysis"] or {}
        rows = [
            ("Title", rec["title"]),
            ("Authors", rec["authors"] or "Not analysed yet"),
            ("Year", rec["year"] or "Not analysed yet"),
            ("Uploaded", rec["date"]),
            ("Pages", f"{rec['pages']} pages with text"),
            ("File", rec["name"]),
        ]
        if a.get("topics"):
            rows.append(("Topics", ", ".join(a["topics"])))
        table = "".join(f"<tr><td>{esc(k)}</td><td>{esc(str(v))}</td></tr>" for k, v in rows)
        st.markdown(f'<table class="rm-details">{table}</table>' + _chip(rec), unsafe_allow_html=True)
        st.write("")
        if st.button("👁 View document", type="primary", key="pp_view", use_container_width=True):
            _preview_dialog(rec["name"])
        has_pdf = uploaded_at(rec["name"]) is not None
        st.download_button("⬇ Download", data=partial(read_pdf, rec["name"]), file_name=rec["name"],
                           mime="application/pdf", key="pp_dl", disabled=not has_pdf, use_container_width=True)
        if not has_pdf:
            st.caption("Upload this PDF again to enable preview and download.")
        if not rec["analysis"]:
            if st.button("🔬 Analyse this paper", key="pp_an", use_container_width=True,
                         help="Extracts title, authors, methods and results. Uses 1 AI request."):
                _analyze(rec["name"])


# ---------- page ----------
def page_documents():
    page_header("📁", "My Documents", "Manage your research papers and explore their content.")

    flash = st.session_state.pop("doc_flash", None)
    if flash:
        getattr(st, flash[0])(flash[1])

    _upload_section()
    for kind, message in st.session_state.get("doc_report", []):
        getattr(st, kind)(message)

    records = _records()
    if not records:
        st.write("")
        empty_state("📚", "No documents yet", "Upload your first PDF above to get started.")
        return

    st.write("")
    f1, f2, f3, f4, f5 = st.columns([3, 1.4, 1.4, 1.4, 1.2])
    query = f1.text_input("Search documents", placeholder="Search by title, author or keyword...",
                          label_visibility="collapsed")
    sort = f2.selectbox("Sort", SORT_OPTIONS, label_visibility="collapsed")
    date_filter = f3.selectbox("Date", DATE_OPTIONS, label_visibility="collapsed")
    status_filter = f4.selectbox("Status", STATUS_OPTIONS, label_visibility="collapsed")
    view = f5.segmented_control("View", ["Grid", "List"], default="Grid", label_visibility="collapsed") or "Grid"

    shown = _apply_filters(records, query, date_filter, status_filter, sort)
    selected_names = [n for n in st.session_state.get("selected_docs", []) if n in {r["name"] for r in records}]
    st.session_state.selected_docs = selected_names

    preview_name = st.session_state.get("preview_doc")
    preview = next((r for r in records if r["name"] == preview_name), None)
    if preview is None and selected_names:
        preview = next((r for r in records if r["name"] == selected_names[-1]), None)
    if preview is None:
        preview = records[0]

    left, right = st.columns([2.7, 1.1], gap="large")
    with left:
        top_a, top_b = st.columns([3, 1])
        top_a.markdown(
            f'<div class="rm-count">{len(shown)} of {len(records)} documents'
            + (f" · {len(selected_names)} selected" if selected_names else "") + "</div>",
            unsafe_allow_html=True,
        )
        if selected_names and top_b.button("Clear selection", key="clear_sel", use_container_width=True):
            for n in selected_names:
                st.session_state[f"chk_{_key(n)}"] = False
            st.session_state.selected_docs = []
            st.rerun()

        if not shown:
            empty_state("🔎", "No matching documents", "Try a different search or filter.")
        elif view == "List":
            for rec in shown:
                _list_row(rec, rec["name"] in selected_names)
        else:
            for start in range(0, len(shown), 3):
                for col, rec in zip(st.columns(3), shown[start:start + 3]):
                    with col:
                        _grid_card(rec, rec["name"] in selected_names)
    with right:
        _preview_panel(preview)