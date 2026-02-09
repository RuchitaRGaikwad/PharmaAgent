"""
Central Orchestrator - Multi-Agent Coordination

This module provides:
1. Central coordination for all agents
2. Message routing between agents
3. Conversation flow management
4. Order processing pipeline
"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from .conversation_agent import ConversationAgent
from .safety_agent import SafetyAgent
from .refill_agent import RefillPredictionAgent
from .action_agent import ActionAgent
from .symptom_agent import SymptomRecommendationAgent
from .language_agent import MultilingualAgent
from .observability import observability


class AgentOrchestrator:
    """
    Central Orchestrator for the multi-agent pharmacy system.
    
    Coordinates the following pipeline:
    1. Conversation Agent: Parse user input → Extract order details
    2. Safety Agent: Validate order against policies
    3. Action Agent: Execute approved orders
    4. Refill Agent: (Runs periodically for predictions)
    """
    
    def __init__(self, db):
        self.db = db
        self.conversation_agent = ConversationAgent(db)
        self.safety_agent = SafetyAgent(db)
        self.refill_agent = RefillPredictionAgent(db)
        self.action_agent = ActionAgent(db)
        self.symptom_agent = SymptomRecommendationAgent(db)
        self.language_agent = MultilingualAgent(db)
        
        # Store pending orders by session
        self.pending_orders: Dict[str, Dict] = {}
        
        # Symptom detection patterns
        self._symptom_keywords = [
            # Symptoms
            "fever", "headache", "cold", "cough", "pain", "ache", "sick",
            "nausea", "vomiting", "diarrhea", "allergy", "itching", "rash",
            "sore throat", "body pain", "stomach", "acidity", "heartburn",
            "sneezing", "congestion", "blocked nose", "runny nose",
            # Symptom phrases
            "feeling", "suffering", "having", "got", "experiencing",
            "not feeling well", "unwell", "temperature"
        ]
    
    def _is_symptom_request(self, message: str) -> bool:
        """
        Detect if message is a symptom-based request rather than a medicine order.
        
        Returns True if:
        - Message contains symptom keywords
        - Message doesn't appear to be a direct medicine order
        """
        message_lower = message.lower()
        
        # Exclude common non-symptom patterns (direct orders, greetings, etc.)
        exclude_patterns = [
            "order", "buy", "purchase", "need medicine", "want medicine",
            "hello", "hi", "hey", "thank", "bye", "cancel", "status",
            "refill", "prescription", "upload", "price", "cost", "stock"
        ]
        
        for pattern in exclude_patterns:
            if pattern in message_lower:
                return False
        
        # Check for symptom keywords
        symptom_count = 0
        for keyword in self._symptom_keywords:
            if keyword in message_lower:
                symptom_count += 1
        
        # If 1+ symptom keywords found, treat as symptom request
        return symptom_count >= 1
    
    async def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a user message through the agent pipeline.
        
        Returns:
            Dict with response, order status, and trace info
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Step 0a: Multilingual Support - Normalize Input
        # Detect language and translate to English for internal processing
        normalized_message, detected_lang, is_translated = self.language_agent.normalize_input(message, session_id)
        
        # Start trace
        trace_id = observability.start_trace(
            name="order_conversation",
            session_id=session_id,
            user_id=str(customer_id) if customer_id else None,
            metadata={
                "message_length": len(message),
                "detected_language": detected_lang
            }
        )
        
        result = {
            "response": "",
            "order": None,
            "requires_action": None,
            "trace_id": trace_id,
            "session_id": session_id,
            "detected_language": detected_lang
        }
        
        # Log language detection decision
        if is_translated:
            observability.log_decision(
                trace_id=trace_id,
                agent="MultilingualAgent",
                decision="translate_input",
                reason=f"Detected {detected_lang}, normalizing to English",
                data={"original": message, "normalized": normalized_message}
            )
            # Use normalized message for internal logic
            processing_message = normalized_message
        else:
            processing_message = message
        
        try:
            # Step 0b: Check if this is a symptom-based request using processed message
            if self._is_symptom_request(processing_message):
                symptom_span = observability.start_span(
                    trace_id=trace_id,
                    name="symptom_analysis",
                    agent="SymptomRecommendationAgent",
                    input_data={"message": processing_message, "session_id": session_id}
                )
                
                # Route to SymptomRecommendationAgent
                symptom_result = self.symptom_agent.process_sync(processing_message, session_id, customer_id)
                
                observability.end_span(trace_id, symptom_span, symptom_result)
                observability.log_decision(
                    trace_id=trace_id,
                    agent="SymptomRecommendationAgent",
                    decision=f"intent:{symptom_result.get('intent', 'symptom_based_request')}",
                    reason=f"Symptoms detected: {symptom_result.get('symptoms', [])}",
                    data={
                        "recommended_medicines": symptom_result.get("recommended_medicines", []),
                        "needs_doctor_consultation": symptom_result.get("needs_doctor_consultation", False)
                    }
                )
                
                # If recommendations available, pass to Safety Agent for validation
                if symptom_result.get("recommended_medicines") and not symptom_result.get("needs_doctor_consultation"):
                    observability.log_agent_communication(
                        trace_id=trace_id,
                        from_agent="SymptomRecommendationAgent",
                        to_agent="SafetyAgent",
                        message_type="recommendation_validation",
                        content={
                            "symptoms": symptom_result.get("symptoms"),
                            "recommended_medicines": symptom_result.get("recommended_medicines")
                        }
                    )
                
                # Localize response back to user language
                response_text = symptom_result.get("response", "")
                localized_response = self.language_agent.localize_response(response_text, detected_lang, session_id)
                
                result["response"] = localized_response
                result["symptoms"] = symptom_result.get("symptoms", [])
                result["recommended_medicines"] = symptom_result.get("recommended_medicines", [])
                result["needs_doctor_consultation"] = symptom_result.get("needs_doctor_consultation", False)
                result["follow_up_question"] = symptom_result.get("follow_up_question")
                result["intent"] = symptom_result.get("intent", "symptom_based_request")
                
                return result
            
            # Step 1: Conversation Agent - Parse message
            conv_span = observability.start_span(
                trace_id=trace_id,
                name="parse_message",
                agent="ConversationAgent",
                input_data={"message": processing_message, "session_id": session_id}
            )
            
            conv_result = self.conversation_agent.process(processing_message, session_id, customer_id)
            
            observability.end_span(trace_id, conv_span, conv_result)
            observability.log_decision(
                trace_id=trace_id,
                agent="ConversationAgent",
                decision=f"intent:{conv_result.get('structured_response', {}).get('intent', conv_result.get('intent', 'unknown'))}",
                reason=f"Urgency: {conv_result.get('urgency', 'normal')}",
                data={
                    "confidence": conv_result.get("confidence", 0),
                    "warnings": conv_result.get("warnings", [])
                }
            )
            
            # Localize response
            response_text = conv_result.get("response", "")
            localized_response = self.language_agent.localize_response(response_text, detected_lang, session_id)
            
            result["response"] = localized_response
            result["requires_action"] = conv_result.get("requires_action")
            
            # Check if order confirmation received
            if conv_result.get("requires_action") == "process_order":
                # Get the pending order from context
                context = self.conversation_agent.memory.get_context(session_id)
                extracted = conv_result.get("extracted_order") or self.pending_orders.get(session_id)
                
                if extracted or context:
                    order_data = extracted or {
                        "medicine_name": context.get("medicine_name"),
                        "quantity": context.get("quantity")
                    }
                    
                    if order_data.get("medicine_name") and order_data.get("quantity"):
                        # Log agent communication
                        observability.log_agent_communication(
                            trace_id=trace_id,
                            from_agent="ConversationAgent",
                            to_agent="SafetyAgent",
                            message_type="order_validation_request",
                            content=order_data
                        )
                        
                        # Step 2: Safety Agent - Validate order
                        result = await self._validate_and_execute_order(
                            trace_id=trace_id,
                            order_data=order_data,
                            customer_id=customer_id or 1,  # Default customer for demo
                            session_id=session_id
                        )
                        result["trace_id"] = trace_id
                        result["session_id"] = session_id
            
            # Store extracted order for later confirmation
            if conv_result.get("extracted_order"):
                self.pending_orders[session_id] = conv_result["extracted_order"]
            
            # Handle stock check action
            if conv_result.get("requires_action") == "check_stock":
                extracted = conv_result.get("extracted_order", {})
                if extracted and extracted.get("medicine_name"):
                    stock_info = self.safety_agent.check_stock(extracted["medicine_name"])
                    result["response"] = stock_info.get("message", result["response"])
        
        except Exception as e:
            observability.log_decision(
                trace_id=trace_id,
                agent="Orchestrator",
                decision="error",
                reason=str(e)
            )
            result["response"] = "I apologize, but I encountered an error. Please try again."
        
        finally:
            observability.end_trace(trace_id)
        
        return result
    
    async def _validate_and_execute_order(
        self,
        trace_id: str,
        order_data: Dict[str, Any],
        customer_id: int,
        session_id: str
    ) -> Dict[str, Any]:
        """Validate and execute an order through Safety and Action agents."""
        
        # Step 2: Safety Agent - Validate
        safety_span = observability.start_span(
            trace_id=trace_id,
            name="validate_order",
            agent="SafetyAgent",
            input_data=order_data
        )
        
        validation = self.safety_agent.validate_order(
            medicine_name=order_data.get("medicine_name", ""),
            quantity=order_data.get("quantity", 0),
            customer_id=customer_id
        )
        
        validation_dict = {
            "approved": validation.approved,
            "reason": validation.reason,
            "order_data": validation.order_data,
            "warnings": validation.warnings,
            "requires_prescription": validation.requires_prescription
        }
        
        observability.end_span(trace_id, safety_span, validation_dict)
        observability.log_decision(
            trace_id=trace_id,
            agent="SafetyAgent",
            decision="approved" if validation.approved else "rejected",
            reason=validation.reason,
            data={"warnings": validation.warnings}
        )
        
        if not validation.approved:
            # Order rejected
            if validation.requires_prescription and not validation.prescription_verified:
                response = f"""⚠️ **Prescription Required**

