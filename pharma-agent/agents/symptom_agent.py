"""
Symptom Recommendation Agent - Backend-Integrated OTC Medicine Recommendations

This agent provides:
1. Symptom extraction from free-text with fuzzy matching
2. Live inventory lookup via backend API
3. OTC-only recommendations (respects prescription_required)
4. Red-flag symptom detection with doctor escalation
5. Structured JSON output for orchestrator integration
6. Safety disclaimers per pharmaceutical standards

Integrates with:
- GET /medicines endpoint for live inventory
- SafetyAgent for order validation
- ConversationAgent for conversation memory
"""
import re
import httpx
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SymptomAnalysis:
    """Result of symptom extraction and analysis."""
    symptoms: List[str] = field(default_factory=list)
    severity: str = "moderate"  # mild, moderate, severe
    duration: Optional[str] = None
    age_group: str = "adult"  # infant, child, adult, elderly
    has_red_flags: bool = False
    red_flags_detected: List[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


@dataclass
class MedicineRecommendation:
    """A single medicine recommendation."""
    name: str
    reason: str
    dosage_info: str
    price: float
    stock_level: int
    medicine_id: int


class SymptomRecommendationAgent:
    """
    Agent for symptom-based OTC medicine recommendations.
    
    Key Features:
    - Queries backend for live inventory
    - Only recommends OTC medicines (prescription_required = false)
    - Only recommends in-stock medicines (stock_level > 0)
    - Detects red-flag symptoms and escalates to doctor
    - Provides structured JSON output
    """
    
    # Backend API URL (configured for proxy in frontend)
    BACKEND_URL = "http://localhost:8000"
    
    # ==================== RED FLAG SYMPTOMS ====================
    RED_FLAG_PATTERNS = [
        # Cardiovascular emergencies
        ("chest pain", "Possible cardiac event"),
        ("chest tightness", "Possible cardiac event"),
        ("heart attack", "Cardiac emergency"),
        # Respiratory emergencies
        ("difficulty breathing", "Respiratory distress"),
        ("shortness of breath", "Respiratory distress"),
        ("can't breathe", "Respiratory emergency"),
        # Neurological emergencies
        ("stroke", "Neurological emergency"),
        ("seizure", "Neurological emergency"),
        ("convulsion", "Neurological emergency"),
        ("unconscious", "Loss of consciousness"),
        ("fainting", "Syncope - needs evaluation"),
        # Severe infections
        ("high fever 102", "High fever requires evaluation"),
        ("high fever 103", "High fever requires evaluation"),
        ("high fever 104", "Dangerously high fever"),
        ("neck stiffness", "Possible meningitis"),
        # Bleeding
        ("severe bleeding", "Hemorrhage"),
        ("vomiting blood", "GI bleeding"),
        ("blood in stool", "GI bleeding"),
        ("black stool", "Possible GI bleeding"),
        # Pregnancy-related
        ("pregnant", "Pregnancy - consult doctor first"),
        ("pregnancy bleeding", "Obstetric emergency"),
        # Children
        ("baby", "Infants need pediatric consultation"),
        ("infant", "Infants need pediatric consultation"),
        ("under 12", "Children under 12 need pediatric guidance"),
        # Mental health
        ("suicidal", "Mental health crisis"),
        ("overdose", "Possible overdose"),
    ]
    
    # ==================== SYMPTOM PATTERNS ====================
    SYMPTOM_PATTERNS = {
        "fever": [
            "fever", "temperature", "pyrexia", "high temp", "feeling hot",
            "burning up", "feverish", "hot to touch"
        ],
        "headache": [
            "headache", "head pain", "migraine", "head hurts", "head ache",
            "pounding head", "throbbing head"
        ],
        "cold": [
            "cold", "runny nose", "blocked nose", "congestion", "sneezing",
            "stuffy nose", "nasal", "coryza"
        ],
        "cough": [
            "cough", "coughing", "dry cough", "wet cough", "productive cough",
            "chesty cough", "tickly cough"
        ],
        "sore_throat": [
            "sore throat", "throat pain", "painful swallowing", "scratchy throat",
            "throat hurts", "tonsilitis"
        ],
        "body_pain": [
            "body pain", "body ache", "muscle pain", "joint pain", "fatigue",
            "aching", "sore muscles", "weakness"
        ],
        "stomach_pain": [
            "stomach pain", "abdominal pain", "belly ache", "cramps",
            "tummy ache", "stomach ache"
        ],
        "diarrhea": [
            "diarrhea", "loose motion", "loose stool", "watery stool",
            "upset stomach", "bowel issues"
        ],
        "constipation": [
            "constipation", "difficulty passing stool", "hard stool",
            "not able to pass stool", "blocked"
        ],
        "nausea": [
            "nausea", "vomiting", "feeling sick", "throwing up",
            "queasy", "upset stomach"
        ],
        "acidity": [
            "acidity", "heartburn", "acid reflux", "burning sensation",
            "indigestion", "gas", "bloating"
        ],
        "allergy": [
            "allergy", "allergic", "itching", "rash", "hives", "urticaria",
            "skin reaction", "sneezing"
        ],
    }
    
    # ==================== SYMPTOM TO MEDICINE MAPPING ====================
    SYMPTOM_MEDICINE_MAP = {
        "fever": ["Paracetamol", "Ibuprofen"],
        "headache": ["Paracetamol", "Ibuprofen", "Aspirin"],
        "cold": ["Cetirizine"],
        "cough": [],  # Most cough syrups need prescription or aren't in stock
        "sore_throat": ["Paracetamol"],  # For pain relief
        "body_pain": ["Paracetamol", "Ibuprofen"],
        "stomach_pain": ["Paracetamol"],  # Avoid NSAIDs for stomach
        "acidity": ["Omeprazole"],
        "allergy": ["Cetirizine"],
        "diarrhea": [],  # ORS recommended but usually not in medicine database
        "nausea": [],
        "constipation": [],
    }
    
    # ==================== SAFETY DISCLAIMERS ====================
    DISCLAIMER = (
        "⚠️ *This is general information, not a medical diagnosis. "
        "Please consult a doctor if symptoms persist or worsen.*"
    )
    
    def __init__(self, db=None, backend_url: str = None):
        self.db = db
        self.agent_name = "SymptomRecommendationAgent"
        if backend_url:
            self.BACKEND_URL = backend_url
        self._medicines_cache = None
        self._cache_timestamp = None
    
    async def _fetch_medicines_from_backend(self) -> List[Dict]:
        """Fetch medicines from backend API with caching."""
        # Cache for 60 seconds to avoid excessive API calls
        now = datetime.now()
        if (self._medicines_cache and self._cache_timestamp and 
            (now - self._cache_timestamp).seconds < 60):
            return self._medicines_cache
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BACKEND_URL}/medicines",
                    timeout=5.0
                )
                if response.status_code == 200:
                    self._medicines_cache = response.json()
                    self._cache_timestamp = now
                    return self._medicines_cache
        except Exception as e:
            print(f"[SymptomAgent] Error fetching medicines: {e}")
        
        return []
    
    def _fetch_medicines_sync(self) -> List[Dict]:
        """Synchronous version for non-async contexts."""
        if self.db:
            from backend.app.models import Medicine
            medicines = self.db.query(Medicine).all()
            return [
                {
                    "id": m.id,
                    "name": m.name,
                    "stock_level": m.stock_level,
                    "unit_type": m.unit_type,
                    "prescription_required": m.prescription_required,
                    "price": m.price,
                    "dosage_info": m.dosage_info or "Follow label instructions"
                }
                for m in medicines
            ]
        return []
    
    def _check_red_flags(self, message: str) -> List[str]:
        """Check for red-flag symptoms that require medical consultation."""
        message_lower = message.lower()
        detected = []
        
        for pattern, reason in self.RED_FLAG_PATTERNS:
            if pattern in message_lower:
                detected.append(f"{pattern}: {reason}")
        
        return detected
    
    def _extract_symptoms(self, message: str) -> SymptomAnalysis:
        """Extract symptoms from user message with fuzzy matching."""
        message_lower = message.lower()
        analysis = SymptomAnalysis()
        
        # Check red flags first
        red_flags = self._check_red_flags(message)
        if red_flags:
            analysis.has_red_flags = True
            analysis.red_flags_detected = red_flags
        
        # Extract symptoms
        for symptom_key, patterns in self.SYMPTOM_PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower:
                    if symptom_key not in analysis.symptoms:
                        analysis.symptoms.append(symptom_key)
                    break
        
        # Extract severity
        if any(word in message_lower for word in ["severe", "very bad", "extreme", "worst", "unbearable"]):
            analysis.severity = "severe"
        elif any(word in message_lower for word in ["mild", "slight", "little", "minor"]):
            analysis.severity = "mild"
        else:
            analysis.severity = "moderate"
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(days?|hours?|weeks?|months?)', message_lower)
        if duration_match:
            analysis.duration = f"{duration_match.group(1)} {duration_match.group(2)}"
        
        # Extract age group - fixed regex patterns
        if any(word in message_lower for word in ["baby", "infant"]) or \
           re.search(r'\b[0-2]\s*(months?|years?)\s*old', message_lower):
            analysis.age_group = "infant"
        elif "child" in message_lower or re.search(r'\b([3-9]|1[0-2])\s*years?\s*old', message_lower):
            analysis.age_group = "child"
        elif re.search(r'\b(6[5-9]|[7-9][0-9])\s*years?\s*old', message_lower) or "elderly" in message_lower:
            analysis.age_group = "elderly"
        else:
            analysis.age_group = "adult"
        
        # Check if we need clarification
        if not analysis.symptoms and not analysis.has_red_flags:
            analysis.needs_clarification = True
            analysis.clarification_question = (
                "I couldn't identify specific symptoms. Could you describe what you're experiencing? "
                "For example: headache, fever, cold, cough, body pain, stomach issues, etc."
            )
        
        return analysis
    
    def _find_otc_medicines(self, symptoms: List[str], medicines: List[Dict]) -> List[MedicineRecommendation]:
        """Find OTC medicines for symptoms from actual inventory."""
        recommendations = []
        seen_medicines = set()
        
        # Get candidate medicine names for symptoms
        candidate_names = set()
        for symptom in symptoms:
            if symptom in self.SYMPTOM_MEDICINE_MAP:
                for med_name in self.SYMPTOM_MEDICINE_MAP[symptom]:
                    candidate_names.add(med_name.lower())
        
        # Find matches in actual inventory
        for medicine in medicines:
            # Skip if prescription required
            if medicine.get("prescription_required", True):
                continue
            
            # Skip if out of stock
            if medicine.get("stock_level", 0) <= 0:
                continue
            
            # Check if medicine matches any candidate
            med_name_lower = medicine.get("name", "").lower()
            for candidate in candidate_names:
                if candidate in med_name_lower and medicine["name"] not in seen_medicines:
                    seen_medicines.add(medicine["name"])
                    
                    # Determine reason based on matching symptoms
                    matching_symptoms = [s for s in symptoms if candidate in [
                        m.lower() for m in self.SYMPTOM_MEDICINE_MAP.get(s, [])
                    ]]
                    reason = f"Helps with {', '.join(matching_symptoms)}" if matching_symptoms else "General relief"
                    
                    recommendations.append(MedicineRecommendation(
                        name=medicine["name"],
                        reason=reason,
                        dosage_info=medicine.get("dosage_info", "Follow label instructions"),
                        price=medicine.get("price", 0),
                        stock_level=medicine.get("stock_level", 0),
                        medicine_id=medicine.get("id", 0)
                    ))
                    break
        
        return recommendations
    
    async def process(
        self, 
        message: str, 
        session_id: str = None,
        customer_id: int = None
    ) -> Dict[str, Any]:
        """
        Process symptom-based request and return structured recommendations.
        
        Returns JSON matching the specification:
        {
          "intent": "symptom_based_request",
          "symptoms": ["fever", "headache"],
          "recommended_medicines": [
              {"name": "Paracetamol", "reason": "reduces fever and pain"}
          ],
          "needs_doctor_consultation": false,
          "follow_up_question": "Do you have any allergies to painkillers?"
        }
        """
        # Step 1: Extract symptoms
        analysis = self._extract_symptoms(message)
        
        # Step 2: Check for red flags - immediate doctor referral
        if analysis.has_red_flags:
            return self._generate_doctor_referral_response(analysis, session_id)
        
        # Step 3: Handle clarification needed
        if analysis.needs_clarification:
            return self._generate_clarification_response(analysis, session_id)
        
        # Step 4: Fetch medicines from backend
        medicines = await self._fetch_medicines_from_backend()
        
        if not medicines:
            # Fallback to database if API fails
            medicines = self._fetch_medicines_sync()
        
        # Step 5: Find OTC recommendations
        recommendations = self._find_otc_medicines(analysis.symptoms, medicines)
        
        # Step 6: Generate response
        if not recommendations:
            return self._generate_no_recommendation_response(analysis, session_id)
        
        return self._generate_recommendation_response(analysis, recommendations, session_id)
    
    def process_sync(
        self, 
        message: str, 
        session_id: str = None,
        customer_id: int = None
    ) -> Dict[str, Any]:
        """Synchronous version for non-async orchestrator."""
        # Step 1: Extract symptoms
        analysis = self._extract_symptoms(message)
        
        # Step 2: Check for red flags
        if analysis.has_red_flags:
            return self._generate_doctor_referral_response(analysis, session_id)
        
        # Step 3: Handle clarification needed
        if analysis.needs_clarification:
            return self._generate_clarification_response(analysis, session_id)
        
        # Step 4: Fetch medicines from database
        medicines = self._fetch_medicines_sync()
        
        # Step 5: Find OTC recommendations
        recommendations = self._find_otc_medicines(analysis.symptoms, medicines)
        
        # Step 6: Generate response
        if not recommendations:
            return self._generate_no_recommendation_response(analysis, session_id)
        
        return self._generate_recommendation_response(analysis, recommendations, session_id)
    
    def _generate_doctor_referral_response(
        self, analysis: SymptomAnalysis, session_id: str
    ) -> Dict[str, Any]:
        """Generate response for red-flag symptoms."""
        flags = ", ".join([f.split(":")[0] for f in analysis.red_flags_detected])
        
        user_message = f"""🚨 **Medical Consultation Required**

I've noticed some symptoms that need professional evaluation:
• {chr(10).join('• ' + f for f in analysis.red_flags_detected)}

**Please consult a doctor before taking any medication.**

For emergencies, call:
📞 Emergency: **112** (India) or your local emergency number

{self.DISCLAIMER}"""
        
        return {
            "intent": "symptom_based_request",
            "symptoms": analysis.symptoms,
            "recommended_medicines": [],
            "needs_doctor_consultation": True,
            "consultation_reason": analysis.red_flags_detected,
            "follow_up_question": None,
            "response": user_message,
            "session_id": session_id,
            "agent": self.agent_name,
            "safety_status": "escalate_human",
            "urgency": "doctor_referral"
        }
    
    def _generate_clarification_response(
        self, analysis: SymptomAnalysis, session_id: str
    ) -> Dict[str, Any]:
        """Generate response when symptoms are unclear."""
        user_message = f"""🤔 **Help Me Understand Your Symptoms**

{analysis.clarification_question}

**Common symptoms I can help with:**
• 🤒 Fever, headache, body pain
• 🤧 Cold, cough, sore throat
• 🤢 Stomach issues, acidity
• 🌡️ Allergies, skin irritation

Just describe what you're feeling and I'll suggest appropriate OTC options."""
        
        return {
            "intent": "symptom_based_request",
            "symptoms": [],
            "recommended_medicines": [],
            "needs_doctor_consultation": False,
            "follow_up_question": analysis.clarification_question,
            "response": user_message,
            "session_id": session_id,
            "agent": self.agent_name,
            "safety_status": "needs_clarification",
            "urgency": "normal"
        }
    
    def _generate_no_recommendation_response(
        self, analysis: SymptomAnalysis, session_id: str
    ) -> Dict[str, Any]:
        """Generate response when no OTC medicine is available."""
        symptoms_text = ", ".join(analysis.symptoms)
        
        user_message = f"""ℹ️ **No OTC Medicine Available**

For your symptoms ({symptoms_text}), I couldn't find a suitable over-the-counter medicine in our current inventory.

**What you can do:**
1. 👨‍⚕️ Consult a doctor for proper diagnosis
2. 📋 If you have a prescription, upload it and I can help with that
3. 💬 Describe different symptoms and I'll check again

{self.DISCLAIMER}"""
        
        return {
            "intent": "symptom_based_request",
            "symptoms": analysis.symptoms,
            "recommended_medicines": [],
            "needs_doctor_consultation": True,
            "consultation_reason": "No suitable OTC medicine available",
            "follow_up_question": "Do you have a prescription from your doctor?",
            "response": user_message,
            "session_id": session_id,
            "agent": self.agent_name,
            "safety_status": "no_otc_available",
            "urgency": "pharmacist_consult"
        }
    
    def _generate_recommendation_response(
        self, analysis: SymptomAnalysis, recommendations: List[MedicineRecommendation], 
        session_id: str
    ) -> Dict[str, Any]:
        """Generate response with medicine recommendations."""
        symptoms_text = ", ".join(analysis.symptoms)
        
        # Format medicine list
        med_lines = []
        for rec in recommendations:
            med_lines.append(
                f"• **{rec.name}** - ${rec.price:.2f}\n"
                f"  _{rec.reason}_\n"
                f"  📋 {rec.dosage_info}"
            )
        
        meds_formatted = "\n".join(med_lines)
        
        # Severity-specific advice
        if analysis.severity == "severe":
            severity_advice = "\n\n⚠️ **Since symptoms are severe**, please consult a doctor if they don't improve in 2-3 days."
        elif analysis.severity == "mild":
            severity_advice = "\n\n✅ For mild symptoms, these should provide relief."
        else:
            severity_advice = "\n\n💡 If symptoms persist beyond 3 days, please consult a doctor."
        
        user_message = f"""💊 **OTC Recommendations for {symptoms_text.title()}**

Based on your symptoms, here are safe over-the-counter options available now:

{meds_formatted}
{severity_advice}

Would you like to order any of these? Just let me know the medicine name and quantity.

{self.DISCLAIMER}"""
        
        return {
            "intent": "symptom_based_request",
            "symptoms": analysis.symptoms,
            "recommended_medicines": [
                {
                    "name": r.name,
                    "reason": r.reason,
                    "dosage_info": r.dosage_info,
                    "price": r.price,
                    "stock_level": r.stock_level,
                    "medicine_id": r.medicine_id
                }
                for r in recommendations
            ],
            "needs_doctor_consultation": False,
            "follow_up_question": (
                "Do you have any allergies to painkillers or other medications?"
                if any(s in analysis.symptoms for s in ["fever", "headache", "body_pain"])
                else None
            ),
            "response": user_message,
            "session_id": session_id,
            "agent": self.agent_name,
            "safety_status": "approved",
            "urgency": "self_care" if analysis.severity != "severe" else "pharmacist_consult"
        }
