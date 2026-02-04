"""
Action Agent - Tool Execution and Real-World Actions

This agent is responsible for:
1. Deducting inventory when orders are approved
2. Creating order records in the database
3. Triggering warehouse fulfillment webhooks
4. Sending confirmation notifications
"""
from typing import Dict, Any, Optional
from datetime import datetime
import httpx


class ActionAgent:
    """
    Agent 4: Action/Tool Agent
    Executes approved orders and triggers real-world actions.
    """
    
    def __init__(self, db, base_url: str = "http://localhost:8000"):
        self.db = db
        self.base_url = base_url
        self.agent_name = "ActionAgent"
    
    async def execute_order(
        self,
        medicine_id: int,
        medicine_name: str,
        quantity: int,
        customer_id: int,
        total_price: float,
        prescription_verified: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a complete order workflow:
        1. Deduct stock
        2. Create order record
        3. Trigger fulfillment webhook
        4. Send notification
        """
        from backend.app.models import Order, Medicine, Customer, OrderHistory
        
        execution_log = {
            "steps": [],
            "success": True,
            "order_id": None,
            "started_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Step 1: Deduct inventory
            stock_result = self._deduct_stock(medicine_id, quantity)
            execution_log["steps"].append({
                "step": "deduct_stock",
                "success": stock_result["success"],
                "details": stock_result
            })
            
            if not stock_result["success"]:
                execution_log["success"] = False
                return execution_log
            
            # Step 2: Create order record
            order_result = self._create_order(
                customer_id=customer_id,
                medicine_id=medicine_id,
                quantity=quantity,
                total_price=total_price,
                prescription_verified=prescription_verified
            )
            execution_log["steps"].append({
                "step": "create_order",
                "success": order_result["success"],
                "details": order_result
            })
            
            if not order_result["success"]:
                # Rollback stock deduction
                self._add_stock(medicine_id, quantity)
                execution_log["success"] = False
                return execution_log
            
            order_id = order_result["order_id"]
            execution_log["order_id"] = order_id
            
            # Step 3: Approve the order
            approve_result = self._approve_order(order_id)
            execution_log["steps"].append({
                "step": "approve_order",
                "success": approve_result["success"],
                "details": approve_result
            })
            
            # Step 4: Trigger fulfillment webhook
            webhook_result = await self._trigger_fulfillment(order_id)
            execution_log["steps"].append({
                "step": "trigger_webhook",
                "success": webhook_result["success"],
                "details": webhook_result
            })
            
            # Step 5: Send notification
            notification_result = await self._send_notification(order_id)
            execution_log["steps"].append({
                "step": "send_notification",
                "success": notification_result["success"],
                "details": notification_result
            })
            
            # Add to order history for refill tracking
            self._add_to_history(
                customer_id=customer_id,
                medicine_id=medicine_id,
                medicine_name=medicine_name,
                quantity=quantity
            )
            
            execution_log["completed_at"] = datetime.utcnow().isoformat()
            
            print(f"\n{'='*60}")
            print("✅ ORDER EXECUTION COMPLETE")
            print(f"{'='*60}")
            print(f"Order ID: {order_id}")
            print(f"Medicine: {medicine_name}")
            print(f"Quantity: {quantity}")
            print(f"Total: ${total_price:.2f}")
            print(f"Steps completed: {len(execution_log['steps'])}")
            print(f"{'='*60}\n")
            
            return execution_log
            
        except Exception as e:
            execution_log["success"] = False
            execution_log["error"] = str(e)
            return execution_log
    
    def _deduct_stock(self, medicine_id: int, quantity: int) -> Dict[str, Any]:
        """Deduct stock from inventory."""
        from backend.app.models import Medicine
        
        medicine = self.db.query(Medicine).filter(Medicine.id == medicine_id).first()
        
        if not medicine:
            return {"success": False, "error": "Medicine not found"}
        
        if medicine.stock_level < quantity:
            return {
                "success": False, 
                "error": f"Insufficient stock: {medicine.stock_level} available, {quantity} requested"
            }
        
        old_stock = medicine.stock_level
        medicine.stock_level -= quantity
        self.db.commit()
        
        print(f"📦 Stock deducted: {medicine.name} ({old_stock} → {medicine.stock_level})")
        
        return {
            "success": True,
            "medicine_id": medicine_id,
            "old_stock": old_stock,
            "new_stock": medicine.stock_level,
            "deducted": quantity
        }
    
    def _add_stock(self, medicine_id: int, quantity: int) -> Dict[str, Any]:
        """Add stock back to inventory (for rollback)."""
        from backend.app.models import Medicine
        
        medicine = self.db.query(Medicine).filter(Medicine.id == medicine_id).first()
        if medicine:
            medicine.stock_level += quantity
            self.db.commit()
            return {"success": True, "new_stock": medicine.stock_level}
        return {"success": False}
    
    def _create_order(
        self,
        customer_id: int,
        medicine_id: int,
        quantity: int,
        total_price: float,
        prescription_verified: bool
    ) -> Dict[str, Any]:
        """Create order record in database."""
        from backend.app.models import Order
        
        order = Order(
            customer_id=customer_id,
            medicine_id=medicine_id,
            quantity=quantity,
            total_price=total_price,
            status="pending",
            prescription_verified=prescription_verified
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        print(f"📝 Order created: #{order.id}")
        
        return {
            "success": True,
            "order_id": order.id
        }
    
    def _approve_order(self, order_id: int) -> Dict[str, Any]:
        """Approve an order."""
        from backend.app.models import Order
        
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = "approved"
            self.db.commit()
            print(f"✅ Order #{order_id} approved")
            return {"success": True, "status": "approved"}
        return {"success": False, "error": "Order not found"}
    
    async def _trigger_fulfillment(self, order_id: int) -> Dict[str, Any]:
        """Trigger warehouse fulfillment webhook."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/webhook/fulfillment",
                    json={"order_id": order_id, "action": "fulfill"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    # Update order webhook status
                    from backend.app.models import Order
                    order = self.db.query(Order).filter(Order.id == order_id).first()
                    if order:
                        order.webhook_triggered = True
                        self.db.commit()
                    
                    return {"success": True, "response": response.json()}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            # Log but don't fail the order
            print(f"⚠️ Webhook failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_notification(self, order_id: int) -> Dict[str, Any]:
        """Send order confirmation notification."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/webhook/notification",
                    json={
                        "order_id": order_id,
                        "notification_type": "confirmation",
                        "channel": "email"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    from backend.app.models import Order
                    order = self.db.query(Order).filter(Order.id == order_id).first()
                    if order:
                        order.notification_sent = True
                        self.db.commit()
                    
                    return {"success": True, "response": response.json()}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            print(f"⚠️ Notification failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _add_to_history(
        self,
        customer_id: int,
        medicine_id: int,
        medicine_name: str,
        quantity: int
    ):
        """Add order to history for refill tracking."""
        from backend.app.models import OrderHistory, Customer
        
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        
        history = OrderHistory(
            customer_id=customer_id,
            customer_name=customer.name if customer else "Unknown",
            customer_email=customer.email if customer else None,
            medicine_id=medicine_id,
            medicine_name=medicine_name,
            quantity=quantity,
            frequency_days=1,  # Default to daily
            purchase_date=datetime.utcnow(),
            status="completed"
        )
        
        self.db.add(history)
        self.db.commit()
    
    def get_execution_summary(self, execution_log: Dict[str, Any]) -> str:
        """Generate human-readable execution summary."""
        if execution_log["success"]:
            summary = f"""✅ Order Executed Successfully!

📦 Order ID: #{execution_log['order_id']}
⏱️ Started: {execution_log['started_at']}
⏱️ Completed: {execution_log.get('completed_at', 'N/A')}

Steps Completed:
"""
            for step in execution_log["steps"]:
                status = "✓" if step["success"] else "✗"
                summary += f"  {status} {step['step']}\n"
        else:
            summary = f"""❌ Order Execution Failed

Error: {execution_log.get('error', 'Unknown error')}

Steps:
"""
            for step in execution_log["steps"]:
                status = "✓" if step["success"] else "✗"
                summary += f"  {status} {step['step']}"
                if not step["success"]:
                    summary += f" - {step['details'].get('error', '')}"
                summary += "\n"
        
        return summary
