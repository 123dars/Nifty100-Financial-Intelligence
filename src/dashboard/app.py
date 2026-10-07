import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('''
<style>
    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
        text-align: center;
        animation: fadeIn 1.5s ease-in-out;
    }
    .hero-title {
        font-size: 4rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #00FF7F, #00BFFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        font-size: 1.5rem;
        color: #A0A0A0;
        max-width: 700px;
        margin-bottom: 40px;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>

<div class="hero-container">
    <div class="hero-title">Nifty 100 Intelligence Platform</div>
    <div class="hero-subtitle">Institutional-grade financial analytics, peer comparisons, and automated screener for India's top 100 equities.</div>
    <div style="color: #444; font-size: 0.9rem; margin-top: 50px;">Please select a module from the sidebar to begin.</div>
</div>
''', unsafe_allow_html=True)
st.markdown('''
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
''', unsafe_allow_html=True)
