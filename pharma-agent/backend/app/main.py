"""
PharmaAgent - Agentic AI Pharmacy System
Main FastAPI application entry point.

This application provides:
- REST API for medicine, order, and customer management
- Agent-based conversational ordering
- Proactive refill predictions
- Webhook automation for fulfillment
"""
import os
import csv
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import sys

# Add parent directory to path for agent imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .database import engine, get_db, init_db, SessionLocal
from .models import Base, Medicine, Customer, OrderHistory, Order, ProactiveAlert

# Import routes
from .routes import medicines, orders, customers, webhooks, alerts


def load_csv_data(db: Session):
    """Load sample data from CSV files on startup."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    
    # Load medicines
    medicines_file = os.path.join(data_dir, 'medicines.csv')
    if os.path.exists(medicines_file):
        # Check if medicines already loaded
        existing = db.query(Medicine).first()
        if not existing:
            print("📦 Loading medicine data...")
            with open(medicines_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    medicine = Medicine(
                        id=int(row['id']),
                        name=row['name'],
                        stock_level=int(row['stock_level']),
                        unit_type=row['unit_type'],
                        prescription_required=row['prescription_required'].lower() == 'true',
                        price=float(row['price']),
                        dosage_info=row.get('dosage_info', '')
                    )
                    db.add(medicine)
            db.commit()
            print(f"✅ Loaded medicines from {medicines_file}")
    
    # Load order history (includes customer data)
    history_file = os.path.join(data_dir, 'order_history.csv')
    if os.path.exists(history_file):
        # Check if customers already loaded
        existing = db.query(Customer).first()
        if not existing:
            print("👥 Loading customer and order history data...")
            customers_added = set()
            with open(history_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    customer_id = int(row['customer_id'])
                    
                    # Create customer if not exists
                    if customer_id not in customers_added:
                        customer = Customer(
                            id=customer_id,
                            name=row['customer_name'],
                            email=row['customer_email'],
                            has_verified_prescription=True  # Assume verified for demo
                        )
                        db.add(customer)
                        customers_added.add(customer_id)
                    
                    # Create order history
                    history = OrderHistory(
                        id=int(row['id']),
                        customer_id=customer_id,
                        customer_name=row['customer_name'],
                        customer_email=row['customer_email'],
                        medicine_id=int(row['medicine_id']),
                        medicine_name=row['medicine_name'],
                        quantity=int(row['quantity']),
                        frequency_days=int(row['frequency_days']),
                        purchase_date=datetime.strptime(row['purchase_date'], '%Y-%m-%d'),
                        status=row['status']
                    )
                    db.add(history)
            db.commit()
            print(f"✅ Loaded order history from {history_file}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    print("\n" + "="*60)
    print("🚀 Starting PharmaAgent - Agentic AI Pharmacy System")
    print("="*60)
    
    # Initialize database
    print("📊 Initializing database...")
    init_db()
    
    # Load sample data
    db = SessionLocal()
    try:
        load_csv_data(db)
    finally:
        db.close()
    
    print("="*60)
    print("✅ PharmaAgent is ready!")
    print("📖 API Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    yield
    
    # Shutdown
    print("\n👋 Shutting down PharmaAgent...")


# Create FastAPI app
app = FastAPI(
    title="PharmaAgent API",
    description="""
    ## Agentic AI Pharmacy System
    
    An autonomous, agent-driven pharmacy ecosystem featuring:
    
    - 💬 **Conversational Ordering**: Natural language order processing
    - 🔒 **Safety Enforcement**: Prescription validation and stock checks
    - 📊 **Predictive Refills**: AI-powered refill predictions
    - ⚡ **Automated Actions**: Webhook-triggered fulfillment
    
    ### Agents
    
    1. **Conversation Agent**: Parses natural language to extract order details
    2. **Safety Agent**: Validates orders against policies
    3. **Refill Agent**: Predicts and alerts on upcoming refills
    4. **Action Agent**: Executes approved orders
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(medicines.router)
app.include_router(orders.router)
app.include_router(customers.router)
app.include_router(webhooks.router)
app.include_router(alerts.router)


# Chat endpoint schema
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    customer_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    order: Optional[dict] = None
    requires_action: Optional[str] = None
    trace_id: Optional[str] = None


@app.get("/")
def root():
    """API root endpoint."""
    return {
        "name": "PharmaAgent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "medicines": "/medicines",
            "orders": "/orders",
            "customers": "/customers",
            "alerts": "/alerts",
            "webhooks": "/webhook",
            "chat": "/chat"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Main chat endpoint for conversational ordering.
    Routes messages through the agent orchestrator.
    """
    try:
        # Import orchestrator (lazy import to avoid circular deps)
        from agents.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(db)
        result = await orchestrator.process_message(
            message=request.message,
            session_id=request.session_id,
            customer_id=request.customer_id
        )
        
        return ChatResponse(
            response=result.get("response", ""),
            order=result.get("order"),
            requires_action=result.get("requires_action"),
            trace_id=result.get("trace_id")
        )
    except ImportError:
        # Fallback if agents not yet implemented
        return ChatResponse(
            response=f"I received your message: '{request.message}'. The agent system is being initialized.",
            order=None,
            requires_action=None,
            trace_id=None
        )
    except Exception as e:
        print(f"Chat error: {e}")
        return ChatResponse(
            response="I apologize, but I encountered an error processing your request. Please try again.",
            order=None,
            requires_action=None,
            trace_id=None
        )


@app.post("/refill-check")
async def trigger_refill_check(db: Session = Depends(get_db)):
    """
    Trigger refill prediction check.
    Analyzes order history and creates proactive alerts.
    """
    try:
        from agents.refill_agent import RefillPredictionAgent
        
        agent = RefillPredictionAgent(db)
        result = agent.check_all_customers()
        
        return {
            "success": True,
            "alerts_created": result.get("alerts_created", 0),
            "customers_checked": result.get("customers_checked", 0),
            "message": "Refill check completed"
        }
    except ImportError:
        return {
            "success": False,
            "message": "Refill agent not yet implemented"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Create uploads directory
os.makedirs("uploads/prescriptions", exist_ok=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
