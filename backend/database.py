"""
🥓 Supabase Database Interface
"""

from supabase import create_client, Client
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(url, key)
    
    async def save_signal(self, signal):
        """Save signal to database"""
        try:
            data = {
                "symbol": signal['symbol'],
                "direction": signal['direction'],
                "entry": signal['entry'],
                "stop": signal['stop'],
                "target": signal['target'],
                "tech_score": signal['tech_score'],
                "social_score": signal['social_score'],
                "total_score": signal['total_score'],
                "rsi": signal['rsi'],
                "volume_ratio": signal['volume_ratio'],
                "created_at": signal['timestamp']
            }
            
            result = self.client.table('signals').insert(data).execute()
            return result
        except Exception as e:
            print(f"Error saving signal: {e}")
    
    async def get_top_signals(self, limit=10):
        """Get top signals from last 24h"""
        try:
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            
            result = self.client.table('signals')\
                .select("*")\
                .gte('created_at', yesterday)\
                .order('total_score', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"Error getting signals: {e}")
            return []
    
    async def get_stats(self):
        """Get trading stats"""
        try:
            # Get today's signals
            today = datetime.now().date().isoformat()
            
            result = self.client.table('signals')\
                .select("*")\
                .gte('created_at', today)\
                .execute()
            
            signals = result.data
            
            if not signals:
                return {
                    "total_signals": 0,
                    "avg_score": 0,
                    "best_signal": None
                }
            
            avg_score = sum(s['total_score'] for s in signals) / len(signals)
            best = max(signals, key=lambda x: x['total_score'])
            
            return {
                "total_signals": len(signals),
                "avg_score": round(avg_score, 1),
                "best_signal": best
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
