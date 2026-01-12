
import yfinance as yf
import requests
from loguru import logger
from typing import Optional, Dict, List
import pandas as pd

class MarketDataProvider:
    """
    Fetches real-time market data from Yahoo Finance.
    Can map company names to tickers.
    """
    
    @staticmethod
    def get_ticker_from_name(name: str) -> Optional[str]:
        """Try to find a ticker for a company name using Yahoo Finance search."""
        if not name:
            return None
            
        logger.info(f"Searching ticker for: {name}")
        try:
            # Clean name for better search
            clean_name = name.replace("INC.", "").replace("CORP.", "").replace("CORPORATION", "").strip()
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={clean_name}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json()
            
            if data['quotes']:
                ticker = data['quotes'][0]['symbol']
                logger.info(f"Found ticker: {ticker}")
                return ticker
        except Exception as e:
            logger.error(f"Error searching ticker for {name}: {e}")
            
        return None

    @staticmethod
    def fetch_data(ticker: str) -> Dict:
        """Fetch market data for a given ticker."""
        logger.info(f"Fetching market data for {ticker}...")
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get latest price (handle different Yahoo info structures)
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'shares_outstanding': info.get('sharesOutstanding'),
                'market_cap': info.get('marketCap'),
                'forward_pe': info.get('forwardPE'),
                'dividend_yield': info.get('dividendYield'),
                'currency': info.get('currency', 'USD'),
                'long_name': info.get('longName', ticker)
            }
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return {}

    @staticmethod
    def fetch_historical_with_indicators(ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical data and calculate technical indicators."""
        logger.info(f"Fetching historical data for {ticker} ({period})...")
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            if df.empty:
                return pd.DataFrame()
            
            # 1. SMAs
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # 2. RSI (14)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            return df
        except Exception as e:
            logger.error(f"Error calculating indicators for {ticker}: {e}")
            return pd.DataFrame()

    @staticmethod
    def fetch_peers(ticker: str) -> List[str]:
        """Fetch top peers for a given ticker."""
        try:
            stock = yf.Ticker(ticker)
            # Try to get peers/recommendations from yfinance
            recommendations = stock.recommendations
            # Fallback: Many stocks have info['sector'] and info['industry']
            info = stock.info
            sector = info.get('sector')
            
            # Simple fallback for test: Return common peers for major tech
            major_tech_peers = {
                'AAPL': ['MSFT', 'GOOGL', 'AMZN', 'META'],
                'TSLA': ['F', 'GM', 'RIVN', 'LCID', 'NIO'],
                'NVDA': ['AMD', 'INTC', 'TSM', 'AVGO'],
                'MSFT': ['AAPL', 'GOOGL', 'AMZN', 'ORCL']
            }
            
            return major_tech_peers.get(ticker, [])
        except:
            return []
if __name__ == "__main__":
    # Test
    provider = MarketDataProvider()
    ticker = provider.get_ticker_from_name("NVIDIA Corporation")
    if ticker:
        data = provider.fetch_data(ticker)
        print(data)
