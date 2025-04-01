import axios from "axios";

// API Base URL - use environment variable or fallback to localhost for development
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StructuredData {
  summary?: string;
  key_points?: string[];
  insights?: string[];
  // Case Study fields
  case_study_client?: string;
  case_study_title?: string;
  case_study_tagline?: string;
  case_study_challenge?: string;
  case_study_design?: string;
  case_study_impact?: string;
  // Index signature for additional string fields
  [key: string]: string | string[] | undefined;
}

export interface ImageData {
  filename: string;
  page: number;
  ocr_text: string;
  image_description?: string;
  image_data: string;
  width?: number;
  height?: number;
  pdf_index?: number;
  image_id?: string;
}

export interface PageData {
  filename: string;
  page: number;
  path: string;
  image_data?: string;
  width?: number;
  height?: number;
  pdf_index?: number;
}

export interface ProcessPDFResponse {
  session_id: string;
  extraction: {
    text: string;
    images: ImageData[];
    pages: PageData[];
  };
  ai_analysis: StructuredData;
  processing_time: {
    extraction: number;
    ocr: number;
    openai: number;
    total: number;
  };
}

export interface DefaultPromptResponse {
  prompt: string;
}

export interface DefaultSchemaResponse {
  title: string;
  summary: string;
  key_points: string[];
  insights_from_images: string[];
}

// Utility function to check if an image is meaningful
const isNonMeaningfulImage = (image: ImageData): boolean => {
  // If no description is available, consider it non-meaningful
  if (!image.image_description) return true;

  const description = image.image_description.toLowerCase();

  // Check if the description indicates a missing or failed description
  if (
    description.includes("description for image") ||
    description.includes("not found")
  ) {
    return true;
  }

  // Immediate rejections for clearly non-meaningful images
  if (
    description.includes("blank canvas") ||
    description.includes("blank space") ||
    description.includes("representing minimalism") ||
    (description.includes("simple") && description.includes("shape")) ||
    (description.includes("white") && description.includes("background"))
  ) {
    return true;
  }

  // List of patterns that indicate decorative or non-meaningful images
  const nonMeaningfulPatterns = [
    "blank",
    "empty",
    "white canvas",
    "canvas",
    "speech bubble",
    "background",
    "decorative",
    "geometric",
    "space",
    "white space",
    "minimalist",
    "minimal",
    "triangular",
    "triangle",
    "rectangular",
    "rectangle",
    "shape",
    "design element",
    "prototype",
    "reserved",
    "placeholder",
    "area",
    "indicating",
    "potential for",
    "future design",
    "eye shape",
    "simple",
    "basic",
    "representing",
  ];

  // Check for multiple patterns in the same description
  const patternMatches = nonMeaningfulPatterns.filter((pattern) =>
    description.includes(pattern)
  );

  // If we match 2 or more patterns, it's likely decorative
  if (patternMatches.length >= 2) {
    // But check for meaningful overrides first
    const meaningfulOverrides = [
      description.includes("chart") && description.includes("data"),
      description.includes("diagram") && description.includes("showing"),
      description.includes("graph") && description.includes("data"),
      description.includes("illustration") && description.includes("detailed"),
      description.includes("screenshot") || description.includes("photo"),
      description.includes("drawing") && description.includes("person"),
      description.includes("hand") && description.includes("holding"),
    ];

    return !meaningfulOverrides.some(Boolean);
  }

  // For single pattern matches, check if it's a standalone decorative term
  const standaloneDecorative = [
    "blank canvas",
    "white space",
    "empty space",
    "simple shape",
    "basic shape",
    "geometric shape",
    "design element",
    "placeholder",
    "minimalist",
  ];

  return standaloneDecorative.some((term) => description.includes(term));
};

// Utility function to generate a content hash for an image
const generateImageHash = (imageData: string): string => {
  // Simple hash function for demo - in production use a proper hashing algorithm
  return imageData.slice(0, 32); // Take first 32 chars of base64 as simple hash
};

// Utility function to validate image-description matching
const validateImageDescriptionMatch = (image: ImageData): boolean => {
  if (!image.image_id) {
    return false;
  }

  // Basic validation - ensure we have an image and description
  return Boolean(image.image_data && image.image_description);
};

// Utility function to validate and clean image data
const validateImageData = (image: ImageData): boolean => {
  // Basic required fields check
  if (!image.filename || !image.image_data) {
    return false;
  }

  // Ensure page number exists and is valid
  if (typeof image.page !== "number" || image.page < 0) {
    return false;
  }

  // Basic description validation
  if (
    !image.image_description ||
    image.image_description.trim().length === 0 ||
    image.image_description.toLowerCase().includes("not found") ||
    image.image_description.toLowerCase().includes("description for image")
  ) {
    return false;
  }

  return validateImageDescriptionMatch(image);
};

export const pdfService = {
  /**
   * Process PDF files and extract content
   */
  async processPDF(
    files: File[],
    customPrompt?: string,
    customSchema?: object
  ): Promise<ProcessPDFResponse> {
    // Create form data
    const formData = new FormData();

    // Append all files
    files.forEach((file) => {
      formData.append("files", file);
    });

    // Append settings
    formData.append("use_ocr", "true");
    formData.append("use_openai", "true");
    formData.append("generate_image_ids", "true");

    if (customPrompt) {
      formData.append("custom_prompt", customPrompt);
    }

    if (customSchema) {
      formData.append("custom_schema", JSON.stringify(customSchema));
    }

    // Get the response from API
    const response = await axios.post<ProcessPDFResponse>(
      `${API_BASE_URL}/api/process-pdf`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

    // Filter out non-meaningful images and clean up displayed text
    const meaningfulImages = response.data.extraction.images
      .filter((image) => {
        // Skip images with no data or description
        if (!image.image_data || !image.image_description) return false;

        // Keep only meaningful images for AI analysis
        return !isNonMeaningfulImage(image);
      })
      .map((image) => {
        // Store the original data for AI processing but hide it from display
        return {
          ...image,
          // These fields are preserved internally for AI processing but not displayed
          _image_description_for_ai: image.image_description,
          _ocr_text_for_ai: image.ocr_text,
          // Clear the visible fields that would be displayed
          image_description: undefined,
          ocr_text: "", // Empty string to prevent OCR text from displaying
        };
      })
      .sort((a, b) => {
        // Sort by page number
        if (a.page !== b.page) return a.page - b.page;

        // Then by position within page if available
        if (a.pdf_index !== undefined && b.pdf_index !== undefined) {
          return a.pdf_index - b.pdf_index;
        }

        return 0;
      });

    // Update the response with filtered images
    response.data.extraction.images = meaningfulImages;

    return response.data;
  },

  /**
   * Get the default prompt
   */
  async getDefaultPrompt(): Promise<string> {
    const response = await axios.get<string>(`${API_BASE_URL}/api/prompt`);
    return response.data;
  },

  /**
   * Get the default schema
   */
  async getDefaultSchema(): Promise<object> {
    const response = await axios.get<object>(`${API_BASE_URL}/api/schema`);
    return response.data;
  },
};
