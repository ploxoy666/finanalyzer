"""
Deep Report Analyzer UI Module.
Handles the main workflow: PDF Upload -> Extraction -> Analysis -> Reporting.
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from pathlib import Path
from loguru import logger

from ..config import config, ScenarioType
from ..core.pdf_parser import PDFParser
from ..core.financial_extractor import FinancialExtractor
from ..core.model_engine import ModelEngine
from ..core.forecast_engine import ForecastEngine
from ..core.report_generator import ReportGenerator
from ..models.schemas import ForecastAssumptions

# Optional AI components
try:
    from ..core.summarizer import FinancialSummarizer
    from ..core.sentiment_analyzer import SentimentAnalyzer
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

from .components import render_export_utility

def render_report_analyzer():
    """Render the main Deep Report Intelligence interface."""
    st.markdown("## 📄 Deep Report Intelligence")
    st.info("Upload 10-K/10-Q PDF files for full automated analysis, 3-statement modeling, and valuation.")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload Financial Report (PDF)", type="pdf")
    
    if uploaded_file:
        _process_file_upload(uploaded_file)
    
    # Display Results if analysis is complete
    if st.session_state.get("analysis_complete") and "model" in st.session_state:
        model = st.session_state.model
        
        # Tabs for result visualization
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Executive Dashboard", 
            "📈 Financials & Forecast", 
            "💎 Valuation (DCF)", 
            "🧠 AI Risk & Sentiment",
            "📥 Report Generation"
        ])
        
        with tab1:
            _render_dashboard(model)
            
        with tab2:
            _render_financials(model)
            
        with tab3:
            _render_valuation(model)
            
        with tab4:
             _render_ai_analysis(model)
             
        with tab5:
            _render_report_generation(model)


def _process_file_upload(uploaded_file):
    """Handle file processing workflow."""
    if st.button("🚀 Analyze Report"):
        with st.status("Running Financial Alpha Intelligence...", expanded=True) as status:
            try:
                # 1. Save temp file
                status.write("📂 Reading PDF file...")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                
                # 2. Parse PDF
                status.write("🔍 Extracting text and tables (OCR)...")
                parser = PDFParser(tmp_path)
                data = parser.extract()
                
                # 3. Extract Financials
                status.write("🔢 Identifying financial statements...")
                # Fix: FinancialExtractor expects Dict[int, str], but parser returns List[str]
                pages_dict = {i: p for i, p in enumerate(data['pages'])}
                extractor = FinancialExtractor(pages_dict)
                statements = extractor.extract()
                
                # 4. Build Model
                status.write("🏗️ Building 3-Statement Model...")
                model_engine = ModelEngine(statements)
                linked_model = model_engine.build_linked_model()
                
                # 5. Forecast & Valuation
                status.write("🔮 Generating Forecasts & DCF Valuation...")
                fc_engine = ForecastEngine(linked_model)
                
                # Use default assumptions initially
                final_model = fc_engine.forecast(years=5, scenario=ScenarioType.BASE)
                
                # 6. AI Analysis (Async-like)
                if AI_AVAILABLE:
                    status.write("🧠 Running AI Sentiment & Risk Analysis...")
                    summarizer = FinancialSummarizer(api_key=config.api.HF_API_KEY)
                    sentiment = SentimentAnalyzer(api_key=config.api.HF_API_KEY)
                    
                    full_text = data['text']
                    st.session_state.ai_summary = summarizer.summarize(full_text)
                    st.session_state.ai_risks = summarizer.extract_risks(full_text)
                    st.session_state.ai_sentiment = sentiment.analyze_report(data['pages'])
                
                # Store results
                st.session_state.model = final_model
                st.session_state.analysis_complete = True
                
                # Cleanup
                os.unlink(tmp_path)
                status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                st.rerun()
                
            except Exception as e:
                status.update(label="❌ Error Occurred", state="error")
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Processing error: {e}")

def _render_dashboard(model):
    """Render Executive Dashboard tab."""
    st.subheader(f"Executive Summary: {model.company_name}")
    
    # Styled AI Summary (Moved to top for visibility)
    if st.session_state.get("ai_summary"):
        st.markdown(f"""
        <div style="
            padding: 20px; 
            background-color: rgba(30, 41, 59, 1); 
            border: 1px solid #334155; 
            border-radius: 10px; 
            margin-bottom: 20px;
            color: #e2e8f0;
        ">
            <h3 style="margin-top: 0; color: #60a5fa;">🧠 AI Key Findings</h3>
            <div style="font-size: 1.05em; line-height: 1.6;">
                {st.session_state.ai_summary}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    
    # Key Metrics
    latest_inc = model.historical_income_statements[-1]
    forecast_inc = model.forecast_income_statements[0]
    
    # Metrics Calculation
    rev_growth = 0.0
    if len(model.historical_income_statements) > 1:
        prev_rev = model.historical_income_statements[-2].revenue
        if prev_rev and prev_rev > 0:
            rev_growth = (latest_inc.revenue - prev_rev) / prev_rev

    # Calculate margins safely
    gross_margin = (latest_inc.gross_profit / latest_inc.revenue) if latest_inc.revenue else 0.0
    op_margin = (latest_inc.operating_income / latest_inc.revenue) if latest_inc.revenue else 0.0
    net_margin = (latest_inc.net_income / latest_inc.revenue) if latest_inc.revenue else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Revenue (TTM)", f"${latest_inc.revenue/1e9:.1f}B", f"{rev_growth:+.1%}")
    m2.metric("Gross Margin", f"{gross_margin:.1%}")
    m3.metric("Operating Margin", f"{op_margin:.1%}")
    m4.metric("Net Margin", f"{net_margin:.1%}")
    
    st.markdown("---")
    
    # Charts (Placeholder for now, can add Plotly later)
    st.info("Visualizations are generated in the Report tab.")

