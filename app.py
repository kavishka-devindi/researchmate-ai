import streamlit as st

from ui.nav import APP_NAME, build_pages, render_sidebar
from ui.styles import inject_styles

st.set_page_config(page_title=APP_NAME, page_icon="📄", layout="wide")
inject_styles()

pages = build_pages()
current = st.navigation(list(pages.values()), position="hidden")
render_sidebar(pages, current.title)
current.run()