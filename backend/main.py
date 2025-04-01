import os
import shutil
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import logging
import time

from extract import PDFExtractor
from ocr import OCRProcessor
from openai_api import OpenAIHandler
from schemas import DEFAULT_OUTPUT_SCHEMA

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Session cleanup settings
CLEANUP_THRESHOLD = 24 * 60 * 60  # 24 hours in seconds

# Cleanup task and background task management
cleanup_task = None

async def cleanup_old_sessions():
    """Clean up session directories older than CLEANUP_THRESHOLD seconds"""
    while True:
        try:
            current_time = time.time()
            logger.info(f"Running scheduled cleanup of sessions older than {CLEANUP_THRESHOLD/3600} hours")
            
            if OUTPUT_DIR.exists():
                for session_dir in OUTPUT_DIR.iterdir():
                    if session_dir.is_dir():
                        # Get the creation time of the directory
                        dir_create_time = session_dir.stat().st_ctime
                        age = current_time - dir_create_time
                        
                        # If directory is older than threshold, remove it
                        if age > CLEANUP_THRESHOLD:
                            logger.info(f"Cleaning up old session: {session_dir}, age: {age/3600:.1f} hours")
                            try:
                                shutil.rmtree(session_dir, ignore_errors=True)
                            except Exception as e:
                                logger.error(f"Error removing directory {session_dir}: {str(e)}")
            
            # Sleep for 1 hour before checking again
            await asyncio.sleep(60 * 60)
        except Exception as e:
            logger.error(f"Error during cleanup task: {str(e)}")
            await asyncio.sleep(60 * 10)  # Wait 10 minutes on error

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create necessary directories and start background tasks
    global cleanup_task
    
    # Create output directory if it doesn't exist
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_sessions())
    logger.info("Started background cleanup task")
    
    yield  # This is where the app runs
    
    # Shutdown: cancel background tasks
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")

# Initialize FastAPI app
app = FastAPI(title="PDF Content Extractor", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://documentation-tool-frontend.onrender.com",
        "http://localhost:3000",  # Keep local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create output directory if it doesn't exist
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Setup static file serving for images
app.mount("/images", StaticFiles(directory=str(OUTPUT_DIR)), name="images")

# Initialize components
pdf_extractor = PDFExtractor()
ocr_processor = OCRProcessor()  # Using Tesseract for OCR
openai_handler = OpenAIHandler()

@app.post("/api/process-pdf")
async def process_pdf(
    files: List[UploadFile] = File(...),
    use_ocr: bool = Form(True),
    use_openai: bool = Form(True),
    custom_prompt: Optional[str] = Form(None),
    custom_schema: Optional[str] = Form(None)
):
    """
    Process PDF files:
    1. Extract content (text and images)
    2. Run OCR on extracted images
    3. Process with OpenAI
    """
    start_time = time.time()
    logger.info(f"Starting to process {len(files)} PDF files")
    
    try:
        # Create a session directory
        session_id = str(uuid.uuid4())
        session_dir = OUTPUT_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        logger.info(f"Created session directory: {session_dir}")
        
        # Save PDF files
        pdf_paths = []
        for file in files:
            file_path = session_dir / file.filename
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            pdf_paths.append(str(file_path))
            logger.info(f"Saved PDF: {file_path}")
        
        # Step 1: Extract content from PDFs
        extract_start = time.time()
        extraction_result = pdf_extractor.extract_content_from_multiple(pdf_paths)
        extract_time = time.time() - extract_start
        logger.info(f"Content extraction completed in {extract_time:.2f} seconds")
        
        # Check if extraction was successful
        if not extraction_result:
            raise HTTPException(status_code=500, detail="Failed to extract content from PDFs")
        
        # Process the images with OCR if requested
        ocr_time = 0
        if use_ocr and extraction_result["images"]:
            ocr_start = time.time()
            ocr_result = ocr_processor.process_images(extraction_result["images"])
            ocr_time = time.time() - ocr_start
            logger.info(f"OCR processing completed in {ocr_time:.2f} seconds")
            
            # Replace the images in the extraction result with OCR processed images
            extraction_result["images"] = ocr_result["processed_images"]
        
        # Process with OpenAI if requested
        openai_time = 0
        ai_analysis = {}
        if use_openai:
            openai_start = time.time()
            
            # Determine what schema to use
            schema = DEFAULT_OUTPUT_SCHEMA
            if custom_schema:
                try:
                    schema = json.loads(custom_schema)
                except:
                    logger.warning("Could not parse custom schema, using default")
            
            # Process with OpenAI
            ai_analysis = openai_handler.process_content(
                extracted_text=extraction_result["text"],
                images=extraction_result["images"],
                schema=schema,
                custom_prompt=custom_prompt
            )
            
            openai_time = time.time() - openai_start
            logger.info(f"OpenAI processing completed in {openai_time:.2f} seconds")
        
        # Create response object
        response = {
            "session_id": session_id,
            "extraction": {
                "text": extraction_result["text"],
                "images": extraction_result["images"],
                "pages": extraction_result["pages"]
            },
            "ai_analysis": ai_analysis,
            "processing_time": {
                "extraction": extract_time,
                "ocr": ocr_time,
                "openai": openai_time,
                "total": time.time() - start_time
            }
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/api/images/{session_id}/{filename}")
async def get_image(session_id: str, filename: str):
    """Get image by session ID and filename"""
    image_path = OUTPUT_DIR / session_id / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(image_path))

@app.get("/api/pages/{session_id}/{filename}")
async def get_page(session_id: str, filename: str):
    """Get page image by session ID and filename"""
    image_path = OUTPUT_DIR / session_id / "pages" / filename
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(str(image_path))

@app.get("/api/schema")
async def get_default_schema():
    """Get the default output schema"""
    return openai_handler.get_default_schema()

@app.get("/api/prompt")
async def get_default_prompt():
    """Get the default prompt"""
    return openai_handler.get_default_prompt()

@app.get("/")
async def read_root():
    return {"message": "PDF Content Extractor API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
