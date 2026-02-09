"""
Cart routes for PharmaAgent.
Handles shopping cart operations including add, remove, and checkout.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

from ..database import get_db
from ..models import Cart, CartItem, Medicine, Customer, Order, AgentTrace
from agents.safety_agent import SafetyAgent

router = APIRouter(prefix="/cart", tags=["Cart"])


# ==================== Pydantic Schemas ====================

class AddToCartRequest(BaseModel):
    medicine_id: int
    quantity: int = 1


class CartItemResponse(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    dosage_info: Optional[str]
    quantity: int
    price: float
    prescription_required: bool
    stock_level: int
    category: str

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_items: int
    total_price: float
    has_prescription_items: bool

    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    customer_id: Optional[int] = 1


class CheckoutResponse(BaseModel):
    success: bool
    order_ids: List[int] = []
    message: str
    warnings: List[str] = []
    blocked: bool = False
    blocked_items: List[str] = []


# ==================== Helper Functions ====================

def get_or_create_cart(db: Session, user_id: int) -> Cart:
    """Get existing cart or create new one for user."""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def log_agent_trace(db: Session, agent_name: str, action: str, input_data: dict, 
                    output_data: dict, decision: str, reason: str):
    """Log agent decision to traces."""
    trace = AgentTrace(
        trace_id=f"cart_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        agent_name=agent_name,
        action=action,
        input_data=json.dumps(input_data),
        output_data=json.dumps(output_data),
        decision=decision,
        reason=reason
    )
    db.add(trace)
    db.commit()


# ==================== Cart Endpoints ====================

@router.get("/{user_id}", response_model=CartResponse)
async def get_cart(user_id: int, db: Session = Depends(get_db)):
    """Get user's cart with all items."""
    cart = get_or_create_cart(db, user_id)
    
    items = []
    total_price = 0.0
    has_prescription_items = False
    
    for item in cart.items:
        medicine = item.medicine
        if medicine:
            item_total = medicine.price * item.quantity
            total_price += item_total
            if medicine.prescription_required:
                has_prescription_items = True
            items.append(CartItemResponse(
                id=item.id,
                medicine_id=medicine.id,
                medicine_name=medicine.name,
                dosage_info=medicine.dosage_info,
                quantity=item.quantity,
                price=medicine.price,
                prescription_required=medicine.prescription_required,
                stock_level=medicine.stock_level,
                category=medicine.category or "General"
            ))
    
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=items,
        total_items=len(items),
        total_price=round(total_price, 2),
        has_prescription_items=has_prescription_items
    )


@router.post("/{user_id}/add")
async def add_to_cart(user_id: int, request: AddToCartRequest, db: Session = Depends(get_db)):
    """Add medicine to cart."""
    # Validate medicine exists
    medicine = db.query(Medicine).filter(Medicine.id == request.medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    # Check stock
    if medicine.stock_level < request.quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient stock. Available: {medicine.stock_level}"
        )
    
    # Get or create cart
    cart = get_or_create_cart(db, user_id)
    
    # Check if item already in cart
    existing_item = db.query(CartItem).filter(
        and_(CartItem.cart_id == cart.id, CartItem.medicine_id == request.medicine_id)
    ).first()
    
    if existing_item:
        # Update quantity
        new_quantity = existing_item.quantity + request.quantity
        if new_quantity > medicine.stock_level:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot add more. Max available: {medicine.stock_level}"
            )
        existing_item.quantity = new_quantity
    else:
        # Add new item
        cart_item = CartItem(
            cart_id=cart.id,
            medicine_id=request.medicine_id,
            quantity=request.quantity
        )
        db.add(cart_item)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Added {request.quantity}x {medicine.name} to cart",
        "cart_id": cart.id
    }


