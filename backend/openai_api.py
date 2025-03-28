import os
import json
import time
import logging
import base64
from typing import Dict, List, Any, Optional
import openai
import re
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
            
            # Add image descriptions from images
            if images and len(images) > 0:
                combined_text += "\n\n--- IMAGE CONTENT ---\n"
                
                for i, img in enumerate(images):
                    # Add image description if available
                    if "image_description" in img and img["image_description"]:
                        combined_text += f"\nImage {i+1}: {img['image_description']}\n"
            
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

    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2)
    )
    def batch_generate_image_descriptions(self, images: List[Dict[str, Any]]) -> List[str]:
        """Generate descriptions for multiple images in a single API call to reduce quota usage"""
        logger.info(f"Generating descriptions for {len(images)} images in a batch")

        try:
            # Handle large batches by splitting if needed
            # OpenAI has an input token limit, so we need to be cautious with very large batches
            MAX_BATCH_SIZE = 30  # Maximum reasonable batch size
            
            if len(images) > MAX_BATCH_SIZE:
                logger.warning(f"Large batch detected ({len(images)} images). Splitting into smaller batches.")
                all_descriptions = []
                
                # Process in smaller batches
                for i in range(0, len(images), MAX_BATCH_SIZE):
                    batch = images[i:i+MAX_BATCH_SIZE]
                    logger.info(f"Processing batch {i//MAX_BATCH_SIZE + 1}/{(len(images) + MAX_BATCH_SIZE - 1)//MAX_BATCH_SIZE} with {len(batch)} images")
                    batch_descriptions = self._process_image_batch(batch)
                    all_descriptions.extend(batch_descriptions)
                    
                return all_descriptions
            else:
                # Process all images in a single batch
                return self._process_image_batch(images)
                
        except Exception as e:
            logger.error(f"Error generating batch image descriptions: {str(e)}")
            # Return error messages for all images
            return [f"[Image description error: {str(e)[:100]}...]" for _ in range(len(images))]
            
    def _process_image_batch(self, images: List[Dict[str, Any]]) -> List[str]:
        """Process a batch of images in a single API call"""
        # Extract base64 content from all images
        image_contents = []
        for img in images:
            image_data = img["image_data"]
            # If the data URL format is correct, extract the base64 content
            if image_data.startswith('data:image/'):
                base64_content = image_data.split(',', 1)[1]
            else:
                base64_content = image_data
            
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_content}",
                    "detail": "low"  # Use low detail as specified to reduce token usage
                }
            })
        
        # Create message content with text and all images
        message_content = [
            {
                "type": "text",
                "text": f"Describe each of these {len(images)} images briefly in 1-2 complete sentences. Provide a separate description for each image, numbered from 1 to {len(images)}. Just use simple numbers like '1.' without adding the word 'Image'. Focus on the general content without excessive detail. Make sure each description is complete and not cut off."
            }
        ]
        message_content.extend(image_contents)
        
        # Call the OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Using smaller, more efficient model
            messages=[
                {
                    "role": "user",
                    "content": message_content
                }
            ],
            max_tokens=150 * len(images)  # Increase max tokens to prevent truncation
        )
        
        # Get the response and parse descriptions
        response_content = response.choices[0].message.content
        
        # Parse the descriptions using more advanced parsing
        descriptions = self._parse_numbered_descriptions(response_content, len(images))
        
        # Clean up descriptions - remove any markdown formatting or prefixes
        cleaned_descriptions = []
        for desc in descriptions:
            # Remove markdown formatting (bold, italics)
            clean_desc = desc.replace('**', '').replace('*', '')
            
            # Remove any "Image X:" prefixes that might have been added
            clean_desc = re.sub(r'^(Image\s+\d+[:.]\s*)', '', clean_desc, flags=re.IGNORECASE)
            
            # Make sure the first letter is capitalized
            if clean_desc and len(clean_desc) > 0:
                clean_desc = clean_desc[0].upper() + clean_desc[1:]
                
            cleaned_descriptions.append(clean_desc)
        
        logger.info(f"Generated {len(cleaned_descriptions)} image descriptions in a single API call")
        return cleaned_descriptions
        
    def _parse_numbered_descriptions(self, text: str, expected_count: int) -> List[str]:
        """Parse numbered descriptions from text with multiple fallback strategies"""
        # Strategy 1: Look for numbered lines with specific formats
        patterns = [
            r'(?:^|\n)\s*(\d+)[:.]\s*(.*?)(?=(?:\n\s*\d+[:.]\s*)|$)',  # "1: description" or "1. description"
            r'(?:^|\n)\s*Image\s*(\d+)[:.]\s*(.*?)(?=(?:\n\s*Image\s*\d+[:.]\s*)|$)',  # "Image 1: description"
            r'(?:^|\n)\s*Image\s*#(\d+)[:.]\s*(.*?)(?=(?:\n\s*Image\s*#\d+[:.]\s*)|$)',  # "Image #1: description"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                # Check if numbers are sequential and match expected count
                descriptions = [None] * expected_count
                has_all_numbers = True
                
                for num_str, desc in matches:
                    try:
                        index = int(num_str) - 1  # Convert to 0-based index
                        if 0 <= index < expected_count:
                            descriptions[index] = desc.strip()
                        else:
                            has_all_numbers = False
                            break
                    except ValueError:
                        has_all_numbers = False
                        break
                
                # If we have all descriptions, return them
                if has_all_numbers and all(d is not None for d in descriptions):
                    return descriptions
        
        # Strategy 2: Split by lines starting with numbers
        try:
            lines = text.split('\n')
            descriptions = []
            current_description = ""
            
            for line in lines:
                # Check if this is a new numbered line
                match = re.match(r'^\s*(\d+)[.:]', line)
                if match:
                    if current_description:
                        descriptions.append(current_description.strip())
                    current_description = re.sub(r'^\s*\d+[.:]', '', line).strip()
                else:
                    current_description += " " + line.strip()
            
            # Add the last description
            if current_description:
                descriptions.append(current_description.strip())
                
            # If we have the correct number, return them
            if len(descriptions) == expected_count:
                return descriptions
        except Exception:
            pass
        
        # Strategy 3: Simple paragraph splitting as fallback
        try:
            paragraphs = re.split(r'\n\s*\n', text)
            descriptions = [p.strip() for p in paragraphs if p.strip()]
            
            # If we have the correct number, return them
            if len(descriptions) == expected_count:
                return descriptions
        except Exception:
            pass
            
        # Final fallback: Just split content evenly
        logger.warning("All parsing strategies failed. Splitting content evenly.")
        total_chars = len(text)
        chars_per_image = total_chars // expected_count
        descriptions = [
            text[i*chars_per_image:(i+1)*chars_per_image].strip()
            for i in range(expected_count)
        ]
        
        return descriptions
