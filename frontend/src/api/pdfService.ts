import axios from "axios";

// API Base URL - replace with your actual API URL when deployed
const API_BASE_URL = "http://localhost:8000";

export interface StructuredData {
  title?: string;
  summary?: string;
  key_points?: string[];
  insights_from_images?: string[];
  // Index signature for additional string fields
  [key: string]: string | string[] | undefined;
}

export interface ProcessPDFResponse {
  structured_data: StructuredData;
  images: {
    filename: string;
    page: number;
    ocr_text: string;
    image_data: string;
    width?: number;
    height?: number;
    source_pdf?: string;
  }[];
  pages: {
    filename: string;
    page: number;
    path: string;
    width?: number;
    height?: number;
    source_pdf?: string;
  }[];
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
    prompt?: string,
    schema?: object
  ): Promise<ProcessPDFResponse> {
    // Create form data
    const formData = new FormData();

    // Append all files
    files.forEach((file) => {
      formData.append("files", file);
    });

    // Append optional prompt and schema
    if (prompt) {
      formData.append("prompt", prompt);
    }

    if (schema) {
      formData.append("schema", JSON.stringify(schema));
    }

    const response = await axios.post<ProcessPDFResponse>(
      `${API_BASE_URL}/process-pdf`,
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
    const response = await axios.get<DefaultPromptResponse>(
      `${API_BASE_URL}/default-prompt`
    );
    return response.data.prompt;
  },

  /**
   * Get the default schema
   */
  async getDefaultSchema(): Promise<DefaultSchemaResponse> {
    const response = await axios.get<DefaultSchemaResponse>(
      `${API_BASE_URL}/default-schema`
    );
    return response.data;
  },
};
