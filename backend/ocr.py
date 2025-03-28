import os
import base64
import time
import logging
import io
from typing import List, Dict, Any, Optional
import pytesseract
from PIL import Image, ImageFile, ImageEnhance
from openai_api import OpenAIHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

class OCRProcessor:
    def __init__(self):
        logger.info("OCRProcessor initialized with Tesseract")
        self.openai_handler = OpenAIHandler()
    
    def process_images(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a list of images using OpenAI Vision API and optionally OCR"""
        result = []
        
        logger.info("Starting to process %d images", len(images))
        
        # Track image hashes to identify duplicates
        image_hash_map = {}  # Map of image content hash to index in result list
        
        for i, img_data in enumerate(images):
            image_path = img_data["path"]
            logger.info("Processing image %d/%d: %s", i+1, len(images), img_data["filename"])
            
            # Read the image data to check for duplicates
            try:
                with open(image_path, "rb") as img_file:
                    image_bytes = img_file.read()
                    # Create a hash of the image content
                    image_hash = hash(image_bytes)
                    
                    # Check if we've already seen this image - skip if duplicate
                    if image_hash in image_hash_map:
                        logger.info(f"Duplicate image detected: {img_data['filename']} is identical to {result[image_hash_map[image_hash]]['filename']} - skipping")
                        # Don't add to results as specified by user
                        continue
                    
                    # Convert to base64 for API use
                    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
                    image_data = f"data:image/{image_path.split('.')[-1]};base64,{encoded_image}"
                    
                    # Add to result without description yet
                    result.append({
                        "filename": img_data["filename"],
                        "page": img_data["page"],
                        "image_description": "",  # Will be added in vision API pass
                        "image_data": image_data
                    })
                    # Store the index in our hash map
                    image_hash_map[image_hash] = len(result) - 1
                    logger.info("Image added to results")
            except Exception as e:
                logger.error("Error processing image: %s", str(e))
        
        # Process all unique images with Vision API
        if result:
            self._add_image_descriptions(result)
        
        logger.info("All images processed successfully")
        return {"processed_images": result}
    
    def _add_image_descriptions(self, images: List[Dict[str, Any]]):
        """Add AI-generated descriptions to images in a single API call"""
        logger.info("Starting image description generation for all images")
        
        # Filter out images without image_data
        valid_images = [img for img in images if img.get("image_data")]
        
        if not valid_images:
            logger.warning("No valid images with image data found for description generation")
            return
            
        try:
            logger.info(f"Using batch processing for {len(valid_images)} images in a single API call")
            description_start_time = time.time()
            
            # Generate descriptions in a single API call
            descriptions = self.openai_handler.batch_generate_image_descriptions(valid_images)
            description_elapsed_time = time.time() - description_start_time
            
            # Assign descriptions back to the original images
            for i, img in enumerate(valid_images):
                if i < len(descriptions):
                    img["image_description"] = descriptions[i]
                else:
                    img["image_description"] = "[Description error: API response mismatch]"
                    
            logger.info(f"Batch description completed for {len(valid_images)} images in {description_elapsed_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error in batch image description generation: {str(e)}")
            # Set error message for all images
            for img in valid_images:
                img["image_description"] = f"[Description error: {str(e)[:100]}...]"
    
    def _is_valid_image(self, img_path: str) -> bool:
        """Check if the image is valid and not corrupt"""
        try:
            with Image.open(img_path) as img:
                img.verify()
            return True
        except Exception:
            return False
            
    def _repair_image(self, img_path: str) -> Optional[Image.Image]:
        """Attempt to repair a corrupt image"""
        try:
            # Approach 1: Try opening with PIL's truncated mode
            img = Image.open(img_path)
            
            # Approach 2: If it's a JPEG, try re-saving it
            if img_path.lower().endswith(('.jpg', '.jpeg')):
                temp_path = img_path + ".temp.png"
                img.save(temp_path, format="PNG")
                img = Image.open(temp_path)
                try:
                    os.remove(temp_path)  # Clean up
                except:
                    pass
                
            return img
        except Exception as e:
            logger.warning(f"Could not repair image {img_path}: {str(e)}")
            return None
    
    def _tesseract_ocr(self, image_path: str) -> str:
        """Tesseract OCR with enhanced error handling and preprocessing"""
        try:
            logger.info("Starting Tesseract OCR for %s", image_path)
            start_time = time.time()
            
            # First check if the image is valid
            if not self._is_valid_image(image_path):
                logger.warning(f"Corrupt image detected: {image_path}, attempting repair")
                img = self._repair_image(image_path)
                if img is None:
                    return "[Could not process corrupt image]"
            else:
                # Load the image normally if it's valid
                img = Image.open(image_path)
            
            # Preprocessing steps to improve OCR quality
            
            # 1. Convert to RGB if needed (handle transparency)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # 2. Basic image enhancement
            try:
                # Increase contrast
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                # Increase sharpness
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.5)
            except Exception as e:
                logger.warning(f"Image enhancement failed: {str(e)}")
            
            # 3. Apply custom OCR configuration for better results
            custom_config = r'--oem 3 --psm 6'  # Page segmentation mode: 6 = Assume a single uniform block of text
            
            # 4. Save to in-memory buffer to avoid file system issues
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img = Image.open(img_buffer)
            
            # 5. Extract text with the custom configuration
            text = pytesseract.image_to_string(img, config=custom_config)
            
            elapsed_time = time.time() - start_time
            logger.info("Tesseract OCR completed in %.2f seconds", elapsed_time)
            
            if text.strip():
                logger.info("Successfully extracted text with Tesseract (%d chars)", len(text))
                return text.strip()
            else:
                logger.warning("No text detected by Tesseract")
                return "[No text detected in image]"
        except Exception as e:
            logger.error("Error with Tesseract OCR: %s", str(e), exc_info=True)
            return f"[OCR text extraction failed: {str(e)[:100]}...]"
