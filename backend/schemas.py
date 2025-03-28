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
        },
        "inside_ideo_client": {
            "type": "string",
            "description": "The name of the client organization"
        },
        "inside_ideo_title": {
            "type": "string",
            "description": "A compelling title that encapsulates the main focus or goal of the project"
        },
        "inside_ideo_tagline": {
            "type": "string",
            "description": "A tagline that provides additional context or emotional resonance to the project"
        },
        "inside_ideo_challenge": {
            "type": "string",
            "description": "A detailed description of the primary issue or problem that the organization faced"
        },
        "inside_ideo_design": {
            "type": "string",
            "description": "A comprehensive description of the approach taken to solve the challenge, including design strategies and methods"
        },
        "inside_ideo_impact": {
            "type": "string",
            "description": "The concrete results and measurable impact of the design efforts"
        }
    },
    "required": ["summary", "key_points", "insights", "inside_ideo_client", "inside_ideo_title", "inside_ideo_tagline", "inside_ideo_challenge", "inside_ideo_design", "inside_ideo_impact"]
}

DEFAULT_PROMPT = """
You are analyzing a case study of an IDEO client project. Your task is to extract key information and structure it in two formats: a PDF summary and an Inside IDEO case study.

The case study content includes:
1. Extracted text from the PDF
2. Text extracted from images using OCR
3. Descriptions of images from the case study

Based on all this content, please provide:
1. PDF Summary:
   - A concise but comprehensive summary of the client project
   - Key deliverables and solutions implemented for the client
   - Project insights including design decisions and broader implications

2. Inside IDEO Structure:
   - Client: Identify the client organization name
   - Title: Create a compelling title that encapsulates the main focus/goal
   - Tagline: Create a phrase that provides additional context or emotional resonance
   - Challenge: Detail the primary issue or problem faced
   - Design/Work: Describe the approach, methods, and strategies used
   - Impact: Document concrete results and measurable outcomes

Focus on extracting factual information from the content - do not invent or embellish details.
Ensure all responses are based on explicit information from the provided content, maintaining accuracy and authenticity in the case study representation.
""" 