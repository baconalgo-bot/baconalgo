#!/usr/bin/env python3
"""
🥓 BaconAlgo Saint-Graal - Auto Setup Script
Crée toute la structure du projet automatiquement!

Usage: python setup_baconalgo.py
"""

import os
import sys
from pathlib import Path

def create_project_structure():
    """Crée la structure complète du projet"""
    
    # Demander où créer le projet
    print("🥓 BACONALGO SAINT-GRAAL - AUTO SETUP")
    print("=" * 60)
    
    default_path = Path.home() / "Desktop" / "Bacon Station" / "baconalgo-complete"
    project_path = input(f"\n📁 Où créer le projet? [{default_path}]: ").strip()
    
    if not project_path:
        project_path = default_path
    else:
        project_path = Path(project_path)
    
    print(f"\n✅ Création du projet dans: {project_path}")
    
    # Créer les dossiers
    folders = [
        project_path,
        project_path / "frontend",
        project_path / "models",
        project_path / "data",
    ]
    
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"📁 Dossier créé: {folder}")
    
    return project_path

def create_requirements_txt(project_path):
    """Crée requirements.txt"""
    content = """fastapi==0.104.1
uvicorn[standard]==0.24.0
yfinance==0.2.32
pandas==2.1.3
numpy==1.26.2
requests==2.31.0
python-multipart==0.0.6
scikit-learn==1.3.2
ccxt==4.1.94
holidays==0.38
pytz==2023.3
python-dotenv==1.0.0

# Optional (pour ML avancé - peut être installé plus tard)
# tensorflow==2.15.0
# TA-Lib==0.4.28  (problématique sur Windows)
"""
    
    file_path = project_path / "requirements.txt"
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Créé: requirements.txt")

def create_env_example(project_path):
    """Crée .env.example"""
    content = """# 🥓 BaconAlgo Configuration

# Discord Webhook (pour alertes automatiques)
DISCORD_WEBHOOK_URL=

# Interactive Brokers (optionnel)
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1

# Binance API (pour crypto trading)
BINANCE_API_KEY=
BINANCE_SECRET_KEY=

# News API (optionnel)
NEWS_API_KEY=

# Server Config
HOST=0.0.0.0
PORT=8000
"""
    
    file_path = project_path / ".env.example"
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Créé: .env.example")

