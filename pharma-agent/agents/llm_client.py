"""
Ollama Client - Local LLM Integration

This module manages communication with the local Ollama instance running Llama 3.
It provides a structured interface for clinical pharmacy tasks.
"""
import json
import logging
import ollama
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger("OllamaClient")

@dataclass
class LLMResponse:
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    success: bool = False
    error: Optional[str] = None

class OllamaClient:
    """
    Client for interacting with local Ollama instance.
    Defaults to 'llama3' model.
    """
    
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.base_system_prompt = """You are an expert Clinical Pharmacist AI assistant. 
Your goal is to analyze user queries, extract clinical entities, and ensure patient safety.
You must JSON output ONLY when requested.
Do not provide medical diagnosis.
Always prioritize patient safety and regulatory compliance (India/WHO standards)."""
        
    def check_connection(self) -> bool:
        """Check if Ollama is running and specific model is available."""
        try:
            models = ollama.list()
            # models['models'] is a list of dicts with 'name' key
            is_model_present = any(self.model_name in m.get('name', '') for m in models.get('models', []))
            
            if not is_model_present:
                logger.warning(f"Ollama connected but model '{self.model_name}' not found. Available: {[m.get('name') for m in models.get('models', [])]}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False

    def analyze_clinical_intent(self, user_message: str) -> LLMResponse:
        """
        Analyze user message for intent, symptoms, medicines, and entities.
        Returns structured JSON.
        """
        prompt = f"""
Analyze the following user message as a Clinical Pharmacist.
Extract entities and determine intent.

User Message: "{user_message}"

Return specific JSON format ONLY:
{{
    "intent": "symptom_check" | "medicine_request" | "refill" | "prescription_validation" | "general_query" | "greeting",
    "entities": {{
        "symptoms": ["list", "of", "symptoms"],
        "medicines": ["list", "of", "medicines"],
        "duration": "string or null",
        "severity": "mild" | "moderate" | "severe",
        "age_group": "infant" | "child" | "adult" | "elderly",
        "conditions": ["list", "of", "conditions"],
        "allergies": ["list", "of", "allergies"]
    }},
    "safety_flags": {{
        "red_flags_detected": boolean,
        "reason": "string if red flag detected"
    }},
    "confidence": float (0.0 to 1.0)
}}
"""
        
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': self.base_system_prompt + " Output valid JSON only."},
                {'role': 'user', 'content': prompt},
            ], format='json')
            
            content = response['message']['content']
            data = json.loads(content)
            return LLMResponse(content=content, structured_data=data, success=True)
            
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM JSON response")
            return LLMResponse(content=response['message']['content'], success=False, error="Invalid JSON")
        except Exception as e:
            logger.error(f"LLM inference error: {e}")
            return LLMResponse(content="", success=False, error=str(e))

    def generate_natural_response(self, context: Dict[str, Any]) -> str:
        """
        Generate a natural language response based on clinical analysis.
        """
        prompt = f"""
Generate a helpful, empathetic, and professional response as a Clinical Pharmacist.
Based on this analysis: {json.dumps(context)}

Rules:
1. Be concise but caring.
2. If red flags are true, strictly advise doctor consultation.
3. If intent is symptom check, confirm symptoms before suggesting.
4. If medicine request, ask for prescription if needed.
5. Do not hallucinate medicines.
"""
        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': self.base_system_prompt},
                {'role': 'user', 'content': prompt},
            ])
            return response['message']['content']
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return "I apologize, but I'm having trouble generating a response right now."
