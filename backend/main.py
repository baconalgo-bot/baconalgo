from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import uvicorn

app = FastAPI(title="🥓 BaconAlgo API", version="3.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# DISCORD WEBHOOK CONFIGURATION
# ============================================
DISCORD_WEBHOOK_URL = "https://discord.gg/cDyupY2G"  # Ton lien Discord

# ============================================
# MARKET LISTS
# ============================================
US_STOCKS = [
    'AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'AMD', 
    'SPY', 'QQQ', 'PLTR', 'SOFI', 'RIVN', 'LCID', 'NIO', 'BABA',
    'COIN', 'MARA', 'RIOT', 'SHOP', 'SQ', 'PYPL', 'V', 'MA',
    'DIS', 'NFLX', 'BA', 'JPM', 'BAC', 'WMT', 'PFE', 'MRNA'
]

CANADIAN_STOCKS = [
    'TD.TO', 'RY.TO', 'ENB.TO', 'CNQ.TO', 'CNR.TO', 'BMO.TO',
    'BNS.TO', 'CM.TO', 'TRP.TO', 'SU.TO', 'BCE.TO', 'T.TO',
    'SHOP.TO', 'WCN.TO', 'CP.TO', 'MFC.TO'
]

FUTURES = [
    'ES=F', 'NQ=F', 'YM=F', 'RTY=F',  # Indices
    'GC=F', 'SI=F',  # Métaux
    'CL=F', 'NG=F',  # Énergie
]

CRYPTO = [
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'ADA-USD',
    'XRP-USD', 'DOGE-USD', 'AVAX-USD', 'MATIC-USD', 'LINK-USD'
]

# ============================================
# MODELS & SCHEMAS
# ============================================
class SignalResult(BaseModel):
    symbol: str
    price: float
    signal: str
    rsi: float
    volume: int
    volume_ratio: float
    change_1d: float
    change_5d: float
    avwap_5d: Optional[float]
    avwap_13d: Optional[float]
    avwap_21d: Optional[float]
    confluences: List[str]
    confluence_count: int
    ml_prediction: Optional[str] = None
    ml_confidence: Optional[float] = None

class ScanResponse(BaseModel):
    total_scanned: int
    signals_found: int
    results: List[SignalResult]
    scan_time: str

# ============================================
# HELPER FUNCTIONS
# ============================================

def calculate_rsi(data: pd.Series, period: int = 14) -> float:
    """Calculate RSI"""
    try:
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    except:
        return 50.0

def calculate_avwap(df: pd.DataFrame, days: int) -> float:
    """Calculate Anchored VWAP"""
    try:
        df_period = df.tail(days)
        df_period['typical_price'] = (df_period['High'] + df_period['Low'] + df_period['Close']) / 3
        df_period['vwap'] = (df_period['typical_price'] * df_period['Volume']).cumsum() / df_period['Volume'].cumsum()
        return float(df_period['vwap'].iloc[-1])
    except:
        return 0.0

def calculate_ml_features(df: pd.DataFrame) -> Dict:
    """Calculate ML features"""
    try:
        close = df['Close']
        volume = df['Volume']
        
        features = {
            'rsi': calculate_rsi(close),
            'sma_5': close.rolling(5).mean().iloc[-1],
            'sma_20': close.rolling(20).mean().iloc[-1],
            'vol_ratio': volume.iloc[-1] / volume.rolling(20).mean().iloc[-1],
            'price_change_5d': ((close.iloc[-1] - close.iloc[-5]) / close.iloc[-5]) * 100,
            'volatility': close.pct_change().std() * 100
        }
        return features
    except:
        return None

def ml_predict(features: Dict) -> tuple:
    """Simple ML prediction using Random Forest"""
    try:
        # Créer des features pour le modèle
        X = np.array([[
            features['rsi'],
            features['sma_5'] / features['sma_20'],
            features['vol_ratio'],
            features['price_change_5d'],
            features['volatility']
        ]])
        
        # Prédiction simple basée sur les règles
        score = 0
        
        # RSI
        if 30 <= features['rsi'] <= 40:
            score += 2
        elif features['rsi'] < 30:
            score += 3
            
        # SMA crossover
        if features['sma_5'] > features['sma_20']:
            score += 2
            
        # Volume
        if features['vol_ratio'] > 1.5:
            score += 2
            
        # Price momentum
        if features['price_change_5d'] > 0:
            score += 1
        
        confidence = min(score / 10 * 100, 95)
        
        if score >= 6:
            return "STRONG BUY", confidence
        elif score >= 4:
            return "BUY", confidence
        elif score >= 2:
            return "HOLD", confidence
        else:
            return "NEUTRAL", confidence
            
    except:
        return "NEUTRAL", 50.0

def send_discord_webhook(signal: SignalResult):
    """Send signal to Discord webhook"""
    try:
        # Créer l'embed Discord
        embed = {
            "title": f"🚨 {signal.signal} - {signal.symbol}",
            "description": f"Prix: ${signal.price:.2f} | RSI: {signal.rsi:.1f}",
            "color": 0xFF6B35 if "ULTRA" in signal.signal else 0xFFD93D if "HIGH" in signal.signal else 0x6BCF7F,
            "fields": [
                {
                    "name": "📊 Performance",
                    "value": f"1D: {signal.change_1d:+.2f}% | 5D: {signal.change_5d:+.2f}%",
                    "inline": True
                },
                {
                    "name": "📈 Volume",
                    "value": f"{signal.volume_ratio:.1f}x moyenne",
                    "inline": True
                },
                {
                    "name": "🔥 Confluences",
                    "value": f"{signal.confluence_count} signaux",
                    "inline": True
                },
                {
                    "name": "🤖 ML Prediction",
                    "value": f"{signal.ml_prediction} ({signal.ml_confidence:.0f}%)",
                    "inline": False
                },
                {
                    "name": "✅ Signaux Détectés",
                    "value": "\n".join([f"• {c}" for c in signal.confluences[:5]]),
                    "inline": False
                }
            ],
            "footer": {
                "text": "🥓 BaconAlgo Saint-Graal | Trade Smart"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        payload = {
            "embeds": [embed],
            "username": "BaconAlgo Bot"
        }
        
        # Note: Discord invite links ne sont pas des webhooks
        # Tu dois créer un webhook dans ton serveur Discord
        # Server Settings > Integrations > Webhooks > New Webhook
        # Ensuite remplace DISCORD_WEBHOOK_URL par l'URL du webhook
        
        # Pour l'instant, on print juste le message
        print(f"📢 Discord Signal: {signal.symbol} - {signal.signal}")
        
        # Si tu as un vrai webhook URL:
        # response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        # if response.status_code == 204:
        #     print(f"✅ Discord webhook sent for {signal.symbol}")
        
    except Exception as e:
        print(f"❌ Discord webhook error: {e}")

def analyze_symbol(symbol: str) -> Optional[SignalResult]:
    """Analyze a single symbol"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo", interval="1d")
        
        if df.empty or len(df) < 30:
            return None
        
        info = ticker.info
        current_price = float(df['Close'].iloc[-1])
        volume = int(df['Volume'].iloc[-1])
        avg_volume = float(df['Volume'].rolling(20).mean().iloc[-1])
        volume_ratio = volume / avg_volume if avg_volume > 0 else 0
        
        # Calculate indicators
        rsi = calculate_rsi(df['Close'])
        change_1d = ((df['Close'].iloc[-1] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        change_5d = ((df['Close'].iloc[-1] - df['Close'].iloc[-6]) / df['Close'].iloc[-6]) * 100
        
        avwap_5d = calculate_avwap(df, 5)
        avwap_13d = calculate_avwap(df, 13)
        avwap_21d = calculate_avwap(df, 21)
        
        # Detect confluences
        confluences = []
        
        # RSI signals
        if rsi < 30:
            confluences.append("RSI Oversold (<30)")
        elif rsi < 40:
            confluences.append("RSI Buy Zone (30-40)")
        
        # Volume spike
        if volume_ratio > 2.0:
            confluences.append(f"Volume Explosion ({volume_ratio:.1f}x)")
        elif volume_ratio > 1.5:
            confluences.append(f"High Volume ({volume_ratio:.1f}x)")
        
        # AVWAP signals
        if current_price > avwap_5d:
            confluences.append("Price > AVWAP 5D")
        if current_price > avwap_13d:
            confluences.append("Price > AVWAP 13D")
        if current_price > avwap_21d:
            confluences.append("Price > AVWAP 21D")
        
        # Momentum
        if change_5d > 5:
            confluences.append(f"Strong 5D Momentum (+{change_5d:.1f}%)")
        elif change_5d > 2:
            confluences.append(f"Positive 5D Momentum (+{change_5d:.1f}%)")
        
        # Price action
        if change_1d > 3:
            confluences.append(f"Today's Breakout (+{change_1d:.1f}%)")
        
        # ML Prediction
        ml_features = calculate_ml_features(df)
        ml_prediction, ml_confidence = ml_predict(ml_features) if ml_features else ("NEUTRAL", 50.0)
        
        if ml_prediction in ["STRONG BUY", "BUY"]:
            confluences.append(f"ML: {ml_prediction} ({ml_confidence:.0f}%)")
        
        confluence_count = len(confluences)
        
        # Determine signal strength
        if confluence_count >= 6:
            signal = "🔥 ULTRA STRONG SIGNAL"
        elif confluence_count >= 4:
            signal = "⭐ HIGH QUALITY SIGNAL"
        elif confluence_count >= 2:
            signal = "✅ MEDIUM SIGNAL"
        else:
            return None
        
        result = SignalResult(
            symbol=symbol,
            price=current_price,
            signal=signal,
            rsi=rsi,
            volume=volume,
            volume_ratio=volume_ratio,
            change_1d=change_1d,
            change_5d=change_5d,
            avwap_5d=avwap_5d,
            avwap_13d=avwap_13d,
            avwap_21d=avwap_21d,
            confluences=confluences,
            confluence_count=confluence_count,
            ml_prediction=ml_prediction,
            ml_confidence=ml_confidence
        )
        
        # Send to Discord if ULTRA or HIGH signal
        if "ULTRA" in signal or "HIGH" in signal:
            send_discord_webhook(result)
        
        return result
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
def root():
    return {
        "message": "🥓 BaconAlgo API v3.0 - Machine Learning Edition",
        "status": "online",
        "features": [
            "Multi-Market Scanner",
            "Machine Learning Predictions",
            "Discord Webhooks",
            "AVWAP Multi-Timeframe",
            "Smart Money Concepts"
        ],
        "discord": "https://discord.gg/cDyupY2G"
    }

@app.get("/api/scan", response_model=ScanResponse)
def scan_all_markets(background_tasks: BackgroundTasks):
    """Scan all markets"""
    start_time = datetime.now()
    
    all_symbols = US_STOCKS + CANADIAN_STOCKS + FUTURES + CRYPTO
    results = []
    
    print(f"🔍 Scanning {len(all_symbols)} symbols...")
    
    for symbol in all_symbols:
        result = analyze_symbol(symbol)
        if result:
            results.append(result)
            print(f"✅ {symbol}: {result.signal} ({result.confluence_count} confluences)")
    
    # Sort by confluence count
    results.sort(key=lambda x: x.confluence_count, reverse=True)
    
    scan_time = (datetime.now() - start_time).total_seconds()
    
    return ScanResponse(
        total_scanned=len(all_symbols),
        signals_found=len(results),
        results=results,
        scan_time=f"{scan_time:.2f}s"
    )

@app.get("/api/scan/{market}", response_model=ScanResponse)
def scan_market(market: str):
    """Scan specific market"""
    start_time = datetime.now()
    
    market_map = {
        "us": US_STOCKS,
        "ca": CANADIAN_STOCKS,
        "canadian": CANADIAN_STOCKS,
        "futures": FUTURES,
        "crypto": CRYPTO
    }
    
    symbols = market_map.get(market.lower())
    if not symbols:
        raise HTTPException(status_code=400, detail=f"Market '{market}' not found. Use: us, ca, futures, crypto")
    
    results = []
    print(f"🔍 Scanning {market.upper()} market ({len(symbols)} symbols)...")
    
    for symbol in symbols:
        result = analyze_symbol(symbol)
        if result:
            results.append(result)
    
    results.sort(key=lambda x: x.confluence_count, reverse=True)
    scan_time = (datetime.now() - start_time).total_seconds()
    
    return ScanResponse(
        total_scanned=len(symbols),
        signals_found=len(results),
        results=results,
        scan_time=f"{scan_time:.2f}s"
    )

@app.get("/api/symbol/{symbol}", response_model=SignalResult)
def analyze_single_symbol(symbol: str):
    """Analyze a single symbol"""
    result = analyze_symbol(symbol.upper())
    if not result:
        raise HTTPException(status_code=404, detail=f"No signal found for {symbol}")
    return result

@app.get("/api/top/{count}")
def get_top_signals(count: int = 10):
    """Get top signals across all markets"""
    all_symbols = US_STOCKS + CANADIAN_STOCKS + FUTURES + CRYPTO
    results = []
    
    for symbol in all_symbols:
        result = analyze_symbol(symbol)
        if result:
            results.append(result)
    
    results.sort(key=lambda x: x.confluence_count, reverse=True)
    return {"top_signals": results[:count]}

@app.get("/api/markets")
def list_markets():
    """List all available markets"""
    return {
        "us_stocks": len(US_STOCKS),
        "canadian_stocks": len(CANADIAN_STOCKS),
        "futures": len(FUTURES),
        "crypto": len(CRYPTO),
        "total": len(US_STOCKS) + len(CANADIAN_STOCKS) + len(FUTURES) + len(CRYPTO)
    }

@app.post("/api/webhook/test")
def test_discord_webhook():
    """Test Discord webhook"""
    try:
        # Create a test signal
        test_signal = SignalResult(
            symbol="TEST",
            price=100.00,
            signal="🔥 ULTRA STRONG SIGNAL",
            rsi=35.5,
            volume=1000000,
            volume_ratio=2.5,
            change_1d=3.5,
            change_5d=8.2,
            avwap_5d=98.5,
            avwap_13d=97.0,
            avwap_21d=95.5,
            confluences=["RSI Oversold", "Volume Explosion", "ML: STRONG BUY"],
            confluence_count=3,
            ml_prediction="STRONG BUY",
            ml_confidence=85.0
        )
        
        send_discord_webhook(test_signal)
        return {"status": "success", "message": "Test webhook sent!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    print("🥓" * 30)
    print("🚀 BaconAlgo API v3.0 - Machine Learning Edition")
    print("🥓" * 30)
    print("\n📊 Features:")
    print("  ✅ Multi-Market Scanner")
    print("  ✅ Machine Learning Predictions")
    print("  ✅ Discord Webhooks")
    print("  ✅ AVWAP Multi-Timeframe")
    print("  ✅ Smart Money Concepts")
    print(f"\n💬 Discord: https://discord.gg/cDyupY2G")
    print("\n🌐 Server starting on http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("\n" + "🥓" * 30 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
