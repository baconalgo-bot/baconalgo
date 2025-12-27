from bacon_signal_pusher import BaconSignalPusher

pusher = BaconSignalPusher()

# Quand tu détectes un signal:
pusher.push_signal({
    'symbol': 'TSLA',
    'timeframe': '1d',
    'style': 'day',
    'rating': 'strong-buy',
    'score': 285,
    'entry': 312.45,
    'tp1': 321.95,
    'tp2': 327.97,
    'tp3': 337.45,
    'stop_loss': 305.60,
    'rr': 2.8,
    'resistance': 320.50,
    'support': 310.20,
    'setup': 'ORB5, VWAP, FVG',
    'wave': 'Wave 3',
    'confluence': 94,
    'description': 'Your detailed description...'
})