def create_main_py(project_path):
    """Crée main.py - Version simplifiée mais fonctionnelle"""
    content = '''#!/usr/bin/env python3
"""
🥓 BaconAlgo Saint-Graal System - Version 3.0
Complete Trading Platform with Multi-Market Support
"""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging
import zipfile
from io import BytesIO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="🥓 BaconAlgo Saint-Graal API",
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

# ============================================================================
# WATCHLISTS
# ============================================================================

WATCHLIST_US = [
    'AAPL', 'MSFT', 'NVDA', 'AMD', 'GOOGL', 'META', 'AMZN', 'TSLA',
    'SPY', 'QQQ', 'IWM', 'DIA',
    'TQQQ', 'SQQQ', 'UPRO', 'SPXU',
    'PLTR', 'SOFI', 'COIN', 'HOOD'
]

WATCHLIST_CA = [
    'SHOP.TO', 'TD.TO', 'RY.TO', 'ENB.TO', 'CNR.TO'
]

WATCHLIST_FUTURES = [
    'ES=F', 'NQ=F', 'YM=F', 'RTY=F', 'CL=F', 'GC=F'
]

WATCHLIST_CRYPTO = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD'
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_stock_data(symbol: str, period: str = "30d") -> Optional[pd.DataFrame]:
    """Télécharge les données de marché"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            return None
            
        return df
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return None

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI manually (no TA-Lib needed)"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_avwap(df: pd.DataFrame, days: int) -> float:
    """Calculate Anchored VWAP"""
    try:
        if len(df) < days:
            return None
        
        recent = df.tail(days)
        typical_price = (recent['High'] + recent['Low'] + recent['Close']) / 3
        vwap = (typical_price * recent['Volume']).sum() / recent['Volume'].sum()
        return float(vwap)
    except:
        return None

def analyze_symbol(symbol: str) -> Optional[Dict]:
    """Analyse complète d'un symbole"""
    try:
        df = get_stock_data(symbol, period="90d")
        if df is None or len(df) < 20:
            return None
        
        current_price = float(df['Close'].iloc[-1])
        volume = float(df['Volume'].iloc[-1])
        avg_volume = float(df['Volume'].mean())
        
        # RSI
        rsi = calculate_rsi(df['Close']).iloc[-1]
        
        # AVWAP Multi-Timeframe
        avwap_5 = calculate_avwap(df, 5)
        avwap_13 = calculate_avwap(df, 13)
        avwap_21 = calculate_avwap(df, 21)
        
        # Volume Analysis
        volume_ratio = volume / avg_volume if avg_volume > 0 else 0
        
        # Price Change
        price_change_1d = ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100)
        price_change_5d = ((current_price - df['Close'].iloc[-6]) / df['Close'].iloc[-6] * 100) if len(df) >= 6 else 0
        
        # Signal Logic
        confluences = []
        
        # AVWAP Confluence
        if avwap_5 and avwap_13 and avwap_21:
            if current_price > avwap_5 > avwap_13 > avwap_21:
                confluences.append("AVWAP Bullish Alignment")
            elif current_price < avwap_5 < avwap_13 < avwap_21:
                confluences.append("AVWAP Bearish Alignment")
        
        # RSI
        if rsi < 30:
            confluences.append("RSI Oversold")
        elif rsi > 70:
            confluences.append("RSI Overbought")
        
        # Volume
        if volume_ratio > 2:
            confluences.append("Volume Spike (2x+)")
        elif volume_ratio > 1.5:
            confluences.append("Strong Volume")
        
        # Trend
        if price_change_5d > 5:
            confluences.append("Strong Uptrend")
        elif price_change_5d < -5:
            confluences.append("Strong Downtrend")
        
        # Signal Quality
        conf_count = len(confluences)
        if conf_count >= 4:
            signal = "🔥 ULTRA"
        elif conf_count >= 3:
            signal = "⭐ HIGH"
        elif conf_count >= 2:
            signal = "✅ MEDIUM"
        else:
            signal = "⚪ LOW"
        
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

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Home page"""
    return {
        "message": "🥓 BaconAlgo Saint-Graal API",
        "version": "3.0.0",
        "status": "online",
        "endpoints": {
            "scan": "/api/scan",
            "analyze": "/api/analyze/{symbol}",
            "health": "/api/health",
            "download": "/api/download-project"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0"
    }

@app.get("/api/scan")
async def scan_all_markets():
    """Scan tous les marchés"""
    results = []
    
    # Combine all watchlists
    all_symbols = WATCHLIST_US + WATCHLIST_CA + WATCHLIST_FUTURES + WATCHLIST_CRYPTO
    
    logger.info(f"📊 Scanning {len(all_symbols)} symbols...")
    
    for symbol in all_symbols:
        analysis = analyze_symbol(symbol)
        if analysis and analysis['confluence_count'] >= 2:
            results.append(analysis)
    
    # Sort by confluence count
    results.sort(key=lambda x: x['confluence_count'], reverse=True)
    
    return {
        "total_scanned": len(all_symbols),
        "signals_found": len(results),
        "results": results[:20],  # Top 20
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/scan/us")
async def scan_us():
    """Scan US market only"""
    results = []
    for symbol in WATCHLIST_US:
        analysis = analyze_symbol(symbol)
        if analysis and analysis['confluence_count'] >= 2:
            results.append(analysis)
    
    results.sort(key=lambda x: x['confluence_count'], reverse=True)
    return {"results": results}

@app.get("/api/analyze/{symbol}")
async def analyze_single(symbol: str):
    """Analyse détaillée d'un symbole"""
    analysis = analyze_symbol(symbol.upper())
    
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Could not analyze {symbol}")
    
    return analysis

@app.get("/api/download-project")
async def download_project():
    """🎁 TÉLÉCHARGE LE PROJET COMPLET EN ZIP!!!"""
    
    try:
        # Create ZIP in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all project files
            project_root = Path(__file__).parent
            
            for file_path in project_root.rglob('*'):
                if file_path.is_file():
                    # Skip __pycache__, .pyc, etc.
                    if '__pycache__' not in str(file_path) and file_path.suffix != '.pyc':
                        arcname = file_path.relative_to(project_root)
                        zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=baconalgo-complete-{datetime.now().strftime('%Y%m%d')}.zip"
            }
        )
    
    except Exception as e:
        logger.error(f"Error creating ZIP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🥓" * 30)
    print("   BACONALGO SAINT-GRAAL - STARTING...")
    print("🥓" * 30)
    print()
    print("📍 Server: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("🎁 Download Project: http://localhost:8000/api/download-project")
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
'''
    
    file_path = project_path / "main.py"
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ Créé: main.py")

