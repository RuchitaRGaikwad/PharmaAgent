"""
PharmaAgent - Clinical AI Pharmacist
=====================================

An autonomous, safety-critical AI Pharmacist following India/WHO standards.

Core Capabilities:
1. Symptom Understanding & Triage
2. OTC Medicine Recommendation
3. Prescription Validation
4. Drug Interaction & Safety Engine
5. Inventory & Availability
6. Refill Prediction & Adherence
7. Autonomous Backend Actions
8. Human-in-the-Loop Escalation
"""
import re
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field


@dataclass
class ExtractedEntities:
    """Structured entities extracted from conversation."""
    symptoms: List[str] = field(default_factory=list)
    medicines: List[str] = field(default_factory=list)
    dosage: Optional[str] = None
    quantity: Optional[int] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    allergies: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    age_group: Optional[str] = None  # infant, child, adult, elderly
    pregnancy_status: Optional[str] = None
    severity: Optional[str] = None  # mild, moderate, severe
    raw_input: str = ""


@dataclass
class PharmaResponse:
    """Structured response from PharmaAgent."""
    intent: str  # symptom_check, medicine_request, refill, order, prescription_validation
    extracted_entities: ExtractedEntities
    safety_status: str  # approved, blocked, needs_clarification, escalate_human
    actions: List[str]
    user_message: str
    confidence: float
    urgency: str = "normal"  # self_care, pharmacist_consult, doctor_referral, emergency
    requires_prescription: bool = False
    warnings: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)


