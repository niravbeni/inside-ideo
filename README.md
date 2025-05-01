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
- Session management with automatic cleanup

## Architecture

This application consists of two main components:

### Backend (FastAPI + Python)

The backend provides a RESTful API for PDF processing, with the following functionality:
- PDF content extraction (text and images)
- OCR processing
- Content structuring with OpenAI
- File management and session handling
- Automatic cleanup of old sessions

### Frontend (Next.js + React)

The frontend provides a modern, responsive UI for interacting with the backend, featuring:
- Drag-and-drop file uploads
- Custom IDEO-inspired loading animations
- Results visualization
- Content copying and image downloading

## Tech Stack

### Backend (FastAPI + Python)

- **FastAPI** (v0.104.1): Modern API framework with automatic OpenAPI docs
- **PyMuPDF** (v1.23.7): PDF text and image extraction
- **OpenAI API** (v1.3.8): OCR and content structuring
- **Tesseract** (v0.3.10): Fallback OCR
- **Python-multipart**: Handling file uploads
- **Pillow** (v10.1.0): Image processing
- **Uvicorn** (v0.23.2): ASGI server
- **Pydantic** (v2.5.2): Data validation
- **Python-dotenv** (v1.0.0): Environment variable management
- **Gunicorn** (v21.2.0): Production WSGI server

### Frontend (Next.js + Shadcn UI)

- **Next.js** (v14.0.3): React framework
- **React** (v18.2.0): UI library
- **TypeScript** (v5.3.2): Type-safe JavaScript
- **Tailwind CSS** (v3.3.5): Utility-first CSS framework
- **Radix UI**: Headless UI components
- **React Dropzone** (v14.2.3): File upload component
- **Axios** (v1.6.2): HTTP client
- **Lucide-React** (v0.294.0): Icon set

## Key Components

### IdeoLoader

A custom loading animation inspired by IDEO's branding, featuring the letters I, D, E, O rotating in a square pattern with smooth animations. The loader supports three size options: small, medium, and large.

### IdeoLoaderCursor

A cursor version of the IdeoLoader that follows the mouse during loading states, providing a consistent and branded loading experience throughout the application.

### PDF Processing Pipeline

1. **Upload**: Users upload one or more PDF files
2. **Extraction**: The backend extracts text and images from the PDFs
3. **OCR**: Images are processed with OCR to extract text
4. **AI Processing**: Content is processed by OpenAI to generate structured data
5. **Results Display**: Structured content is displayed in the UI

## Setup and Installation

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
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at http://localhost:8000, with interactive docs at http://localhost:8000/docs

### Frontend Setup

1. Navigate to the frontend directory:

   ```
   cd frontend
   ```

2. Install dependencies:

   ```
   npm install
   ```

3. Configure the environment:

   Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Run the development server:

   ```
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. Upload one or more PDF files using the drag-and-drop area or file browser
2. Toggle options for OCR and OpenAI processing as needed
3. Click "Process PDFs" to extract and analyze the content
4. View the structured content in the results section
5. Navigate between different tabs to see various extracted information
6. Use the "Copy" buttons to copy text to your clipboard
7. Use the "Download" buttons to save extracted images

## API Endpoints

- `GET /` - Health check
- `POST /api/process-pdf` - Process uploaded PDF files
- `GET /api/schema` - Get the default output schema
- `GET /api/prompt` - Get the default prompt
- `GET /api/images/{session_id}/{filename}` - Get extracted images
- `GET /api/pages/{session_id}/{filename}` - Get extracted page images

## Deployment

This application is configured for deployment on Render.com using the included `render.yaml` file.

### Render Deployment

1. Create a Render account and connect your GitHub repository
2. Use the Blueprint feature to deploy from the `render.yaml` file
3. Set the required environment variables:
   - `OPENAI_API_KEY` for the backend
   - `NEXT_PUBLIC_API_URL` for the frontend (pointing to your deployed backend URL)

### Manual Deployment

#### Backend

1. Set up a Python environment with Python 3.11
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `MAX_IMAGES`: Maximum number of images to process (default: 60)
4. Start the server: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Frontend

1. Set up a Node.js 18.17.0 environment
2. Install dependencies: `npm install`
3. Build the app: `npm run build`
4. Configure environment variables:
   - `NEXT_PUBLIC_API_URL`: URL of your backend API
5. Start the server: `npm start`

## Customization

### OpenAI Integration

You can customize the OpenAI processing by modifying:

1. **Prompts**: Change the instructions sent to OpenAI by editing the default prompt or providing a custom prompt in the UI
2. **Schema**: Modify the output structure by editing the default schema or providing a custom schema in the UI
3. **Model**: Change the OpenAI model used by editing the `openai_api.py` file

### UI Customization

The frontend uses Tailwind CSS and Radix UI components, which can be customized by:

1. Modifying the `tailwind.config.js` file for theme changes
2. Editing the UI components in the `src/components` directory

## Maintenance

The application includes automatic maintenance features:

- Old sessions are automatically cleaned up after 24 hours
- Background tasks handle cleanup to avoid resource exhaustion

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Ensure your API key is valid and has sufficient credits
2. **PDF Extraction Issues**: Some PDFs may not extract properly if they are scanned or contain complex layouts
3. **CORS Errors**: If testing across different domains, ensure CORS is properly configured

### Debug Mode

Enable debug mode by setting the logging level to DEBUG in the backend:

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

## License

MIT
