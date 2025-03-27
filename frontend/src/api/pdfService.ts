import axios from "axios";

// API Base URL - replace with your actual API URL when deployed
const API_BASE_URL = "http://localhost:8000";

export interface StructuredData {
  summary: string;
  key_points: string[];
  insights: string[];
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

    // Append optional prompt and schema
    if (customPrompt) {
      formData.append("custom_prompt", customPrompt);
    }

    if (customSchema) {
      formData.append("custom_schema", JSON.stringify(customSchema));
    }

    const response = await axios.post<ProcessPDFResponse>(
      `${API_BASE_URL}/api/process-pdf`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );

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
