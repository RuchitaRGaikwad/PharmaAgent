"""
Prescription Routes - OCR and Prescription Processing

Provides endpoints for:
1. Upload and OCR prescription images
2. Extract medicine information from prescriptions
3. Validate prescription data
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import os
import tempfile
import uuid

from ..services.ocr_module import EasyOCRReader

router = APIRouter()

# Initialize OCR reader (lazy loaded on first use)
_ocr_reader: Optional[EasyOCRReader] = None


def get_ocr_reader() -> EasyOCRReader:
    """Get or create OCR reader instance."""
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = EasyOCRReader(languages=['en'])
    return _ocr_reader


@router.post("/upload")
async def upload_prescription(file: UploadFile = File(...)):
    """
    Upload and process a prescription image using OCR.
    
    Accepts: JPG, PNG, JPEG images
    Returns: Extracted text and detected medicine information
    """
    # Validate file type
    allowed_types = {'image/jpeg', 'image/png', 'image/jpg'}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    # Save uploaded file temporarily
    temp_dir = tempfile.gettempdir()
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
    temp_path = os.path.join(temp_dir, f"prescription_{file_id}{file_ext}")
    
    try:
        # Write file to temp location
        contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Perform OCR
        reader = get_ocr_reader()
        result = reader.extract_prescription_info(temp_path)
        
        if not result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"OCR processing failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "filename": file.filename,
            "extracted_text": result['raw_text'],
            "detected_medicines": result['medicines'],
            "confidence": result['confidence'],
            "items_detected": result['total_items_detected']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing prescription: {str(e)}"
        )
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/extract-text")
async def extract_text_only(file: UploadFile = File(...)):
    """
    Extract raw text from an image using OCR.
    
    Returns only the text without medicine parsing.
    """
    # Validate file type
    allowed_types = {'image/jpeg', 'image/png', 'image/jpg'}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {allowed_types}"
        )
    
    temp_dir = tempfile.gettempdir()
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
    temp_path = os.path.join(temp_dir, f"ocr_{file_id}{file_ext}")
    
    try:
        contents = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        reader = get_ocr_reader()
        result = reader.read_image(temp_path, preprocess=True)
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"OCR failed: {result.error}"
            )
        
        return {
            "success": True,
            "text": result.full_text,
            "confidence": result.average_confidence,
            "items": [item.to_dict() for item in result.detected_items]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting text: {str(e)}"
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/status")
async def ocr_status():
    """Check OCR service status."""
    try:
        reader = get_ocr_reader()
        return {
            "status": "ready",
            "languages": reader.languages,
            "gpu_enabled": reader.gpu
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
