#!/usr/bin/env python3
"""
?? BaconAlgo - Auto Download Main.py
Ce script télécharge et installe automatiquement main.py
"""

import urllib.request
import os

def download_main_py():
    """Télécharge main.py depuis un serveur"""
    
    # Le code complet (version simplifiée - 800 lignes)
    main_py_content = '''#!/usr/bin/env python3
"""
?? BaconAlgo Saint-Graal System - Version 3.0
Complete Trading Platform - Simplified & Working
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="?? BaconAlgo Saint-Graal API",
    version="3.0.0",
    description="Ultimate Trading System"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Watchlists
WATCHLIST_US = [
    'AAPL', 'MSFT', 'NVDA', 'AMD', 'GOOGL', 'META', 'AMZN', 'TSLA',
    'SPY', 'QQQ', 'IWM', 'DIA', 'TQQQ', 'SQQQ', 'UPRO', 'SPXU',
    'PLTR', 'SOFI', 'COIN', 'HOOD', 'RIVN'
]

WATCHLIST_CA = ['SHOP.TO', 'TD.TO', 'RY.TO', 'ENB.TO', 'CNR.TO']
WATCHLIST_FUTURES = ['ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'CL=F', 'GC=F']
WATCHLIST_CRYPTO = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD']

def get_stock_data(symbol: str, period: str = "30d") -> Optional[pd.DataFrame]:
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        return df if not df.empty else None
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return None

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_avwap(df: pd.DataFrame, days: int) -> Optional[float]:
    try:
        if len(df) < days:
            return None
        recent = df.tail(days)
        typical_price = (recent['High'] + recent['Low'] + recent['Close']) / 3
        return float((typical_price * recent['Volume']).sum() / recent['Volume'].sum())
    except:
        return None

def analyze_symbol(symbol: str) -> Optional[Dict]:
    try:
        df = get_stock_data(symbol, period="90d")
        if df is None or len(df) < 20:
            return None
        
        current_price = float(df['Close'].iloc[-1])
        volume = float(df['Volume'].iloc[-1])
        avg_volume = float(df['Volume'].mean())
        
        rsi = calculate_rsi(df['Close']).iloc[-1]
        avwap_5 = calculate_avwap(df, 5)
        avwap_13 = calculate_avwap(df, 13)
        avwap_21 = calculate_avwap(df, 21)
        
        volume_ratio = volume / avg_volume if avg_volume > 0 else 0
        price_change_1d = ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100)
        price_change_5d = ((current_price - df['Close'].iloc[-6]) / df['Close'].iloc[-6] * 100) if len(df) >= 6 else 0
        
        confluences = []
        
        if avwap_5 and avwap_13 and avwap_21:
            if current_price > avwap_5 > avwap_13 > avwap_21:
                confluences.append("AVWAP Bullish")
            elif current_price < avwap_5 < avwap_13 < avwap_21:
                confluences.append("AVWAP Bearish")
        
        if rsi < 30:
            confluences.append("RSI Oversold")
        elif rsi > 70:
            confluences.append("RSI Overbought")
        
        if volume_ratio > 2:
            confluences.append("Volume Spike 2x+")
        elif volume_ratio > 1.5:
            confluences.append("Strong Volume")
        
        if price_change_5d > 5:
            confluences.append("Strong Uptrend")
        elif price_change_5d < -5:
            confluences.append("Strong Downtrend")
        
        conf_count = len(confluences)
        signal = "?? ULTRA" if conf_count >= 4 else "? HIGH" if conf_count >= 3 else "? MEDIUM" if conf_count >= 2 else "? LOW"
        
        return {
            "symbol": symbol,
            "price": round(current_price, 2),
            "volume": int(volume),
            "volume_ratio": round(volume_ratio, 2),
            "rsi": round(rsi, 2),
            "avwap_5d": round(avwap_5, 2) if avwap_5 else None,
            "avwap_13d": round(avwap_13, 2) if avwap_13 else None,
            "avwap_21d": round(avwap_21, 2) if avwap_21 else None,
            "change_1d": round(price_change_1d, 2),
            "change_5d": round(price_change_5d, 2),
            "confluences": confluences,
            "confluence_count": conf_count,
            "signal": signal,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return None

@app.get("/")
async def root():
    return HTMLResponse(content="""
    <html>
        <head><title>?? BaconAlgo</title></head>
        <body style="font-family:Arial;background:#0a0e27;color:white;text-align:center;padding:50px;">
            <h1 style="font-size:3em;">?? BaconAlgo Saint-Graal API</h1>
            <p style="font-size:1.5em;">Ultimate Trading System v3.0</p>
            <div style="margin-top:40px;">
                <a href="/docs" style="padding:15px 4JUdGzvrMFDWrUUwY3toJATSeNwjn54LkCnKBPRzDuhzi5vSepHfUckJNxRL2gjkNrSqtCoRUrEDAgRwsQvVCjZbRyFTLRNyDmT1a1boZV>
                <a href="/api/scan" style="padding:15px 4JUdGzvrMFDWrUUwY3toJATSeNwjn54LkCnKBPRzDuhzi5vSepHfUckJNxRL2gjkNrSqtCoRUrEDAgRwsQvVCjZbRyFTLRNyDmT1a1boZV>
            </div>
        </body>
    </html>
    """)

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "3.0.0", "timestamp": datetime.now().isoformat()}

@app.get("/api/scan")
async def scan_all():
    results = []
    all_symbols = WATCHLIST_US + WATCHLIST_CA + WATCHLIST_FUTURES + WATCHLIST_CRYPTO
    
    logger.info(f"?? Scanning {len(all_symbols)} symbols...")
    
    for symbol in all_symbols:
        analysis = analyze_symbol(symbol)
        if analysis and analysis['confluence_count'] >= 2:
            results.append(analysis)
    
    results.sort(key=lambda x: x['confluence_count'], reverse=True)
    
    return {
        "total_scanned": len(all_symbols),
        "signals_found": len(results),
        "results": results[:20],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/scan/us")
async def scan_us():
    results = []
    for symbol in WATCHLIST_US:
        analysis = analyze_symbol(symbol)
        if analysis and analysis['confluence_count'] >= 2:
            results.append(analysis)
    results.sort(key=lambda x: x['confluence_count'], reverse=True)
    return {"results": results}

@app.get("/api/scan/ca")
async def scan_ca():
    results = []
    for symbol in WATCHLIST_CA:
        analysis = analyze_symbol(symbol)
        if analysis and analysis['confluence_count'] >= 2:
            results.append(analysis)
    results.sort(key=lambda x: x['confluence_count'], reverse=True)
    return {"results": results}

@app.get("/api/scan/futures")
async def scan_futures():
    results = []
    for symbol in WATCHLIST_FUTURES:
        analysis = analyze_symbol(symbol)
        if analysis and analysis['confluence_count'] >= 2:
            results.append(analysis)
    results.sort(key=lambda x: x['confluence_count'], reverse=True)
    return {"results": results}

@app.get("/api/scan/crypto")
async def scan_crypto():
    results = []
    for symbol in WATCHLIST_CRYPTO:
        analysis = analyze_symbol(symbol)
        if analysis and analysis['confluence_count'] >= 2:
            results.append(analysis)
    results.sort(key=lambda x: x['confluence_count'], reverse=True)
    return {"results": results}

@app.get("/api/analyze/{symbol}")
async def analyze_single(symbol: str):
    analysis = analyze_symbol(symbol.upper())
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Could not analyze {symbol}")
    return analysis

if __name__ == "__main__":
    import uvicorn
    print("??" * 30)
    print("   BACONALGO SAINT-GRAAL - STARTING...")
    print("??" * 30)
    print()
    print("?? Server: http://localhost:8000")
    print("?? Docs: http://localhost:8000/docs")
    print()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''
    
    # Sauvegarde
    backend_path = os.path.join(os.getcwd(), 'main.py')
    
    with open(backend_path, 'w', encoding='utf-8') as f:
        f.write(main_py_content)
    
    print(f"? main.py créé avec succès!")
    print(f"?? Emplacement: {backend_path}")
    print("\n?? Lance maintenant: python main.py")

if __name__ == "__main__":
    download_main_py()
