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
import plotly.graph_objects as go
import plotly.express as px

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
        
        # Data Adjustment Sidebar
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 🛠️ Data Adjustments")
            
            # Scale Selector
            scale_options = {
                "Actuals": 1.0,
                "Thousands (x1k)": 1000.0,
                "Millions (x1MM)": 1000000.0,
                "Billions (x1B)": 1000000000.0
            }
            current_scale_key = st.session_state.get("current_scale", "Actuals")
            selected_scale = st.selectbox(
                "Report Units (Source)", 
                list(scale_options.keys()), 
                index=list(scale_options.keys()).index(current_scale_key) if current_scale_key in scale_options else 0,
                help="If the report lists figures as '137' for $137M, select 'Millions'."
            )
            
            if selected_scale != current_scale_key:
                _apply_scale_and_rebuild(selected_scale, scale_options[selected_scale])

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
                # Save raw statements for potential re-scaling
                extractor = FinancialExtractor(pages_dict)
                statements = extractor.extract()
                
                # Store RAW statements (unscaled) for reference
                # We need to deepcopy because ModelEngine modifies them? No, but let's be safe.
                import copy
                st.session_state.raw_statements = copy.deepcopy(statements)
                st.session_state.current_scale = "Actuals"
                
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
    m1.metric("Revenue (TTM)", _format_metric(latest_inc.revenue), f"{rev_growth:+.1%}")
    m2.metric("Gross Margin", f"{gross_margin:.1%}")
    m3.metric("Operating Margin", f"{op_margin:.1%}")
    m4.metric("Net Margin", f"{net_margin:.1%}")
    
    st.markdown("---")
    
    # Charts Section
    st.subheader("Financial Trends")
    import plotly.graph_objects as go
    import pandas as pd
    
    if len(model.historical_income_statements) > 0:
        hist_data = {
            "Year": [s.period_end.year for s in model.historical_income_statements],
            "Revenue": [s.revenue for s in model.historical_income_statements],
            "Net Income": [s.net_income for s in model.historical_income_statements],
            "Operating Income": [s.operating_income for s in model.historical_income_statements]
        }
        df_chart = pd.DataFrame(hist_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_chart['Year'], 
            y=df_chart['Revenue'], 
            name='Revenue',
            marker_color='#3b82f6'
        ))
        fig.add_trace(go.Scatter(
            x=df_chart['Year'], 
            y=df_chart['Net Income'], 
            name='Net Income',
            mode='lines+markers',
            line=dict(color='#22c55e', width=3)
        ))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient historical data for visualization.")

    
def _format_metric(value):
    """Format large numbers adaptively (Full, Mil, Bil)."""
    if value is None:
        return "N/A"
    abs_val = abs(value)
    if abs_val >= 1e9:
        return f"${value/1e9:.1f} bil"
    elif abs_val >= 1e6:
        return f"${value/1e6:.1f} mil"
    else:
        return f"${value:,.0f}"

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
            "Revenue": _format_metric(inc.revenue),
            "Growth": f"{growth:.1%}",
            "Net Income": _format_metric(inc.net_income)
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

def _render_valuation(model):
    """Render Valuation tab."""
    dcf = model.dcf_valuation
    st.subheader("Discounted Cash Flow (DCF)")
    
    c1, c2 = st.columns(2)
    # Safe rendering for assumptions
    wacc = model.assumptions.wacc if model.assumptions and model.assumptions.wacc is not None else 0.0
    term_growth = model.assumptions.terminal_growth_rate if model.assumptions and model.assumptions.terminal_growth_rate is not None else 0.0
    
    c1.metric("WACC", f"{wacc:.1%}")
    c1.metric("Terminal Growth", f"{term_growth:.1%}")
    
    # Intreactive WACC Adjustment
    with st.expander("⚙️ Adjust Valuation Assumptions", expanded=True):
        new_wacc = st.slider("WACC (%)", 0.0, 20.0, float(wacc * 100), 0.1) / 100.0
        new_tg = st.slider("Terminal Growth (%)", 0.0, 5.0, float(term_growth * 100), 0.1) / 100.0
        
        if new_wacc != wacc or new_tg != term_growth:
            if st.button("Recalculate DCF"):
                # Update assumptions and re-run forecast
                model.assumptions.wacc = new_wacc
                model.assumptions.terminal_growth_rate = new_tg
                # Re-run forecast engine to update DCF
                fc = ForecastEngine(model)
                st.session_state.model = fc.forecast(model.forecast_years, model.assumptions.scenario or ScenarioType.BASE)
                st.rerun()

    if dcf and dcf.enterprise_value > 0:
        c2.metric("Enterprise Value", _format_metric(dcf.enterprise_value))
        c2.metric("Equity Value", _format_metric(dcf.equity_value))
        st.metric("Implied Price per Share", f"${dcf.implied_price_per_share:,.2f}")
    else:
        if wacc == 0:
            st.warning("⚠️ WACC is 0%. Please adjust WACC above to generate DCF.")
        else:
            st.warning("DCF Valuation could not be computed (Negative Cash Flows or NaN).")

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
            import io
            pdf_buffer = io.BytesIO()
            
            generator = ReportGenerator(model)
            generator.generate_pdf(pdf_buffer)
            pdf_data = pdf_buffer.getvalue()
            
            st.success("Report Generated!")
            st.download_button(
                label="📥 Download Investment Memo (PDF)",
                data=pdf_data,
                file_name=f"{model.ticker}_Investment_Memo.pdf",
                mime="application/pdf"
            )

def _apply_scale_and_rebuild(scale_name, scale_factor):
    """Rebuild model with scaled data."""
    import copy
    
    # Avoid infinite reruns if scale is same
    if st.session_state.get("current_scale") == scale_name:
        return

    with st.spinner(f"Rescaling data to {scale_name}..."):
        if "raw_statements" not in st.session_state:
            st.error("Raw data missing. Please upload a report first.")
            return

        # 1. Get Clean Copy
        raw = copy.deepcopy(st.session_state.raw_statements)
        
        # 2. Multiply numeric fields
        skip_fields = {'period_end', 'period_start', 'fiscal_year'}
        
        # Helper to scale object
        def scale_obj(obj):
            if hasattr(obj, '__dict__'):
                for field, value in obj.__dict__.items():
                    if field not in skip_fields and isinstance(value, (int, float)) and value is not None:
                        # Skip small numbers that look like ratios (e.g. EPS < 1000) if scaling by Million?
                        # No, if Shares are in millions, they must be scaled too.
                        # If everything is 'in millions', then everything scales.
                        # Except margins? Margins are calculated, not extracted usually.
                        setattr(obj, field, value * scale_factor)
        
        for category in ['income_statements', 'balance_sheets', 'cash_flows']:
            if category in raw:
                for stmt in raw[category]:
                    scale_obj(stmt)
        
        # 3. Rebuild
        try:
            model_engine = ModelEngine(raw)
            linked_model = model_engine.build_linked_model()
            
            fc_engine = ForecastEngine(linked_model)
            current_scenario = ScenarioType.BASE
            if "model" in st.session_state and hasattr(st.session_state.model, 'assumptions') and st.session_state.model.assumptions:
                 if st.session_state.model.assumptions.scenario:
                     current_scenario = st.session_state.model.assumptions.scenario

            final_model = fc_engine.forecast(years=5, scenario=current_scenario)
            
            st.session_state.model = final_model
            st.session_state.current_scale = scale_name
            st.success(f"Rescaled to {scale_name}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error rescaling model: {e}")
