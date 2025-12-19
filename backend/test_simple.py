from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "🥓 BaconAlgo API Running!"}

@app.get("/api/scan")
def scan():
    # Test simple avec 3 symboles
    symbols = ['AAPL', 'TSLA', 'SPY']
    signals = []
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            price = data['Close'].iloc[-1]
            
            signals.append({
                'symbol': symbol,
                'price': float(price),
                'direction': 'BUY',
                'score': 85
            })
        except:
            pass
    
    return {
        'success': True,
        'signals': signals
    }

if __name__ == "__main__":
    import uvicorn
    print("🥓 Starting BaconAlgo...")
    uvicorn.run(app, host="localhost", port=8000)
