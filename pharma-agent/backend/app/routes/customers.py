"""
Customers API routes.
Handles customer management and order history.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import aiofiles

from ..database import get_db
from ..models import Customer, OrderHistory

router = APIRouter(prefix="/customers", tags=["Customers"])

# Upload directory for prescriptions
UPLOAD_DIR = "uploads/prescriptions"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Pydantic schemas
class CustomerBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    has_verified_prescription: bool
    prescription_file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderHistoryResponse(BaseModel):
    id: int
    customer_id: int
    medicine_id: int
    medicine_name: Optional[str] = None
    quantity: int
    frequency_days: int
    purchase_date: datetime
    status: str
    
    class Config:
        from_attributes = True


# Endpoints
@router.get("", response_model=List[CustomerResponse])
def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get all customers."""
    return db.query(Customer).offset(skip).limit(limit).all()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get a specific customer by ID."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/history", response_model=List[OrderHistoryResponse])
def get_customer_history(
    customer_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get order history for a specific customer.
    Used by the Refill Prediction Agent.
    """
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    history = db.query(OrderHistory).filter(
        OrderHistory.customer_id == customer_id
    ).order_by(OrderHistory.purchase_date.desc()).limit(limit).all()
    
    return history


@router.post("", response_model=CustomerResponse)
def create_customer(customer: CustomerBase, db: Session = Depends(get_db)):
    """Create a new customer."""
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


@router.post("/{customer_id}/prescription")
async def upload_prescription(
    customer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload prescription for a customer.
    Automatically verifies the customer's prescription status.
    """
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    # Save file
    filename = f"prescription_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    async with aiofiles.open(filepath, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Update customer prescription status
    customer.has_verified_prescription = True
    customer.prescription_file_path = filepath
    db.commit()
    
    return {
        "success": True,
        "customer_id": customer_id,
        "file_path": filepath,
        "message": "Prescription uploaded and verified successfully"
    }


@router.patch("/{customer_id}/verify-prescription")
def verify_prescription(
    customer_id: int,
    verified: bool = True,
    db: Session = Depends(get_db)
):
    """Manually verify or unverify a customer's prescription status."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.has_verified_prescription = verified
    db.commit()
    
    return {
        "success": True,
        "customer_id": customer_id,
        "has_verified_prescription": verified
    }


@router.get("/by-email/{email}", response_model=CustomerResponse)
def get_customer_by_email(email: str, db: Session = Depends(get_db)):
    """Get a customer by email address."""
    customer = db.query(Customer).filter(Customer.email == email).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
