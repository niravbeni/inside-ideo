import os
import fitz  # PyMuPDF
import uuid
from PIL import Image
import io
import logging
import hashlib

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
        self.min_image_width = 500
        self.min_image_height = 500
        
        # Track image hashes to avoid duplicates
        self.processed_image_hashes = set()
    
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
                self._extract_meaningful_images(doc, page, page_num, result)
                
                # Extract the full page as an image
                self._extract_full_page(page, page_num, result)
            
            return result
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}", exc_info=True)
            return result
    
    def _hash_image(self, image_bytes):
        """Create a hash of the image to detect duplicates"""
        return hashlib.md5(image_bytes).hexdigest()
    
    def _extract_meaningful_images(self, doc, page, page_num, result):
        """Extract only meaningful images (filtering out icons, small decorations, etc.)"""
        try:
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Generate hash to check for duplicates
                    image_hash = self._hash_image(image_bytes)
                    
                    # Skip if we've already processed this exact image
                    if image_hash in self.processed_image_hashes:
                        logger.info(f"Skipping duplicate image on page {page_num+1}")
                        continue
                    
                    # Check image dimensions
                    if 'width' in base_image and 'height' in base_image:
                        width, height = base_image['width'], base_image['height']
                    else:
                        # If dimensions not available in metadata, load the image to get dimensions
                        img_obj = Image.open(io.BytesIO(image_bytes))
                        width, height = img_obj.size
                    
                    # Filter out small images
                    if width < self.min_image_width or height < self.min_image_height:
                        logger.info(f"Skipping small image ({width}x{height}) on page {page_num+1}")
                        continue
                    
                    # Add to processed hashes
                    self.processed_image_hashes.add(image_hash)
                    
                    # Generate a unique filename
                    image_ext = base_image["ext"]
                    image_filename = f"{uuid.uuid4()}.{image_ext}"
                    image_path = os.path.join(self.image_dir, image_filename)
                    
                    # Save the image
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # Add image info to result
                    result["images"].append({
                        "path": image_path,
                        "page": page_num + 1,
                        "filename": image_filename,
                        "width": width,
                        "height": height
                    })
                    logger.info(f"Extracted meaningful image: {image_filename} ({width}x{height})")
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} on page {page_num+1}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error extracting images from page {page_num+1}: {str(e)}")
    
    def _extract_full_page(self, page, page_num, result):
        """Extract the full page as an image"""
        try:
            # Set high resolution for page rendering
            zoom = 2.0  # higher zoom for better quality
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Generate a unique filename for the page
            page_filename = f"page_{page_num+1:03d}_{uuid.uuid4()}.png"
            page_path = os.path.join(self.page_dir, page_filename)
            
            # Save the page as a PNG
            pix.save(page_path)
            
            # Add page info to result
            result["pages"].append({
                "path": page_path,
                "page": page_num + 1,
                "filename": page_filename,
                "width": pix.width,
                "height": pix.height
            })
            logger.info(f"Extracted page {page_num+1} as image: {page_filename}")
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
