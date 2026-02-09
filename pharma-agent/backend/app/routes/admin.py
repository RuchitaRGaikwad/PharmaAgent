"""
Admin Routes - Admin Dashboard Endpoints

Provides admin-only endpoints for:
1. Inventory management (full CRUD)
2. Proactive alerts
3. Order management with webhook status
4. Agent traces and observability
5. JWT Authentication
6. Dashboard statistics
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import jwt
import hashlib

from ..database import get_db
from ..models import Medicine, Order, ProactiveAlert

router = APIRouter(prefix="/admin", tags=["Admin"])
security = HTTPBearer(auto_error=False)

# Configure logging for admin actions
admin_logger = logging.getLogger("admin")
admin_logger.setLevel(logging.INFO)

# JWT Configuration
JWT_SECRET = "pharmaagent-admin-secret-key-2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Demo admin credentials (in production, use database)
ADMIN_USERS = {
    "admin@pharmaagent.com": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "Admin User",
        "role": "super_admin"
    }
}

# In-memory agent traces storage (in production, use database)
AGENT_TRACES = []


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class AdminLogin(BaseModel):
    email: str
    password: str

class MedicineCreate(BaseModel):
    name: str
    stock_level: int = 0
    unit_type: str = "tablets"
    price: float = 0.0
    prescription_required: bool = False
    category: Optional[str] = None
    manufacturer: Optional[str] = None

class MedicineUpdate(BaseModel):
    name: Optional[str] = None
    stock_level: Optional[int] = None
    unit_type: Optional[str] = None
    price: Optional[float] = None
    prescription_required: Optional[bool] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None

class AgentTrace(BaseModel):
    agent_name: str
    input_text: str
    output_text: str
    decision: str
    confidence: float = 0.0
    duration_ms: int = 0


# =============================================================================
# JWT AUTHENTICATION
# =============================================================================

def create_jwt_token(email: str, name: str, role: str) -> str:
    """Create JWT token for admin user."""
    payload = {
        "email": email,
        "name": name,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token from Authorization header."""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/login")
def admin_login(credentials: AdminLogin):
    """Authenticate admin user and return JWT token."""
    admin_logger.info(f"Admin login attempt: {credentials.email}")
    
    user = ADMIN_USERS.get(credentials.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(credentials.email, user["name"], user["role"])
    admin_logger.info(f"Admin login successful: {credentials.email}")
    
    return {
        "success": True,
        "token": token,
        "user": {
            "email": credentials.email,
            "name": user["name"],
            "role": user["role"]
        }
    }


@router.get("/me")
def get_current_admin(payload: dict = Depends(verify_jwt_token)):
    """Get current authenticated admin user."""
    if not payload:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "email": payload.get("email"),
        "name": payload.get("name"),
        "role": payload.get("role")
    }


# =============================================================================
# DASHBOARD STATISTICS
# =============================================================================

