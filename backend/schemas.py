"""
Schema definitions for the PDF processing application.
"""

DEFAULT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A concise summary of the document's main content and purpose"
        },
        "key_points": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "A list of the most important points or takeaways from the document"
        },
        "insights": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Key insights, implications, or conclusions that can be drawn from the document"
        }
    },
    "required": ["summary", "key_points", "insights"]
}

DEFAULT_PROMPT = """
You are an expert document analyzer. Your task is to analyze the provided document content and extract the most important information.

The document content includes:
1. Extracted text from the PDF
2. Text extracted from images using OCR
3. Descriptions of images found in the document

Based on all this content, please provide:
- A concise but comprehensive summary of the document
- The key points or facts presented
- Important insights that can be drawn from the content

Consider the context of the document, including both textual content and information from images.
""" 