def _render_financials(model):
    """Render Financials tab with forecast controls."""
    st.subheader("Financial Forecast")
    
    # Scenario Controls
    col_s1, col_s2 = st.columns(2)
    scenario = col_s1.selectbox("Growth Scenario", [s.value for s in ScenarioType], index=0)
    
    if st.button("Update Forecast"):
        fc_engine = ForecastEngine(model)
        new_model = fc_engine.forecast(years=5, scenario=scenario)
        st.session_state.model = new_model
        st.rerun()
    
    # Display Forecast Table
    rows = []
    
    # Initial previous revenue for growth calc
    prev_revenue = model.historical_income_statements[-1].revenue if model.historical_income_statements else 0
    
    for inc in model.forecast_income_statements:
        # Calculate growth
        growth = 0.0
        if prev_revenue and prev_revenue > 0:
            growth = (inc.revenue - prev_revenue) / prev_revenue
        prev_revenue = inc.revenue
        
        rows.append({
            "Year": inc.period_end.year,
            "Revenue": f"${inc.revenue:,.0f}",
            "Growth": f"{growth:.1%}",
            "Net Income": f"${inc.net_income:,.0f}"
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

def _render_valuation(model):
    """Render Valuation tab."""
    dcf = model.dcf_valuation
    st.subheader("Discounted Cash Flow (DCF)")
    
    c1, c2 = st.columns(2)
    c1.metric("WACC", f"{model.assumptions.wacc:.1%}")
    c1.metric("Terminal Growth", f"{model.assumptions.terminal_growth_rate:.1%}")
    
    c2.metric("Enterprise Value", f"${dcf.enterprise_value:,.0f}")
    c2.metric("Equity Value", f"${dcf.equity_value:,.0f}")
    
    st.metric("Implied Price per Share", f"${dcf.implied_price_per_share:,.2f}")

def _render_ai_analysis(model):
    """Render AI Analysis tab."""
    st.subheader("🧠 Sentiment & Risk Analysis")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Key Risks")
        if st.session_state.get("ai_risks"):
            for risk in st.session_state.ai_risks:
                st.warning(f"• {risk}")
        else:
            st.info("AI analysis not available.")
            
    with c2:
        st.markdown("### Sentiment Analysis")
        sent = st.session_state.get("ai_sentiment")
        if sent:
            st.metric("Dominant Sentiment", sent['dominant_sentiment'].upper())
            st.progress(sent['breakdown'].get('positive', 0))
            st.caption(f"Positive Score: {sent['breakdown'].get('positive', 0):.0%}")

def _render_report_generation(model):
    """Render Report Generation tab."""
    st.subheader("📄 Generate PDF Report")
    
    if st.button("Generate Comprehensive Investment Memo"):
        with st.spinner("Generating PDF..."):
            generator = ReportGenerator(model)
            pdf_data = generator.generate_pdf()
            
            st.success("Report Generated!")
            st.download_button(
                label="📥 Download Investment Memo (PDF)",
                data=pdf_data,
                file_name=f"{model.ticker}_Investment_Memo.pdf",
                mime="application/pdf"
            )
