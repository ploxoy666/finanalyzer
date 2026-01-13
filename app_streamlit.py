import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import tempfile
from pathlib import Path
from loguru import logger
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
matplotlib.use('Agg') # Prevent Segfault on Mac
import sys

# Import Core Modules
from src.core.pdf_parser import PDFParser
from src.core.gaap_ifrs_classifier import GaapIfrsClassifier
from src.core.financial_extractor import FinancialExtractor
from src.core.model_engine import ModelEngine
from src.core.forecast_engine import ForecastEngine
from src.core.report_generator import ReportGenerator
from src.core.sentiment_analyzer import SentimentAnalyzer # FinBERT
from src.core.market_data import MarketDataProvider
from src.core.summarizer import FinancialSummarizer
try:
    from src.core.markov_integration import run_markov_chain_analysis
    MARKOV_AVAILABLE = True
except ImportError:
    MARKOV_AVAILABLE = False

from src.core.snapshot_service import SnapshotService

def render_export_utility(tab_name, title, subtitle, metrics=None, data_frames=None, figures=None):
    """Adds a standardized export section at the bottom of tabs."""
    st.write("---")
    with st.expander(f"📸 Export {tab_name} View", expanded=False):
        col_ex1, col_ex2 = st.columns(2)
        
        # 1. PDF Snapshot
        with col_ex1:
            if st.button(f"📄 Generate PDF Snapshot", key=f"btn_pdf_{tab_name}"):
                with st.spinner("Preparing document..."):
                    pdf_buffer = SnapshotService.create_pdf_snapshot(title, subtitle, data_frames, metrics, figures)
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer,
                        file_name=f"Snapshot_{tab_name.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{tab_name}"
                    )
        
        # 2. Data Exports
        with col_ex2:
            if data_frames:
                for df_name, df in data_frames.items():
                    csv = df.to_csv(index=True).encode('utf-8')
                    st.download_button(
                        label=f"📊 Download {df_name} (CSV)",
                        data=csv,
                        file_name=f"{df_name.replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"dl_csv_{tab_name}_{df_name}"
                    )
            else:
                st.info("No table data available for CSV export in this view.")
        
        st.markdown("*Note: For charts, use the camera icon 📸 in the top right of the diagram to save as high-quality PNG.*")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Financial Analyzer AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "model" not in st.session_state:
    st.session_state.model = None
if "sentiment" not in st.session_state:
    st.session_state.sentiment = None
if "markov_results" not in st.session_state:
    st.session_state.markov_results = None
if "ai_summary" not in st.session_state:
    st.session_state.ai_summary = None
if "ai_narrative" not in st.session_state:
    st.session_state.ai_narrative = None
if "ai_risks" not in st.session_state:
    st.session_state.ai_risks = []

