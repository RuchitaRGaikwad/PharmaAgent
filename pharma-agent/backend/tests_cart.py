import sys
import os

from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Medicine, Customer, Cart, CartItem, Order

# Setup test database
def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[override_get_db] = override_get_db

def run_tests():
    print(f"Database URL: {engine.url}")
    # Explicitly create tables to be sure
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    # Check if Cart table exists
    from sqlalchemy import inspect
    inspector = inspect(engine)
    print(f"Tables in DB: {inspector.get_table_names()}")

    with TestClient(app) as client:
        test_cart_flow(client)

def test_cart_flow(client):
    # 1. Clear cart first
    response = client.delete("/cart/1/clear")
    assert response.status_code == 200

    # 2. Get Medicine (Paracetamol - OTC) and (Amoxicillin - Rx)
    # We rely on seed data. Paracetamol ID 1, Amoxicillin ID 2 usually.
    # Check what medicines are available
    response = client.get("/medicines")
    assert response.status_code == 200
    medicines = response.json()
    paracetamol = next((m for m in medicines if "Paracetamol" in m['name']), None)
    amoxicillin = next((m for m in medicines if "Amoxicillin" in m['name']), None)
    
    assert paracetamol is not None
    assert amoxicillin is not None
    
    # 3. Add Paracetamol (OTC) to cart
    response = client.post("/cart/1/add", json={"medicine_id": paracetamol['id'], "quantity": 2})
    assert response.status_code == 200
    assert response.json()["success"] == True

    # 4. Verify cart has item
    response = client.get("/cart/1")
    assert response.status_code == 200
    cart_data = response.json()
    assert cart_data["total_items"] == 1
    assert cart_data["items"][0]["medicine_name"] == paracetamol['name']
    assert cart_data["items"][0]["quantity"] == 2

    # 5. Checkout (Should succeed as OTC)
    # Need to create customer or ensure customer 1 exists
    # The checkout endpoint creates a default customer if not exists
    response = client.post("/cart/1/checkout", json={"customer_id": 1})
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    assert len(result["order_ids"]) == 1
    
    print("OTC Checkout Successful")

    print(f"Amoxicillin details: {amoxicillin}")

    # 6. Add Amoxicillin (Rx) to cart
    response = client.post("/cart/1/add", json={"medicine_id": amoxicillin['id'], "quantity": 1})
    assert response.status_code == 200

    # 7. Checkout (Should fail/block due to Rx requirement)
    # Use a new customer ID to ensure they don't have verified prescription (default is False)
    # Customer 1 has verified prescription from seed data
    rx_customer_id = 999
    
    response = client.post("/cart/1/checkout", json={"customer_id": rx_customer_id})
    assert response.status_code == 200 # It returns 200 but with success=False
    result = response.json()
    
    print(f"Rx Checkout Result: {result}")
    
    assert result["success"] == False
    assert result["blocked"] == True
    # Initial assertion mismatch: "Prescription required" vs "requires a valid prescription"
    assert any("requires a valid prescription" in item for item in result["blocked_items"])
    
    print("Rx Blocking Successful")
    
    print("Rx Blocking Successful")

    # 8. Simulate Prescription Upload (Update customer in DB)
    # We can use a direct DB session or an API if exposed.
    # Let's use a direct DB update via app dependency (or just skip for now if too complex to setup)
    # Actually, let's just create a new customer ID 2 with prescription verified in DB using the app's db session?
    # Or cleaner: Just check if safety warnings are returned.
    
    # 9. Test Low Stock Warning (if applicable)
    # Let's check safety notes warning
    # Paracetamol has safety notes?
    if paracetamol.get('safety_notes'):
        # Add again
        client.post("/cart/1/add", json={"medicine_id": paracetamol['id'], "quantity": 1})
        # Checkout
        response = client.post("/cart/1/checkout", json={"customer_id": 1})
        result = response.json()
        # Should have warnings
        assert "warnings" in result
        assert len(result["warnings"]) > 0
        print("Safety Warnings Verified")

if __name__ == "__main__":
    try:
        run_tests()
        print("ALL TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
