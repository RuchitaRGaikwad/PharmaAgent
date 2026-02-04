"""
Medicines API routes.
Provides endpoints for medicine inventory management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import Medicine

router = APIRouter(prefix="/medicines", tags=["Medicines"])


# Pydantic schemas
class MedicineBase(BaseModel):
    name: str
    stock_level: int = 0
    unit_type: str = "tablets"
    prescription_required: bool = False
    price: float = 0.0
    dosage_info: Optional[str] = None


class MedicineResponse(MedicineBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MedicineUpdate(BaseModel):
    stock_level: Optional[int] = None
    price: Optional[float] = None


class InventoryUpdate(BaseModel):
    stock_level: int
    action: str = "set"  # "set", "add", "subtract"


# Endpoints
@router.get("", response_model=List[MedicineResponse])
def get_medicines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = None,
    prescription_only: Optional[bool] = None,
    in_stock: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get all medicines with optional filtering.
    
    - **search**: Search by medicine name
    - **prescription_only**: Filter by prescription requirement
    - **in_stock**: Filter by stock availability
    """
    query = db.query(Medicine)
    
    if search:
        query = query.filter(Medicine.name.ilike(f"%{search}%"))
    
    if prescription_only is not None:
        query = query.filter(Medicine.prescription_required == prescription_only)
    
    if in_stock is not None:
        if in_stock:
            query = query.filter(Medicine.stock_level > 0)
        else:
            query = query.filter(Medicine.stock_level == 0)
    
    return query.offset(skip).limit(limit).all()


@router.get("/{medicine_id}", response_model=MedicineResponse)
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    """Get a specific medicine by ID."""
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine


@router.get("/search/{name}", response_model=List[MedicineResponse])
def search_medicines(name: str, db: Session = Depends(get_db)):
    """
    Search medicines by name (fuzzy matching).
    Used by the Conversation Agent for medicine lookup.
    """
    medicines = db.query(Medicine).filter(
        Medicine.name.ilike(f"%{name}%")
    ).limit(10).all()
    return medicines


@router.patch("/inventory/{medicine_id}")
def update_inventory(
    medicine_id: int,
    update: InventoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update medicine inventory.
    
    - **action**: "set" (replace), "add" (increment), "subtract" (decrement)
    """
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    if update.action == "set":
        medicine.stock_level = update.stock_level
    elif update.action == "add":
        medicine.stock_level += update.stock_level
    elif update.action == "subtract":
        new_level = medicine.stock_level - update.stock_level
        if new_level < 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Current: {medicine.stock_level}"
            )
        medicine.stock_level = new_level
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    db.commit()
    db.refresh(medicine)
    
    return {
        "success": True,
        "medicine_id": medicine_id,
        "new_stock_level": medicine.stock_level,
        "message": f"Inventory updated successfully"
    }


@router.post("", response_model=MedicineResponse)
def create_medicine(medicine: MedicineBase, db: Session = Depends(get_db)):
    """Create a new medicine entry."""
    db_medicine = Medicine(**medicine.model_dump())
    db.add(db_medicine)
    db.commit()
    db.refresh(db_medicine)
    return db_medicine
