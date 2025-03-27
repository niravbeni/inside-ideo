import os
import fitz  # PyMuPDF
import uuid
from PIL import Image
import io
import logging
import hashlib
import base64
import numpy as np
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(self, image_dir="images", page_dir="pages"):
        self.image_dir = image_dir
        self.page_dir = page_dir
        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(page_dir, exist_ok=True)
        
        # Minimum size for "meaningful" images (in pixels)
        self.min_image_size = 100  # Minimum dimension in pixels
        self.min_image_area = 10000  # Minimum area in pixels
        self.max_image_size = 4096  # Maximum dimension in pixels
        
        # Track image hashes to avoid duplicates
        self.processed_image_hashes = set()
        
        logger.info("PDFExtractor initialized")
    
    def extract_content(self, pdf_path):
        """Extract text and images from a PDF file"""
        result = {
            "text": "",
            "images": [],
            "pages": []
        }
        
        try:
            doc = fitz.open(pdf_path)
            
            # Extract text and images from each page
            for page_num, page in enumerate(doc):
                # Extract text
                text = page.get_text()
                result["text"] += f"\n--- Page {page_num + 1} ---\n{text}"
                
                # Extract meaningful embedded images
                self._extract_meaningful_images(page, page_num, result)
                
                # Extract the full page as an image
                self._extract_full_page(page, page_num, result)
            
            return result
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}", exc_info=True)
            return result
    
    def _hash_image(self, image_bytes):
        """Create a hash of the image to detect duplicates"""
        return hashlib.md5(image_bytes).hexdigest()
    
    def _extract_meaningful_images(self, page, page_num, result):
        """Extract meaningful images from a PDF page."""
        images = []
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                
                if base_image is None:
                    continue
                
                # Convert image data to PIL Image for analysis
                image_data = base_image["image"]
                image = Image.open(io.BytesIO(image_data))
                
                # Get image dimensions
                width, height = image.size
                area = width * height
                
                # Skip if image is too small or too large
                if (width < self.min_image_size or 
                    height < self.min_image_size or 
                    area < self.min_image_area or
                    width > self.max_image_size or 
                    height > self.max_image_size):
                    continue
                
                # Convert to base64
                image_bytes = io.BytesIO()
                image.save(image_bytes, format=base_image["ext"].upper())
                base64_image = base64.b64encode(image_bytes.getvalue()).decode()
                
                images.append({
                    "page": page_num + 1,
                    "data": f"data:image/{base_image['ext']};base64,{base64_image}"
                })
                
            except Exception as e:
                logger.error(f"Error extracting image {img_index} from page {page_num+1}: {e}")
                continue
        
        result["images"].extend(images)
    
    def _extract_full_page(self, page, page_num, result):
        """Extract the full page as an image"""
        try:
            # Convert page to a pixmap
            zoom = 2  # Increase resolution
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Convert to base64
            image_bytes = io.BytesIO()
            img.save(image_bytes, format='JPEG', quality=85)
            base64_image = base64.b64encode(image_bytes.getvalue()).decode()
            
            result["pages"].append({
                "page": page_num + 1,
                "data": f"data:image/jpeg;base64,{base64_image}"
            })
            logger.info(f"Extracted page {page_num+1} as image")
        except Exception as e:
            logger.warning(f"Failed to extract page {page_num+1} as image: {str(e)}")

    def extract_content_from_multiple(self, pdf_paths):
        """Extract content from multiple PDFs and combine results"""
        combined_result = {
            "text": "",
            "images": [],
            "pages": []
        }
        
        # Reset image hash tracking between batch processing
        self.processed_image_hashes = set()
        
        for pdf_path in pdf_paths:
            try:
                result = self.extract_content(pdf_path)
                pdf_name = os.path.basename(pdf_path)
                
                # Add PDF name to text
                combined_result["text"] += f"\n\n=== PDF: {pdf_name} ===\n{result['text']}"
                
                # Add source PDF name to images and pages
                for img in result["images"]:
                    img["source_pdf"] = pdf_name
                    combined_result["images"].append(img)
                
                for page in result["pages"]:
                    page["source_pdf"] = pdf_name
                    combined_result["pages"].append(page)
                    
            except Exception as e:
                logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
                combined_result["text"] += f"\n\n=== PDF: {pdf_name} ===\nError extracting content: {str(e)}"
        
        return combined_result
