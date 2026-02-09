"""
EasyOCR Module - Local Offline OCR for Prescription Images

A modular, production-ready OCR module using EasyOCR for extracting
text from prescription images. Runs completely locally with no cloud APIs.

Features:
- Supports JPG, PNG, JPEG image formats
- Returns text with confidence scores
- Supports multiple languages
- Basic image preprocessing
- Graceful error handling
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Represents a single OCR detection result."""
    text: str
    confidence: float
    bounding_box: Optional[List[Tuple[int, int]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": round(self.confidence, 4),
            "bounding_box": self.bounding_box
        }


@dataclass
class OCRResponse:
    """Complete OCR response with all detected text."""
    success: bool
    image_path: str
    detected_items: List[OCRResult]
    full_text: str
    average_confidence: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "image_path": self.image_path,
            "detected_items": [item.to_dict() for item in self.detected_items],
            "full_text": self.full_text,
            "average_confidence": round(self.average_confidence, 4),
            "error": self.error
        }


class EasyOCRReader:
    """
    Local OCR module using EasyOCR.
    
    Features:
    - Completely offline operation
    - Supports multiple languages
    - Returns structured results with confidence scores
    - Image preprocessing support
    """
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    def __init__(
        self, 
        languages: List[str] = None,
        gpu: bool = False,
        download_enabled: bool = True
    ):
        """
        Initialize the EasyOCR reader.
        
        Args:
            languages: List of language codes (default: ['en'])
            gpu: Whether to use GPU acceleration
            download_enabled: Whether to allow model downloads
        """
        self.languages = languages or ['en']
        self.gpu = gpu
        self.download_enabled = download_enabled
        self._reader = None
        
        logger.info(f"EasyOCRReader initialized with languages: {self.languages}")
    
    def _get_reader(self):
        """Lazy initialization of EasyOCR reader."""
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(
                    self.languages,
                    gpu=self.gpu,
                    download_enabled=self.download_enabled
                )
                logger.info("EasyOCR reader loaded successfully")
            except ImportError:
                raise ImportError(
                    "EasyOCR is not installed. Install it with: pip install easyocr"
                )
        return self._reader
    
    def _validate_image(self, image_path: str) -> Tuple[bool, str]:
        """Validate that the image exists and has a supported format."""
        path = Path(image_path)
        
        if not path.exists():
            return False, f"Image file not found: {image_path}"
        
        if not path.is_file():
            return False, f"Path is not a file: {image_path}"
        
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file format: {path.suffix}. Supported: {self.SUPPORTED_EXTENSIONS}"
        
        return True, ""
    
    def _preprocess_image(self, image_path: str) -> str:
        """
        Basic image preprocessing for better OCR results.
        Returns the path to the processed image.
        """
        try:
            from PIL import Image, ImageEnhance, ImageFilter
            
            img = Image.open(image_path)
            
            # Convert to grayscale if it's a color image
            if img.mode == 'RGB' or img.mode == 'RGBA':
                img = img.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            # Apply slight sharpening
            img = img.filter(ImageFilter.SHARPEN)
            
            # Save to temp file
            temp_path = f"/tmp/ocr_preprocessed_{os.path.basename(image_path)}"
            img.save(temp_path)
            
            return temp_path
        except ImportError:
            logger.warning("PIL not available for preprocessing, using original image")
            return image_path
        except Exception as e:
            logger.warning(f"Preprocessing failed: {e}, using original image")
            return image_path
    
    def read_image(
        self, 
        image_path: str,
        preprocess: bool = False,
        detail: int = 1,
        paragraph: bool = False
    ) -> OCRResponse:
        """
        Perform OCR on an image file.
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to apply image preprocessing
            detail: 0 for simple output, 1 for full output with bounding boxes
            paragraph: If True, merge text into paragraphs
            
        Returns:
            OCRResponse with detected text and confidence scores
        """
        # Validate image
        valid, error_msg = self._validate_image(image_path)
        if not valid:
            return OCRResponse(
                success=False,
                image_path=image_path,
                detected_items=[],
                full_text="",
                average_confidence=0.0,
                error=error_msg
            )
        
        try:
            # Get reader
            reader = self._get_reader()
            
            # Preprocess if requested
            process_path = self._preprocess_image(image_path) if preprocess else image_path
            
            # Perform OCR
            logger.info(f"Running OCR on: {image_path}")
            results = reader.readtext(process_path, detail=detail, paragraph=paragraph)
            
            # Parse results
            detected_items = []
            texts = []
            confidences = []
            
            for result in results:
                if detail == 1 and len(result) >= 3:
                    bbox, text, confidence = result[0], result[1], result[2]
                    detected_items.append(OCRResult(
                        text=text,
                        confidence=float(confidence),
                        bounding_box=bbox
                    ))
                    texts.append(text)
                    confidences.append(float(confidence))
                elif detail == 0:
                    # Simple mode: result is just text
                    detected_items.append(OCRResult(
                        text=str(result),
                        confidence=1.0,
                        bounding_box=None
                    ))
                    texts.append(str(result))
                    confidences.append(1.0)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Combine all text
            full_text = "\n".join(texts)
            
            logger.info(f"OCR completed: {len(detected_items)} items detected, avg confidence: {avg_confidence:.2%}")
            
            return OCRResponse(
                success=True,
                image_path=image_path,
                detected_items=detected_items,
                full_text=full_text,
                average_confidence=avg_confidence
            )
            
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            return OCRResponse(
                success=False,
                image_path=image_path,
                detected_items=[],
                full_text="",
                average_confidence=0.0,
                error=str(e)
            )
    
    def read_multiple_images(
        self, 
        image_paths: List[str],
        preprocess: bool = False
    ) -> List[OCRResponse]:
        """
        Perform OCR on multiple images.
        
        Args:
            image_paths: List of image file paths
            preprocess: Whether to apply preprocessing
            
        Returns:
            List of OCRResponse objects
        """
        return [self.read_image(path, preprocess) for path in image_paths]
    
    def add_language(self, language_code: str):
        """
        Add a language and reinitialize the reader.
        
        Args:
            language_code: ISO language code (e.g., 'hi' for Hindi)
        """
        if language_code not in self.languages:
            self.languages.append(language_code)
            self._reader = None  # Force reinitialization
            logger.info(f"Added language: {language_code}")
    
    def extract_prescription_info(self, image_path: str) -> Dict[str, Any]:
        """
        Specialized method for extracting prescription information.
        
        Returns structured prescription data including:
        - Full text
        - Detected medicine names (heuristic-based)
        - Confidence score
        """
        result = self.read_image(image_path, preprocess=True)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error,
                "raw_text": "",
                "medicines": [],
                "confidence": 0.0
            }
        
        # Heuristic medicine name extraction
        # Common medicine patterns (can be enhanced with NLP)
        medicine_keywords = [
            'tablet', 'tab', 'capsule', 'cap', 'syrup', 'injection', 'inj',
            'mg', 'ml', 'mcg', 'cream', 'ointment', 'drops', 'solution'
        ]
        
        detected_medicines = []
        for item in result.detected_items:
            text_lower = item.text.lower()
            if any(keyword in text_lower for keyword in medicine_keywords):
                detected_medicines.append({
                    "text": item.text,
                    "confidence": item.confidence
                })
        
        return {
            "success": True,
            "raw_text": result.full_text,
            "medicines": detected_medicines,
            "confidence": result.average_confidence,
            "total_items_detected": len(result.detected_items)
        }