class ConversationMemory:
    """Manages conversation context per user session."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def get_session(self, session_id: str) -> Dict:
        """Get or create a session context."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "context": {},
                "patient_profile": {
                    "allergies": [],
                    "conditions": [],
                    "current_medications": [],
                    "age_group": None,
                    "pregnancy_status": None
                },
                "extracted_entities": None,
                "state": "greeting",
                "customer_id": None,
                "created_at": datetime.utcnow().isoformat(),
                "safety_checks": []
            }
        return self.sessions[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to session history."""
        session = self.get_session(session_id)
        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        session["last_activity"] = datetime.utcnow().isoformat()
    
    def update_patient_profile(self, session_id: str, key: str, value: Any):
        """Update patient profile."""
        session = self.get_session(session_id)
        if key in session["patient_profile"]:
            if isinstance(session["patient_profile"][key], list):
                if isinstance(value, list):
                    session["patient_profile"][key].extend(value)
                else:
                    session["patient_profile"][key].append(value)
            else:
                session["patient_profile"][key] = value
    
    def get_patient_profile(self, session_id: str) -> Dict:
        """Get patient profile."""
        return self.get_session(session_id).get("patient_profile", {})
    
    def update_context(self, session_id: str, key: str, value: Any):
        """Update session context."""
        session = self.get_session(session_id)
        session["context"][key] = value
    
    def get_context(self, session_id: str) -> Dict:
        """Get session context."""
        return self.get_session(session_id).get("context", {})
    
    def set_state(self, session_id: str, state: str):
        """Set conversation state."""
        self.get_session(session_id)["state"] = state
    
    def get_state(self, session_id: str) -> str:
        """Get conversation state."""
        return self.get_session(session_id).get("state", "greeting")
    
    def add_safety_check(self, session_id: str, check: Dict):
        """Log safety check."""
        session = self.get_session(session_id)
        session["safety_checks"].append({
            **check,
            "timestamp": datetime.utcnow().isoformat()
        })


class ClinicalPharmaAgent:
    """
    PharmaAgent - Clinical AI Pharmacist
    
    Behaves like a licensed clinical pharmacist following India/WHO standards.
    Prioritizes patient safety and regulatory compliance.
    """
    
    # ==================== RED FLAG SYMPTOMS ====================
    RED_FLAGS = [
        "chest pain", "chest tightness", "heart attack",
        "difficulty breathing", "shortness of breath", "can't breathe",
        "severe bleeding", "bleeding heavily", "blood loss",
        "unconscious", "fainting", "seizure", "convulsion",
        "severe allergic", "anaphylaxis", "throat swelling",
        "stroke symptoms", "facial drooping", "arm weakness", "speech difficulty",
        "suicidal", "self harm", "overdose",
        "high fever with rash", "neck stiffness", "photophobia",
        "severe abdominal pain", "vomiting blood", "black stool",
        "pregnancy bleeding", "pregnant and severe pain"
    ]
    
    # ==================== SYMPTOM PATTERNS ====================
    SYMPTOM_PATTERNS = {
        "fever": ["fever", "temperature", "pyrexia", "high temp", "feeling hot"],
        "headache": ["headache", "head pain", "migraine", "head hurts"],
        "cold": ["cold", "runny nose", "blocked nose", "congestion", "sneezing"],
        "cough": ["cough", "coughing", "dry cough", "wet cough", "productive cough"],
        "sore_throat": ["sore throat", "throat pain", "painful swallowing", "scratchy throat"],
        "body_pain": ["body pain", "body ache", "muscle pain", "joint pain", "fatigue"],
        "stomach_pain": ["stomach pain", "abdominal pain", "belly ache", "cramps"],
        "diarrhea": ["diarrhea", "loose motion", "loose stool", "watery stool"],
        "constipation": ["constipation", "difficulty passing stool", "hard stool"],
        "nausea": ["nausea", "vomiting", "feeling sick", "throwing up"],
        "acidity": ["acidity", "heartburn", "acid reflux", "burning sensation"],
        "allergy": ["allergy", "allergic", "itching", "rash", "hives", "urticaria"],
        "insomnia": ["insomnia", "can't sleep", "trouble sleeping", "sleeplessness"],
        "anxiety": ["anxiety", "anxious", "nervous", "panic", "worried"],
    }
    
    # ==================== OTC MEDICINES (India) ====================
    OTC_MEDICINES = {
        "fever": {
            "adult": [
                {"name": "Paracetamol 500mg", "dosage": "1-2 tablets", "frequency": "every 4-6 hours", "max_daily": "8 tablets", "precautions": ["Do not exceed 4g/day", "Avoid alcohol"]},
                {"name": "Ibuprofen 400mg", "dosage": "1 tablet", "frequency": "every 6-8 hours", "max_daily": "3 tablets", "precautions": ["Take with food", "Avoid if stomach ulcer"]}
            ],
            "child": [
                {"name": "Paracetamol Syrup 120mg/5ml", "dosage": "5-10ml based on weight", "frequency": "every 4-6 hours", "precautions": ["Use measuring cup", "Consult doctor for infants"]}
            ]
        },
        "headache": {
            "adult": [
                {"name": "Paracetamol 500mg", "dosage": "1-2 tablets", "frequency": "every 4-6 hours", "precautions": ["Do not exceed 4g/day"]},
                {"name": "Disprin (Aspirin) 350mg", "dosage": "1-2 tablets", "frequency": "every 4-6 hours", "precautions": ["Not for children under 16", "Avoid if asthma"]}
            ]
        },
        "cold": {
            "adult": [
                {"name": "Cetirizine 10mg", "dosage": "1 tablet", "frequency": "once daily", "precautions": ["May cause drowsiness", "Avoid driving"]},
                {"name": "Sinarest", "dosage": "1 tablet", "frequency": "every 6 hours", "precautions": ["Contains paracetamol - check other medications"]}
            ]
        },
        "cough": {
            "adult": [
                {"name": "Benadryl Cough Syrup", "dosage": "10ml", "frequency": "every 6-8 hours", "precautions": ["May cause drowsiness"]},
                {"name": "Honitus Cough Syrup (Herbal)", "dosage": "10ml", "frequency": "3 times daily", "precautions": ["Herbal, generally safe"]}
            ]
        },
        "sore_throat": {
            "adult": [
                {"name": "Strepsils Lozenges", "dosage": "1 lozenge", "frequency": "every 2-3 hours", "max_daily": "12 lozenges", "precautions": ["Dissolve slowly in mouth"]},
                {"name": "Betadine Gargle", "dosage": "15ml diluted", "frequency": "3-4 times daily", "precautions": ["Do not swallow"]}
            ]
        },
        "acidity": {
            "adult": [
                {"name": "Digene Tablets", "dosage": "1-2 tablets", "frequency": "after meals", "precautions": ["Chew before swallowing"]},
                {"name": "Omeprazole 20mg OTC", "dosage": "1 capsule", "frequency": "before breakfast", "precautions": ["Max 14 days without doctor"]}
            ]
        },
        "diarrhea": {
            "adult": [
                {"name": "ORS (Oral Rehydration Salt)", "dosage": "1 sachet in 1L water", "frequency": "sip frequently", "precautions": ["Most important for hydration"]},
                {"name": "Loperamide 2mg (Imodium)", "dosage": "2 tablets initially, then 1 after each loose stool", "max_daily": "8 tablets", "precautions": ["Not for bloody diarrhea", "Not for children under 12"]}
            ]
        },
        "allergy": {
            "adult": [
                {"name": "Cetirizine 10mg", "dosage": "1 tablet", "frequency": "once daily", "precautions": ["May cause drowsiness"]},
                {"name": "Loratadine 10mg", "dosage": "1 tablet", "frequency": "once daily", "precautions": ["Non-drowsy option"]}
            ]
        }
    }
    
    # ==================== PRESCRIPTION REQUIRED ====================
    PRESCRIPTION_MEDICINES = [
        "antibiotics", "amoxicillin", "azithromycin", "ciprofloxacin", "metronidazole",
        "antidepressants", "anxiolytics", "sleeping pills", "sedatives",
        "opioids", "tramadol", "codeine", "morphine",
        "steroids", "prednisolone", "dexamethasone",
        "blood pressure", "antihypertensives", "amlodipine", "losartan",
        "diabetes", "metformin", "glimepiride", "insulin",
        "thyroid", "levothyroxine",
        "contraceptives", "birth control"
    ]
    
    # ==================== DRUG INTERACTIONS ====================
    DRUG_INTERACTIONS = {
        "aspirin": ["warfarin", "ibuprofen", "blood thinners"],
        "ibuprofen": ["aspirin", "warfarin", "lithium", "methotrexate"],
        "paracetamol": ["warfarin", "alcohol"],
        "cetirizine": ["alcohol", "sedatives"],
        "omeprazole": ["clopidogrel", "methotrexate"],
    }
    
    # ==================== PREGNANCY SAFETY ====================
    PREGNANCY_UNSAFE = ["ibuprofen", "aspirin", "naproxen", "retinoids", "statins", "warfarin"]
    PREGNANCY_SAFE = ["paracetamol", "antacids", "iron supplements", "folic acid"]
    
    def __init__(self, db=None):
        self.db = db
        self.memory = ConversationMemory()
        self.agent_name = "ClinicalPharmaAgent"
        
        # Initialize Ollama Client
        from .llm_client import OllamaClient
        self.llm_client = OllamaClient()
        self.use_llm = False
        
        # Check if Ollama is available immediately
        if self.llm_client.check_connection():
            self.use_llm = True
            print("✅ Ollama (Llama 3) connected successfully")
        else:
            print("⚠️ Ollama not detected - falling back to rule-based logic")
    
    def process(self, message: str, session_id: str = None, customer_id: int = None) -> Dict[str, Any]:
        """
        Process user message with clinical pharmacist intelligence.
        Uses LLM (Llama 3) if available, otherwise falls back to heuristics.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Add message to memory
        self.memory.add_message(session_id, "user", message)
        
        # Check current state for overrides (e.g. waiting for confirmation)
        state = self.memory.get_state(session_id)
        if state == "awaiting_order_confirmation":
            return self._handle_order_confirmation(message, session_id, "medicine_request")
        
        # Handle quantity response
        if state == "awaiting_quantity":
            return self._handle_quantity_response(message, session_id)
        
        # Try LLM processing first
        if self.use_llm:
            try:
                return self._process_with_llm(message, session_id, customer_id)
            except Exception as e:
                print(f"LLM Processing failed: {e} - falling back to rules")
                # Fallthrough to legacy logic
        
        # ==================== LEGACY RULE-BASED LOGIC (FALLBACK) ====================
        
        # Get current state and context
        state = self.memory.get_state(session_id)
        context = self.memory.get_context(session_id)
        patient_profile = self.memory.get_patient_profile(session_id)
        
        # 1. Check for red flags FIRST
        red_flag = self._check_red_flags(message)
        if red_flag:
            return self._emergency_response(red_flag, session_id)
        
        # 2. Detect intent
        intent = self._detect_intent(message)
        
        # 3. Extract entities
        entities = self._extract_entities(message, patient_profile)
        
        # 4. Check if prescription medicine requested
        prescription_check = self._check_prescription_required(entities)
        
        # 5. Safety analysis
        safety_result = self._analyze_safety(entities, patient_profile)
        
        # 6. Generate clinical response
        response = self._generate_clinical_response(
            message, entities, intent, state, 
            patient_profile, safety_result, prescription_check, session_id
        )
        
        # Update memory
        self.memory.add_message(session_id, "assistant", response.user_message)
        
        # Return structured response
        return {
            "response": response.user_message,
            "session_id": session_id,
            "structured_response": {
                "intent": response.intent,
                "extracted_entities": asdict(response.extracted_entities),
                "safety_status": response.safety_status,
                "actions": response.actions,
                "user_message": response.user_message
            },
            "confidence": response.confidence,
            "urgency": response.urgency,
            "requires_prescription": response.requires_prescription,
            "warnings": response.warnings,
            "alternatives": response.alternatives,
            "agent": self.agent_name
        }
    
    def _check_red_flags(self, message: str) -> Optional[str]:
        """Check for emergency red flag symptoms."""
        message_lower = message.lower()
        for red_flag in self.RED_FLAGS:
            if red_flag in message_lower:
                return red_flag
        return None
    
    def _emergency_response(self, red_flag: str, session_id: str) -> Dict:
        """Generate emergency response for red flag symptoms."""
        emergency_message = f"""🚨 **URGENT MEDICAL ATTENTION REQUIRED**

I've detected a potentially serious symptom: **{red_flag}**

**Please do NOT rely on pharmacy assistance for this.**

📞 **Immediate Actions:**
1. Call Emergency Services: **112** (India) or local emergency number
2. Go to nearest hospital Emergency Department
3. If with someone, do not leave them alone

Your safety is the priority. This is beyond pharmacy scope.

---
*If this was mentioned in a different context and you're not experiencing an emergency, please clarify and I'll be happy to assist.*"""

        self.memory.add_message(session_id, "assistant", emergency_message)
        
        return {
            "response": emergency_message,
            "session_id": session_id,
            "structured_response": {
                "intent": "emergency_triage",
                "extracted_entities": {"symptoms": [red_flag]},
                "safety_status": "escalate_human",
                "actions": ["emergency_referral"],
                "user_message": emergency_message
            },
            "confidence": 1.0,
            "urgency": "emergency",
            "requires_prescription": False,
            "warnings": [f"Red flag symptom detected: {red_flag}"],
            "alternatives": [],
            "agent": self.agent_name
        }
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message."""
        message_lower = message.lower()
        
        intent_patterns = {
            "symptom_check": ["symptom", "feeling", "suffering", "since", "days", "pain", "ache", "sick", "unwell"],
            "medicine_request": ["need", "want", "order", "buy", "get me", "purchase", "medicine", "tablet", "capsule"],
            "refill": ["refill", "reorder", "running out", "need more", "same as before", "repeat"],
            "prescription_validation": ["prescription", "doctor prescribed", "rx", "prescribed"],
            "query": ["available", "stock", "price", "cost", "how much"],
            "allergy_info": ["allergic", "allergy", "react to", "sensitive to"],
            "greeting": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
            "help": ["help", "what can you", "how do i", "guide me"],
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return intent
        
        return "general_query"
    
    def _extract_entities(self, message: str, patient_profile: Dict) -> ExtractedEntities:
        """Extract clinical entities from message."""
        message_lower = message.lower()
        entities = ExtractedEntities(raw_input=message)
        
        # Extract symptoms
        for symptom_key, patterns in self.SYMPTOM_PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower:
                    entities.symptoms.append(symptom_key)
                    break
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(days?|hours?|weeks?|months?)', message_lower)
        if duration_match:
            entities.duration = f"{duration_match.group(1)} {duration_match.group(2)}"
        
        # Extract severity
        if any(word in message_lower for word in ["severe", "very bad", "extreme", "unbearable", "worst"]):
            entities.severity = "severe"
        elif any(word in message_lower for word in ["mild", "slight", "little", "minor"]):
            entities.severity = "mild"
        else:
            entities.severity = "moderate"
        
        # Extract medicine names
        medicine_patterns = [
            r'\b(paracetamol|crocin|dolo)\b',
            r'\b(ibuprofen|brufen|combiflam)\b',
            r'\b(cetirizine|cetzine|zyrtec)\b',
            r'\b(azithromycin|azee|zithromax)\b',
            r'\b(amoxicillin|amoxyclav|augmentin)\b',
            r'\b(omeprazole|omez|pan)\b',
            r'\b(pantoprazole|pantop)\b',
            r'\b(metformin|glycomet)\b',
            r'\b(aspirin|disprin|ecosprin)\b',
            r'\b(loratadine|claritin)\b',
            r'\b(ors|electral)\b',
        ]
        
        for pattern in medicine_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities.medicines.append(match.group(1).title())
        
        # Extract quantity
        qty_match = re.search(r'(\d+)\s*(tablets?|tabs?|capsules?|strips?|bottles?)', message_lower)
        if qty_match:
            entities.quantity = int(qty_match.group(1))
        
        # Extract dosage
        dosage_match = re.search(r'(\d+)\s*(mg|mcg|ml)', message_lower)
        if dosage_match:
            entities.dosage = f"{dosage_match.group(1)}{dosage_match.group(2)}"
        
        # Extract frequency
        freq_patterns = [
            (r'once\s*(a|per)\s*day|daily', 'once daily'),
            (r'twice\s*(a|per)\s*day', 'twice daily'),
            (r'three\s*times?\s*(a|per)\s*day', 'three times daily'),
        ]
        for pattern, freq in freq_patterns:
            if re.search(pattern, message_lower):
                entities.frequency = freq
                break
        
        # Extract allergies mentioned
        allergy_match = re.search(r'allergic\s+to\s+(\w+)', message_lower)
        if allergy_match:
            entities.allergies.append(allergy_match.group(1))
        
        # Check for pregnancy
        if any(word in message_lower for word in ["pregnant", "pregnancy", "expecting", "breastfeeding", "lactating"]):
            entities.pregnancy_status = "pregnant" if "pregnant" in message_lower else "breastfeeding"
        
        # Age group detection
        if "baby" in message_lower or "infant" in message_lower or re.search(r'\b[0-2]\s*(months?|years?)\s*old', message_lower):
            entities.age_group = "infant"
        elif "child" in message_lower or re.search(r'\b([3-9]|1[0-2])\s*years?\s*old', message_lower):
            entities.age_group = "child"
        elif re.search(r'\b(6[5-9]|[7-9]\d|\d{3})\s*years?\s*old', message_lower) or "elderly" in message_lower:
            entities.age_group = "elderly"
        else:
            entities.age_group = "adult"
        
        return entities
    
    def _check_prescription_required(self, entities: ExtractedEntities) -> Dict:
        """Check if any requested medicine requires prescription."""
        result = {"required": False, "medicines": []}
        
        for medicine in entities.medicines:
            medicine_lower = medicine.lower()
            for rx_med in self.PRESCRIPTION_MEDICINES:
                if rx_med in medicine_lower or medicine_lower in rx_med:
                    result["required"] = True
                    result["medicines"].append(medicine)
                    break
        
        return result
    
    def _analyze_safety(self, entities: ExtractedEntities, patient_profile: Dict) -> Dict:
        """Comprehensive safety analysis."""
        warnings = []
        blocked = False
        alternatives = []
        
        # Check drug interactions
        all_meds = entities.medicines + patient_profile.get("current_medications", [])
        for med in entities.medicines:
            med_lower = med.lower()
            if med_lower in self.DRUG_INTERACTIONS:
                for interaction in self.DRUG_INTERACTIONS[med_lower]:
                    if any(interaction in m.lower() for m in all_meds if m.lower() != med_lower):
                        warnings.append(f"⚠️ Potential interaction: {med} with {interaction}")
        
        # Check pregnancy safety
        if entities.pregnancy_status:
            for med in entities.medicines:
                if any(unsafe in med.lower() for unsafe in self.PREGNANCY_UNSAFE):
                    blocked = True
                    warnings.append(f"🚫 {med} is not safe during pregnancy")
                    alternatives.append("Paracetamol is generally safe during pregnancy for pain/fever")
        
        # Check allergy
        patient_allergies = patient_profile.get("allergies", []) + entities.allergies
        for med in entities.medicines:
            if any(allergy.lower() in med.lower() for allergy in patient_allergies):
                blocked = True
                warnings.append(f"🚫 You indicated allergy to {med}")
        
        # Age-specific warnings
        if entities.age_group == "infant":
            blocked = True
            warnings.append("⚠️ Infants require pediatrician consultation before any medication")
        elif entities.age_group == "elderly":
            warnings.append("ℹ️ Elderly patients may need dose adjustments - consult pharmacist")
        elif entities.age_group == "child":
            warnings.append("ℹ️ Pediatric dosing required - will provide child-appropriate recommendations")
        
        return {
            "blocked": blocked,
            "warnings": warnings,
            "alternatives": alternatives,
            "confidence": 0.95 if not warnings else 0.75 if not blocked else 0.5
        }
    
    def _generate_clinical_response(
        self, message: str, entities: ExtractedEntities, intent: str, 
        state: str, patient_profile: Dict, safety_result: Dict, prescription_check: Dict,
        session_id: str = None
    ) -> PharmaResponse:
        """Generate clinical pharmacist response."""
        
        # Handle greeting
        if intent == "greeting":
            return PharmaResponse(
                intent="greeting",
                extracted_entities=entities,
                safety_status="approved",
                actions=[],
                user_message="""Hello! 👋 I'm PharmaAgent, your AI Pharmacist assistant.

I'm here to help you with:
• 💊 OTC medicine recommendations for common symptoms
• 📋 Checking medicine availability
• 🔍 Drug safety information
• ⏰ Refill reminders

**Before we start:**
- Do you have any known **allergies** to medications?
- Are you currently taking any **other medicines**?
- Are you **pregnant** or **breastfeeding**?

How can I help you today?""",
                confidence=1.0
            )
        
        if intent == "help":
            return PharmaResponse(
                intent="help",
                extracted_entities=entities,
                safety_status="approved",
                actions=[],
                user_message="""I'm your AI Pharmacist! Here's how I can assist:

🩺 **Symptom Check**
"I have fever and headache since 2 days"

💊 **Medicine Request**
"I need paracetamol 500mg"

🔄 **Refill Request**
"I need to refill my previous order"

📋 **Prescription Medicines**
"Doctor prescribed Amoxicillin" — I'll need to see the prescription

⚠️ **Important**: For emergencies (chest pain, severe bleeding, difficulty breathing), please call 112 immediately.

What would you like help with?""",
                confidence=1.0
            )

        # Handle pending confirmation
        if state == "awaiting_order_confirmation":
            return self._handle_order_confirmation(message, session_id, "medicine_request")
        
        # Handle prescription medicine request
        if prescription_check["required"]:
            meds = ", ".join(prescription_check["medicines"])
            return PharmaResponse(
                intent="prescription_validation",
                extracted_entities=entities,
                safety_status="blocked",
                actions=["request_prescription"],
                user_message=f"""📋 **Prescription Required**

The medicine(s) you requested (**{meds}**) require a valid prescription.

**Please upload your prescription:**
• Must be from a registered medical practitioner
• Should be dated within the last 6 months
• Must include: Patient name, medicine, dosage, and doctor's signature

You can use the 📎 button to upload your prescription image.

*I cannot dispense prescription medicines without valid documentation — this is for your safety and regulatory compliance.*""",
                confidence=1.0,
                requires_prescription=True
            )
        
        # Handle symptom-based consultation
        if intent == "symptom_check" or entities.symptoms:
            return self._symptom_consultation(entities, safety_result)
        
        # Handle OTC medicine request
        if intent == "medicine_request" and entities.medicines:
            return self._medicine_request_response(entities, safety_result, patient_profile, session_id)
        
        # Handle allergy information
        if intent == "allergy_info":
            return PharmaResponse(
                intent="allergy_info",
                extracted_entities=entities,
                safety_status="needs_clarification",
                actions=["record_allergy"],
                user_message=f"""Thank you for sharing your allergy information. I've noted that you're allergic to: **{', '.join(entities.allergies) if entities.allergies else 'the mentioned medications'}**

I'll ensure to:
✅ Avoid recommending these medicines
✅ Check for cross-reactivity with other drugs
✅ Suggest safe alternatives

Is there anything else about your medical history I should know?""",
                confidence=0.9
            )
        
        # Handle refill
        if intent == "refill":
            return PharmaResponse(
                intent="refill",
                extracted_entities=entities,
                safety_status="needs_clarification",
                actions=["check_order_history"],
                user_message="""🔄 **Refill Request**

I can help you reorder your previous medicines. Let me check your order history...

Could you confirm:
1. Which medicine do you need refilled?
2. Same quantity as before?

Or would you like me to show your recent orders?""",
                confidence=0.8
            )
        
        # Default: ask for clarification
        return PharmaResponse(
            intent="general_query",
            extracted_entities=entities,
            safety_status="needs_clarification",
            actions=["clarify"],
            user_message="""I'd like to help you better. Could you please tell me:

1. **What symptoms** are you experiencing? (e.g., fever, headache, cold)
   - OR -
2. **Which medicine** do you need?

Also, please let me know if you have any allergies or are currently on any medications.""",
            confidence=0.6
        )
    
    def _symptom_consultation(self, entities: ExtractedEntities, safety_result: Dict) -> PharmaResponse:
        """Generate symptom-based consultation response."""
        symptoms = entities.symptoms
        severity = entities.severity
        duration = entities.duration
        age_group = entities.age_group or "adult"
        
        if not symptoms:
            return PharmaResponse(
                intent="symptom_check",
                extracted_entities=entities,
                safety_status="needs_clarification",
                actions=["clarify_symptoms"],
                user_message="Could you please describe your symptoms in more detail? For example: \"I have headache and fever since 2 days\"",
                confidence=0.5
            )
        
        # Check severity for doctor referral
        if severity == "severe" or (duration and int(re.search(r'\d+', duration).group()) > 5):
            return PharmaResponse(
                intent="symptom_check",
                extracted_entities=entities,
                safety_status="escalate_human",
                actions=["doctor_referral"],
                urgency="doctor_referral",
                user_message=f"""Based on your symptoms ({', '.join(symptoms)}), the severity level ({severity}), and duration ({duration or 'ongoing'}), I recommend consulting a doctor.

**Why?**
• Symptoms persisting beyond 5 days need medical evaluation
• Severe symptoms may indicate underlying conditions requiring diagnosis

**In the meantime:**
• Stay hydrated
• Rest adequately
• Monitor your temperature

Would you like me to suggest any OTC relief while you arrange a doctor visit?""",
                confidence=0.85,
                warnings=["Symptoms require medical evaluation"]
            )
        
        # Build recommendation
        recommendations = []
        primary_symptom = symptoms[0]
        
        if primary_symptom in self.OTC_MEDICINES:
            meds = self.OTC_MEDICINES[primary_symptom].get(age_group, self.OTC_MEDICINES[primary_symptom].get("adult", []))
            recommendations = meds[:2]  # Top 2 recommendations
        
        if not recommendations:
            return PharmaResponse(
                intent="symptom_check",
                extracted_entities=entities,
                safety_status="needs_clarification",
                actions=["doctor_referral"],
                user_message=f"For {', '.join(symptoms)}, I recommend consulting a doctor for proper diagnosis and treatment.",
                confidence=0.7
            )
        
        # Build response
        rec_text = "\n".join([
            f"\n**{i+1}. {r['name']}**\n   • Dosage: {r['dosage']}\n   • Frequency: {r['frequency']}\n   • Precautions: {', '.join(r['precautions'])}"
            for i, r in enumerate(recommendations)
        ])
        
        warnings_text = "\n".join([f"• {w}" for w in safety_result["warnings"]]) if safety_result["warnings"] else ""
        
        response_text = f"""Based on your symptoms (**{', '.join(symptoms)}**), here are my OTC recommendations:

{rec_text}

**General Advice:**
• Stay hydrated (drink plenty of water)
• Get adequate rest
• Monitor symptoms

{f'**⚠️ Warnings:**' + chr(10) + warnings_text if warnings_text else ''}

**When to see a doctor:**
• If symptoms worsen or persist beyond 3-5 days
• If fever exceeds 103°F (39.4°C)
• If you experience any new concerning symptoms

Would you like me to add any of these medicines to your order?"""
        
        return PharmaResponse(
            intent="symptom_check",
            extracted_entities=entities,
            safety_status="approved" if not safety_result["blocked"] else "blocked",
            actions=["suggest_otc"],
            user_message=response_text,
            confidence=0.9,
            urgency="self_care",
            warnings=safety_result["warnings"],
            alternatives=[r["name"] for r in recommendations]
        )
    
    def _medicine_request_response(self, entities: ExtractedEntities, safety_result: Dict, patient_profile: Dict, session_id: str = None) -> PharmaResponse:
        """Handle direct medicine request."""
        medicines = entities.medicines
        quantity = entities.quantity
        
        if safety_result["blocked"]:
            return PharmaResponse(
                intent="medicine_request",
                extracted_entities=entities,
                safety_status="blocked",
                actions=["block_order"],
                user_message=f"""🚫 **Order Cannot Be Processed**

I cannot proceed with this order due to safety concerns:

{chr(10).join(['• ' + w for w in safety_result["warnings"]])}

**Alternatives:**
{chr(10).join(['• ' + a for a in safety_result["alternatives"]]) if safety_result["alternatives"] else "Please consult a pharmacist or doctor."}

Your safety is my priority. Would you like help with alternative options?""",
                confidence=0.95,
                warnings=safety_result["warnings"],
                alternatives=safety_result["alternatives"]
            )
        
        # Ask for quantity if not specified
        if not quantity or quantity == "not specified":
            if session_id:
                self.memory.set_state(session_id, "awaiting_quantity")
                self.memory.update_context(session_id, "pending_medicine", {
                    "medicines": medicines,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            medicine_name = medicines[0] if medicines else "this medicine"
            return PharmaResponse(
                intent="quantity_needed",
                extracted_entities=entities,
                safety_status="pending",
                actions=["await_quantity"],
                user_message=f"""💊 I found **{medicine_name}** in our inventory!

To proceed with your order, please let me know:
- **How many** units/tablets do you need?
- Any **specific dosage** requirements?

For example: "20 tablets" or "2 strips of 10".""",
                confidence=0.9,
                warnings=safety_result.get("warnings", [])
            )
        
        warnings_section = ""
        if safety_result["warnings"]:
            warnings_section = f"\n**⚠️ Please Note:**\n" + "\n".join([f"• {w}" for w in safety_result["warnings"]])
        
        # Save intent and entities for confirmation if session_id is available
        if session_id:
            self.memory.set_state(session_id, "awaiting_order_confirmation")
            # Store pending order details in context
            self.memory.update_context(session_id, "pending_order", {
                "medicines": medicines,
                "quantity": quantity,
                "dosage": entities.dosage,
                "frequency": entities.frequency,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return PharmaResponse(
            intent="medicine_request_proposal",
            extracted_entities=entities,
            safety_status="approved",
            actions=["reserve_stock", "propose_order"],
            user_message=f"""✅ **Order Summary**

**Medicine(s):** {', '.join(medicines)}
**Quantity:** {quantity}
{f'**Dosage:** {entities.dosage}' if entities.dosage else ''}
{f'**Frequency:** {entities.frequency}' if entities.frequency else ''}
{warnings_section}

**Safety Status:** ✓ Cleared

Would you like to:
1. ✅ **Confirm** this order
2. 📝 **Modify** quantity or add more items
3. ❌ **Cancel**

Please reply with your choice.""",
            confidence=0.9,
            warnings=safety_result["warnings"]
        )
    
    def _process_with_llm(self, message: str, session_id: str, customer_id: int) -> Dict[str, Any]:
        """Process using LLM client."""
        from dataclasses import asdict
        
        # 1. Analyze intent and extract entities
        analysis = self.llm_client.analyze_clinical_intent(message)
        
        if not analysis.success or not analysis.structured_data:
            raise Exception("LLM analysis failed")
            
        data = analysis.structured_data
        
        # KEY FIX: Delegate medicine requests to rule-based engine
        # The rule-based engine handles state ("awaiting_order_confirmation"), 
        # safety checks, and structured responses much better than the raw LLM.
        if data.get("intent") == "medicine_request":
             raise Exception("Delegating medicine_request to rule-based engine for safety and state management")
        
        entities = ExtractedEntities(
            symptoms=data.get("entities", {}).get("symptoms", []),
            medicines=data.get("entities", {}).get("medicines", []),
            duration=data.get("entities", {}).get("duration"),
            severity=data.get("entities", {}).get("severity"),
            age_group=data.get("entities", {}).get("age_group"),
            conditions=data.get("entities", {}).get("conditions", []),
            allergies=data.get("entities", {}).get("allergies", []),
            raw_input=message
        )
        
        # 3. Check safety internally (Hybrid approach: LLM + Rules)
        patient_profile = self.memory.get_patient_profile(session_id)
        safety_result = self._analyze_safety(entities, patient_profile)
        
        # Check prescription requirements (Rules are stricter/safer)
        prescription_check = self._check_prescription_required(entities)
        
        # 4. Generate response
        # We pass the combined context to the LLM generator
        context = {
            "intent": data.get("intent"),
            "safety_warnings": safety_result["warnings"],
            "is_blocked": safety_result["blocked"],
            "requires_prescription": prescription_check["required"],
            "entities": asdict(entities)
        }
        
        natural_response = self.llm_client.generate_natural_response(context)
        
        # Update memory
        self.memory.add_message(session_id, "assistant", natural_response)
        
        # 5. Return standard format
        return {
            "response": natural_response,
            "session_id": session_id,
            "structured_response": {
                "intent": data.get("intent"),
                "extracted_entities": asdict(entities),
                "safety_status": "blocked" if safety_result["blocked"] else "approved",
                "actions": [], # Actions would be determined by logic here
                "user_message": natural_response
            },
            "confidence": data.get("confidence", 0.9),
            "urgency": "normal",
            "requires_prescription": prescription_check["required"],
            "warnings": safety_result["warnings"],
            "alternatives": safety_result["alternatives"],
            "agent": f"{self.agent_name} (Llama3)"
        }
    
    def _handle_quantity_response(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Handle quantity response when awaiting quantity.
        Parses the quantity and transitions to order confirmation.
        """
        import re
        
        context = self.memory.get_context(session_id)
        pending_medicine = context.get("pending_medicine")
        
        if not pending_medicine:
            self.memory.set_state(session_id, "idle")
            return {
                "response": "I apologize, I lost track of which medicine you wanted. Please start again.",
                "intent": "error",
                "requires_action": None,
                "confidence": 1.0
            }
        
        # Extract quantity from message
        quantity_match = re.search(r'(\d+)', message)
        if quantity_match:
            quantity = int(quantity_match.group(1))
        else:
            # If no number found, ask again
            return {
                "response": "I couldn't understand the quantity. Please specify a number, for example: **20 tablets** or **2 strips**.",
                "intent": "quantity_needed",
                "requires_action": None,
                "confidence": 0.7
            }
        
        medicines = pending_medicine.get("medicines", [])
        medicine_name = medicines[0] if medicines else "Unknown medicine"
        
        # Set up pending order and transition to confirmation state
        self.memory.set_state(session_id, "awaiting_order_confirmation")
        self.memory.update_context(session_id, "pending_order", {
            "medicines": medicines,
            "quantity": quantity,
            "dosage": None,
            "frequency": None,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "response": f"""✅ **Order Summary**

**Medicine:** {medicine_name}
**Quantity:** {quantity} units

**Safety Status:** ✓ Cleared

Would you like to:
1. ✅ **Confirm** this order
2. 📝 **Modify** quantity or add more items  
3. ❌ **Cancel**

Please reply with your choice.""",
            "intent": "medicine_request_proposal",
            "requires_action": None,
            "confidence": 0.9
        }
    
    def _handle_order_confirmation(self, message: str, session_id: str, original_intent: str) -> Dict[str, Any]:
        """
        Handle confirmation response.
        Returns a dict (not PharmaResponse) so orchestrator can properly route to ActionAgent.
        """
        message_lower = message.lower()
        context = self.memory.get_context(session_id)
        pending_order = context.get("pending_order")
        
        if not pending_order:
            # Error state - lost context
            self.memory.set_state(session_id, "idle")
            return {
                "response": "I apologize, but I lost the details of your order. Please request the medicine again.",
                "intent": "error",
                "requires_action": None,
                "confidence": 1.0
            }

        # Check for confirmation
        confirm_keywords = ["1", "one", "confirm", "yes", "sure", "ok", "proceed", "place order", "done", "correct", "right"]
        cancel_keywords = ["2", "3", "two", "three", "modify", "change", "cancel", "no", "stop"]
        
        if any(w in message_lower for w in confirm_keywords) and not any(w in message_lower for w in cancel_keywords):
            # Order Confirmed - Signal orchestrator to process through ActionAgent
            medicine_name = pending_order["medicines"][0] if pending_order.get("medicines") else None
            quantity = pending_order.get("quantity")
            
            # Parse quantity if it's a string like "20 tablets"
            if isinstance(quantity, str):
                import re
                qty_match = re.search(r'(\d+)', str(quantity))
                quantity = int(qty_match.group(1)) if qty_match else 1
            elif quantity is None or quantity == "not specified":
                quantity = 1
            
            # Store the confirmed order details for the orchestrator
            self.memory.update_context(session_id, "medicine_name", medicine_name)
            self.memory.update_context(session_id, "quantity", quantity)
            
            # Return dict to signal order processing
            return {
                "response": "Processing your order...",
                "intent": "order_confirmed",
                "requires_action": "process_order",
                "extracted_order": {
                    "medicine_name": medicine_name,
                    "quantity": quantity
                },
                "session_id": session_id,
                "confidence": 1.0
            }
            
        elif any(w in message_lower for w in cancel_keywords):
            # Order Cancelled
            self.memory.set_state(session_id, "idle")
            return {
                "response": "Order cancelled. Let me know if you need anything else.",
                "intent": "order_cancelled",
                "requires_action": None,
                "confidence": 1.0
            }
            
        else:
            # Unclear response - ask for clarification
            return {
                "response": "I'm not sure I understood. Please reply with **1** or **yes** to confirm your order, or **2** or **cancel** to cancel.",
                "intent": "clarification",
                "requires_action": None,
                "confidence": 0.8
            }
            
    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary of a conversation session."""
        session = self.memory.get_session(session_id)
        return {
            "session_id": session_id,
            "state": session.get("state"),
            "patient_profile": session.get("patient_profile"),
            "message_count": len(session.get("messages", [])),
            "safety_checks": session.get("safety_checks", []),
            "created_at": session.get("created_at"),
            "last_activity": session.get("last_activity")
        }


# Create alias for backward compatibility
ConversationAgent = ClinicalPharmaAgent
