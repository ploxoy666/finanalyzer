"""
Startup Valuator UI Module.
Handles manual driver input for private company valuation.
"""

import streamlit as st
from datetime import date
import pandas as pd

from ..config import config, DefaultMetrics
from ..models.schemas import (
    ForecastAssumptions, 
    FinancialStatements, 
    IncomeStatement, 
    BalanceSheet, 
    CashFlowStatement,
    ReportType,
    AccountingStandard,
    Currency
)
from ..core.model_engine import ModelEngine
from ..core.forecast_engine import ForecastEngine
from .components import render_export_utility

def render_startup_valuator():
    """Render the private/startup valuation interface."""
    st.markdown("## 🦄 Startup & Private Company Valuation")
    st.info("Build professional 3-Statement Models and DCF Valuations from manual drivers - perfect for pre-IPO companies.")

    p_tab1, p_tab2 = st.tabs(["✍️ Driver Inputs", "📂 Excel Upload (Beta)"])

    with p_tab1:
        with st.form("startup_drivers"):
            st.markdown("### 1. Company Profile")
            col_a, col_b = st.columns(2)
            p_company = col_a.text_input("Company Name", "My Startup Inc.")
            p_currency = col_b.selectbox("Currency", [c.value for c in Currency], index=0)
            
            st.markdown("### 2. Current Year Financials (Base Year)")
            c1, c2, c3 = st.columns(3)
            p_rev = c1.number_input("Revenue ($)", min_value=0.0, value=1_000_000.0, step=1000.0)
            p_ni = c2.number_input("Net Income ($)", value=100_000.0, step=1000.0)
            p_cash = c3.number_input("Cash on Hand ($)", min_value=0.0, value=500_000.0, step=1000.0)
            
            p_shares = st.number_input("Shares Outstanding", min_value=1, value=1_000_000, step=100)
            
            st.markdown("### 3. Forecast Assumptions")
            a1, a2, a3 = st.columns(3)
            a_growth = a1.slider("Annual Revenue Growth", 0.0, 2.0, config.defaults.REVENUE_GROWTH_RATE)
            a_margin = a2.slider("Target Operating Margin", -0.5, 0.8, config.defaults.OPERATING_MARGIN)
            a_tax = a3.slider("Tax Rate", 0.0, 0.40, config.defaults.TAX_RATE)
            
            st.markdown("### 4. Valuation Drivers")
            v1, v2 = st.columns(2)
            a_wacc = v1.slider("WACC (Discount Rate)", 0.05, 0.25, 0.12)
            a_term = v2.slider("Terminal Growth", 0.01, 0.06, config.defaults.TERMINAL_GROWTH_RATE)
            
            submit_startup = st.form_submit_button("🔨 Build Model & Value")
            
        if submit_startup:
            with st.spinner("Synthesizing financial model from drivers..."):
                # 1. Create Base Year Data (Synthetic)
                curr_date = date.today()
                
                # Simplified Income Statement
                base_inc = IncomeStatement(
                    period_start=date(curr_date.year-1, 1, 1),
                    period_end=date(curr_date.year-1, 12, 31),
                    revenue=p_rev,
                    cost_of_revenue=p_rev * 0.4, # Assumption
                    gross_profit=p_rev * 0.6,
                    operating_expenses=p_rev * 0.6 - (p_rev * a_margin), # Backsolve
                    operating_income=p_rev * a_margin,
                    net_income=p_ni,
                    shares_outstanding_basic=p_shares,
                    shares_outstanding_diluted=p_shares
                )
                
                # Simplified Balance Sheet
                base_bs = BalanceSheet(
                    period_end=date(curr_date.year-1, 12, 31),
                    total_assets=p_cash + (p_rev * 0.2), # Approx
                    total_liabilities=(p_rev * 0.1),
                    total_shareholders_equity=(p_cash + (p_rev * 0.2)) - (p_rev * 0.1),
                    cash_and_equivalents=p_cash,
                    total_current_assets=p_cash,
                    retained_earnings=p_ni
                )
                
                # Simplified Cash Flow
                base_cf = CashFlowStatement(
                    period_start=date(curr_date.year-1, 1, 1),
                    period_end=date(curr_date.year-1, 12, 31),
                    net_income=p_ni,
                    cash_from_operations=p_ni, # simplified
                    net_change_in_cash=0
                )
                
                stmts = FinancialStatements(
                    company_name=p_company,
                    fiscal_year=curr_date.year-1,
                    report_type=ReportType.ANNUAL_REPORT,
                    currency=Currency(p_currency),
                    income_statements=[base_inc],
                    balance_sheets=[base_bs],
                    cash_flow_statements=[base_cf]
                )
                
                # 2. Initialize Engines
                model_engine = ModelEngine(stmts)
                linked_model = model_engine.build_linked_model()
                
                assumptions = ForecastAssumptions(
                    revenue_growth_rate=a_growth,
                    gross_margin=0.6, # Simplified
                    operating_margin=a_margin,
                    tax_rate=a_tax,
                    wacc=a_wacc,
                    terminal_growth_rate=a_term,
                    capex_percent_of_revenue=0.05,
                    weeks_working_capital=0 # Not used yet
                )
                
                fc_engine = ForecastEngine(linked_model)
                final_model = fc_engine.forecast(years=5, assumptions=assumptions)
                
                # 3. Store in session
                st.session_state.model = final_model
                st.session_state.startup_mode = True
                
                st.success("Valuation Model Built Successfully!")
                
    with p_tab2:
        st.warning("Excel upload feature is coming in v1.1")

    # Display Results if model exists and is in startup mode
    if st.session_state.get("startup_mode") and "model" in st.session_state:
        model = st.session_state.model
        dcf = model.dcf_valuation
        
        st.markdown("---")
        st.subheader(f"Valuation Results: {model.company_name}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Enterprise Value", f"${dcf.enterprise_value/1e6:,.1f}M")
        m2.metric("Equity Value", f"${dcf.equity_value/1e6:,.1f}M")
        m3.metric("Implied Share Price", f"${dcf.implied_price_per_share:,.2f}")
        
        # Show DCF Table
        st.markdown("#### Discounted Cash Flow Forecast")
        
        # Construct DataFrame for display
        rows = []
        for year_data in dcf.forecast_period_fcf:
            rows.append({
                "Year": year_data.year,
                "Revenue ($)": f"{year_data.revenue:,.0f}",
                "EBIT ($)": f"{year_data.ebit:,.0f}",
                "Free Cash Flow ($)": f"{year_data.free_cash_flow:,.0f}",
                "PV of FCF ($)": f"{year_data.pv_free_cash_flow:,.0f}"
            })
            
        df_dcf = pd.DataFrame(rows)
        st.dataframe(df_dcf, use_container_width=True)
        
        render_export_utility("startup", "Valuation Model", "Download the full DCF model.", data_frames={"DCF_Model": df_dcf})

