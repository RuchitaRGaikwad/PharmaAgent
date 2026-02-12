"""
Notifications Routes - Stock Alert System

Provides endpoints for:
1. Real-time stock notifications
2. Admin notification management
3. WebSocket for live updates
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging
import json
import asyncio

from ..database import get_db
from ..models import StockNotification, Medicine

router = APIRouter(prefix="/notifications", tags=["Notifications"])

# Configure logging
notify_logger = logging.getLogger("notifications")
notify_logger.setLevel(logging.INFO)

# Active WebSocket connections
active_connections: List[WebSocket] = []


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class NotificationResponse(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    stock_level: int
    threshold: int
    notification_type: str
    is_read: bool
    is_acknowledged: bool
    created_at: str


class BulkActionRequest(BaseModel):
    notification_ids: List[int]


# =============================================================================
# NOTIFICATION ENDPOINTS
# =============================================================================

@router.get("/stock-alerts")
def get_stock_alerts(
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all stock notifications."""
    query = db.query(StockNotification)
    
    if unread_only:
        query = query.filter(StockNotification.is_read == False)
    
    notifications = query.order_by(desc(StockNotification.created_at)).limit(limit).all()
    
    return {
        "total": len(notifications),
        "unread_count": db.query(StockNotification).filter(StockNotification.is_read == False).count(),
        "notifications": [
            {
                "id": n.id,
                "medicine_id": n.medicine_id,
                "medicine_name": n.medicine_name,
                "stock_level": n.stock_level,
                "threshold": n.threshold,
                "notification_type": n.notification_type,
                "is_read": n.is_read,
                "is_acknowledged": n.is_acknowledged,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in notifications
        ]
    }


@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    """Get count of unread notifications for badge."""
    count = db.query(StockNotification).filter(StockNotification.is_read == False).count()
    return {"count": count}


@router.patch("/{notification_id}/read")
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read."""
    notification = db.query(StockNotification).filter(StockNotification.id == notification_id).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"success": True, "notification_id": notification_id}


@router.patch("/{notification_id}/acknowledge")
def acknowledge_notification(notification_id: int, db: Session = Depends(get_db)):
    """Acknowledge a notification (dismiss it)."""
    notification = db.query(StockNotification).filter(StockNotification.id == notification_id).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_acknowledged = True
    notification.is_read = True
    db.commit()
    
    notify_logger.info(f"Notification {notification_id} acknowledged")
    
    return {"success": True, "notification_id": notification_id}


@router.post("/mark-all-read")
def mark_all_read(db: Session = Depends(get_db)):
    """Mark all notifications as read."""
    db.query(StockNotification).filter(StockNotification.is_read == False).update({"is_read": True})
    db.commit()
    
    return {"success": True, "message": "All notifications marked as read"}


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    """Delete a notification."""
    notification = db.query(StockNotification).filter(StockNotification.id == notification_id).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"success": True, "message": "Notification deleted"}


# =============================================================================
# STOCK ALERT TRIGGER (Called internally)
# =============================================================================

def check_and_create_stock_alert(medicine_id: int, medicine_name: str, stock_level: int, db: Session):
    """Check stock level and create notification if needed."""
    LOW_STOCK_THRESHOLD = 20
    
    # Determine notification type
    if stock_level <= 0:
        notification_type = "out_of_stock"
    elif stock_level < LOW_STOCK_THRESHOLD:
        notification_type = "low_stock"
    else:
        return None  # No alert needed
    
    # Check if similar unacknowledged notification exists
    existing = db.query(StockNotification).filter(
        StockNotification.medicine_id == medicine_id,
        StockNotification.is_acknowledged == False,
        StockNotification.notification_type == notification_type
    ).first()
    
    if existing:
        # Update existing notification with new stock level
        existing.stock_level = stock_level
        existing.created_at = datetime.utcnow()
        existing.is_read = False
        db.commit()
        return existing
    
    # Create new notification
    notification = StockNotification(
        medicine_id=medicine_id,
        medicine_name=medicine_name,
        stock_level=stock_level,
        threshold=LOW_STOCK_THRESHOLD,
        notification_type=notification_type
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    notify_logger.info(f"Stock alert created: {medicine_name} at {stock_level} units ({notification_type})")
    
    # Broadcast to WebSocket clients
    asyncio.create_task(broadcast_notification({
        "type": "stock_alert",
        "notification": {
            "id": notification.id,
            "medicine_name": medicine_name,
            "stock_level": stock_level,
            "notification_type": notification_type
        }
    }))
    
    return notification


# =============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# =============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications."""
    await websocket.accept()
    active_connections.append(websocket)
    notify_logger.info(f"WebSocket connected. Active connections: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection alive, listen for messages
            data = await websocket.receive_text()
            
            # Handle ping/pong for keep-alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        notify_logger.info(f"WebSocket disconnected. Active connections: {len(active_connections)}")


async def broadcast_notification(message: dict):
    """Broadcast notification to all connected WebSocket clients."""
    if not active_connections:
        return
    
    message_json = json.dumps(message)
    
    for connection in active_connections:
        try:
            await connection.send_text(message_json)
        except Exception as e:
            notify_logger.error(f"Failed to send WebSocket message: {e}")
