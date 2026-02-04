"""
Webhooks and automation routes.
Handles fulfillment webhooks and notification triggers.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import json

from ..database import get_db
from ..models import Order, Medicine, Customer

router = APIRouter(prefix="/webhook", tags=["Webhooks"])


# Pydantic schemas
class FulfillmentPayload(BaseModel):
    order_id: int
    action: str = "fulfill"  # fulfill, cancel, return
    notes: Optional[str] = None


class FulfillmentResponse(BaseModel):
    success: bool
    order_id: int
    status: str
    message: str
    timestamp: str
    payload: dict


class NotificationPayload(BaseModel):
    order_id: int
    notification_type: str = "confirmation"  # confirmation, refill_reminder, status_update
    channel: str = "email"  # email, whatsapp, sms


# In-memory webhook log for demo purposes
webhook_logs = []


@router.post("/fulfillment", response_model=FulfillmentResponse)
def trigger_fulfillment(
    payload: FulfillmentPayload,
    db: Session = Depends(get_db)
):
    """
    Warehouse fulfillment webhook.
    Called by the Action Agent when an order is approved.
    
    This simulates triggering warehouse automation:
    - Pick and pack
    - Shipping label generation
    - Dispatch notification
    """
    # Get order
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Validate order can be fulfilled
    if order.status != "approved":
        raise HTTPException(
            status_code=400, 
            detail=f"Order cannot be fulfilled. Current status: {order.status}"
        )
    
    # Get medicine and customer details for the response
    medicine = db.query(Medicine).filter(Medicine.id == order.medicine_id).first()
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    
    # Create fulfillment record
    fulfillment_data = {
        "order_id": order.id,
        "customer_name": customer.name if customer else "Unknown",
        "customer_email": customer.email if customer else None,
        "medicine_name": medicine.name if medicine else "Unknown",
        "quantity": order.quantity,
        "unit_type": medicine.unit_type if medicine else "units",
        "action": payload.action,
        "notes": payload.notes,
        "warehouse_zone": "A-12",  # Simulated warehouse zone
        "pick_location": "RACK-A12-SHELF-3",  # Simulated pick location
        "estimated_dispatch": datetime.utcnow().isoformat()
    }
    
    # Log the webhook
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "/webhook/fulfillment",
        "payload": fulfillment_data,
        "status": "success"
    }
    webhook_logs.append(log_entry)
    
    # Update order status
    order.status = "fulfilled"
    order.webhook_triggered = True
    db.commit()
    
    # Console log for demo visibility
    print(f"\n{'='*50}")
    print("📦 WAREHOUSE FULFILLMENT WEBHOOK TRIGGERED")
    print(f"{'='*50}")
    print(f"Order ID: {order.id}")
    print(f"Customer: {fulfillment_data['customer_name']}")
    print(f"Medicine: {fulfillment_data['medicine_name']}")
    print(f"Quantity: {fulfillment_data['quantity']} {fulfillment_data['unit_type']}")
    print(f"Pick Location: {fulfillment_data['pick_location']}")
    print(f"{'='*50}\n")
    
    return FulfillmentResponse(
        success=True,
        order_id=order.id,
        status="fulfilled",
        message="Order sent to warehouse for fulfillment",
        timestamp=datetime.utcnow().isoformat(),
        payload=fulfillment_data
    )


@router.post("/notification")
def trigger_notification(
    payload: NotificationPayload,
    db: Session = Depends(get_db)
):
    """
    Notification webhook.
    Simulates sending email/WhatsApp/SMS notifications.
    """
    # Get order details
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
    medicine = db.query(Medicine).filter(Medicine.id == order.medicine_id).first()
    
    # Build notification content
    if payload.notification_type == "confirmation":
        subject = f"Order Confirmation - #{order.id}"
        message = f"""
        Dear {customer.name if customer else 'Customer'},
        
        Your order has been confirmed!
        
        Order Details:
        - Order ID: #{order.id}
        - Medicine: {medicine.name if medicine else 'N/A'}
        - Quantity: {order.quantity}
        - Total: ${order.total_price:.2f}
        
        Your order is being prepared for dispatch.
        
        Thank you for choosing PharmaAgent!
        """
    elif payload.notification_type == "refill_reminder":
        subject = "Refill Reminder"
        message = f"""
        Dear {customer.name if customer else 'Customer'},
        
        It's time to refill your prescription for {medicine.name if medicine else 'your medication'}!
        
        Would you like us to process a refill order for you?
        
        Reply to this message or visit our app to confirm.
        
        Stay healthy!
        PharmaAgent Team
        """
    else:
        subject = f"Order Update - #{order.id}"
        message = f"Your order #{order.id} status: {order.status}"
    
    notification_data = {
        "order_id": order.id,
        "customer_id": customer.id if customer else None,
        "channel": payload.channel,
        "type": payload.notification_type,
        "subject": subject,
        "message": message.strip(),
        "recipient": customer.email if payload.channel == "email" else customer.phone,
        "sent_at": datetime.utcnow().isoformat()
    }
    
    # Log the notification
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "/webhook/notification",
        "payload": notification_data,
        "status": "success"
    }
    webhook_logs.append(log_entry)
    
    # Update order notification status
    order.notification_sent = True
    db.commit()
    
    # Console log for demo visibility
    print(f"\n{'='*50}")
    print(f"📧 {payload.channel.upper()} NOTIFICATION SENT")
    print(f"{'='*50}")
    print(f"To: {notification_data['recipient']}")
    print(f"Subject: {subject}")
    print(f"Type: {payload.notification_type}")
    print(f"{'='*50}\n")
    
    return {
        "success": True,
        "order_id": order.id,
        "notification_type": payload.notification_type,
        "channel": payload.channel,
        "message": "Notification sent successfully",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/logs")
def get_webhook_logs(limit: int = 50):
    """Get recent webhook logs for debugging/observability."""
    return {
        "total": len(webhook_logs),
        "logs": webhook_logs[-limit:]
    }


@router.delete("/logs")
def clear_webhook_logs():
    """Clear webhook logs."""
    global webhook_logs
    webhook_logs = []
    return {"success": True, "message": "Webhook logs cleared"}
