"""
Safety & Policy Agent - Order Validation and Compliance

This agent is responsible for:
1. Validating orders against Medicine Master Data
2. Checking stock availability
3. Enforcing prescription requirements
4. Returning approval/rejection with detailed reasons
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of order validation."""
    approved: bool
    order_data: Dict[str, Any]
    reason: str
    warnings: list
    requires_prescription: bool = False
    prescription_verified: bool = False
    stock_available: int = 0
    

class SafetyAgent:
    """
    Agent 2: Safety & Policy Agent
    Validates orders against policies and medicine database.
    """
    
    def __init__(self, db):
        self.db = db
        self.agent_name = "SafetyAgent"
    
    def validate_order(
        self,
        medicine_name: str,
        quantity: int,
        customer_id: Optional[int] = None,
        prescription_verified: bool = False
    ) -> ValidationResult:
        """
        Validate an order against safety policies.
        
        Args:
            medicine_name: Name of the medicine
            quantity: Requested quantity
            customer_id: Customer ID (for prescription verification)
            prescription_verified: Whether prescription has been verified
            
        Returns:
            ValidationResult with approval status and details
        """
        from backend.app.models import Medicine, Customer
        
        warnings = []
        order_data = {
            "medicine_name": medicine_name,
            "quantity": quantity,
            "customer_id": customer_id,
            "validated_at": datetime.utcnow().isoformat()
        }
        
        # Find medicine in database
        medicine = self._find_medicine(medicine_name)
        
        if not medicine:
            return ValidationResult(
                approved=False,
                order_data=order_data,
                reason=f"Medicine '{medicine_name}' not found in our database. Please check the spelling or try a different name.",
                warnings=warnings,
                stock_available=0
            )
        
        order_data["medicine_id"] = medicine.id
        order_data["medicine_name"] = medicine.name
        order_data["unit_price"] = medicine.price
        order_data["total_price"] = medicine.price * quantity
        order_data["unit_type"] = medicine.unit_type
        
        # Check stock availability
        if medicine.stock_level < quantity:
            if medicine.stock_level == 0:
                return ValidationResult(
                    approved=False,
                    order_data=order_data,
                    reason=f"Sorry, {medicine.name} is currently out of stock.",
                    warnings=warnings,
                    stock_available=0
                )
            else:
                return ValidationResult(
                    approved=False,
                    order_data=order_data,
                    reason=f"Insufficient stock. Only {medicine.stock_level} {medicine.unit_type} of {medicine.name} available. You requested {quantity}.",
                    warnings=warnings,
                    stock_available=medicine.stock_level
                )
        
        # Check prescription requirement
        requires_prescription = medicine.prescription_required
        order_data["requires_prescription"] = requires_prescription
        
        if requires_prescription:
            # Check if customer has verified prescription
            customer_verified = False
            
            if customer_id:
                customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
                if customer and customer.has_verified_prescription:
                    customer_verified = True
            
            if not customer_verified and not prescription_verified:
                return ValidationResult(
                    approved=False,
                    order_data=order_data,
                    reason=f"{medicine.name} requires a valid prescription. Please upload your prescription to proceed.",
                    warnings=warnings,
                    requires_prescription=True,
                    prescription_verified=False,
                    stock_available=medicine.stock_level
                )
            
            order_data["prescription_verified"] = True
        
        # Check for quantity warnings
        if quantity > 90:
            warnings.append(f"Large quantity ordered ({quantity} {medicine.unit_type}). This may require additional verification.")
        
        if quantity > medicine.stock_level * 0.5:
            warnings.append(f"Your order represents more than 50% of current stock.")
        
        # Low stock warning
        if medicine.stock_level - quantity < 20:
            warnings.append(f"Stock will be low after this order ({medicine.stock_level - quantity} remaining).")
        
        # All checks passed
        return ValidationResult(
            approved=True,
            order_data=order_data,
            reason="Order validated successfully. Ready for processing.",
            warnings=warnings,
            requires_prescription=requires_prescription,
            prescription_verified=True if requires_prescription else False,
            stock_available=medicine.stock_level
        )
    
    def _find_medicine(self, medicine_name: str):
        """Find medicine by name (fuzzy matching)."""
        from backend.app.models import Medicine
        
        # Try exact match first
        medicine = self.db.query(Medicine).filter(
            Medicine.name.ilike(medicine_name)
        ).first()
        
        if medicine:
            return medicine
        
        # Try partial match
        medicine = self.db.query(Medicine).filter(
            Medicine.name.ilike(f"%{medicine_name}%")
        ).first()
        
        if medicine:
            return medicine
        
        # Try matching just the medicine base name (without dosage)
        base_name = medicine_name.split()[0] if medicine_name else ""
        medicine = self.db.query(Medicine).filter(
            Medicine.name.ilike(f"%{base_name}%")
        ).first()
        
        return medicine
    
    def check_stock(self, medicine_name: str) -> Dict[str, Any]:
        """Check stock availability for a medicine."""
        medicine = self._find_medicine(medicine_name)
        
        if not medicine:
            return {
                "found": False,
                "medicine_name": medicine_name,
                "message": f"Medicine '{medicine_name}' not found."
            }
        
        return {
            "found": True,
            "medicine_id": medicine.id,
            "medicine_name": medicine.name,
            "stock_level": medicine.stock_level,
            "unit_type": medicine.unit_type,
            "price": medicine.price,
            "prescription_required": medicine.prescription_required,
            "in_stock": medicine.stock_level > 0,
            "message": f"{medicine.name}: {medicine.stock_level} {medicine.unit_type} in stock at ${medicine.price} each."
        }
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """Generate human-readable validation summary."""
        if result.approved:
            summary = f"✅ Order Approved\n\n"
            summary += f"Medicine: {result.order_data.get('medicine_name')}\n"
            summary += f"Quantity: {result.order_data.get('quantity')} {result.order_data.get('unit_type', 'units')}\n"
            summary += f"Total: ${result.order_data.get('total_price', 0):.2f}\n"
            
            if result.warnings:
                summary += f"\n⚠️ Warnings:\n"
                for warning in result.warnings:
                    summary += f"  • {warning}\n"
        else:
            summary = f"❌ Order Rejected\n\n"
            summary += f"Reason: {result.reason}\n"
            
            if result.requires_prescription and not result.prescription_verified:
                summary += "\n📋 Action Required: Upload a valid prescription to proceed."
            
            if result.stock_available > 0:
                summary += f"\nAvailable stock: {result.stock_available} units"
        
        return summary