# Convenience function for quick OCR
def extract_text_from_image(
    image_path: str, 
    languages: List[str] = None
) -> str:
    """
    Quick helper function to extract text from an image.
    
    Args:
        image_path: Path to the image file
        languages: List of language codes
        
    Returns:
        Extracted text as a string
    """
    reader = EasyOCRReader(languages=languages)
    result = reader.read_image(image_path)
    return result.full_text if result.success else ""


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        print(f"\n📷 Processing image: {image_path}\n")
        
        reader = EasyOCRReader(languages=['en'])
        result = reader.read_image(image_path)
        
        if result.success:
            print("✅ OCR Successful!\n")
            print("=" * 50)
            print("EXTRACTED TEXT:")
            print("=" * 50)
            print(result.full_text)
            print("=" * 50)
            print(f"\n📊 Statistics:")
            print(f"   Items detected: {len(result.detected_items)}")
            print(f"   Average confidence: {result.average_confidence:.2%}")
            print("\n📝 Detailed Results:")
            for i, item in enumerate(result.detected_items, 1):
                print(f"   {i}. '{item.text}' (confidence: {item.confidence:.2%})")
        else:
            print(f"❌ OCR Failed: {result.error}")
    else:
        print("Usage: python ocr_module.py <image_path>")
        print("\nExample:")
        print("  python ocr_module.py prescription.jpg")