{validation.order_data.get('medicine_name', 'This medicine')} requires a valid prescription.

Please upload your prescription to proceed with this order.

You can:
1. Upload a photo of your prescription
2. Have your doctor send it to us directly

Would you like to upload your prescription now?"""
            else:
                response = f"""❌ **Order Cannot Be Processed**

{validation.reason}

Would you like to try a different quantity or medicine?"""
            
            observability.log_agent_communication(
                trace_id=trace_id,
                from_agent="SafetyAgent",
                to_agent="ConversationAgent",
                message_type="validation_result",
                content={"approved": False, "reason": validation.reason}
            )
            
            return {
                "response": response,
                "order": validation.order_data,
                "requires_action": "prescription_upload" if validation.requires_prescription else None
            }
        
        # Step 3: Action Agent - Execute
        observability.log_agent_communication(
            trace_id=trace_id,
            from_agent="SafetyAgent",
            to_agent="ActionAgent",
            message_type="execute_order",
            content=validation.order_data
        )
        
        action_span = observability.start_span(
            trace_id=trace_id,
            name="execute_order",
            agent="ActionAgent",
            input_data=validation.order_data
        )
        
        execution_result = await self.action_agent.execute_order(
            medicine_id=validation.order_data.get("medicine_id"),
            medicine_name=validation.order_data.get("medicine_name"),
            quantity=validation.order_data.get("quantity"),
            customer_id=customer_id,
            total_price=validation.order_data.get("total_price", 0),
            prescription_verified=validation.prescription_verified
        )
        
        observability.end_span(trace_id, action_span, execution_result)
        observability.log_decision(
            trace_id=trace_id,
            agent="ActionAgent",
            decision="executed" if execution_result.get("success") else "failed",
            reason=f"Order #{execution_result.get('order_id', 'N/A')}",
            data={"steps": len(execution_result.get("steps", []))}
        )
        
        if execution_result.get("success"):
            order_id = execution_result.get("order_id")
            response = f"""✅ **Order Confirmed!**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 **Order #{order_id}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Medicine: {validation.order_data.get('medicine_name')}
