"""
Schema definitions for the PDF processing application.
"""

DEFAULT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "A concise summary of the client project, its objectives, and delivered outcomes"
        },
        "key_points": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Key deliverables, solutions, and outcomes achieved for the client"
        },
        "insights": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Project insights including design decisions, client impact, and broader implications for future work"
        }
    },
    "required": ["summary", "key_points", "insights"]
}

DEFAULT_PROMPT = """
You are analyzing a case study of an IDEO client project. Your task is to extract the key information about the project, its execution, and outcomes.

The case study content includes:
1. Extracted text from the PDF
2. Text extracted from images using OCR
3. Descriptions of images from the case study

Based on all this content, please provide:
- A concise but comprehensive summary of the client project, including the challenge, approach, and key outcomes
- The key deliverables and solutions implemented for the client, highlighting specific impacts and results
- Project insights that include:
  * Key design decisions and their impact on the project success
  * Client-specific outcomes and value delivered
  * Broader implications and learnings for future client work

Focus on the concrete project outcomes, client impact, and the specific solutions developed through the design process.
""" 