#!/usr/bin/env python3
import os
import sys
import argparse
from ocr import OCRProcessor

def main():
    """Test the OCR functionality with local image files"""
    parser = argparse.ArgumentParser(description='Test OCR on image files')
    parser.add_argument('image_paths', metavar='image_path', type=str, nargs='+',
                        help='paths to image files for OCR testing')
    args = parser.parse_args()
    
    # Initialize OCR processor
    processor = OCRProcessor()
    
    # Process each image
    for img_path in args.image_paths:
        if not os.path.exists(img_path):
            print(f"Error: Image file not found: {img_path}")
            continue
            
        # Create the image data structure expected by the processor
        test_images = [{
            "path": img_path,
            "filename": os.path.basename(img_path),
            "page": 1
        }]
        
        # Process the image
        print(f"\nProcessing image: {img_path}")
        result = processor.process_images(test_images)
        
        # Print the OCR result
        for img_result in result["processed_images"]:
            print("\n=== OCR TEXT ===")
            print(img_result["ocr_text"])
            print("=== END OCR TEXT ===\n")

if __name__ == "__main__":
    main() 