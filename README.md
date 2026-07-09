# Property Revenue Dashboard - Bug Fixes

## 3 Bugs Fixed

### BUG #1: PRIVACY VIOLATION
**Problem:** Clients seeing other clients' revenue data  
**Cause:** Cache key missing tenant_id - was `revenue:prop-001` for all tenants  
**Fix:** Added tenant_id to cache key → `revenue:tenant-a:prop-001`  
**File:** `backend/app/services/cache.py` line 26

---

### BUG #2: WRONG REVENUE NUMBERS
**Problem:** Client A's March revenue didn't match their records  
**Cause:** Queries used UTC time, ignored property timezones. Booking at Feb 29 23:30 UTC = March 1 00:30 Paris, but counted in February  
**Fix:** Get property timezone from database, create month boundaries in local time, convert to UTC for query  
**File:** `backend/app/services/reservations.py` lines 1-100

---

### BUG #3: CENTS OFF
**Problem:** Finance team said numbers slightly off  
**Cause:** Converting database NUMERIC to float caused rounding. 333.333 + 333.333 + 333.334 = 999.999999 instead of 1000.000  
**Fix:** Keep as Decimal, return as string. Frontend parses string instead of receiving number  
**Files:** `backend/app/api/v1/dashboard.py` + `frontend/src/components/RevenueSummary.tsx`
