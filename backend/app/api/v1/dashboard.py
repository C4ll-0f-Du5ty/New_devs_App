from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from decimal import Decimal  # Added by Allem for exact financial precision
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    # ========================================
    # BUG FIX #3 - DECIMAL PRECISION FOR FINANCIAL DATA
    # Fixed by: Allem
    # Date: 9th July 2026
    # 
    # PROBLEM: Converting exact decimal values to float caused rounding errors.
    # The database stores amounts as NUMERIC(10,3) for exact precision, but
    # converting to float introduces binary representation errors. This caused
    # the "few cents off" issues reported by the finance team.
    #
    # Example: 333.333 + 333.333 + 333.334 = 1000.000 (exact in DB)
    # But float arithmetic could give 999.9999999 causing rounding discrepancies.
    #
    # OLD CODE (BROKEN - Precision Loss):
    # total_revenue_float = float(revenue_data['total'])
    # return {
    #     "property_id": revenue_data['property_id'],
    #     "total_revenue": total_revenue_float,  # Float with precision loss
    #     ...
    # }
    #
    # NEW CODE (FIXED - Exact Decimal Precision):
    total_revenue = Decimal(str(revenue_data['total']))
    # ========================================
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": str(total_revenue),  # Return as string to preserve exact precision
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
