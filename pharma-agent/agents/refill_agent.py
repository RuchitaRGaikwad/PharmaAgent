"""
Refill Prediction Agent - Proactive Refill Intelligence

This agent is responsible for:
1. Analyzing customer order history
2. Computing expected refill dates based on purchase patterns
3. Creating proactive refill alerts when refill is due within 3 days
4. Running as a scheduled check or on-demand
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class RefillPrediction:
    """Prediction for a customer's refill need."""
    customer_id: int
    customer_name: str
    customer_email: str
    medicine_id: int
    medicine_name: str
    last_purchase_date: datetime
    quantity_purchased: int
    frequency_days: int
    expected_refill_date: datetime
    days_until_refill: int
    needs_alert: bool
    

class RefillPredictionAgent:
    """
    Agent 3: Refill Prediction Agent
    Analyzes order history and predicts refill needs.
    """
    
    # Number of days before refill date to trigger alert
    ALERT_THRESHOLD_DAYS = 3
    
    def __init__(self, db):
        self.db = db
        self.agent_name = "RefillPredictionAgent"
    
    def check_all_customers(self) -> Dict[str, Any]:
        """
        Check all customers for upcoming refill needs.
        Creates proactive alerts for those within threshold.
        """
        from backend.app.models import OrderHistory, Customer, ProactiveAlert
        
        predictions = []
        alerts_created = 0
        customers_checked = set()
        
        # Get all customers with order history
        history_records = self.db.query(OrderHistory).filter(
            OrderHistory.frequency_days > 0  # Only recurring prescriptions
        ).all()
        
        for record in history_records:
            customer_id = record.customer_id
            customers_checked.add(customer_id)
            
            # Get the most recent purchase of this medicine for this customer
            latest = self.db.query(OrderHistory).filter(
                OrderHistory.customer_id == customer_id,
                OrderHistory.medicine_id == record.medicine_id
            ).order_by(OrderHistory.purchase_date.desc()).first()
            
            if latest:
                prediction = self._calculate_refill_date(latest)
                predictions.append(prediction)
                
                if prediction.needs_alert:
                    # Check if alert already exists
                    existing = self.db.query(ProactiveAlert).filter(
                        ProactiveAlert.customer_id == customer_id,
                        ProactiveAlert.medicine_id == prediction.medicine_id,
                        ProactiveAlert.status == "pending"
                    ).first()
                    
                    if not existing:
                        alert = self._create_alert(prediction)
                        alerts_created += 1
        
        return {
            "success": True,
            "customers_checked": len(customers_checked),
            "predictions_made": len(predictions),
            "alerts_created": alerts_created,
            "predictions": [self._prediction_to_dict(p) for p in predictions[:20]]  # Limit response size
        }
    
    def check_customer(self, customer_id: int) -> Dict[str, Any]:
        """
        Check a specific customer for upcoming refill needs.
        """
        from backend.app.models import OrderHistory, Customer
        
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found"
            }
        
        predictions = []
        
        # Get all unique medicines this customer has ordered
        history_records = self.db.query(OrderHistory).filter(
            OrderHistory.customer_id == customer_id,
            OrderHistory.frequency_days > 0
        ).all()
        
        medicines_checked = set()
        
        for record in history_records:
            if record.medicine_id in medicines_checked:
                continue
            medicines_checked.add(record.medicine_id)
            
            # Get the most recent purchase
            latest = self.db.query(OrderHistory).filter(
                OrderHistory.customer_id == customer_id,
                OrderHistory.medicine_id == record.medicine_id
            ).order_by(OrderHistory.purchase_date.desc()).first()
            
            if latest:
                prediction = self._calculate_refill_date(latest)
                predictions.append(prediction)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "customer_name": customer.name,
            "predictions": [self._prediction_to_dict(p) for p in predictions],
            "needs_refill_soon": any(p.needs_alert for p in predictions)
        }
    
    def _calculate_refill_date(self, order_history) -> RefillPrediction:
        """
        Calculate expected refill date from order history.
        
        Formula: refill_date = purchase_date + (quantity * frequency_days)
        If frequency_days is 1 (daily), quantity directly gives days supply.
        """
        # Calculate days supply
        # Assuming 1 unit per dose, frequency_days indicates doses per day
        if order_history.frequency_days == 1:
            days_supply = order_history.quantity  # Daily use
        elif order_history.frequency_days == 0:
            days_supply = 365  # PRN/as needed, set far future
        else:
            days_supply = order_history.quantity * order_history.frequency_days
        
        # Calculate expected refill date
        purchase_date = order_history.purchase_date
        if isinstance(purchase_date, str):
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
        
        expected_refill = purchase_date + timedelta(days=days_supply)
        days_until_refill = (expected_refill - datetime.now()).days
        
        return RefillPrediction(
            customer_id=order_history.customer_id,
            customer_name=order_history.customer_name or "Unknown",
            customer_email=order_history.customer_email or "",
            medicine_id=order_history.medicine_id,
            medicine_name=order_history.medicine_name or "Unknown",
            last_purchase_date=purchase_date,
            quantity_purchased=order_history.quantity,
            frequency_days=order_history.frequency_days,
            expected_refill_date=expected_refill,
            days_until_refill=days_until_refill,
            needs_alert=days_until_refill <= self.ALERT_THRESHOLD_DAYS and days_until_refill >= -7
        )
    
    def _create_alert(self, prediction: RefillPrediction):
        """Create a proactive refill alert in the database."""
        from backend.app.models import ProactiveAlert
        
        message = self._generate_alert_message(prediction)
        
        alert = ProactiveAlert(
            customer_id=prediction.customer_id,
            medicine_id=prediction.medicine_id,
            medicine_name=prediction.medicine_name,
            expected_refill_date=prediction.expected_refill_date,
            alert_message=message,
            status="pending"
        )
        
        self.db.add(alert)
        self.db.commit()
        
        print(f"\n{'='*50}")
        print("🔔 PROACTIVE REFILL ALERT CREATED")
        print(f"{'='*50}")
        print(f"Customer: {prediction.customer_name}")
        print(f"Medicine: {prediction.medicine_name}")
        print(f"Days until refill: {prediction.days_until_refill}")
        print(f"{'='*50}\n")
        
        return alert
    
    def _generate_alert_message(self, prediction: RefillPrediction) -> str:
        """Generate alert message for notification."""
        if prediction.days_until_refill <= 0:
            urgency = "Your prescription is due for refill!"
        elif prediction.days_until_refill == 1:
            urgency = "Your prescription will need refilling tomorrow!"
        else:
            urgency = f"Your prescription will need refilling in {prediction.days_until_refill} days."
        
        return f"""Hi {prediction.customer_name},

{urgency}

📋 Medication: {prediction.medicine_name}
📅 Last purchase: {prediction.last_purchase_date.strftime('%B %d, %Y')}
📦 Quantity: {prediction.quantity_purchased} units

Would you like us to prepare your refill order?

Reply to confirm or visit our app to order.

- PharmaAgent Team"""
    
    def _prediction_to_dict(self, prediction: RefillPrediction) -> Dict[str, Any]:
        """Convert prediction to dictionary for API response."""
        return {
            "customer_id": prediction.customer_id,
            "customer_name": prediction.customer_name,
            "customer_email": prediction.customer_email,
            "medicine_id": prediction.medicine_id,
            "medicine_name": prediction.medicine_name,
            "last_purchase_date": prediction.last_purchase_date.isoformat(),
            "quantity_purchased": prediction.quantity_purchased,
            "frequency_days": prediction.frequency_days,
            "expected_refill_date": prediction.expected_refill_date.isoformat(),
            "days_until_refill": prediction.days_until_refill,
            "needs_alert": prediction.needs_alert
        }
    
    def get_upcoming_refills(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get all refills expected within the specified number of days."""
        from backend.app.models import OrderHistory
        
        predictions = []
        
        # Get all recurring prescriptions
        history_records = self.db.query(OrderHistory).filter(
            OrderHistory.frequency_days > 0
        ).all()
        
        seen = set()  # Track (customer_id, medicine_id) pairs
        
        for record in history_records:
            key = (record.customer_id, record.medicine_id)
            if key in seen:
                continue
            seen.add(key)
            
            # Get most recent purchase
            latest = self.db.query(OrderHistory).filter(
                OrderHistory.customer_id == record.customer_id,
                OrderHistory.medicine_id == record.medicine_id
            ).order_by(OrderHistory.purchase_date.desc()).first()
            
            if latest:
                prediction = self._calculate_refill_date(latest)
                if prediction.days_until_refill <= days_ahead and prediction.days_until_refill >= -7:
                    predictions.append(prediction)
        
        # Sort by days until refill
        predictions.sort(key=lambda p: p.days_until_refill)
        
        return [self._prediction_to_dict(p) for p in predictions]