• Quantity: {validation.order_data.get('quantity')} {validation.order_data.get('unit_type', 'units')}
• Total: ${validation.order_data.get('total_price', 0):.2f}

📋 Status: Order placed and sent to fulfillment
📧 Confirmation email sent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Thank you for your order! Is there anything else I can help you with?"""
            
            # Clear pending order
            if session_id in self.pending_orders:
                del self.pending_orders[session_id]
            
            # Reset conversation state to idle
            self.conversation_agent.memory.set_state(session_id, "idle")
            
            return {
                "response": response,
                "order": {
                    "order_id": order_id,
                    **validation.order_data,
                    "status": "fulfilled"
                },
                "requires_action": None
            }
        else:
            response = f"""❌ **Order Processing Failed**

We encountered an issue while processing your order:
{execution_result.get('error', 'Unknown error')}

Please try again or contact support for assistance."""
            
            return {
                "response": response,
                "order": validation.order_data,
                "requires_action": "retry"
            }
    
    def run_refill_check(self) -> Dict[str, Any]:
        """Run the refill prediction agent to check all customers."""
        trace_id = observability.start_trace(
            name="refill_check",
            metadata={"type": "scheduled_check"}
        )
        
        refill_span = observability.start_span(
            trace_id=trace_id,
            name="check_all_customers",
            agent="RefillPredictionAgent",
            input_data={"check_type": "all_customers"}
        )
        
        result = self.refill_agent.check_all_customers()
        
        observability.end_span(trace_id, refill_span, result)
        observability.log_decision(
            trace_id=trace_id,
            agent="RefillPredictionAgent",
            decision=f"alerts_created:{result.get('alerts_created', 0)}",
            reason=f"Checked {result.get('customers_checked', 0)} customers",
            data=result
        )
        
        observability.end_trace(trace_id)
        
        return result
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of a conversation session."""
        summary = self.conversation_agent.get_session_summary(session_id)
        pending = self.pending_orders.get(session_id)
        
        return {
            **summary,
            "pending_order": pending
        }
