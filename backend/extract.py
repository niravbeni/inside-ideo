import os
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Union, Optional, Set
import fitz  # PyMuPDF
from PIL import Image
import io
import hashlib
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(self):
        """Initialize the PDF content extractor"""
        logger.info("PDFExtractor initialized")
    
    def extract_content(self, pdf_path: str, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Extract text and images from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images and pages
            
        Returns:
            Dict containing extracted text, images, and pages
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return {"error": "File not found"}
        
        # Use the directory from the pdf_path if not specified
        if output_dir is None:
            output_dir = Path(os.path.dirname(pdf_path))
        
        # Create directories if they don't exist
        images_dir = output_dir
        pages_dir = output_dir / "pages"
        pages_dir.mkdir(exist_ok=True)
        
        logger.info(f"Extracting content from {pdf_path}")
        
        result = {
            "text": "",
            "images": [],
            "pages": []
        }
        
        try:
            # Open the PDF
            pdf_document = fitz.open(pdf_path)
            pdf_filename = os.path.basename(pdf_path)
            
            # Extract text and images from each page
            for page_idx, page in enumerate(pdf_document):
                # Extract text
                page_text = page.get_text()
                result["text"] += f"\n--- Page {page_idx + 1} ---\n{page_text}\n"
                
                # Extract images
                self._extract_meaningful_images(page, page_idx, images_dir, result["images"])
                
                # Extract full page as image
                self._extract_full_page(page, page_idx, pages_dir, pdf_filename, result["pages"])
            
            logger.info(f"Extracted {len(result['images'])} images and {len(result['pages'])} page images from {pdf_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting content from PDF: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def _extract_meaningful_images(self, page, page_idx: int, output_dir: Path, images_list: List[Dict[str, Any]]):
        """Extract only meaningful images from a page (filter by size and uniqueness)"""
        # Track image hashes to prevent duplicates
        image_hashes = set()
        
        # Get page dimensions
        page_width, page_height = page.rect.width, page.rect.height
        min_size = 600  # Minimum size in pixels to consider - increase to 600
        
        # Skip if we already have too many images (limit to ~60 by default)
        max_images_per_doc = int(os.environ.get("MAX_IMAGES", "60"))
        if len(images_list) >= max_images_per_doc:
            logger.info(f"Already reached maximum image count ({max_images_per_doc}), skipping extraction for page {page_idx + 1}")
            return
        
        # Image index on this page
        img_idx = 0
        
        # Extract images using PyMuPDF
        image_list = page.get_images(full=True)
        
        # Limit images per page
        max_images_per_page = 3
        images_from_this_page = 0
        
        for img_idx, img in enumerate(image_list):
            # Skip if we've reached the limit for this page
            if images_from_this_page >= max_images_per_page:
                logger.debug(f"Reached max images ({max_images_per_page}) for page {page_idx + 1}, skipping remaining images")
                break
                
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            
            if base_image:
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                try:
                    # Compute image hash to detect duplicates
                    img_hash = hashlib.md5(image_bytes).hexdigest()
                    
                    if img_hash in image_hashes:
                        logger.debug(f"Skipping duplicate image on page {page_idx + 1}")
                        continue
                    
                    # Add to tracked hashes
                    image_hashes.add(img_hash)
                    
                    # Load image to get dimensions
                    with Image.open(io.BytesIO(image_bytes)) as pil_img:
                        img_width, img_height = pil_img.size
                    
                    # Skip small images (likely icons, bullets, etc.)
                    if img_width < min_size or img_height < min_size:
                        logger.debug(f"Skipping small image ({img_width}x{img_height}) on page {page_idx + 1}")
                        continue
                    
                    # Calculate relative size compared to page
                    rel_size = (img_width * img_height) / (page_width * page_height)
                    
                    # Skip small images relative to page size
                    if rel_size < 0.15:  # Increase threshold to 15% of page
                        logger.debug(f"Skipping relatively small image ({rel_size:.2%} of page) on page {page_idx + 1}")
                        continue
                    
                    # Generate a unique filename
                    img_filename = f"img_{page_idx + 1}_{img_idx + 1}_{uuid.uuid4().hex[:8]}.{image_ext}"
                    img_path = output_dir / img_filename
                    
                    # Save the image
                    with open(img_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # Add image info to the result
                    images_list.append({
                        "filename": img_filename,
                        "path": str(img_path),
                        "page": page_idx + 1,
                        "width": img_width,
                        "height": img_height
                    })
                    
                    images_from_this_page += 1
                    logger.info(f"Extracted meaningful image: {img_filename} ({img_width}x{img_height})")
                    
                except Exception as e:
                    logger.error(f"Error processing image on page {page_idx + 1}: {str(e)}")
    
    def _extract_full_page(self, page, page_idx: int, output_dir: Path, pdf_filename: str, pages_list: List[Dict[str, Any]]):
        """Extract the full page as an image"""
        try:
            # Create a unique filename for the page
            pdf_name = os.path.splitext(pdf_filename)[0]  # Remove extension
            page_filename = f"page_{page_idx + 1}_{uuid.uuid4().hex[:8]}.png"
            page_path = output_dir / page_filename
            
            # Render page to an image (at a higher DPI for better quality)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Save the image
            pix.save(str(page_path))
            
            # Add page info to the result
            pages_list.append({
                "filename": page_filename,
                "path": str(page_path),
                "page": page_idx + 1,
                "width": pix.width,
                "height": pix.height
            })
            
        except Exception as e:
            logger.error(f"Error extracting page {page_idx + 1} as image: {str(e)}")
    
    def extract_content_from_multiple(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """Extract content from multiple PDF files and combine the results"""
        if not pdf_paths:
            return {"error": "No PDF files provided"}
        
        combined_result = {
            "text": "",
            "images": [],
            "pages": []
        }
        
        # Get the output directory from the first PDF
        first_pdf_dir = Path(os.path.dirname(pdf_paths[0]))
        
        for pdf_idx, pdf_path in enumerate(pdf_paths):
            logger.info(f"Processing PDF {pdf_idx + 1}/{len(pdf_paths)}: {pdf_path}")
            
            # Extract content from this PDF
            result = self.extract_content(pdf_path, first_pdf_dir)
            
            if "error" in result:
                logger.error(f"Error processing {pdf_path}: {result['error']}")
                continue
            
            # Add to combined result with PDF index
            pdf_filename = os.path.basename(pdf_path)
            combined_result["text"] += f"\n\n===== PDF {pdf_idx + 1}: {pdf_filename} =====\n\n"
            combined_result["text"] += result["text"]
            
            # Add images with PDF index
            for img in result["images"]:
                img["pdf_index"] = pdf_idx
                combined_result["images"].append(img)
            
            # Add pages with PDF index
            for page in result["pages"]:
                page["pdf_index"] = pdf_idx
                combined_result["pages"].append(page)
        
        return combined_result
