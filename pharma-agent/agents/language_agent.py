"""
Multilingual Agent - Language Detection and Translation Layer

This agent provides:
1. Automatic language detection for user input
2. Translation of non-English input to English (normalization)
3. Translation of English responses back to user's language (localization)
4. Persistent language preference handling per session

It acts as a middleware layer:
User Input (L1) -> Detect L1 -> Translate to EN -> Core Agents -> Response (EN) -> Translate to L1 -> User
"""
from typing import Dict, Any, Optional, Tuple
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MultilingualAgent")

class MultilingualAgent:
    """
    Handles language detection and translation for the agent system.
    Uses deep-translator (Google Translate) for free translation.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.agent_name = "MultilingualAgent"
        # Correctly supported languages by Google Translate
        # We don't need to list them all, but good to know common ones
        self.default_language = "en"
        
        # In-memory session language store (in prod, use Redis/DB)
        # Map: session_id -> language_code
        self.session_languages: Dict[str, str] = {}
        
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        Returns ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'hi').
        """
        if not text or len(text.strip()) < 2:
            return self.default_language
            
        # Hardcode common English greetings that are often misclassified on short text
        common_en_greetings = {"hello", "hi", "hey", "medicine", "pharmacy", "help", "start", "restart"}
        if text.lower().strip().strip('?!.,') in common_en_greetings:
            return "en"
            
        try:
            # langdetect is robust for short text but can hallucinate on single words
            # Use detect_langs for probability if needed, but detect() is usually fine with guards
            from langdetect import detect_langs
            probs = detect_langs(text)
            if not probs:
                return self.default_language
                
            # If English is a top candidate with decent probability, prefer it
            # e.g. [en:0.99] or [fi:0.5, en:0.4]
            best_match = probs[0]
            
            # If confidence is low (< 0.8) for non-English, and text looks like ASCII, default to EN
            if best_match.lang != 'en' and best_match.prob < 0.9:
                # Simple heuristic: if it's purely ASCII, bias towards English for programming context
                if text.isascii():
                    return 'en'
            
            return best_match.lang
        except LangDetectException:
            logger.warning(f"Could not detect language for: {text}")
            return self.default_language
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return self.default_language
            
    def normalize_input(self, text: str, session_id: str = None) -> Tuple[str, str, bool]:
        """
        Detect language and translate to English if necessary.
        
        Returns:
            (normalized_text_en, detected_lang_code, is_translated)
        """
        if not text:
            return "", "en", False
            
        # Detect language
        detected_lang = self.detect_language(text)
        
        # Determine target language (English)
        if detected_lang == 'en':
            # Update session language if provided
            if session_id:
                self.session_languages[session_id] = 'en'
            return text, 'en', False
            
        # Translate to English
        try:
            translator = GoogleTranslator(source='auto', target='en')
            translated_text = translator.translate(text)
            
            # Retrieve session language preference
            # If we detected a new language with high confidence, update session
            # For now, we trust the current detection
            if session_id:
                self.session_languages[session_id] = detected_lang
                
            logger.info(f"Translated input ({detected_lang} -> en): '{text}' -> '{translated_text}'")
            return translated_text, detected_lang, True
            
        except Exception as e:
            logger.error(f"Translation error (to English): {e}")
            # Fallback to original text
            return text, detected_lang, False

    def localize_response(self, text: str, target_lang: str, session_id: str = None) -> str:
        """
        Translate the English response to the target language.
        If target_lang is 'en', returns original text.
        If session_id is provided, tries to use stored language preference if target_lang is not specified.
        """
        # Determine effective target language
        lang = target_lang
        
        if not lang and session_id:
            lang = self.session_languages.get(session_id, self.default_language)
            
        if not lang or lang == 'en':
            return text
            
        try:
            # GoogleTranslator handles long text but splitting paragraphs helps preserve structure
            translator = GoogleTranslator(source='en', target=lang)
            
            # Simple localization strategy: translate the whole block
            # For complex markdown, we might need a smarter splitter, 
            # but deep-translator usually handles markdown okay-ish.
            # To be safe, let's translate, but keep an eye on markdown artifacts
            
            localized_text = translator.translate(text)
            
            logger.info(f"Localized response (en -> {lang})")
            return localized_text
            
        except Exception as e:
            logger.error(f"Translation error (to {lang}): {e}")
            return text

    def get_session_language(self, session_id: str) -> str:
        """Get the stored language for a session."""
        return self.session_languages.get(session_id, self.default_language)
