import json
import redis.asyncio as redis
from typing import Dict, Any
import os

# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

async def get_revenue_summary(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    """
    # ========================================
    # BUG FIX #1 - TENANT ISOLATION (Critical Data Privacy Issue)
    # Fixed by: Allem
    # Date: 9th July 2026
    # 
    # PROBLEM: Cache key was missing tenant_id, causing data from different
    # tenants to be mixed. When Client A viewed prop-001, it would cache as
    # "revenue:prop-001". Then Client B viewing their own prop-001 would
    # retrieve Client A's confidential revenue data from cache.
    #
    # OLD CODE (BROKEN - Data Privacy Violation):
    # cache_key = f"revenue:{property_id}"
    #
    # NEW CODE (FIXED - Complete Tenant Isolation):
    cache_key = f"revenue:{tenant_id}:{property_id}"
    # 
    # This ensures each tenant's data is completely isolated in the cache.
    # ========================================
    
    # Try to get from cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    
    # Calculate revenue
    result = await calculate_total_revenue(property_id, tenant_id)
    
    # Cache the result for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result