def process_file():
    if not uploaded_file:
        return

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    progress_bar = st.progress(0, text="Initializing...")
    status_text = st.empty()

    try:
        # 1. Parsing
        progress_bar.progress(10, text="Step 1/6: Parsing PDF structure...")
        parser = PDFParser(tmp_path)
        extracted_data = parser.extract()
        
        # 2. Classification
        progress_bar.progress(30, text="Step 2/6: Classifying GAAP vs IFRS...")
        classifier = GaapIfrsClassifier()
        standard, confidence, evidence = classifier.classify(" ".join(extracted_data['pages']))
        st.toast(f"Standard: {standard.value} ({confidence:.0%})", icon="✅")

        # 3. Sentiment Analysis (FinBERT)
        sentiment_result = None
        if use_sentiment:
            progress_bar.progress(40, text="Step 3/6: Analyzing Sentiment (FinBERT)...")
            try:
                analyzer = SentimentAnalyzer(api_key=hf_token)
                sentiment_result = analyzer.analyze_report(extracted_data['pages'])
                if sentiment_result.get('dominant_sentiment'):
                    st.toast(f"Sentiment: {sentiment_result['dominant_sentiment'].title()}", icon="🧠")
                else:
                    st.warning("⚠️ FinBERT skipped: Local execution disabled on Cloud to prevent crash. Provide a Hugging Face Token in Settings.")
            except Exception as e:
                st.error(f"FinBERT Error: {e}")

        # 4. Data Extraction (Local)
        progress_bar.progress(50, text="Step 4/6: Extracting Financial Data...")
        pages_dict = {i: page for i, page in enumerate(extracted_data['pages'])}
        local_extractor = FinancialExtractor(pages_dict)
        statements = local_extractor.extract()

        # 5. Market Data (Optional)
        progress_bar.progress(60, text="Step 5/7: Fetching Market Data...")
        market_data = None
        ticker = statements.ticker
        if not ticker:
            ticker = MarketDataProvider.get_ticker_from_name(statements.company_name)
        
        if ticker:
            market_data = MarketDataProvider.fetch_data(ticker)
            if market_data:
                statements.ticker = ticker
                st.toast(f"Market Data Found: {ticker}", icon="💹")
                if market_data.get('shares_outstanding'):
                    for s in statements.income_statements:
                        s.shares_outstanding_diluted = market_data['shares_outstanding']

        # 6. Modeling
        progress_bar.progress(75, text="Step 6/7: Building Linked Model...")
        model_engine = ModelEngine(statements)
        linked_model = model_engine.build_linked_model()
        linked_model.market_data = market_data

        # 7. Forecasting
        progress_bar.progress(85, text="Step 7/7: Generating Forecasts...")
        forecast_engine = ForecastEngine(linked_model)
        final_model = forecast_engine.forecast(years=forecast_years)
        final_model = forecast_engine.generate_investment_advice(sentiment_result=sentiment_result)
        
        # 8. AI Insights (Summary & Risks)
        progress_bar.progress(90, text="Step 8/8: Distilling AI Insights...")
        summarizer = FinancialSummarizer(api_key=hf_token)
        full_sample = "\n".join(list(pages_dict.values())[:10])
        ai_summary = summarizer.summarize(full_sample)
        ai_risks = summarizer.extract_risks(full_sample)
        ai_narrative = summarizer.generate_executive_narrative(final_model, ai_summary)
        
        final_model.ai_summary = ai_summary
        final_model.ai_risks = ai_risks
        final_model.ai_narrative = ai_narrative

        # 7. Report Generation
        progress_bar.progress(95, text="Generating PDF...")
        generator = ReportGenerator(final_model, sentiment_data=sentiment_result)
        
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        report_name = f"Financial_Analysis_{uploaded_file.name.replace('.pdf', '')}.pdf"
        report_path = os.path.join(output_dir, report_name)
        generator.generate_pdf(report_path)

        # Store in session
        st.session_state.model = final_model
        st.session_state.report_path = report_path
        st.session_state.sentiment = sentiment_result
        st.session_state.market_data = market_data
        st.session_state.markov_results = None 
        st.session_state.ai_summary = ai_summary
        st.session_state.ai_risks = ai_risks
        st.session_state.ai_narrative = ai_narrative
        st.session_state.analysis_complete = True
        
        progress_bar.progress(100, text="Done!")
        status_text.success("Analysis Complete!")
        st.rerun()

    except Exception as e:
        st.error(f"An error occurred: {e}")
        logger.exception(e)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# Custom CSS for modern look
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
    }
    .stButton>button:hover {
        background-color: #3b6bbf;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    h1, h2, h3 {
        color: #1f4788;
        font-family: 'Helvetica Neue', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

from datetime import date

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/272/272525.png", width=80)
    st.title("Settings")
    
    st.markdown("### 🧠 AI Features")
    use_sentiment = st.toggle("Enable FinBERT Analysis", value=True)
    hf_token = st.text_input("Hugging Face API Token", type="password", help="Optional. Uses Cloud API instead of local CPU.")
    
    st.markdown("---")
    st.markdown("### 📊 Forecast Settings")
    forecast_years = st.slider("Forecast Period (Years)", 3, 10, 5)
    growth_scenario = st.selectbox("Growth Scenario", ["Base", "Aggressive", "Conservative"])
    
    st.markdown("---")
    st.info("💡 **Note:** Financial Data is extracted using advanced Regex pattern matching.")

# --- MAIN CONTENT ---
st.title("🚀 Financial Alpha Intelligence")

# Mode Selection
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "🔎 Quick Market Pulse"

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🛠️ Navigation Mode")
    mode = st.radio("Choose Analysis Type", ["🔎 Quick Market Pulse", "📄 Deep Report Intelligence", "🦄 Private / Startup Valuator"])
    st.session_state.app_mode = mode

if st.session_state.app_mode == "🔎 Quick Market Pulse":
    st.markdown("Get immediate technical signals, peer comparisons, and price predictions just by entering a ticker.")
    quick_ticker = st.text_input("Enter Stock Ticker (e.g., TSLA, NVDA)", value="", placeholder="AAPL").upper()
    if st.button("🚀 Analyze Market Pulse"):
        if quick_ticker:
            with st.spinner(f"Fetching market data for {quick_ticker}..."):
                m_data = MarketDataProvider.fetch_data(quick_ticker)
                if m_data and m_data.get('current_price'):
                    st.session_state.market_data = m_data
                    st.session_state.analysis_complete = True
                    # In quick mode, we don't have a full extracted model, so we create a stub
                    # to make common UI components work
                    from src.models.schemas import LinkedModel, ReportType, AccountingStandard
                    from datetime import date
                    stub_model = type('Stub', (), {
                        'ticker': quick_ticker,
                        'company_name': m_data['long_name'],
                        'target_price': m_data.get('current_price', 0), # Default to current price if no DCF
                        'report_type': ReportType.FORM_10K,
                        'base_year': date.today().year,
                        'accounting_standard': AccountingStandard.GAAP,
                        'forecast_years': 0,
                        'historical_income_statements': [],
                        'historical_balance_sheets': [],
                        'forecast_income_statements': [],
                        'dcf_valuation': None,
                        'upside_potential': 0,
                        'recommendation': "NEUTRAL",
                        'investment_thesis': "Market pulse mode: Technical & Probability signals only."
                    })
                    st.session_state.model = stub_model
                    st.toast(f"Pulse analysis ready for {quick_ticker}", icon="✅")
                else:
                    st.error("Could not fetch data for this ticker. Please check the symbol.")
        else:
            st.warning("Please enter a ticker symbol.")

elif st.session_state.app_mode == "🦄 Private / Startup Valuator":
    st.markdown("## 🦄 Startup & Private Company Valuation")
    st.info("Build professional 3-Statement Models and DCF Valuations from manual drivers - perfect for pre-IPO companies.")

    p_tab1, p_tab2 = st.tabs(["✍️ Driver Inputs", "📂 Excel Upload (Beta)"])

    with p_tab1:
        with st.form("startup_drivers"):




            st.markdown("### 🏢 Company Basics")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_company = st.text_input("Company Name", "My Startup Inc")
                p_rev = st.number_input("Last Year Revenue ($)", min_value=0.0, value=1000000.0, step=100000.0)
                p_ni = st.number_input("Last Year Net Income ($)", value=100000.0, step=50000.0)
                p_shares = st.number_input("Total Shares Outstanding", min_value=1, value=1000000, step=10000)
            with col_p2:
                p_currency = st.selectbox("Currency", ["USD", "EUR", "GBP"])
                p_cash = st.number_input("Current Cash Balance ($)", min_value=0.0, value=250000.0)
                p_debt = st.number_input("Total Debt ($)", min_value=0.0, value=0.0)

            st.markdown("### 📈 Growth & Margin Drivers")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                p_growth = st.slider("Proj. Annual Growth (%)", -20, 200, 25) / 100
            with col_d2:
                p_gross_margin = st.slider("Gross Margin (%)", 0, 100, 60) / 100
            with col_d3:
                p_op_margin = st.slider("Operating Margin (%)", -50, 50, 15) / 100
            
            st.markdown("### 🎯 Valuation Targets (Reverse DCF)")
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                p_target_val = st.number_input("Target Valuation ($)", min_value=0.0, value=10000000.0, step=1000000.0)
            with col_v2:
                p_target_irr = st.slider("Target Investor IRR (%)", 10, 50, 25) / 100

            submit_startup = st.form_submit_button("🚀 Generate Valuation Model")

        if submit_startup:
            with st.spinner("Synthesizing financial model from drivers..."):
                from src.models.schemas import LinkedModel, ReportType, AccountingStandard, FinancialStatements, IncomeStatement, BalanceSheet, CashFlowStatement, ForecastAssumptions, Currency
                
                # 1. Create Baseline Financial Statements (Synthetic)
                curr_date = date.today()
                base_is = IncomeStatement(
                    period_start=date(curr_date.year-1, 1, 1),
                    period_end=date(curr_date.year-1, 12, 31),
                    currency=p_currency,
                    revenue=p_rev,
                    cost_of_revenue=p_rev * (1 - p_gross_margin),
                    gross_profit=p_rev * p_gross_margin,
                    operating_income=p_rev * p_op_margin,
                    net_income=p_ni,
                    shares_outstanding_basic=p_shares,
                    shares_outstanding_diluted=p_shares
                )
                
                # Simplified BS
                base_bs = BalanceSheet(
                    period_end=date(curr_date.year-1, 12, 31),
                    currency=p_currency,
                    total_assets=p_cash + (p_rev * 0.2), # Approx
                    cash_and_equivalents=p_cash,
                    total_liabilities=p_debt,
                    short_term_debt=0,
                    long_term_debt=p_debt,
                    total_shareholders_equity=(p_cash + (p_rev * 0.2)) - p_debt,
                    common_stock=p_shares # Storing shares count in common stock field for simpler retrieval if needed, though strictly it's value
                )
                
                # Simplified CF
                base_cf = CashFlowStatement(
                    period_start=date(curr_date.year-1, 1, 1),
                    period_end=date(curr_date.year-1, 12, 31),
                    currency=p_currency,
                    net_income=p_ni,
                    cash_from_operations=p_ni, # simplified
                    net_change_in_cash=0,
                    cash_beginning_of_period=p_cash,
                    cash_end_of_period=p_cash
                )
                
                stmts = FinancialStatements(
                    company_name=p_company,
                    fiscal_year=curr_date.year-1,
                    report_type=ReportType.ANNUAL_REPORT,
                    accounting_standard=AccountingStandard.GAAP,
                    currency=p_currency,
                    income_statements=[base_is],
                    balance_sheets=[base_bs],
                    cash_flow_statements=[base_cf]
                )
                
                # 2. Build Model
                engine = ModelEngine(stmts)
                linked_model = engine.build_linked_model()
                # Manually inject market data for simpler processing downstream
                linked_model.market_data = {'shares_outstanding': p_shares, 'current_price': 0, 'currency': p_currency}
                
                # 3. Forecast
                assumptions = ForecastAssumptions(
                    revenue_growth_rate=p_growth,
                    gross_margin=p_gross_margin,
                    operating_margin=p_op_margin,
                    tax_rate=0.21,
                    capex_percent_of_revenue=0.03,
                    wacc=0.12 # Startup Cost of Capital default
                )
                
                fc_engine = ForecastEngine(linked_model)
                final_model = fc_engine.forecast(years=forecast_years, assumptions=assumptions)
                
                # 3.1 Force DCF Calculation for Base Case
                final_model = fc_engine.generate_investment_advice(sentiment_result=None)
                
                # 4. Reverse DCF
                reverse_dcf = fc_engine.calculate_reverse_dcf(p_target_val, p_target_irr)
                final_model.reverse_dcf = reverse_dcf
                
                # 5. AI Narrative
                final_model.ai_summary = f"Generated startup model for {p_company} based on user drivers. Projected growth: {p_growth:.1%}."
                final_model.investment_thesis = f"Targeting ${p_target_val:,.0f} valuation requires sustaining {reverse_dcf.required_growth_rate:.1%} CAGR."
                final_model.recommendation = "VC TRACK"
                
                # 6. Generate PDF Report
                from src.core.report_generator import ReportGenerator
                generator = ReportGenerator(final_model, sentiment_data=None)
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                report_name = f"Startup_Valuation_{p_company.replace(' ', '_')}.pdf"
                report_path = os.path.join(output_dir, report_name)
                generator.generate_pdf(report_path)
                
                st.session_state.model = final_model
                st.session_state.report_path = report_path
                st.session_state.analysis_complete = True
                st.session_state.market_data = linked_model.market_data # Use injected data
                st.toast("Startup Model Generated!", icon="🦄")
                st.rerun()

    with p_tab2:
        st.info("🔜 Excel Upload coming in next update. Use 'Driver Inputs' for now.")

else:
    st.markdown("Upload an Annual/Quarterly Report (PDF) to generate a full 3-Statement Model with DCF and AI Sentiment Analysis.")
    uploaded_file = st.file_uploader("Drop PDF here", type=['pdf'])
    if uploaded_file:
        if st.button("🚀 Start Deep Analysis", type="primary"):
            process_file()



# --- SENSITIVITY SIDEBAR ---
if st.session_state.analysis_complete and st.session_state.model and (st.session_state.app_mode == "📄 Deep Report Intelligence" or st.session_state.app_mode == "🦄 Private / Startup Valuator"):
    if st.session_state.model.dcf_valuation:
        with st.sidebar:
            st.header("⚡ Sensitivity Analysis")
            st.write("Stress-test the valuation by adjusting key drivers.")
            
            orig_growth = st.session_state.model.assumptions.revenue_growth_rate
            orig_wacc = st.session_state.model.dcf_valuation.wacc_used
            
            new_growth = st.slider("Revenue Growth (%)", -10.0, 50.0, float(orig_growth*100), 1.0) / 100
            new_wacc = st.slider("Discount Rate (WACC %)", 4.0, 20.0, float(orig_wacc*100), 0.5) / 100
            
            if st.button("🔄 Recalculate DCF"):
                # Update assumptions and re-forecast
                from src.core.forecast_engine import ForecastEngine
                st.session_state.model.assumptions.revenue_growth_rate = new_growth
                st.session_state.model.assumptions.wacc = new_wacc
                
                # Re-run forecast engine
                engine = ForecastEngine(st.session_state.model)
                # Clear previous forecasts
                st.session_state.model.forecast_income_statements = []
                st.session_state.model.forecast_balance_sheets = []
                st.session_state.model.forecast_cash_flows = []
                st.session_state.model.forecast_ratios = []
                
                # Generate new forecast and recalculate DCF/Advice
                st.session_state.model = engine.forecast(years=forecast_years)
                st.session_state.model = engine.generate_investment_advice(sentiment_result=st.session_state.sentiment)
                
                st.toast("Valuation Updated!", icon="📊")
                st.rerun()

if st.session_state.analysis_complete and st.session_state.model:
    model = st.session_state.model
    sentiment = st.session_state.sentiment
    is_report_mode = st.session_state.app_mode == "📄 Deep Report Intelligence"
    is_q = False
    
    if is_report_mode and hasattr(model, 'report_type'):
        is_q = (model.report_type.value == "10-Q")
        report_label = "Quarterly (Annualized)" if is_q else "Annual Report"
        st.markdown(f"**📑 Report Mode:** {report_label}")
    else:
        st.markdown(f"**📑 Report Mode:** Ticker-Only Pulse")
    
    # 1. KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    if is_report_mode and model.historical_income_statements:
        hist_inc = model.historical_income_statements[-1]
        with col1:
            rev_msg = "FY 2025 (Est)" if is_q else "FY 2025"
            st.metric("Revenue", f"${hist_inc.revenue:,.0f}", delta=rev_msg)
        with col2:
            margin_str = f"{hist_inc.net_income/hist_inc.revenue:.1%} Margin" if hist_inc.revenue > 0 else "N/A Margin"
            st.metric("Net Income", f"${hist_inc.net_income:,.0f}", delta=margin_str)
    elif st.session_state.market_data:
        mkt = st.session_state.market_data
        with col1:
            st.metric("Price", f"${mkt['current_price']:,.2f}")
        with col2:
            mcap = mkt.get('market_cap')
            mcap_str = f"${mcap/1e9:,.1f}B" if mcap else "N/A"
            st.metric("Market Cap", mcap_str)
    
    with col3:
        if sentiment:
            score = sentiment['composite_score']
            label = sentiment['dominant_sentiment'].upper()
            st.metric("AI Sentiment", label, delta=f"{score:.2f} Score")
        else:
            st.metric("AI Sentiment", "OFF")
            
    with col4:
        st.metric("Forecast Growth", f"Base Case", delta=f"{forecast_years} Years")
        
    # 2. Market Context (Extra Cards if available)
    if st.session_state.market_data:
        mkt = st.session_state.market_data
        st.info(f"💹 **Live Market Data:** {mkt['long_name']} ({mkt['ticker']})")
        m2_col1, m2_col2, m2_col3, m2_col4 = st.columns(4)
        with m2_col1:
            st.metric("Price", f"${mkt['current_price']:,.2f}", delta=mkt['currency'])
        with m2_col2:
            mcap = mkt.get('market_cap')
            mcap_str = f"${mcap/1e9:,.1f}B" if mcap else "N/A"
            st.metric("Market Cap", mcap_str)
        with m2_col3:
            upside = model.upside_potential or 0
            st.metric("Target Price", f"${model.target_price:,.2f}", delta=f"{upside:+.1%}")
        with m2_col4:
            st.metric("Forward P/E", f"{mkt['forward_pe']:.1f}x" if mkt['forward_pe'] else "N/A")

    # 3. Recommendation Card
    rec_colors = {"BUY": "green", "HOLD": "orange", "SELL": "red"}
    rec = model.recommendation or "N/A"
    st.markdown(f"""
    <div style="background-color: {rec_colors.get(rec, 'grey')}; padding: 20px; border-radius: 10px; text-align: center; color: white;">
        <h2 style="margin: 0;">RECOMMENDATION: {rec}</h2>
        <p style="margin: 10px 0 0 0; font-size: 1.1em; opacity: 0.9;">{model.investment_thesis}</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    
    # 4. AI Executive Summary (NEW)
    if st.session_state.ai_summary:
        with st.expander("📝 AI Executive Summary & Risk Factors", expanded=True):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.markdown("### AI Summary")
                st.write(st.session_state.ai_summary)
                st.markdown("---")
                st.markdown("### 🏆 Investor's View (Narrative)")
                st.info(st.session_state.ai_narrative)
            with col_b:
                st.markdown("### Key Risk Markers")
                for risk in st.session_state.ai_risks:
                    st.warning(risk)

    # 5. NEW TAB SYSTEM
    is_private_mode = st.session_state.app_mode == "🦄 Private / Startup Valuator"
    
    tab_list = ["🚀 Timing & Momentum", "🏢 Peer Benchmarking", "🔮 Markov Chain"]
    if is_report_mode:
        tab_list = ["📈 Financial Visuals", "💎 DCF Valuation"] + tab_list + ["📋 Model Data", "📥 Download Report"]
    elif is_private_mode:
        tab_list = ["📈 Financial Visuals", "💎 DCF & VC Valuation", "📋 Model Data", "📥 Download Report"]
    
    tabs = st.tabs(tab_list)
    
    # Logic to map tabs based on mode
    if is_report_mode:
        t_visuals, t_dcf, t_momentum, t_peers, t_markov, t_data, t_download = tabs
    elif is_private_mode:
        t_visuals, t_dcf, t_data, t_download = tabs
        t_momentum, t_peers, t_markov = None, None, None # Not used
    else:
        t_momentum, t_peers, t_markov = tabs

    if is_report_mode or is_private_mode:
        with t_visuals:
            if model.historical_income_statements:
                years = [s.period_end.year for s in model.historical_income_statements] + \
                        [s.period_end.year for s in model.forecast_income_statements]
                rev_hist = [s.revenue for s in model.historical_income_statements]
                rev_fcst = [s.revenue for s in model.forecast_income_statements]
                
                # Revenue Chart
                fig = go.Figure()
                fig.add_trace(go.Bar(x=years[:len(rev_hist)], y=rev_hist, name='Actual', marker_color='#1f4788'))
                fig.add_trace(go.Bar(x=years[len(rev_hist):], y=rev_fcst, name='Forecast', marker_color='#6fa8dc'))
                fig.update_layout(title="Revenue Trajectory", barmode='overlay', template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Upload a report to see financial visuals.")

        with t_dcf:
            if model.dcf_valuation:
                dcf = model.dcf_valuation
                st.subheader("Intrinsic Value Breakdown")
                c1, c2, c3 = st.columns(3)
                c1.metric("WACC", f"{dcf.wacc_used:.1%}")
                c2.metric("Terminal Growth", f"{dcf.terminal_growth_used:.1%}")
                c3.metric("Target Price", f"${dcf.implied_price_per_share:,.2f}")
                
                st.write("---")
                st.markdown("**Valuation Bridge**")
                st.table(pd.DataFrame({
                    "Item": ["Sum PV FCF", "PV Terminal Value", "Enterprise Value", "Net Debt", "Equity Value", "Implied Price"],
                    "Value": [dcf.sum_pv_fcf, dcf.pv_terminal_value, dcf.enterprise_value, -dcf.net_debt, dcf.equity_value, dcf.implied_price_per_share]
                }).style.format(subset=["Value"], formatter="{:,.2f}"))
                
                # Reverse DCF Section (Private Mode)
                if hasattr(model, 'reverse_dcf') and model.reverse_dcf:
                     st.markdown("---")
                     st.subheader("🎯 Reverse DCF (Goal Seek)")
                     rdcf = model.reverse_dcf
                     
                     st.markdown(f"To achieve a **${rdcf.target_price:,.0f}** valuation:")
                     
                     rc1, rc2, rc3 = st.columns(3)
                     rc1.metric("Required Growth CAGR", f"{rdcf.required_growth_rate:.1%}", 
                        delta=f"{rdcf.required_growth_rate - model.assumptions.revenue_growth_rate:.1%} vs Base")
                     rc2.metric("Implied Multiple", f"{rdcf.implied_arr_multiple:.1f}x Revenue")
                     rc3.metric("Breakeven Year", f"Year {rdcf.years_to_breakeven}" if rdcf.years_to_breakeven else "> 5 Years")
                     
                     if rdcf.required_growth_rate > 0.5:
                         st.error("⚠️ **High Risk:** Required growth exceeds 50% CAGR. This implies 'Unicorn' trajectory.")
                     elif rdcf.required_growth_rate > 0.2:
                         st.warning("⚠️ **Moderate Risk:** Requires aggressive execution.")
                     else:
                         st.success("✅ **Achievable:** Growth target is within standard benchmarks.")
            else:
                st.warning("DCF analysis requires a processed financial report.")

    with t_momentum:
        st.subheader("📉 Technical Momentum & Entry Context")
        if st.session_state.market_data:
            ticker = st.session_state.market_data['ticker']
            hist_df = MarketDataProvider.fetch_historical_with_indicators(ticker)
            
            if not hist_df.empty:
                # Value vs Price Chart
                fig_v = go.Figure()
                fig_v.add_trace(go.Scatter(x=hist_df.index, y=hist_df['Close'], name="Market Price", line=dict(color='#fff')))
                fig_v.add_trace(go.Scatter(x=hist_df.index, y=[model.target_price]*len(hist_df), 
                                         name="Intrinsic/Target Baseline", line=dict(color='gold', dash='dash', width=2)))
                fig_v.add_trace(go.Scatter(x=hist_df.index, y=hist_df['SMA_200'], name="SMA 200 (Long Trend)", line=dict(color='cyan', width=1)))
                fig_v.update_layout(title=f"{ticker} Momentum vs Valuation Baseline", template="plotly_dark", height=450)
                st.plotly_chart(fig_v, use_container_width=True)
                
                # Decision Matrix
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    last_rsi = hist_df['RSI'].iloc[-1]
                    rsi_status = "OVERBOUGHT" if last_rsi > 70 else ("OVERSOLD" if last_rsi < 30 else "NEUTRAL")
                    st.metric("RSI (14)", f"{last_rsi:.1f}", delta=rsi_status, delta_color="inverse")
                with col_m2:
                    curr = hist_df['Close'].iloc[-1]
                    upside = (model.target_price / curr - 1)
                    st.metric("Valuation Room", f"{upside:+.1%}", help="Distance to Intrinsic/Target price")
                with col_m3:
                    trend = "Bullish" if curr > hist_df['SMA_200'].iloc[-1] else "Bearish"
                    st.metric("Trend Alignment", trend)
                
                # Recommendation logic
                if upside > 0.15 and last_rsi < 40:
                    st.success("💎 **STRONG BUY SIGNAL:** High Margin of Safety combined with favorable technical entry.")
                elif upside < -0.10 or last_rsi > 75:
                    st.error("⚠️ **CAUTION:** Overvalued fundamentals or extreme overbought momentum detected.")
                else:
                    st.info("💡 **HOLD/MONITOR:** Price is trading near fair value or momentum is neutral.")
                
                # Export Utility
                render_export_utility(
                    "Timing & Momentum",
                    f"Technical Analysis: {ticker}",
                    "Fundamental DCF Intrinsic Value vs Technical Price Action",
                    metrics={"RSI (14)": f"{last_rsi:.1f}", "Trend": trend, "Valuation Upside": f"{upside:+.1%}"}
                )
            else:
                st.error("Historical data unavailable for this ticker.")
        else:
            st.info("Market data required for momentum analysis.")

    with t_peers:
        st.subheader("🏢 Sector Benchmarking")
        if st.session_state.market_data:
            ticker = st.session_state.market_data['ticker']
            peers = MarketDataProvider.fetch_peers(ticker)
            if peers:
                peer_data = [st.session_state.market_data]
                for p in peers[:4]:
                    p_info = MarketDataProvider.fetch_data(p)
                    if p_info: peer_data.append(p_info)
                
                bench_df = pd.DataFrame(peer_data)
                st.dataframe(bench_df[['ticker', 'long_name', 'current_price', 'forward_pe', 'market_cap']].set_index('ticker'), use_container_width=True)
                
                bcol1, bcol2 = st.columns(2)
                with bcol1:
                    st.plotly_chart(px.bar(bench_df, x='ticker', y='forward_pe', color='ticker', title="P/E Multiples Comparison", template="plotly_dark"), use_container_width=True)
                with bcol2:
                    st.plotly_chart(px.pie(bench_df, values='market_cap', names='ticker', title="Relative Market Cap (Sector)", template="plotly_dark"), use_container_width=True)
                
                # Export Utility
                render_export_utility(
                    "Peer Comparison",
                    f"Sector Benchmarking: {ticker}",
                    "Relative Valuation & Market Cap vs Sector Peers",
                    data_frames={"Peer Metrics": bench_df[['ticker', 'long_name', 'current_price', 'forward_pe', 'market_cap']]}
                )
            else:
                st.write("No direct sector peers found for this ticker.")
        else:
            st.info("Add a valid stock ticker to enable peer benchmarking.")

    with t_markov:
        if MARKOV_AVAILABLE:
            st.subheader("🔮 Probabilistic Price Prediction")
            m_ticker = st.text_input("Refine Ticker for Markov Analysis", value=model.ticker or "")
            
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                m_period = st.selectbox("History Period", ["1y", "2y", "5y", "10y"], index=1)
            with m_col2:
                m_states = st.selectbox("Complexity (States)", [3, 5, 7, 10], index=1)
            with m_col3:
                m_method = st.selectbox("Method", ["returns", "std_dev"], index=0)
            with m_col4:
                m_days = st.slider("Forecast (Days)", 1, 30, 5)
                
            if st.button("🔮 Run Markov Simulation"):
                with st.spinner("Calculating state transitions..."):
                    m_out, m_preds, m_data, m_viz, m_discretizer, m_mc = run_markov_chain_analysis(
                        m_ticker, period=m_period, n_states=m_states, method=m_method, n_days=m_days
                    )
                    st.session_state.markov_results = (m_out, m_preds, m_data, m_viz, m_discretizer, m_mc)
                    st.rerun()

            if st.session_state.markov_results:
                console_out, m_preds, m_data, m_viz, m_discretizer, m_mc = st.session_state.markov_results
                if m_preds:
                    last_price = m_data['Close'].iloc[-1]
                    expected_price = m_preds['expected_price']
                    change_pct = (expected_price / last_price - 1) * 100
                    st.metric(f"Forecast ({m_days}d)", f"${expected_price:,.2f}", delta=f"{change_pct:+.2f}%")
                    v_col1, v_col2 = st.columns(2)
                    # Create figures list for export
                    m_figs = []
                    f1 = m_viz.plot_multi_day_prediction(m_preds) if m_days > 1 else m_viz.plot_prediction(m_preds)
                    f2 = m_viz.plot_transition_matrix(m_mc.transition_matrix, m_discretizer.state_labels)
                    
                    with v_col1: st.pyplot(f1)
                    with v_col2: st.pyplot(f2)
                    
                    # Export Utility
                    render_export_utility(
                        "Markov Simulation",
                        f"Probabilistic Forecast: {m_ticker}",
                        f"{m_days}-Day Price Trajectory & State Transition Matrix",
                        metrics={"Expected Price": f"${expected_price:,.2f}", "Proj. Change": f"{change_pct:+.2f}%", "Simulation Horizon": f"{m_days} days"},
                        figures=[f1, f2]
                    )
                    plt.close('all')

    if is_report_mode:
        with t_data:
            st.subheader("Raw Data Snapshot")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.json({
                    "Company": model.company_name,
                    "Ticker": model.ticker,
                    "Base Year": model.base_year,
                    "Report Type": model.report_type.value if hasattr(model.report_type, 'value') else "N/A",
                    "Currency": "USD"
                })
            with col_r2:
                if model.historical_income_statements:
                    st.write("**Base Year Indicators**")
                    hist_inc = model.historical_income_statements[-1]
                    st.table(pd.DataFrame({
                        "Metric": ["Revenue", "Net Income", "EBIT"],
                        "Value": [hist_inc.revenue, hist_inc.net_income, hist_inc.ebit]
                    }).style.format(subset=["Value"], formatter="{:,.0f}"))

        with t_download:
            if os.path.exists(st.session_state.report_path):
                st.success(f"✅ Report Available: {os.path.basename(st.session_state.report_path)}")
                with open(st.session_state.report_path, "rb") as f:
                    pdf_data = f.read()
                st.download_button(
                    label="📥 Download Professional Investment Report (PDF)",
                    data=pdf_data,
                    file_name=os.path.basename(st.session_state.report_path),
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            else:
                st.error("Report file not found. Please re-run the analysis.")
