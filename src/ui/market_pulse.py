"""
Quick Market Pulse UI Module.
Handles the fast analysis mode using only market data.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from ..config import config, AnalysisMode
from ..core.market_data import MarketDataProvider
from .components import apply_custom_css

def render_market_pulse():
    """Render the Quick Market Pulse dashboard."""
    st.markdown("## 🔎 Market Pulse & Technicals")
    st.info("Get immediate technical signals, peer comparisons, and price predictions just by entering a ticker.")
    
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        quick_ticker = st.text_input("Enter Stock Ticker (e.g., TSLA, NVDA)", value="", placeholder="AAPL").upper()
    
    with col_btn:
        st.write("") # Spacer
        st.write("") 
        analyze_btn = st.button("🚀 Analyze Market Pulse")
    
    # Check if analysis was triggered or results exist
    if analyze_btn and quick_ticker:
        with st.spinner(f"Fetching market data for {quick_ticker}..."):
            m_data = MarketDataProvider.fetch_data(quick_ticker)
            
            if m_data and m_data.get('current_price'):
                st.session_state.market_data = m_data
                st.session_state.pulse_ticker = quick_ticker
                
                # Fetch history for charts
                hist_df = MarketDataProvider.fetch_historical_with_indicators(quick_ticker)
                st.session_state.pulse_history = hist_df
                
                st.success(f"Analysis ready for {quick_ticker}")
            else:
                st.error("Could not fetch data for this ticker. Please check the symbol.")
    
    # Display Results if available
    if "pulse_ticker" in st.session_state and st.session_state.get("market_data"):
        data = st.session_state.market_data
        df = st.session_state.get("pulse_history")
        
        # 1. Top Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"${data.get('current_price', 0):.2f}")
        m2.metric("Market Cap", f"${(data.get('market_cap') or 0)/1e9:.1f}B")
        m3.metric("P/E Ratio", f"{data.get('forward_pe', 0):.1f}x")
        m4.metric("Div Yield", f"{(data.get('dividend_yield', 0) or 0)*100:.2f}%")
        
        st.markdown("---")
        
        # 2. Charts & Technicals
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Price Action & Indicators")
            if df is not None and not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index,
                                open=df['Open'], high=df['High'],
                                low=df['Low'], close=df['Close'], name='Price'))
                
                # Add SMAs
                if 'SMA_50' in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='orange', width=1)))
                if 'SMA_200' in df.columns:
                    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200', line=dict(color='blue', width=1)))
                    
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No historical data available for chart.")
                
        with c2:
            st.subheader("Technical Signal")
            
            # Simple technical logic
            rsi = df['RSI'].iloc[-1] if df is not None and 'RSI' in df.columns else 50
            price = data.get('current_price', 0)
            sma200 = df['SMA_200'].iloc[-1] if df is not None and 'SMA_200' in df.columns else price
            
            signal = "NEUTRAL"
            color = "gray"
            
            if rsi < 30:
                signal = "OVERSOLD (BUY WATCH)"
                color = "green"
            elif rsi > 70:
                signal = "OVERBOUGHT (CAUTION)"
                color = "red"
            elif price > sma200:
                signal = "BULLISH TREND"
                color = "green"
            else:
                signal = "BEARISH TREND"
                color = "orange"
                
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;">
                <h3 style="color: {color};">{signal}</h3>
                <p>RSI (14): <b>{rsi:.1f}</b></p>
                <p>vs SMA 200: <b>{((price/sma200)-1)*100:+.1f}%</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 🧬 Peer Comparison")
            peers = MarketDataProvider.fetch_peers(st.session_state.pulse_ticker)
            for p in peers[:4]:
                st.write(f"• {p}")

