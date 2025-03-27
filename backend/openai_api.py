import os
import json
import time
import random
import logging
from typing import Dict, Any, List, Optional
import openai
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OpenAIHandler:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        
        # Initialize the OpenAI client with timeout
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=60.0  # 60 second timeout
        )
        
        # For rate limiting
        self.base_retry_delay = 0.5  # Starting with 0.5 second
        self.max_retries = 3
        
        logger.info("OpenAIHandler initialized successfully")
    
    def _handle_api_error(self, e: Exception, attempt: int) -> Dict[str, Any]:
        """Common error handling method for API errors"""
        error_type = type(e).__name__
        error_message = str(e)
        
        logger.error(f"{error_type}: {error_message}")
        
        error_response = {
            "error": error_message,
            "error_type": error_type,
            "title": "Error processing document",
            "summary": "An error occurred while analyzing your document.",
            "key_points": ["Processing error", "Try again later"],
            "insights_from_images": []
        }
        
        if isinstance(e, RateLimitError):
            error_response.update({
                "title": "Analysis limited due to API rate limits",
                "summary": "The PDF analysis was interrupted due to API rate limits. Please try again in a few moments or with a smaller document.",
                "key_points": ["API rate limit reached", "Try again later", "Consider processing smaller documents"]
            })
        elif isinstance(e, APITimeoutError):
            error_response.update({
                "title": "Request timed out",
                "summary": "The request to analyze your document timed out. This might be due to the document size or temporary API issues.",
                "key_points": ["Request timed out", "Try again later", "Consider processing a smaller document"]
            })
        
        return error_response
    
    def _should_retry(self, e: Exception) -> bool:
        """Determine if we should retry based on the exception type"""
        return isinstance(e, (RateLimitError, APITimeoutError)) or (
            isinstance(e, APIError) and str(e).startswith(("500", "503"))
        )
    
    def process_content(self, 
                        text_content: str, 
                        ocr_content: List[Dict[str, Any]], 
                        prompt: str,
                        output_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process extracted PDF content with OpenAI and return structured data
        using the chat completions API
        """
        logger.info("Processing content with %d OCR images", len(ocr_content))
        start_time = time.time()
        
        # Prepare the combined input
        combined_text = text_content
        
        # Add OCR text from images
        if ocr_content and len(ocr_content) > 0:
            combined_text += "\n\n=== OCR TEXT FROM IMAGES ===\n"
            for idx, img in enumerate(ocr_content):
                combined_text += f"\nImage {idx+1} (Page {img['page']}): {img['ocr_text']}\n"
        
        logger.info("Combined text prepared (%d characters)", len(combined_text))
        
        # Check if the combined text is too large (rough estimate)
        max_tokens = 120000  # gpt-4o-mini has a 128K context window, use a bit less to be safe
        est_token_count = len(combined_text) / 3  # Very rough estimate (3 chars per token)
        
        if est_token_count > max_tokens:
            logger.warning("Combined text likely exceeds token limit (%d chars)", len(combined_text))
            return {
                "error": "Content too large",
                "title": "Document too large",
                "summary": "The document is too large to process in a single request.",
                "key_points": ["Document size exceeds limits", "Try processing a smaller document"],
                "insights_from_images": []
            }
        
        # Call the OpenAI API with retry logic
        retries = 0
        
        while retries < self.max_retries:
            try:
                logger.info("Calling OpenAI Chat Completions API (attempt %d/%d)...", retries+1, self.max_retries)
                api_start_time = time.time()
                
                # Format the prompt with the schema information
                full_prompt = f"{prompt}\n\nContent:\n{combined_text}\n\nOutput Schema: {json.dumps(output_schema, indent=2)}\n\nPlease provide your response as valid JSON matching the provided schema."
                
                # Use chat completions API with JSON response format
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are an AI that analyzes PDF content and extracts structured information based on user requirements."},
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.3,  # Lower temperature for more predictable outputs
                    max_tokens=4000  # Limit response size
                )
                
                api_elapsed_time = time.time() - api_start_time
                logger.info("OpenAI API call completed in %.2f seconds", api_elapsed_time)
                
                # Extract the response content - already in JSON format
                response_content = response.choices[0].message.content
                logger.info("Received response from OpenAI (%d characters)", len(response_content))
                
                try:
                    structured_data = json.loads(response_content)
                    logger.info("Successfully parsed JSON response")
                    
                    total_elapsed_time = time.time() - start_time
                    logger.info("Total processing completed in %.2f seconds", total_elapsed_time)
                    
                    return structured_data
                except json.JSONDecodeError as e:
                    logger.error("Error parsing JSON response: %s", str(e))
                    logger.error("Raw response: %s", response_content[:500] + "..." if len(response_content) > 500 else response_content)
                    return {
                        "error": "Invalid JSON response from API",
                        "title": "Error processing document",
                        "summary": "The system received an invalid response while analyzing your document.",
                        "key_points": ["Processing error", "Try again later"],
                        "insights_from_images": []
                    }
                
            except Exception as e:
                retries += 1
                if self._should_retry(e) and retries < self.max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = (self.base_retry_delay * (2 ** retries)) + (random.random() * 0.1)
                    logger.info("Error occurred, retrying in %.2f seconds... (attempt %d/%d)", 
                               delay, retries, self.max_retries)
                    time.sleep(delay)
                else:
                    return self._handle_api_error(e, retries)
            
    def get_default_schema(self) -> Dict[str, Any]:
        """Return a default output schema"""
        return {
            "title": "string",
            "summary": "string",
            "key_points": ["string"],
            "insights_from_images": ["string"]
        }
        
    def get_default_prompt(self) -> str:
        """Return a default prompt"""
        return "Given the extracted text and image descriptions from the uploaded PDF, generate a document title, short summary, 3-5 key points, and any relevant insights from the images."
