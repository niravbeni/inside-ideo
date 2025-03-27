import os
import base64
import logging
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
from openai_api import OpenAIHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        self.openai_handler = OpenAIHandler()
        logger.info("OCR Processor initialized")
    
    def _is_valid_image(self, img: np.ndarray) -> bool:
        """Check if the image is valid for OCR processing."""
        if img is None or img.size == 0:
            return False
        height, width = img.shape[:2]
        min_dimension = 50
        return height >= min_dimension and width >= min_dimension

    def _repair_image(self, img: np.ndarray) -> np.ndarray:
        """Apply image preprocessing to improve OCR results."""
        try:
            # Convert to grayscale if not already
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img

            # Apply thresholding to get black and white image
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

            # Denoise
            denoised = cv2.fastNlMeansDenoising(binary)

            return denoised
        except Exception as e:
            logger.error(f"Error repairing image: {e}")
            return img

    def _tesseract_ocr(self, img: np.ndarray) -> str:
        """Extract text from image using Tesseract OCR."""
        try:
            # Convert numpy array to PIL Image
            pil_img = Image.fromarray(img)
            
            # Extract text
            text = pytesseract.image_to_string(pil_img)
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return ""

    def process_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of images, extract text using OCR, and generate descriptions."""
        results = []
        
        for img_data in images:
            try:
                # Extract base64 image data
                if not img_data.get('data'):
                    logger.warning("No image data found")
                    continue

                # Convert base64 to numpy array
                img_bytes = base64.b64decode(img_data['data'].split(',')[1])
                nparr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if not self._is_valid_image(img):
                    logger.warning("Invalid image detected")
                    continue

                # Process image
                processed_img = self._repair_image(img)
                
                # Extract text using OCR
                text = self._tesseract_ocr(processed_img)
                
                # Generate image description
                description = self.openai_handler.generate_image_description(img_data['data'])

                # Prepare result
                result = {
                    'page': img_data.get('page', 0),
                    'text': text,
                    'image_description': description
                }
                
                results.append(result)
                logger.info(f"Successfully processed image from page {img_data.get('page', 0)}")
                
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                continue

        return results
