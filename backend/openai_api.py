import os
import json
import time
import logging
import base64
from typing import Dict, List, Any, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from schemas import DEFAULT_PROMPT, DEFAULT_OUTPUT_SCHEMA

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpenAIHandler:
    def __init__(self):
        """Initialize OpenAI client and handle credentials"""
        # Try to get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            # Check if there's a .env file or credentials file
            try:
                with open(".env", "r") as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            api_key = line.strip().split("=")[1].strip('"').strip("'")
                            break
            except:
                pass
        
        if not api_key:
            logger.warning("No OpenAI API key found. OpenAI features will not work.")
            raise ValueError("No OpenAI API key found")
        
        # Initialize the OpenAI client
        try:
            self.client = openai.OpenAI(api_key=api_key)
            # Set reasonable timeouts
            self.client.timeout = 60
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
            
        logger.info("OpenAI client initialized successfully")
    
    def _handle_api_error(self, error: Exception) -> Dict[str, Any]:
        """Handle OpenAI API errors gracefully"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Log the error
        logger.error(f"OpenAI API Error: {error_type} - {error_msg}")
        
        # Return a structured error response
        return {
            "error": True,
            "error_type": error_type,
            "error_message": error_msg,
            "summary": "Sorry, there was an error processing this document with AI.",
            "key_points": ["AI processing failed", f"Error: {error_msg}"],
            "insights": ["Please try again or process manually"]
        }
    
    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2)
    )
    def generate_image_description(self, image_data: str) -> str:
        """Generate a description of an image using the OpenAI Vision model"""
        logger.info("Generating image description")

        try:
            # If the data URL format is correct, extract the base64 content
            if image_data.startswith('data:image/'):
                base64_content = image_data.split(',', 1)[1]
            else:
                base64_content = image_data

            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using smaller, more efficient model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Give a brief, concise description of this image in 1-2 sentences only. Focus on what it generally shows without excessive detail."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_content}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100  # Reduce max tokens to encourage brevity
            )
            
            # Get the description from the response
            description = response.choices[0].message.content
            logger.info(f"Generated image description: {description[:50]}...")
            return description
        
        except Exception as e:
            logger.error(f"Error generating image description: {str(e)}")
            return f"[Image description error: {str(e)[:100]}...]"

    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2)
    )
    def process_content(
        self, 
        extracted_text: str, 
        images: List[Dict[str, Any]], 
        schema: Dict[str, Any] = None,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process extracted content with OpenAI"""
        try:
            # Use default schema if none provided
            if schema is None:
                schema = DEFAULT_OUTPUT_SCHEMA
                
            # Use default or custom prompt
            prompt = custom_prompt if custom_prompt else DEFAULT_PROMPT
            
            # Combine all text for analysis
            combined_text = extracted_text
            
            # Add OCR text and image descriptions from images
            if images and len(images) > 0:
                combined_text += "\n\n--- IMAGE CONTENT ---\n\n"
                
                for i, img in enumerate(images):
                    combined_text += f"\nIMAGE {i+1}:\n"
                    
                    # Add OCR text if available
                    if "ocr_text" in img and img["ocr_text"]:
                        if img["ocr_text"] != "[No text detected in image]":
                            combined_text += f"OCR Text: {img['ocr_text']}\n"
                    
                    # Add image description if available
                    if "image_description" in img and img["image_description"]:
                        combined_text += f"Image Description: {img['image_description']}\n"
            
            # Check if we're exceeding token limits
            # Rough estimate: 1 token ~= 4 chars for English text
            est_tokens = len(combined_text) / 4
            
            # GPT-4 has an 8k token limit, but we need to leave room for the response
            if est_tokens > 7000:
                logger.warning(f"Content exceeds token limit (~{est_tokens:.0f} tokens). Truncating.")
                # Truncate to ~7000 tokens (28000 chars)
                combined_text = combined_text[:28000] + "...[Content truncated due to length]"
            
            # Call OpenAI API
            logger.info("Calling OpenAI API")
            start_time = time.time()
            
            # Function to create a JSON structure from the text content
            system_prompt = """You are an expert document analyzer. Your task is to analyze the provided content and extract structured information.
            You MUST return a valid JSON object with the following structure:
            {
              "summary": "A concise but comprehensive summary of the document content",
              "key_points": ["Key point 1", "Key point 2", "..."],
              "insights": ["Insight 1", "Insight 2", "..."]
            }"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt + "\n\nDOCUMENT CONTENT:\n" + combined_text}
                ],
                temperature=0.0,
                top_p=1.0
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"OpenAI API call completed in {elapsed_time:.2f} seconds")
            
            # Parse the response
            try:
                content = response.choices[0].message.content
                # Try to extract JSON from the response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                    return result
                else:
                    # If no JSON found, try to parse the whole response
                    result = json.loads(content)
                    return result
            except json.JSONDecodeError:
                logger.error("Failed to parse OpenAI response as JSON")
                logger.error(f"Raw response: {response.choices[0].message.content[:500]}")
                return {
                    "error": True,
                    "summary": "Error parsing AI response",
                    "key_points": ["The AI returned an invalid format"],
                    "insights": ["Please try again"]
                }
                
        except Exception as e:
            return self._handle_api_error(e)
    
    def get_default_schema(self) -> Dict[str, Any]:
        """Return the default output schema"""
        return DEFAULT_OUTPUT_SCHEMA
    
    def get_default_prompt(self) -> str:
        """Return the default prompt"""
        return DEFAULT_PROMPT
