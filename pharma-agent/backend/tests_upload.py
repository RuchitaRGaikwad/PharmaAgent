import sys
import os
from fastapi.testclient import TestClient
import io

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import Base, engine, SessionLocal

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
    with TestClient(app) as client:
        test_upload_flow(client)

def test_upload_flow(client):
    # 1. Create a new unverified customer
    customer_data = {"name": "Test User", "email": "test@example.com"}
    response = client.post("/customers", json=customer_data)
    assert response.status_code == 200
    customer = response.json()
    customer_id = customer['id']
    print(f"Created customer {customer_id}: {customer}")
    
    # Verify initial status is False
    assert customer['has_verified_prescription'] == False

    # 2. Upload prescription
    # Create valid dummy image file
    file_content = b"fake image content"
    files = {"file": ("prescription.jpg", file_content, "image/jpeg")}
    
    print("Uploading prescription...")
    response = client.post(f"/customers/{customer_id}/prescription", files=files)
    assert response.status_code == 200
    result = response.json()
    print(f"Upload result: {result}")
    
    assert result['success'] == True
    
    # 3. Verify status updated to True
    print("Verifying customer status...")
    response = client.get(f"/customers/{customer_id}")
    assert response.status_code == 200
    updated_customer = response.json()
    print(f"Updated customer: {updated_customer}")
    
    assert updated_customer['has_verified_prescription'] == True
    print("Verification Successful!")

if __name__ == "__main__":
    try:
        run_tests()
        print("ALL TESTS PASSED")
    except AssertionError as e:
        print(f"TEST FAILED: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