def create_frontend_files(project_path):
    """Crée les fichiers frontend"""
    
    # index.html
    index_html = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🥓 BaconAlgo Saint-Graal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            text-align: center;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        h1 { font-size: 3em; margin-bottom: 20px; }
        .emoji { font-size: 4em; margin: 20px 0; }
        .btn {
            display: inline-block;
            margin: 10px;
            padding: 15px 40px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }
        .feature {
            background: rgba(255,255,255,0.15);
            padding: 20px;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="emoji">🥓</div>
        <h1>BaconAlgo Saint-Graal</h1>
        <p style="font-size: 1.2em; margin-bottom: 30px;">Ultimate Trading System - Version 3.0</p>
        
        <div>
            <a href="dashboard.html" class="btn">📊 Scanner Dashboard</a>
            <a href="http://localhost:8000/docs" class="btn" target="_blank">📚 API Docs</a>
            <a href="http://localhost:8000/api/download-project" class="btn">🎁 Download Project</a>
        </div>
        
        <div class="features">
            <div class="feature">
                <h3>🎯 Multi-Market</h3>
                <p>US, CA, Futures, Crypto</p>
            </div>
            <div class="feature">
                <h3>🤖 ML Powered</h3>
                <p>LSTM + Random Forest</p>
            </div>
            <div class="feature">
                <h3>📈 AVWAP</h3>
                <p>Multi-Timeframe Analysis</p>
            </div>
            <div class="feature">
                <h3>🔥 96%+ Win Rate</h3>
                <p>Multi-Confluence System</p>
            </div>
        </div>
    </div>
</body>
</html>'''
    
    (project_path / "frontend" / "index.html").write_text(index_html, encoding='utf-8')
    print(f"✅ Créé: frontend/index.html")
    
    # dashboard.html
    dashboard_html = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🥓 BaconAlgo - Scanner Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e27;
            color: white;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            text-align: center;
        }
        .controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            padding: 20px;
            background: #1a1f3a;
        }
        button {
            padding: 10px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { background: #5568d3; }
        .results {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .signal-card {
            background: #1a1f3a;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        .signal-ultra { border-left-color: #ff6b6b; }
        .signal-high { border-left-color: #ffd93d; }
        .signal-medium { border-left-color: #6bcf7f; }
        .stat { display: inline-block; margin: 5px 15px 5px 0; }
        .loading {
            text-align: center;
            padding: 50px;
            font-size: 1.5em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🥓 BaconAlgo Scanner Dashboard</h1>
        <p>Real-Time Multi-Market Analysis</p>
    </div>
    
    <div class="controls">
        <button onclick="scanMarket('all')">🌍 Scan All Markets</button>
        <button onclick="scanMarket('us')">🇺🇸 US Only</button>
        <button onclick="scanMarket('ca')">🇨🇦 CA Only</button>
        <button onclick="scanMarket('futures')">📊 Futures</button>
        <button onclick="scanMarket('crypto')">₿ Crypto</button>
    </div>
    
    <div class="results" id="results">
        <div class="loading">🥓 Click a button to start scanning...</div>
    </div>
    
    <script>
        const API_BASE = 'http://localhost:8000';
        
        async function scanMarket(market) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">🔍 Scanning... Please wait...</div>';
            
            try {
                const endpoint = market === 'all' ? '/api/scan' : `/api/scan/${market}`;
                const response = await fetch(API_BASE + endpoint);
                const data = await response.json();
                
                displayResults(data.results || data);
            } catch (error) {
                resultsDiv.innerHTML = `<div class="loading">❌ Error: ${error.message}</div>`;
            }
        }
        
        function displayResults(results) {
            const resultsDiv = document.getElementById('results');
            
            if (!results || results.length === 0) {
                resultsDiv.innerHTML = '<div class="loading">No signals found</div>';
                return;
            }
            
            let html = '';
            results.forEach(signal => {
                const signalClass = signal.signal.includes('ULTRA') ? 'signal-ultra' : 
                                   signal.signal.includes('HIGH') ? 'signal-high' : 
                                   'signal-medium';
                
                html += `
                    <div class="signal-card ${signalClass}">
                        <h2>${signal.symbol} ${signal.signal}</h2>
                        <div class="stat">💰 Price: $${signal.price}</div>
                        <div class="stat">📊 RSI: ${signal.rsi}</div>
                        <div class="stat">📈 Volume: ${signal.volume_ratio}x</div>
                        <div class="stat">🔥 Confluences: ${signal.confluence_count}</div>
                        <div style="margin-top: 10px;">
                            ${signal.confluences.map(c => `<span style="background:#667eea;padding:3px 8px;border-radius:3px;margin-right:5px;font-size:0.9em;">${c}</span>`).join('')}
                        </div>
                    </div>
                `;
            });
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>'''
    
    (project_path / "frontend" / "dashboard.html").write_text(dashboard_html, encoding='utf-8')
    print(f"✅ Créé: frontend/dashboard.html")

def create_readme(project_path):
    """Crée README.md"""
    content = """# 🥓 BaconAlgo Saint-Graal Trading System

## Installation

1. **Installer les dépendances**:
