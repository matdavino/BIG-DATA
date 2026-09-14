import streamlit as st
from utils.style import inject_css, render_sidebar # <--- Importa anche render_sidebar

st.set_page_config(
    page_title="MA CH STAI DICENN",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
render_sidebar() # <--- Disegna la sidebar qui

# ── Homepage — contenuto principale ───────────────────────────
st.markdown(
    """
    <div style="display:flex;flex-direction:column;align-items:center;
                justify-content:center;height:60vh;gap:0.5rem;">
        <div style="font-size:3rem;">🎙️</div>
        <div style="text-align: center; line-height: 1.2;">
    <div style="font-size:4.0rem; font-weight:600; background: linear-gradient(135deg, #023e8a 0%, #00b4d8 25%, #caf0f8 50%, #0077b6 75%, #03045e 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: inline-block;">
        MA CH STAI DICENN
    </div>
    <br>
    <div style="font-size:1.8rem; font-weight:500; font-style: italic; background: linear-gradient(135deg, #4b5563 0%, #9ca3af 25%, #f3f4f6 50%, #6b7280 75%, #374151 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: inline-block; margin-top: -10px;">
        PARLA CHIARO
    </div>
</div>
        <div style="font-size:0.9rem;color:#555;">
            Seleziona una sezione dalla barra laterale per iniziare.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)