@router.get("/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get summary statistics for admin dashboard."""
    admin_logger.info("Admin accessed dashboard stats")
    
    # Medicine stats
    total_medicines = db.query(Medicine).count()
    low_stock = db.query(Medicine).filter(Medicine.stock_level < 20, Medicine.stock_level > 0).count()
    out_of_stock = db.query(Medicine).filter(Medicine.stock_level <= 0).count()
    
    # Order stats
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    
    # Alert stats
    total_alerts = db.query(ProactiveAlert).count()
    active_alerts = db.query(ProactiveAlert).filter(ProactiveAlert.status == "pending").count()
    
    return {
        "medicines": {
            "total": total_medicines,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders
        },
        "alerts": {
            "total": total_alerts,
            "active": active_alerts
        },
        "traces": {
            "total": len(AGENT_TRACES)
        }
    }


# =============================================================================
# INVENTORY ENDPOINTS (FULL CRUD)
# =============================================================================

@router.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    """Get all medicines with stock levels for admin view."""
    admin_logger.info("Admin accessed inventory")
    
    medicines = db.query(Medicine).all()
    
    inventory = []
    for med in medicines:
        status = "ok"
        if med.stock_level <= 0:
            status = "out_of_stock"
        elif med.stock_level < 20:
            status = "low"
        
        inventory.append({
            "id": med.id,
            "name": med.name,
            "stock_level": med.stock_level,
            "unit_type": getattr(med, 'unit_type', 'tablets'),
            "price": getattr(med, 'price', 0),
            "prescription_required": getattr(med, 'prescription_required', False),
            "category": getattr(med, 'category', None),
            "manufacturer": getattr(med, 'manufacturer', None),
            "status": status
        })
    
    return {
        "total": len(inventory),
        "low_stock_count": sum(1 for i in inventory if i["status"] == "low"),
        "out_of_stock_count": sum(1 for i in inventory if i["status"] == "out_of_stock"),
        "inventory": inventory
    }


@router.post("/inventory")
def create_medicine(medicine: MedicineCreate, db: Session = Depends(get_db)):
    """Create a new medicine entry."""
    admin_logger.info(f"Admin creating medicine: {medicine.name}")
    
    new_medicine = Medicine(
        name=medicine.name,
        stock_level=medicine.stock_level,
        unit_type=medicine.unit_type,
        price=medicine.price,
        prescription_required=medicine.prescription_required
    )
    
    db.add(new_medicine)
    db.commit()
    db.refresh(new_medicine)
    
    admin_logger.info(f"Medicine created: {new_medicine.id} - {new_medicine.name}")
    
    return {
        "success": True,
        "medicine": {
            "id": new_medicine.id,
            "name": new_medicine.name,
            "stock_level": new_medicine.stock_level
        }
    }


@router.put("/inventory/{medicine_id}")
def update_medicine(medicine_id: int, medicine: MedicineUpdate, db: Session = Depends(get_db)):
    """Update an existing medicine."""
    existing = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    # Update only provided fields
    if medicine.name is not None:
        existing.name = medicine.name
    if medicine.stock_level is not None:
        existing.stock_level = medicine.stock_level
    if medicine.unit_type is not None:
        existing.unit_type = medicine.unit_type
    if medicine.price is not None:
        existing.price = medicine.price
    if medicine.prescription_required is not None:
        existing.prescription_required = medicine.prescription_required
    
    db.commit()
    admin_logger.info(f"Medicine updated: {medicine_id}")
    
    return {
        "success": True,
        "medicine": {
            "id": existing.id,
            "name": existing.name,
            "stock_level": existing.stock_level
        }
    }


@router.delete("/inventory/{medicine_id}")
def delete_medicine(medicine_id: int, db: Session = Depends(get_db)):
    """Delete a medicine."""
    existing = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    name = existing.name
    db.delete(existing)
    db.commit()
    
    admin_logger.info(f"Medicine deleted: {medicine_id} - {name}")
    
    return {
        "success": True,
        "message": f"Medicine '{name}' deleted"
    }


@router.post("/restock")
def restock_medicine(medicine_id: int, quantity: int, db: Session = Depends(get_db)):
    """Restock a medicine by adding quantity."""
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    old_stock = medicine.stock_level
    medicine.stock_level += quantity
    db.commit()
    
    admin_logger.info(f"Admin restocked {medicine.name}: {old_stock} -> {medicine.stock_level}")
    
    return {
        "success": True,
        "medicine_id": medicine_id,
        "name": medicine.name,
        "old_stock": old_stock,
        "new_stock": medicine.stock_level,
        "added": quantity
    }


# =============================================================================
# ALERTS ENDPOINTS
# =============================================================================

@router.get("/alerts")
def get_admin_alerts(db: Session = Depends(get_db)):
    """Get all proactive alerts for admin view."""
    admin_logger.info("Admin accessed alerts")
    
    alerts = db.query(ProactiveAlert).order_by(desc(ProactiveAlert.created_at)).limit(50).all()
    
    return {
        "total": len(alerts),
        "alerts": [
            {
                "id": alert.id,
                "customer_id": alert.customer_id,
                "type": alert.alert_type,
                "message": alert.message,
                "priority": alert.priority,
                "status": alert.status,
                "created_at": alert.created_at.isoformat() if alert.created_at else None
            }
            for alert in alerts
        ]
    }


@router.patch("/alerts/{alert_id}/dismiss")
def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    """Dismiss an alert."""
    alert = db.query(ProactiveAlert).filter(ProactiveAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "dismissed"
    db.commit()
    
    admin_logger.info(f"Alert dismissed: {alert_id}")
    
    return {"success": True, "alert_id": alert_id}


# =============================================================================
# ORDERS ENDPOINTS
# =============================================================================

@router.get("/orders")
def get_admin_orders(db: Session = Depends(get_db)):
    """Get all orders with webhook status for admin view."""
    admin_logger.info("Admin accessed orders")
    
    orders = db.query(Order).order_by(desc(Order.created_at)).limit(100).all()
    
    return {
        "total": len(orders),
        "orders": [
            {
                "id": order.id,
                "customer_id": order.customer_id,
                "medicine_id": order.medicine_id,
                "quantity": order.quantity,
                "status": order.status,
                "webhook_status": getattr(order, 'webhook_status', 'unknown'),
                "created_at": order.created_at.isoformat() if order.created_at else None
            }
            for order in orders
        ]
    }


@router.get("/orders/{order_id}")
def get_order_details(order_id: int, db: Session = Depends(get_db)):
    """Get detailed order information."""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get medicine name
    medicine = db.query(Medicine).filter(Medicine.id == order.medicine_id).first()
    medicine_name = medicine.name if medicine else "Unknown"
    
    return {
        "id": order.id,
        "customer_id": order.customer_id,
        "medicine": {
            "id": order.medicine_id,
            "name": medicine_name
        },
        "quantity": order.quantity,
        "status": order.status,
        "webhook_status": getattr(order, 'webhook_status', 'unknown'),
        "created_at": order.created_at.isoformat() if order.created_at else None
    }


@router.patch("/orders/{order_id}/status")
def update_order_status(order_id: int, new_status: str, db: Session = Depends(get_db)):
    """Update order status."""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    old_status = order.status
    order.status = new_status
    db.commit()
    
    admin_logger.info(f"Order {order_id} status: {old_status} -> {new_status}")
    
    return {"success": True, "order_id": order_id, "status": new_status}


@router.post("/webhook-retry")
def retry_webhook(order_id: int, db: Session = Depends(get_db)):
    """Retry webhook for a failed order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    admin_logger.info(f"Admin triggered webhook retry for order {order_id}")
    
    return {
        "success": True,
        "order_id": order_id,
        "message": "Webhook retry initiated",
        "status": "retrying"
    }


# =============================================================================
# AGENT TRACES ENDPOINTS
# =============================================================================

@router.get("/traces")
def get_traces():
    """Get agent traces and observability data."""
    admin_logger.info("Admin accessed traces")
    
    # Return stored traces + observability links
    return {
        "agent_traces": AGENT_TRACES[-50:],  # Last 50 traces
        "observability_links": [
            {
                "id": "link-001",
                "name": "Order Processing Pipeline",
                "tool": "langfuse",
                "url": "https://cloud.langfuse.com/traces/order-pipeline",
                "description": "Full order flow from chat to fulfillment"
            },
            {
                "id": "link-002", 
                "name": "Safety Agent Decisions",
                "tool": "langfuse",
                "url": "https://cloud.langfuse.com/traces/safety-agent",
                "description": "Safety checks and drug interaction analysis"
            },
            {
                "id": "link-003",
                "name": "LLM Conversations",
                "tool": "langsmith",
                "url": "https://smith.langchain.com/traces/conversations",
                "description": "Chat agent conversation traces"
            },
            {
                "id": "link-004",
                "name": "Refill Predictions",
                "tool": "langfuse",
                "url": "https://cloud.langfuse.com/traces/refill-agent",
                "description": "Proactive refill prediction accuracy"
            }
        ]
    }


@router.post("/traces")
def add_trace(trace: AgentTrace):
    """Add a new agent trace (called by agents)."""
    trace_entry = {
        "id": f"trace-{len(AGENT_TRACES) + 1:04d}",
        "agent_name": trace.agent_name,
        "input": trace.input_text,
        "output": trace.output_text,
        "decision": trace.decision,
        "confidence": trace.confidence,
        "duration_ms": trace.duration_ms,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    AGENT_TRACES.append(trace_entry)
    admin_logger.info(f"Agent trace added: {trace.agent_name}")
    
    return {"success": True, "trace_id": trace_entry["id"]}


# =============================================================================
# ADMIN MODE TOGGLE LOG
# =============================================================================

@router.post("/toggle-log")
def log_admin_toggle(enabled: bool):
    """Log when admin mode is toggled."""
    action = "enabled" if enabled else "disabled"
    admin_logger.info(f"Admin Mode {action}")
    
    return {
        "logged": True,
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    }
