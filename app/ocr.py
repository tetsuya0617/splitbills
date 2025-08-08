"""
Google Cloud Vision API OCR module
"""
import logging
from typing import Optional
from google.cloud import vision
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)


def extract_text_from_image(image_data: bytes) -> Optional[str]:
    """
    Extract text from image using Google Cloud Vision API
    
    Args:
        image_data: Image binary data
        
    Returns:
        Extracted text string or None if extraction fails
    """
    try:
        # Initialize Vision API client (uses ADC)
        client = vision.ImageAnnotatorClient()
        
        # Create image object
        image = vision.Image(content=image_data)
        
        # Perform text detection
        response = client.text_detection(image=image)
        
        # Check for errors in response
        if response.error.message:
            logger.error(f"Vision API error: {response.error.message}")
            return None
        
        # Extract full text from annotations
        texts = response.text_annotations
        
        if texts:
            # First annotation contains the full text
            full_text = texts[0].description
            logger.info(f"OCR extracted {len(full_text)} characters")
            return full_text
        else:
            logger.warning("No text found in image")
            return None
            
    except GoogleAPIError as e:
        logger.error(f"Google API error during OCR: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during OCR: {e}")
        raise