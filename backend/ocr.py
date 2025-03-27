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
        """Process a list of images and extract text using Tesseract OCR and generate descriptions using OpenAI"""
        result = []
        
        logger.info("Starting to process %d images", len(images))
        
        # First pass: process all images with OCR
        for i, img_data in enumerate(images):
            image_path = img_data["path"]
            logger.info("Processing image %d/%d: %s", i+1, len(images), img_data["filename"])
            
            start_time = time.time()
            
            # Extract text using Tesseract OCR
            ocr_text = self._tesseract_ocr(image_path)
            
            elapsed_time = time.time() - start_time
            logger.info("OCR completed in %.2f seconds", elapsed_time)
            
            # Prepare the image data 
            try:
                with open(image_path, "rb") as img_file:
                    encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
                    image_data = f"data:image/{image_path.split('.')[-1]};base64,{encoded_image}"
                    
                    # Add to result without description yet
                    result.append({
                        "filename": img_data["filename"],
                        "page": img_data["page"],
                        "ocr_text": ocr_text,
                        "image_description": "",  # Will be added in second pass
                        "image_data": image_data
                    })
                    logger.info("Image added to results with OCR")
            except Exception as e:
                logger.error("Error processing image: %s", str(e))
                result.append({
                    "filename": img_data["filename"],
                    "page": img_data["page"],
                    "ocr_text": ocr_text,
                    "image_description": "[Image description failed]",
                    "image_data": ""
                })
        
        # Second pass: add descriptions in batches with rate limiting
        self._add_image_descriptions(result)
        
        logger.info("All images processed successfully")
        return {"processed_images": result}
    
    def _add_image_descriptions(self, images: List[Dict[str, Any]]):
        """Add AI-generated descriptions to images with rate limiting"""
        logger.info("Starting image description generation for %d images", len(images))
        
        # Process images in smaller batches to avoid rate limits
        batch_size = min(5, len(images))  # Process max 5 images at a time
        delay_between_batches = 15  # 15 seconds between batches to avoid rate limits
        
        # Skip description generation for very large sets
        if len(images) > 30:
            logger.warning(f"Too many images ({len(images)}), skipping AI descriptions for all but first 20")
            # Only process the first 20 images
            for i, img in enumerate(images):
                if i >= 20:
                    img["image_description"] = "[Image description skipped - too many images]"
            # Trim the images list to first 20 for processing
            images_to_process = images[:20]
        else:
            images_to_process = images
            
        for i in range(0, len(images_to_process), batch_size):
            batch = images_to_process[i:i+batch_size]
            logger.info(f"Processing description batch {i//batch_size + 1}/{(len(images_to_process) + batch_size - 1)//batch_size}")
            
            for j, img in enumerate(batch):
                if not img["image_data"]:
                    continue
                    
                try:
                    logger.info(f"Generating image description for {img['filename']} ({i+j+1}/{len(images_to_process)})")
                    description_start_time = time.time()
                    
                    # Add random delay between individual images (1-3 seconds)
                    if j > 0:
                        delay = 1.0 + (hash(img["filename"]) % 200) / 100.0  # Random but deterministic delay
                        logger.info(f"Rate limiting - waiting {delay:.2f}s before next description")
                        time.sleep(delay)
                    
                    # Generate description
                    description = self.openai_handler.generate_image_description(img["image_data"])
                    description_elapsed_time = time.time() - description_start_time
                    
                    img["image_description"] = description
                    logger.info(f"Description for {img['filename']} completed in {description_elapsed_time:.2f}s")
                except Exception as e:
                    logger.error(f"Error generating description: {str(e)}")
                    img["image_description"] = f"[Description error: {str(e)[:100]}...]"
            
            # Add delay between batches to avoid rate limits
            if i + batch_size < len(images_to_process):
                logger.info(f"Rate limiting - waiting {delay_between_batches}s before next batch")
                time.sleep(delay_between_batches)
    
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
