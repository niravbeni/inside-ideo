# Inside IDEO

A modern PDF processing tool with custom IDEO-inspired loader animations. This application allows users to extract text and images from PDFs, perform OCR, and structure content using OpenAI's GPT models.

## Features

- Custom IDEO-inspired loading animations
- PDF text and image extraction
- OpenAI integration for content processing
- Responsive UI built with Next.js and Tailwind CSS

## Key Components

### IdeoLoader

A custom loading animation inspired by IDEO's branding, featuring the letters I, D, E, O rotating in a square pattern with smooth animations. The loader supports three size options: small, medium, and large.

### IdeoLoaderCursor

A cursor version of the IdeoLoader that follows the mouse during loading states, providing a consistent and branded loading experience throughout the application.

### PDF Processing

The application extracts text and images from PDF files, processes them through OpenAI's GPT models, and returns structured data that can be easily displayed and interacted with.