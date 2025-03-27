import os
import json
import time
import random
import logging
from typing import Dict, Any, List, Optional, Union
import openai
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from dotenv import load_dotenv
import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OpenAIHandler:
    def __init__(self):
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key, timeout=60.0)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
        
        # For rate limiting
        self.base_retry_delay = 0.5  # Starting with 0.5 second
        self.max_retries = 3
        
        logger.info("OpenAIHandler initialized successfully")
    
    def _handle_api_error(self, e: Union[RateLimitError, APIError], retry_count: int) -> None:
        if isinstance(e, RateLimitError):
            wait_time = min(2 ** retry_count, 60)
            logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
        else:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def generate_image_description(self, image_data: str) -> str:
        """Generate a description of an image using GPT-4 Vision."""
        try:
            logger.info("Generating image description...")
            # Extract base64 content from data URL
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]

            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please describe this image concisely in 1-2 sentences, focusing on the key content and any visible text."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100
            )
            description = response.choices[0].message.content
            logger.info("Successfully generated image description")
            return description
        except Exception as e:
            logger.error(f"Error generating image description: {e}")
            return ""
    
    def process_content(self, extracted_text: str, ocr_content: List[Dict[str, Any]], max_retries: int = 3) -> Dict:
        """Process the extracted content using OpenAI API with retry logic."""
        retry_count = 0
        combined_text = extracted_text

        # Add OCR content and image descriptions to the combined text
        for item in ocr_content:
            if item.get("text"):
                combined_text += f"\n{item['text']}"
            if item.get("image_description"):
                combined_text += f"\n[Image Description: {item['image_description']}]"

        # Check token count and truncate if necessary
        if len(combined_text.split()) > 12000:
            logger.warning("Content too long, truncating...")
            combined_text = " ".join(combined_text.split()[:12000])

        while retry_count < max_retries:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": self.get_default_prompt()},
                        {"role": "user", "content": combined_text}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )
                return response.choices[0].message.content
            except (RateLimitError, APIError) as e:
                self._handle_api_error(e, retry_count)
                retry_count += 1

        raise Exception("Max retries exceeded for OpenAI API call")
    
    def get_default_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
    def get_default_prompt(self) -> str:
        return """You are a helpful assistant that processes document content and extracts key information.
Please analyze the provided text and generate a JSON response with the following structure:
{
    "title": "A clear title for the document",
    "summary": "A concise summary of the main content",
    "key_points": ["Array of key points or takeaways"]
}
Focus on the most important information and ensure the summary is clear and informative."""
