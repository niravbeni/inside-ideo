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
            "description": "A comprehensive description (3-5 paragraphs) of the business context, primary issues or problems the organization faced, market conditions, user needs, and the specific design challenge framed as a 'How might we' question. Include details about what was at stake for the client and why this challenge was significant."
        },
        "inside_ideo_design": {
            "type": "string",
            "description": "A detailed explanation (3-5 paragraphs) of the approach, methods, and strategies used to address the challenge. Include information about the design process, research conducted, prototyping techniques, key insights that shaped the solution, collaboration methods, and how the team iterated toward the final solution. Describe specific design interventions, tools developed, or frameworks created."
        },
        "inside_ideo_impact": {
            "type": "string",
            "description": "A thorough account (3-5 paragraphs) of the concrete results and measurable outcomes of the project. Include quantitative metrics when available (e.g., percentage increases, user numbers, revenue impact), qualitative feedback from stakeholders, how the solution transformed the client's business or user experience, and any ongoing effects or future implications of the work. Describe how the solution addressed the original challenge and any unexpected positive outcomes."
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
   - Challenge: Provide a detailed description (3-5 paragraphs) of the business context, primary issues faced, market conditions, user needs, and the specific challenge. Include what was at stake for the client and why this challenge was significant. If possible, frame part of the challenge as a "How might we" question.
   - Design/Work: Explain thoroughly (3-5 paragraphs) the approach, methods, and strategies used. Include information about the design process, research conducted, prototyping techniques, key insights, collaboration methods, and iteration toward the final solution. Describe specific design interventions, tools, or frameworks created.
   - Impact: Detail comprehensively (3-5 paragraphs) the concrete results and measurable outcomes. Include quantitative metrics when available, qualitative feedback from stakeholders, how the solution transformed the client's business or user experience, and any ongoing effects. Describe how the solution addressed the original challenge and any unexpected positive outcomes.

Focus on extracting factual information from the content - do not invent or embellish details.
Ensure all responses are based on explicit information from the provided content, maintaining accuracy and authenticity in the case study representation.
""" 