@router.delete("/{user_id}/remove/{item_id}")
async def remove_from_cart(user_id: int, item_id: int, db: Session = Depends(get_db)):
    """Remove item from cart."""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    item = db.query(CartItem).filter(
        and_(CartItem.id == item_id, CartItem.cart_id == cart.id)
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    db.delete(item)
    db.commit()
    
    return {"success": True, "message": "Item removed from cart"}


@router.patch("/{user_id}/update/{item_id}")
async def update_cart_item(user_id: int, item_id: int, quantity: int, db: Session = Depends(get_db)):
    """Update item quantity in cart."""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    item = db.query(CartItem).filter(
        and_(CartItem.id == item_id, CartItem.cart_id == cart.id)
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    if quantity <= 0:
        db.delete(item)
    else:
        # Check stock
        if item.medicine.stock_level < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {item.medicine.stock_level}"
            )
        item.quantity = quantity
    
    db.commit()
    
    return {"success": True, "message": "Cart updated"}


@router.post("/{user_id}/checkout", response_model=CheckoutResponse)
async def checkout(user_id: int, request: CheckoutRequest, db: Session = Depends(get_db)):
    """
    Process checkout with prescription validation and safety checks using SafetyAgent.
    Creates orders and decrements stock.
    """
    # Initialize Safety Agent
    safety_agent = SafetyAgent(db)

    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart or not cart.items:
        return CheckoutResponse(
            success=False,
            message="Cart is empty",
            blocked=True
        )
    
    # Get customer for prescription verification
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        # Create default customer if not exists
        customer = Customer(
            id=request.customer_id,
            name="Default User",
            email="user@example.com"
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    
    warnings = []
    blocked_items = []
    order_ids = []
    
    # Check each item
    for item in cart.items:
        medicine = item.medicine
        
        # Comprehensive Agent Validation
        validation = safety_agent.validate_order(
            medicine_name=medicine.name,
            quantity=item.quantity,
            customer_id=customer.id,
            prescription_verified=customer.has_verified_prescription
        )
        
        if not validation.approved:
            blocked_items.append(f"{medicine.name} - {validation.reason}")
            continue
            
        # Check specific safety notes (Agent method)
        item_warnings = safety_agent.check_safety_warnings(medicine)
        if item_warnings:
            warnings.extend(item_warnings)
    
    # If any items are blocked, don't proceed
    if blocked_items:
        log_agent_trace(
            db,
            agent_name="SafetyAgent",
            action="checkout_validation",
            input_data={"cart_id": cart.id, "items": len(cart.items)},
            output_data={"blocked_items": blocked_items},
            decision="BLOCKED",
            reason="Prescription or stock validation failed"
        )
        return CheckoutResponse(
            success=False,
            message="Some items cannot be purchased",
            blocked=True,
            blocked_items=blocked_items,
            warnings=warnings
        )
    
    # Process orders
    for item in cart.items:
        medicine = item.medicine
        
        # Create order
        order = Order(
            customer_id=customer.id,
            medicine_id=medicine.id,
            quantity=item.quantity,
            total_price=round(medicine.price * item.quantity, 2),
            status="pending",
            prescription_verified=medicine.prescription_required and customer.has_verified_prescription
        )
        db.add(order)
        db.flush()
        order_ids.append(order.id)
        
        # Decrement stock
        medicine.stock_level -= item.quantity
    
    # Clear cart
    for item in cart.items:
        db.delete(item)
    
    db.commit()
    
    # Log successful checkout
    log_agent_trace(
        db,
        agent_name="SafetyAgent",
        action="checkout_completed",
        input_data={"cart_id": cart.id, "order_count": len(order_ids)},
        output_data={"order_ids": order_ids},
        decision="APPROVED",
        reason="All safety checks passed"
    )
    
    return CheckoutResponse(
        success=True,
        order_ids=order_ids,
        message=f"Successfully created {len(order_ids)} order(s)",
        warnings=warnings
    )


@router.delete("/{user_id}/clear")
async def clear_cart(user_id: int, db: Session = Depends(get_db)):
    """Clear all items from cart."""
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if cart:
        for item in cart.items:
            db.delete(item)
        db.commit()
    
    return {"success": True, "message": "Cart cleared"}
