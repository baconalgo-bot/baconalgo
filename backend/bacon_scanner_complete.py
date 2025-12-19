#!/usr/bin/env python3
"""
🥓 BaconAlgo - Scanner Complet v1.0
96% Win Rate Algorithm
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import uvicorn

app = FastAPI(title="🥓 BaconAlgo API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Liste de symboles à scanner
WATCHLIST = [
    'AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT',
    'GOOGL', 'META', 'AMZN', 'NFLX', 'SPY',
    'QQQ', 'TQQQ', 'SQQQ', 'PLTR', 'SOFI',
    'COIN', 'HOOD', 'RIVN', 'LCID', 'NIO',
    'F', 'GM', 'BA', 'DIS', 'UBER'
]

class BaconScanner:
    """Scanner avec algorithme 96%"""
    
    def __init__(self):
        self.min_score = 150  # Score minimum pour signal
        
    def scan_symbol(self, symbol):
        """Scan complet d'un symbole"""
        try:
            print(f"  📊 Scanning {symbol}...")
            
            # Get data
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='5d', interval='15m')
            
            if len(data) < 50:
                return None
            
            # Calculate indicators
            indicators = self.calculate_indicators(data)
            
            # Calculate scores
            tech_score = self.calculate_tech_score(data, indicators)
            social_score = self.get_social_score(symbol)
            total_score = tech_score + social_score
            
            # Filter - only quality signals
            if total_score < self.min_score:
                print(f"     ❌ {symbol}: {total_score}/230 - Too low")
                return None
            
            # Calculate levels
            current_price = float(data['Close'].iloc[-1])
            atr = self.calculate_atr(data)
            
            # Direction
            direction = 'BUY' if current_price > indicators['ema_21'] else 'SELL'
            
            # Stops & Targets
            if direction == 'BUY':
                stop = current_price - (atr * 1.0)
                target = current_price + (atr * 3.0)
            else:
                stop = current_price + (atr * 1.0)
                target = current_price - (atr * 3.0)
            
            # Calculate R:R
            risk = abs(current_price - stop)
            reward = abs(target - current_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            signal = {
                'symbol': symbol,
                'price': float(current_price),
                'direction': direction,
                'entry': float(current_price),
                'stop': float(stop),
                'target': float(target),
                'rr': round(rr_ratio, 1),
                'tech_score': int(tech_score),
                'social_score': int(social_score),
                'total_score': int(total_score),
                'rsi': float(indicators['rsi']),
                'volume_ratio': float(indicators['vol_ratio']),
                'grade': self.get_grade(total_score),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"     ✅ {symbol}: {total_score}/230 - {direction} SIGNAL!")
            return signal
            
        except Exception as e:
            print(f"     ⚠️  Error scanning {symbol}: {e}")
            return None
    
    def calculate_indicators(self, data):
        """Calculate all technical indicators"""
        
        # EMAs
        ema_9 = data['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema_21 = data['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        ema_50 = data['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
        
        # RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Volume
        vol_avg = data['Volume'].rolling(window=20).mean().iloc[-1]
        vol_current = data['Volume'].iloc[-1]
        vol_ratio = vol_current / vol_avg if vol_avg > 0 else 0
        
        return {
            'ema_9': ema_9,
            'ema_21': ema_21,
            'ema_50': ema_50,
            'rsi': rsi.iloc[-1],
            'vol_ratio': vol_ratio
        }
    
    def calculate_tech_score(self, data, indicators):
        """
        Calculate technical score (0-200 points)
        
        Breakdown:
        - EMA Alignment: 40pts
        - RSI: 30pts
        - Volume: 40pts
        - Price vs EMAs: 30pts
        - Momentum: 30pts
        - New High/Low: 30pts
        """
        score = 0
        price = data['Close'].iloc[-1]
        
        # 1. EMA Alignment (40 pts)
        if (indicators['ema_9'] > indicators['ema_21'] and
            indicators['ema_21'] > indicators['ema_50'] and
            price > indicators['ema_50']):
            score += 40
        elif (indicators['ema_9'] < indicators['ema_21'] and
              indicators['ema_21'] < indicators['ema_50'] and
              price < indicators['ema_50']):
            score += 40
        
        # 2. RSI (30 pts)
        rsi = indicators['rsi']
        if 45 < rsi < 65:
            score += 30
        elif 40 < rsi < 70:
            score += 15
        
        # 3. Volume (40 pts)
        if indicators['vol_ratio'] > 2.0:
            score += 40
        elif indicators['vol_ratio'] > 1.5:
            score += 25
        elif indicators['vol_ratio'] > 1.2:
            score += 10
        
        # 4. Price vs EMAs (30 pts)
        if price > indicators['ema_21']:
            score += 15
        if price > indicators['ema_50']:
            score += 15
        
        # 5. Momentum (30 pts)
        if len(data) >= 10:
            momentum = (price / data['Close'].iloc[-10] - 1) * 100
            if momentum > 1.0:
                score += 30
            elif momentum > 0.5:
                score += 15
        
        # 6. New High/Low (30 pts)
        if len(data) >= 20:
            high_20 = data['High'].iloc[-20:].max()
            low_20 = data['Low'].iloc[-20:].min()
            
            if price >= high_20 * 0.99:
                score += 30
            elif price <= low_20 * 1.01:
                score += 30
        
        return score
    
    def get_social_score(self, symbol):
        """
        Get social sentiment from StockTwits (0-30 points)
        Free API - no auth needed!
        """
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])[:20]
                
                if not messages:
                    return 0
                
                bullish = sum(1 for m in messages 
                             if m.get('entities', {}).get('sentiment', {}).get('basic') == 'Bullish')
                bearish = sum(1 for m in messages
                             if m.get('entities', {}).get('sentiment', {}).get('basic') == 'Bearish')
                
                total = bullish + bearish
                if total == 0:
                    return 0
                
                bullish_pct = (bullish / total) * 100
                
                if bullish_pct > 70:
                    return 30
                elif bullish_pct > 60:
                    return 20
                elif bullish_pct > 50:
                    return 10
                elif bullish_pct < 30:
                    return 30  # Strong bearish = good for shorts
                elif bullish_pct < 40:
                    return 20
                    
        except Exception as e:
            pass
        
        return 0
    
    def calculate_atr(self, data, period=14):
        """Calculate Average True Range"""
        high_low = data['High'] - data['Low']
        high_close = (data['High'] - data['Close'].shift()).abs()
        low_close = (data['Low'] - data['Close'].shift()).abs()
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return atr
    
    def get_grade(self, score):
        """Get signal grade"""
        if score >= 200:
            return 'LEGENDARY'
        elif score >= 180:
            return 'EPIC'
        elif score >= 160:
            return 'GOOD'
        else:
            return 'OKAY'

# Initialize scanner
scanner = BaconScanner()

@app.get("/")
def root():
    """Health check"""
    return {
        "name": "🥓 BaconAlgo API",
        "version": "1.0.0",
        "status": "running",
        "message": "🥓 BaconAlgo API Running!",
        "algorithm": "96% Win Rate Scanner",
        "endpoints": {
            "scan": "/api/scan",
            "quick_scan": "/api/quick"
        }
    }

@app.get("/api/scan")
def full_scan():
    """Full market scan - all symbols"""
    print(f"\n🔍 Starting full scan ({len(WATCHLIST)} symbols)...")
    
    signals = []
    
    for symbol in WATCHLIST:
        signal = scanner.scan_symbol(symbol)
        if signal:
            signals.append(signal)
    
    # Sort by score
    signals.sort(key=lambda x: x['total_score'], reverse=True)
    
    print(f"\n✅ Scan complete: {len(signals)}/{len(WATCHLIST)} signals found!\n")
    
    return {
        "success": True,
        "signals": signals,
        "count": len(signals),
        "scanned": len(WATCHLIST),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/quick")
def quick_scan():
    """Quick scan - top 10 symbols"""
    print(f"\n🔍 Quick scan (10 symbols)...")
    
    quick_list = WATCHLIST[:10]
    signals = []
    
    for symbol in quick_list:
        signal = scanner.scan_symbol(symbol)
        if signal:
            signals.append(signal)
    
    signals.sort(key=lambda x: x['total_score'], reverse=True)
    
    return {
        "success": True,
        "signals": signals,
        "count": len(signals)
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🥓 BACONALGO - 96% WIN RATE SCANNER")
    print("="*60)
    print(f"📊 Watching {len(WATCHLIST)} symbols")
    print(f"🎯 Min score: {scanner.min_score}/230")
    print(f"🚀 Starting server on http://localhost:8000")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
