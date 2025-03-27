import React, { useState } from "react";
import Head from "next/head";
import { UploadSection } from "@/components/UploadSection";
import { ResultsSection } from "@/components/ResultsSection";
import { pdfService, ProcessPDFResponse } from "@/api/pdfService";
// import IdeoLoaderCursor from "@/components/IdeoLoaderCursor";

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [processedResult, setProcessedResult] =
    useState<ProcessPDFResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processingProgress, setProcessingProgress] = useState({
    step: 0,
    message: "",
  });

  const handleFilesSelected = (selectedFiles: File[]) => {
    setFiles(selectedFiles);
    // Reset results when new files are selected
    setProcessedResult(null);
    setError(null);
  };

  const handleSubmit = async () => {
    if (files.length === 0) {
      setError("Please select at least one PDF file to process");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // Process the PDF - this kicks off the actual processing
      const processingPromise = pdfService.processPDF(files);

      // Update the processing message as we go
      setProcessingProgress({
        step: 1,
        message: "Extracting text from document",
      });

      // Continue showing progress messages while processing
      await new Promise((resolve) => setTimeout(resolve, 2000));

      setProcessingProgress({
        step: 2,
        message: "Identifying images in document",
      });

      await new Promise((resolve) => setTimeout(resolve, 2000));

      setProcessingProgress({
        step: 3,
        message: "Processing images and analyzing content",
      });

      // Prepare to show final analysis message
      let finalPromiseResolved = false;

      // Set up an interval that will check when the API call finishes
      const checkInterval = setInterval(() => {
        if (finalPromiseResolved) {
          clearInterval(checkInterval);
        }
      }, 500);

      // Wait for the results from the API
      const result = await processingPromise;
      finalPromiseResolved = true;

      // Show completion state briefly before showing results
      await new Promise((resolve) => setTimeout(resolve, 800));

      setProcessedResult(result);
    } catch (err) {
      console.error("Error processing PDFs:", err);
      setError(
        err instanceof Error
          ? err.message
          : "An error occurred while processing the PDFs"
      );
    } finally {
      setIsLoading(false);
      // Reset progress
      setProcessingProgress({ step: 0, message: "" });
    }
  };

  return (
    <>
      <Head>
        <title>PDF Extraction + LLM Structuring</title>
        <meta
          name="description"
          content="Extract and structure content from PDFs using AI"
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* <IdeoLoaderCursor isLoading={isLoading} /> */}

      <main className="min-h-screen bg-background">
        <div className="container py-10">
          <header className="mb-10 text-center">
            <h1 className="text-4xl font-bold mb-2">
              Case Study Documentation Tool
            </h1>
            <p className="text-muted-foreground text-lg">
              Extract text and images from PDFs and convert them into structured
              outputs for documentation.
            </p>
          </header>

          <div className="max-w-4xl mx-auto">
            <div className="mb-8">
              <UploadSection
                onFilesSelected={handleFilesSelected}
                isLoading={isLoading}
              />

              {error && (
                <div className="mt-4 p-3 bg-destructive/10 border border-destructive rounded-md text-destructive text-sm">
                  {error}
                </div>
              )}

              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleSubmit}
                  disabled={isLoading || files.length === 0}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-2 rounded-md font-medium disabled:opacity-50 disabled:pointer-events-none"
                >
                  {isLoading ? "Processing" : "Process PDFs"}
                </button>
              </div>
            </div>

            <ResultsSection
              structuredData={processedResult?.structured_data || null}
              images={processedResult?.images || []}
              pages={processedResult?.pages || []}
              isLoading={isLoading}
              processingStep={processingProgress}
            />
          </div>
        </div>
      </main>
    </>
  );
}
