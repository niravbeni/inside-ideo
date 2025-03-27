import os
import shutil
import uuid
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import json

from extract import PDFExtractor
from ocr import OCRProcessor
from openai_api import OpenAIHandler

# Initialize FastAPI app
app = FastAPI(title="PDF Extraction API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pdf_extractor = PDFExtractor(image_dir="images", page_dir="pages")
ocr_processor = OCRProcessor()  # Using Tesseract for OCR
openai_handler = OpenAIHandler()

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("images", exist_ok=True)
os.makedirs("pages", exist_ok=True)

# Mount static directories for serving images and pages
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/pages", StaticFiles(directory="pages"), name="pages")

@app.get("/")
async def root():
    return {"message": "PDF Extraction API is running"}

@app.post("/process-pdf")
async def process_pdf(
    files: List[UploadFile] = File(...),
    prompt: Optional[str] = Form(None),
    schema: Optional[str] = Form(None)
):
    """Process uploaded PDF files, extract content, run OCR, and analyze with OpenAI"""
    try:
        # Save uploaded files
        pdf_paths = []
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
            # Generate a unique filename
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join("uploads", unique_filename)
            
            # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            pdf_paths.append(file_path)
        
        # Extract content from PDFs
        extracted_content = pdf_extractor.extract_content_from_multiple(pdf_paths)
        
        # Process images with OCR
        ocr_result = ocr_processor.process_images(extracted_content["images"])
        
        # Use default or provided prompt and schema
        using_prompt = prompt if prompt else openai_handler.get_default_prompt()
        using_schema = json.loads(schema) if schema else openai_handler.get_default_schema()
        
        # Process with OpenAI
        structured_data = openai_handler.process_content(
            extracted_content["text"],
            ocr_result["processed_images"],
            using_prompt,
            using_schema
        )
        
        # Return the combined result
        result = {
            "structured_data": structured_data,
            "images": ocr_result["processed_images"],
            "pages": extracted_content["pages"]
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images")
async def get_images():
    """Return list of all extracted images without OCR processing"""
    try:
        images = []
        image_dir = "images"
        
        if os.path.exists(image_dir):
            for filename in os.listdir(image_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    image_path = os.path.join(image_dir, filename)
                    # Get basic info
                    with open(image_path, "rb") as img_file:
                        images.append({
                            "filename": filename,
                            "path": image_path,
                            "size": os.path.getsize(image_path)
                        })
        
        return {"images": images}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pages")
async def get_pages():
    """Return list of all PDF pages as images"""
    try:
        pages = []
        page_dir = "pages"
        
        if os.path.exists(page_dir):
            for filename in os.listdir(page_dir):
                if filename.lower().endswith('.png'):
                    page_path = os.path.join(page_dir, filename)
                    
                    # Get page number from filename (format: page_XXX_uuid.png)
                    try:
                        page_num = int(filename.split('_')[1])
                    except:
                        page_num = 0
                    
                    # Read and encode the image
                    try:
                        with open(page_path, "rb") as img_file:
                            import base64
                            encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
                            image_data = f"data:image/png;base64,{encoded_image}"
                            
                            pages.append({
                                "filename": filename,
                                "path": page_path,
                                "page": page_num,
                                "size": os.path.getsize(page_path),
                                "image_data": image_data
                            })
                    except Exception as e:
                        pages.append({
                            "filename": filename,
                            "path": page_path,
                            "page": page_num,
                            "size": os.path.getsize(page_path),
                            "error": str(e)
                        })
        
        # Sort by page number
        pages.sort(key=lambda x: x["page"])
        
        return {"pages": pages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/default-schema")
async def get_default_schema():
    """Return the default output schema"""
    return openai_handler.get_default_schema()

@app.get("/default-prompt")
async def get_default_prompt():
    """Return the default prompt"""
    return {"prompt": openai_handler.get_default_prompt()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
