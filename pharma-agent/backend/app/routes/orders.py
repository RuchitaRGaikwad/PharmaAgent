"""
Orders API routes.
Handles order creation, status updates, and order history.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models import Order, Medicine, Customer, OrderHistory

router = APIRouter(prefix="/orders", tags=["Orders"])


# Pydantic schemas
class OrderCreate(BaseModel):
    customer_id: int
    medicine_id: int
    quantity: int
    prescription_verified: bool = False


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    medicine_id: int
    quantity: int
    total_price: float
    status: str
    rejection_reason: Optional[str] = None
    prescription_verified: bool
    webhook_triggered: bool
    notification_sent: bool
    created_at: datetime
    updated_at: datetime
    medicine_name: Optional[str] = None
    customer_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
    rejection_reason: Optional[str] = None


# Endpoints
@router.get("", response_model=List[OrderResponse])
def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all orders with optional filtering."""
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    # Enrich with medicine and customer names
    result = []
    for order in orders:
        order_dict = {
            "id": order.id,
            "customer_id": order.customer_id,
            "medicine_id": order.medicine_id,
            "quantity": order.quantity,
            "total_price": order.total_price,
            "status": order.status,
            "rejection_reason": order.rejection_reason,
            "prescription_verified": order.prescription_verified,
            "webhook_triggered": order.webhook_triggered,
            "notification_sent": order.notification_sent,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "medicine_name": order.medicine.name if order.medicine else None,
            "customer_name": order.customer.name if order.customer else None
        }
        result.append(order_dict)
    
    return result


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Get a specific order by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "medicine_id": order.medicine_id,
        "quantity": order.quantity,
        "total_price": order.total_price,
        "status": order.status,
        "rejection_reason": order.rejection_reason,
        "prescription_verified": order.prescription_verified,
        "webhook_triggered": order.webhook_triggered,
        "notification_sent": order.notification_sent,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "medicine_name": order.medicine.name if order.medicine else None,
        "customer_name": order.customer.name if order.customer else None
    }


@router.post("", response_model=OrderResponse)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    Create a new order.
    Note: This is a direct order creation. 
    For agent-based ordering, use the /chat endpoint.
    """
    # Validate medicine exists
    medicine = db.query(Medicine).filter(Medicine.id == order.medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    # Validate customer exists
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Calculate total price
    total_price = medicine.price * order.quantity
    
    # Create order
    db_order = Order(
        customer_id=order.customer_id,
        medicine_id=order.medicine_id,
        quantity=order.quantity,
        total_price=total_price,
        status="pending",
        prescription_verified=order.prescription_verified
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    return {
        "id": db_order.id,
        "customer_id": db_order.customer_id,
        "medicine_id": db_order.medicine_id,
        "quantity": db_order.quantity,
        "total_price": db_order.total_price,
        "status": db_order.status,
        "rejection_reason": db_order.rejection_reason,
        "prescription_verified": db_order.prescription_verified,
        "webhook_triggered": db_order.webhook_triggered,
        "notification_sent": db_order.notification_sent,
        "created_at": db_order.created_at,
        "updated_at": db_order.updated_at,
        "medicine_name": medicine.name,
        "customer_name": customer.name
    }


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    update: OrderStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update order status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    valid_statuses = ["pending", "approved", "rejected", "fulfilled", "cancelled"]
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    order.status = update.status
    if update.rejection_reason:
        order.rejection_reason = update.rejection_reason
    
    db.commit()
    
    return {"success": True, "order_id": order_id, "new_status": update.status}


@router.patch("/{order_id}/webhook")
def mark_webhook_triggered(order_id: int, db: Session = Depends(get_db)):
    """Mark order as having triggered webhook."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.webhook_triggered = True
    db.commit()
    
    return {"success": True, "order_id": order_id, "webhook_triggered": True}


@router.patch("/{order_id}/notification")
def mark_notification_sent(order_id: int, db: Session = Depends(get_db)):
    """Mark order as having sent notification."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.notification_sent = True
    db.commit()
    
    return {"success": True, "order_id": order_id, "notification_sent": True}
