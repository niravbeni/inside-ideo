# Inside IDEO

A modern PDF processing tool with custom IDEO-inspired loader animations. This application allows users to extract text and images from PDFs, perform OCR, and structure content using OpenAI's GPT models.

## Features

- Custom IDEO-inspired loading animations
- PDF text and image extraction
- OpenAI integration for content processing
- Responsive UI built with Next.js and Tailwind CSS
- Upload one or multiple PDF files
- Perform OCR on images using OpenAI Vision API or Tesseract
- Process content with OpenAI to return structured data
- Copy text fields to clipboard
- Download extracted images

## Key Components

### IdeoLoader

A custom loading animation inspired by IDEO's branding, featuring the letters I, D, E, O rotating in a square pattern with smooth animations. The loader supports three size options: small, medium, and large.

### IdeoLoaderCursor

A cursor version of the IdeoLoader that follows the mouse during loading states, providing a consistent and branded loading experience throughout the application.

### PDF Processing

The application extracts text and images from PDF files, processes them through OpenAI's GPT models, and returns structured data that can be easily displayed and interacted with.

## Tech Stack

### Backend (FastAPI + Python)

- FastAPI for the API framework
- PyMuPDF for PDF text and image extraction
- OpenAI API for OCR and content structuring
- Tesseract (as fallback OCR)
- Python-multipart for handling file uploads

### Frontend (Next.js + Shadcn UI)

- Next.js for the frontend framework
- Shadcn UI (built on Radix UI and Tailwind CSS)
- React Dropzone for file uploads
- Axios for API calls

## Setup

### Backend Setup

1. Navigate to the backend directory:

   ```
   cd backend
   ```

2. Create a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and add your OpenAI API key:

   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. Run the FastAPI server:
   ```
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```
   cd frontend
   ```

2. Install dependencies:

   ```
   npm install
   ```

3. Run the development server:

   ```
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. Upload one or more PDF files using the drag-and-drop area or file browser
2. Click "Process PDFs" to extract and analyze the content
3. View the structured content and extracted images
4. Use the "Copy" buttons to copy text to your clipboard
5. Use the "Download" buttons to save extracted images

## API Endpoints

- `GET /` - Health check
- `POST /process-pdf` - Process uploaded PDF files
- `GET /default-schema` - Get the default output schema
- `GET /default-prompt` - Get the default prompt

## Customization

You can customize the output structure by modifying:

- The prompt sent to OpenAI (in `openai_api.py`)
- The output schema (in `openai_api.py`)

## License

MIT
