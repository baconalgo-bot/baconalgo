"""
🥓 Bacon 96% Scanner
Core scanning logic
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaconScanner:
    def __init__(self):
        self.min_score = 150
    
    async def scan(self, symbols):
        """Scan multiple symbols"""
        signals = []
        
        for symbol in symbols:
            try:
                signal = await self.scan_symbol(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
        
        # Sort by score
        signals.sort(key=lambda x: x['total_score'], reverse=True)
        
        return signals
    
    async def scan_symbol(self, symbol):
        """Scan single symbol"""
        logger.info(f"📊 Scanning {symbol}...")
        
        # Get data
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='5d', interval='15m')
        
        if len(data) < 50:
            return None
        
        # Calculate indicators
        indicators = self.calculate_indicators(data)
        
        # Calculate technical score
        tech_score = self.calculate_score(data, indicators)
        
        # Get social sentiment
        social_score = await self.get_social_sentiment(symbol)
        
        # Total score
        total_score = tech_score + social_score
        
        # Filter
        if total_score < self.min_score:
            logger.info(f"   {symbol}: {total_score}/230 - Below threshold")
            return None
        
        # Calculate levels
        current_price = data['Close'].iloc[-1]
        atr = self.calculate_atr(data)
        
        direction = 'BUY' if current_price > indicators['ema_21'] else 'SELL'
        
        if direction == 'BUY':
            stop = current_price - (atr * 1.0)
            target = current_price + (atr * 3.0)
        else:
            stop = current_price + (atr * 1.0)
            target = current_price - (atr * 3.0)
        
        signal = {
            'symbol': symbol,
            'direction': direction,
            'entry': float(current_price),
            'stop': float(stop),
            'target': float(target),
            'tech_score': int(tech_score),
            'social_score': int(social_score),
            'total_score': int(total_score),
            'rsi': float(indicators['rsi']),
            'volume_ratio': float(indicators['vol_ratio']),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ {symbol}: {total_score}/230 - SIGNAL!")
        return signal
    
    def calculate_indicators(self, data):
        """Calculate technical indicators"""
        # EMAs
        ema_9 = data['Close'].ewm(span=9).mean().iloc[-1]
        ema_21 = data['Close'].ewm(span=21).mean().iloc[-1]
        ema_50 = data['Close'].ewm(span=50).mean().iloc[-1]
        
        # RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Volume
        vol_avg = data['Volume'].rolling(20).mean().iloc[-1]
        vol_current = data['Volume'].iloc[-1]
        vol_ratio = vol_current / vol_avg if vol_avg > 0 else 0
        
        return {
            'ema_9': ema_9,
            'ema_21': ema_21,
            'ema_50': ema_50,
            'rsi': rsi.iloc[-1],
            'vol_ratio': vol_ratio
        }
    
    def calculate_score(self, data, indicators):
        """Calculate technical score /200"""
        score = 0
        price = data['Close'].iloc[-1]
        
        # EMA Alignment (40)
        if (indicators['ema_9'] > indicators['ema_21'] and
            indicators['ema_21'] > indicators['ema_50'] and
            price > indicators['ema_50']):
            score += 40
        
        # RSI (30)
        rsi = indicators['rsi']
        if 45 < rsi < 65:
            score += 30
        elif 40 < rsi < 70:
            score += 15
        
        # Volume (40)
        if indicators['vol_ratio'] > 2.0:
            score += 40
        elif indicators['vol_ratio'] > 1.5:
            score += 20
        
        # Price vs EMAs (30)
        if price > indicators['ema_21']:
            score += 15
        if price > indicators['ema_50']:
            score += 15
        
        # Momentum (30)
        momentum = (price / data['Close'].iloc[-10] - 1) * 100
        if momentum > 1.0:
            score += 30
        elif momentum > 0.5:
            score += 15
        
        # New High (30)
        if price >= data['High'].iloc[-20:].max():
            score += 30
        
        return score
    
    async def get_social_sentiment(self, symbol):
        """Get social sentiment score /30"""
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('messages', [])[:20]
                
                bullish = sum(1 for m in messages 
                             if m.get('entities', {}).get('sentiment', {}).get('basic') == 'Bullish')
                bearish = sum(1 for m in messages
                             if m.get('entities', {}).get('sentiment', {}).get('basic') == 'Bearish')
                
                total = bullish + bearish
                if total == 0:
                    return 0
                
                pct = (bullish / total) * 100
                if pct > 70:
                    return 30
                elif pct > 60:
                    return 20
                elif pct > 50:
                    return 10
        except:
            pass
        
        return 0
    
    def calculate_atr(self, data, period=14):
        """Calculate ATR"""
        high_low = data['High'] - data['Low']
        atr = high_low.rolling(period).mean().iloc[-1]
        return atr
