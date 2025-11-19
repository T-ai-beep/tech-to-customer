import sys
print("=" * 50, flush=True)
print("DEBUG TEST - Finding Where It Hangs", flush=True)
print("=" * 50, flush=True)

print("\n1. Importing models...", flush=True)
try:
    from models import get_engine, get_session
    print("   ✅ Models imported", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    sys.exit(1)

print("\n2. Getting DATABASE_URL...", flush=True)
try:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    db_url = os.getenv('DATABASE_URL')
    print(f"   DATABASE_URL: {db_url[:50]}...", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    sys.exit(1)

print("\n3. Creating engine...", flush=True)
try:
    engine = get_engine()
    print("   ✅ Engine created", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    sys.exit(1)

print("\n4. Testing connection...", flush=True)
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("   ✅ Connection works!", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    sys.exit(1)

print("\n5. Creating session...", flush=True)
try:
    session = get_session(engine)
    print("   ✅ Session created", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    sys.exit(1)

print("\n6. Importing DatabaseHelper...", flush=True)
try:
    from database import DatabaseHelper
    print("   ✅ DatabaseHelper imported", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    sys.exit(1)

print("\n7. Creating DatabaseHelper instance...", flush=True)
try:
    db = DatabaseHelper(session)
    print("   ✅ DatabaseHelper created", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    sys.exit(1)

print("\n8. Getting customers (this queries the database)...", flush=True)
print("   (This may take 10-30 seconds on Render free tier...)", flush=True)
try:
    customers = db.get_all_customers()
    print(f"   ✅ Found {len(customers)} customers", flush=True)
    for c in customers:
        print(f"      - {c.name}", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n9. Getting technicians...", flush=True)
try:
    techs = db.get_all_technicians()
    print(f"   ✅ Found {len(techs)} technicians", flush=True)
    for t in techs:
        print(f"      - {t.name} (skills: {', '.join(t.skills)})", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n10. Testing distance calculation...", flush=True)
try:
    distance = db.calculate_distance(30.2672, -97.7431, 30.2808, -97.7461)
    print(f"   ✅ Distance calculation works: {distance:.2f} miles", flush=True)
except Exception as e:
    print(f"   ❌ FAILED: {e}", flush=True)
    sys.exit(1)

print("\n" + "=" * 50, flush=True)
print("✅ ALL TESTS PASSED!", flush=True)
print("=" * 50, flush=True)
print("\nYour system is working correctly.", flush=True)
print("Render's free tier is just slow (10-30 second delays).", flush=True)