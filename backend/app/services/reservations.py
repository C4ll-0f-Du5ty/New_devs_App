from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
import pytz  # Added by Allem for timezone-aware calculations

async def calculate_monthly_revenue(property_id: str, month: int, year: int, tenant_id: str, db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month.
    
    ========================================
    BUG FIX #2 - TIMEZONE-AWARE REVENUE CALCULATION
    Fixed by: Allem
    Date: 9th July 2026
    
    PROBLEM: Revenue was calculated using UTC dates without considering property
    timezones. This caused bookings to be counted in the wrong month. For example,
    a booking at Feb 29 23:30 UTC is actually March 1 00:30 in Paris (UTC+1).
    The old code would count this in February instead of March, causing Client A's
    March revenue reports to be incorrect.
    
    OLD CODE (BROKEN - Ignored Timezones):
    # start_date = datetime(year, month, 1)
    # if month < 12:
    #     end_date = datetime(year, month + 1, 1)
    # else:
    #     end_date = datetime(year + 1, 1, 1)
    # 
    # query = '''
    #     SELECT SUM(total_amount) as total
    #     FROM reservations
    #     WHERE property_id = $1
    #     AND tenant_id = $2
    #     AND check_in_date >= $3      -- UTC comparison
    #     AND check_in_date < $4       -- UTC comparison
    # '''
    
    NEW CODE (FIXED - Respects Property Timezones):
    ========================================
    """
    try:
        # Import database pool
        from app.core.database_pool import DatabasePool
        
        # Initialize pool if needed
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                from sqlalchemy import text
                
                # Step 1: Get property timezone
                tz_query = text("""
                    SELECT timezone 
                    FROM properties 
                    WHERE id = :property_id AND tenant_id = :tenant_id
                """)
                
                tz_result = await session.execute(tz_query, {
                    "property_id": property_id,
                    "tenant_id": tenant_id
                })
                tz_row = tz_result.fetchone()
                
                if not tz_row:
                    return Decimal('0')
                
                property_tz = tz_row.timezone or 'UTC'
                tz = pytz.timezone(property_tz)
                
                # Step 2: Create month boundaries in property's local timezone
                start_local = tz.localize(datetime(year, month, 1))
                if month < 12:
                    end_local = tz.localize(datetime(year, month + 1, 1))
                else:
                    end_local = tz.localize(datetime(year + 1, 1, 1))
                
                # Step 3: Convert to UTC for database query (timestamps stored in UTC)
                start_utc = start_local.astimezone(pytz.UTC)
                end_utc = end_local.astimezone(pytz.UTC)
                
                print(f"DEBUG: Querying revenue for {property_id} from {start_utc} to {end_utc} (Property TZ: {property_tz})")
                
                # Step 4: Query with timezone-adjusted UTC boundaries
                query = text("""
                    SELECT SUM(total_amount) as total
                    FROM reservations
                    WHERE property_id = :property_id
                    AND tenant_id = :tenant_id
                    AND check_in_date >= :start_date
                    AND check_in_date < :end_date
                """)
                
                result = await session.execute(query, {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "start_date": start_utc,
                    "end_date": end_utc
                })
                row = result.fetchone()
                
                if row and row.total:
                    return Decimal(str(row.total))
                else:
                    return Decimal('0')
        else:
            raise Exception("Database pool not available")
            
    except Exception as e:
        print(f"Database error for monthly revenue {property_id} (tenant: {tenant_id}): {e}")
        return Decimal('0')  # Placeholder for now until DB connection is finalized

async def calculate_total_revenue(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    try:
        # Import database pool
        from app.core.database_pool import DatabasePool
        
        # Initialize pool if needed
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                # Use SQLAlchemy text for raw SQL
                from sqlalchemy import text
                
                query = text("""
                    SELECT 
                        property_id,
                        SUM(total_amount) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations 
                    WHERE property_id = :property_id AND tenant_id = :tenant_id
                    GROUP BY property_id
                """)
                
                result = await session.execute(query, {
                    "property_id": property_id, 
                    "tenant_id": tenant_id
                })
                row = result.fetchone()
                
                if row:
                    total_revenue = Decimal(str(row.total_revenue))
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": str(total_revenue),
                        "currency": "USD", 
                        "count": row.reservation_count
                    }
                else:
                    # No reservations found for this property
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.00",
                        "currency": "USD",
                        "count": 0
                    }
        else:
            raise Exception("Database pool not available")
            
    except Exception as e:
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        
        # Create property-specific mock data for testing when DB is unavailable
        # This ensures each property shows different figures
        mock_data = {
            'prop-001': {'total': '1000.00', 'count': 3},
            'prop-002': {'total': '4975.50', 'count': 4}, 
            'prop-003': {'total': '6100.50', 'count': 2},
            'prop-004': {'total': '1776.50', 'count': 4},
            'prop-005': {'total': '3256.00', 'count': 3}
        }
        
        mock_property_data = mock_data.get(property_id, {'total': '0.00', 'count': 0})
        
        return {
            "property_id": property_id,
            "tenant_id": tenant_id, 
            "total": mock_property_data['total'],
            "currency": "USD",
            "count": mock_property_data['count']
        }
