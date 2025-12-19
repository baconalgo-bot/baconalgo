"""
🥓 Upstash Redis Cache
"""

from upstash_redis import Redis
import os
import json

class Cache:
    def __init__(self):
        self.redis = Redis(
            url=os.getenv("UPSTASH_REDIS_URL"),
            token=os.getenv("UPSTASH_REDIS_TOKEN")
        )
    
    async def get(self, key):
        """Get from cache"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except:
            pass
        return None
    
    async def set(self, key, value, ttl=300):
        """Set in cache with TTL"""
        try:
            self.redis.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            print(f"Cache error: {e}")
