"""
Reusable UI Components for Streamlit App.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict
from ..config import config

def render_sidebar():
    """Render the application sidebar."""
    with st.sidebar:
        st.title(f"🚀 {config.APP_NAME}")
        st.caption(f"v{config.APP_VERSION}")
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🛠️ Navigation Mode")
        mode = st.radio(
            "Choose Analysis Type", 
            [m.value for m in config.AnalysisMode],
            key="app_mode_selection"
        )
        
        # Update session state
        st.session_state.app_mode = mode
        
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        
        # Model Selection (Placeholder for future llm config)
        st.selectbox("AI Model", ["Hybrid (Local + Cloud)", "Cloud Only (Fast)", "Local Only (Secure)"], index=0)
        
        st.markdown("---")
        with st.expander("ℹ️ About"):
            st.info(
                "Financial Alpha Intelligence is an advanced AI agent demonstrating "
                "financial modeling capabilities."
            )

def render_export_utility(
    tab_name: str, 
    title: str, 
    subtitle: str, 
    metrics: Dict = None,
    data_frames: Dict[str, pd.DataFrame] = None
):
    """
    Render a standardized export section at the bottom of tabs.
    Allows downloading data as CSV/Excel.
    """
    st.markdown("---")
    st.subheader(f"📥 Export {title} Data")
    st.markdown(subtitle)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if data_frames:
            for name, df in data_frames.items():
                csv = df.to_csv(index=True).encode('utf-8')
                st.download_button(
                    label=f"Download {name} (CSV)",
                    data=csv,
                    file_name=f"{name.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    key=f"dl_{tab_name}_{name}"
                )
    
    with col2:
        st.info("💡 Pro Tip: You can also generate a full PDF report in the 'Report Generation' tab.")

def apply_custom_css():
    """Apply custom CSS styles to the application."""
    st.markdown("""
        <style>
            .main {
                background-color: #f8f9fa;
            }
            .stButton>button {
                width: 100%;
                border-radius: 8px;
                height: 3em;
                background-color: #1f4788;
                color: white;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #2d5aa0;
                border-color: #2d5aa0;
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .metric-card {
                background-color: white;
                padding: 1.5rem;
                border-radius: 10px;
                border: 1px solid #e9ecef;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            h1, h2, h3 {
                color: #1f4788;
                font-family: 'Helvetica Neue', sans-serif;
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 24px;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: pre-wrap;
                background-color: white;
                border-radius: 4px 4px 0px 0px;
                gap: 1px;
                padding-top: 10px;
                padding-bottom: 10px;
            }
            .stTabs [aria-selected="true"] {
                background-color: #f0f2f6;
                border-bottom: 2px solid #1f4788;
            }
        </style>
    """, unsafe_allow_html=True)
