"""
Notification services for the Pharmacy Agent system.
Handles mock implementations of email, WhatsApp, and SMS notifications.
"""
from datetime import datetime
from typing import Optional
import json


class NotificationService:
    """
    Mock notification service for demo purposes.
    In production, replace with actual email/SMS/WhatsApp providers.
    """
    
    def __init__(self):
        self.sent_notifications = []
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        order_id: Optional[int] = None
    ) -> dict:
        """Send a mock email notification."""
        notification = {
            "type": "email",
            "to": to_email,
            "subject": subject,
            "body": body,
            "order_id": order_id,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        
        self.sent_notifications.append(notification)
        
        # Console output for demo visibility
        print(f"\n{'='*60}")
        print("📧 EMAIL NOTIFICATION")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print(f"{'='*60}\n")
        
        return notification
    
    def send_whatsapp(
        self,
        to_phone: str,
        message: str,
        order_id: Optional[int] = None
    ) -> dict:
        """Send a mock WhatsApp notification."""
        notification = {
            "type": "whatsapp",
            "to": to_phone,
            "message": message,
            "order_id": order_id,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        
        self.sent_notifications.append(notification)
        
        # Console output for demo visibility
        print(f"\n{'='*60}")
        print("💬 WHATSAPP NOTIFICATION")
        print(f"{'='*60}")
        print(f"To: {to_phone}")
        print(f"Message:\n{message}")
        print(f"{'='*60}\n")
        
        return notification
    
    def send_sms(
        self,
        to_phone: str,
        message: str,
        order_id: Optional[int] = None
    ) -> dict:
        """Send a mock SMS notification."""
        notification = {
            "type": "sms",
            "to": to_phone,
            "message": message[:160],  # SMS character limit
            "order_id": order_id,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        
        self.sent_notifications.append(notification)
        
        # Console output for demo visibility
        print(f"\n{'='*60}")
        print("📱 SMS NOTIFICATION")
        print(f"{'='*60}")
        print(f"To: {to_phone}")
        print(f"Message: {message[:160]}")
        print(f"{'='*60}\n")
        
        return notification
    
    def send_order_confirmation(
        self,
        customer_name: str,
        customer_email: str,
        order_id: int,
        medicine_name: str,
        quantity: int,
        total_price: float
    ) -> dict:
        """Send order confirmation notification."""
        subject = f"Order Confirmation - #{order_id}"
        body = f"""
Dear {customer_name},

Your order has been confirmed and is being prepared!

📦 Order Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Order ID: #{order_id}
Medicine: {medicine_name}
Quantity: {quantity}
Total: ₹{total_price:.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your prescription is being processed and will be dispatched shortly.

Thank you for choosing PharmaAgent! 💊

Best regards,
The PharmaAgent Team
        """.strip()
        
        return self.send_email(customer_email, subject, body, order_id)
    
    def send_refill_reminder(
        self,
        customer_name: str,
        customer_email: str,
        customer_phone: Optional[str],
        medicine_name: str,
        days_until_refill: int
    ) -> dict:
        """Send proactive refill reminder notification."""
        subject = "⏰ Time for Your Refill!"
        body = f"""
Dear {customer_name},

It's almost time to refill your prescription!

💊 Medication: {medicine_name}
📅 Estimated refill needed in: {days_until_refill} days

Would you like us to prepare your refill order?

Simply reply to this email or visit our app to confirm.

Stay healthy! 🌟

Best regards,
The PharmaAgent Team
        """.strip()
        
        # Send both email and WhatsApp if phone available
        email_result = self.send_email(customer_email, subject, body)
        
        if customer_phone:
            whatsapp_message = f"Hi {customer_name}! 👋 Time to refill {medicine_name}. Only {days_until_refill} days left. Reply YES to confirm your refill order!"
            self.send_whatsapp(customer_phone, whatsapp_message)
        
        return email_result
    
    def get_notification_history(self, limit: int = 50) -> list:
        """Get recent notification history."""
        return self.sent_notifications[-limit:]
    
    def clear_history(self):
        """Clear notification history."""
        self.sent_notifications = []


# Global notification service instance
notification_service = NotificationService()
