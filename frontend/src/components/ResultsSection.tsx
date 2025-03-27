import React, { useState, useEffect, useCallback } from "react";
import {
  Download,
  FileText,
  Image as ImageIcon,
  Clock,
  Loader2,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { CopyButton } from "@/components/CopyButton";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { StructuredData } from "@/api/pdfService";
import Image from "next/image";
import IdeoLoader from "./IdeoLoader";

interface ImageData {
  filename: string;
  page: number;
  ocr_text: string;
  image_data: string;
  width?: number;
  height?: number;
  source_pdf?: string;
}

interface PageData {
  filename: string;
  page: number;
  path: string;
  image_data?: string;
  width?: number;
  height?: number;
  source_pdf?: string;
}

interface ResultsSectionProps {
  structuredData: StructuredData | null;
  images: ImageData[];
  pages?: PageData[];
  isLoading: boolean;
  processingStep?: {
    step: number;
    message: string;
  };
}

export function ResultsSection({
  structuredData,
  images,
  pages = [],
  isLoading,
  processingStep = { step: 0, message: "" },
}: ResultsSectionProps) {
  const [activeTab, setActiveTab] = useState("structured");
  const [processedPages, setProcessedPages] = useState<PageData[]>([]);
  const [loadingPages, setLoadingPages] = useState<Record<number, boolean>>({});

  // Convert path to image_data on init
  useEffect(() => {
    if (pages && pages.length > 0) {
      // Initialize all pages
      const pagesCopy = pages.map((page) => ({
        ...page,
        isLoading: false,
      }));

      setProcessedPages(pagesCopy);
    } else {
      setProcessedPages([]);
    }
  }, [pages]);

  // Create a memoized version of loadVisiblePages
  const loadVisiblePages = useCallback(() => {
    // Find pages that need loading
    const pagesToLoad = processedPages
      .map((page, index) => ({ page, index }))
      .filter(({ page }) => !page.image_data && page.path);

    // Only load a few at a time
    const batchSize = 3;
    const batch = pagesToLoad.slice(0, batchSize);

    // Mark pages as loading
    const newLoadingState: Record<number, boolean> = {};
    batch.forEach(({ index }) => {
      newLoadingState[index] = true;
    });
    setLoadingPages({ ...loadingPages, ...newLoadingState });

    // Load each page in the batch
    batch.forEach(({ page, index }) => {
      fetchPageImage(page.path, index).finally(() => {
        // Remove from loading state when done
        setLoadingPages((prev) => {
          const updated = { ...prev };
          delete updated[index];
          return updated;
        });
      });
    });
  }, [processedPages, loadingPages]);

  // Batch fetch images when pages tab is active
  useEffect(() => {
    if (activeTab === "pages") {
      // Load pages in batches to avoid overwhelming the browser
      loadVisiblePages();
    }
  }, [activeTab, loadVisiblePages]);

  // Call this when a batch is finished loading
  useEffect(() => {
    // If we're on pages tab and there are no pages currently loading
    if (activeTab === "pages" && Object.keys(loadingPages).length === 0) {
      // Check if there are any pages still needing to be loaded
      const hasUnloadedPages = processedPages.some(
        (page) => !page.image_data && page.path
      );

      if (hasUnloadedPages) {
        // Load the next batch after a short delay
        const timer = setTimeout(() => {
          loadVisiblePages();
        }, 100);

        return () => clearTimeout(timer);
      }
    }
  }, [activeTab, loadingPages, processedPages, loadVisiblePages]);

  if (isLoading) {
    const step1Complete = processingStep.step > 1;
    const step2Complete = processingStep.step > 2;
    const step3Complete = processingStep.step > 3;

    const step1Active = processingStep.step === 1;
    const step2Active = processingStep.step === 2;
    const step3Active = processingStep.step === 3;

    return (
      <div className="w-full py-12 flex flex-col items-center justify-center">
        <div className="w-full max-w-lg p-6 bg-background border rounded-lg shadow-sm">
          <div className="flex flex-col items-center space-y-6">
            {/* <Loader2 className="h-12 w-12 text-primary animate-spin" /> */}
            <div className="w-16 h-16 relative flex items-center justify-center">
              <IdeoLoader size="medium" />
            </div>
            <h3 className="text-xl font-semibold text-center">
              Processing PDF
            </h3>

            <div className="w-full space-y-4">
              <div className="flex items-center space-x-3">
                <FileText
                  className={`h-5 w-5 ${
                    step1Complete
                      ? "text-primary"
                      : step1Active
                      ? "text-primary"
                      : "text-muted-foreground"
                  }`}
                />
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">Extracting text</span>
                    <span className="text-sm text-muted-foreground">
                      Step 1/3
                    </span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        step1Complete
                          ? "bg-primary"
                          : step1Active
                          ? "bg-primary animate-pulse"
                          : "bg-muted-foreground"
                      } rounded-full`}
                      style={{
                        width: step1Complete
                          ? "100%"
                          : step1Active
                          ? "75%"
                          : "0%",
                      }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <ImageIcon
                  className={`h-5 w-5 ${
                    step2Complete
                      ? "text-primary"
                      : step2Active
                      ? "text-primary"
                      : "text-muted-foreground"
                  }`}
                />
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">Finding images</span>
                    <span className="text-sm text-muted-foreground">
                      Step 2/3
                    </span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        step2Complete
                          ? "bg-primary"
                          : step2Active
                          ? "bg-primary animate-pulse"
                          : "bg-muted-foreground"
                      } rounded-full`}
                      style={{
                        width: step2Complete
                          ? "100%"
                          : step2Active
                          ? "65%"
                          : "0%",
                      }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <Clock
                  className={`h-5 w-5 ${
                    step3Complete
                      ? "text-primary"
                      : step3Active
                      ? "text-primary"
                      : "text-muted-foreground"
                  }`}
                />
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">
                      Processing Images
                    </span>
                    <span className="text-sm text-muted-foreground">
                      Step 3/3
                    </span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${
                        step3Complete
                          ? "bg-primary"
                          : step3Active
                          ? "bg-primary animate-pulse"
                          : "bg-muted-foreground"
                      } rounded-full`}
                      style={{
                        width: step3Complete
                          ? "100%"
                          : step3Active
                          ? "40%"
                          : "0%",
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            <p className="text-sm text-muted-foreground text-center">
              {processingStep.message ||
                "This may take a minute or two depending on the size and complexity of your document."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!structuredData && images.length === 0 && pages.length === 0) {
    return null;
  }

  const downloadImage = (imageData: string, filename: string) => {
    const link = document.createElement("a");
    link.href = imageData;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const fetchPageImage = async (path: string, pageIndex: number) => {
    try {
      // Extract only the filename from the path to use with the mounted static directory
      const filename = path.split("/").pop() || "";
      const response = await fetch(`http://localhost:8000/pages/${filename}`);

      if (!response.ok) {
        throw new Error(
          `Failed to fetch image: ${response.status} ${response.statusText}`
        );
      }

      const blob = await response.blob();
      const reader = new FileReader();
      return new Promise<void>((resolve, reject) => {
        reader.onload = () => {
          if (reader.result && typeof reader.result === "string") {
            // Create a new array with the updated page
            setProcessedPages((prevPages) => {
              const updatedPages = [...prevPages];
              updatedPages[pageIndex] = {
                ...updatedPages[pageIndex],
                image_data: reader.result as string,
              };
              return updatedPages;
            });
            resolve();
          } else {
            reject(new Error("Failed to read image data"));
          }
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    } catch (error) {
      console.error("Error fetching page image:", error);
      throw error;
    }
  };

  return (
    <div className="w-full space-y-8 mt-8">
      <Tabs
        defaultValue="structured"
        className="w-full"
        value={activeTab}
        onValueChange={setActiveTab}
      >
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="structured">Structured Data</TabsTrigger>
          <TabsTrigger value="images">
            Meaningful Images ({images.length})
          </TabsTrigger>
          <TabsTrigger value="pages">
            PDF Pages ({processedPages.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="structured">
          {structuredData && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">Extracted Content</h2>

              <div className="space-y-4">
                {structuredData.title && (
                  <div>
                    <label
                      htmlFor="title"
                      className="block text-sm font-medium mb-1"
                    >
                      Title
                    </label>
                    <div className="flex space-x-2">
                      <Input
                        id="title"
                        value={structuredData.title}
                        readOnly
                        className="flex-1"
                      />
                      <CopyButton text={structuredData.title} />
                    </div>
                  </div>
                )}

                {structuredData.summary && (
                  <div>
                    <label
                      htmlFor="summary"
                      className="block text-sm font-medium mb-1"
                    >
                      Summary
                    </label>
                    <div className="flex space-x-2">
                      <Textarea
                        id="summary"
                        value={structuredData.summary}
                        readOnly
                        rows={4}
                        className="flex-1"
                      />
                      <CopyButton
                        text={structuredData.summary}
                        className="self-start"
                      />
                    </div>
                  </div>
                )}

                {structuredData.key_points &&
                  structuredData.key_points.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Key Points
                      </label>
                      <ul className="space-y-2">
                        {structuredData.key_points.map((point, index) => (
                          <li key={index} className="flex space-x-2">
                            <Input value={point} readOnly className="flex-1" />
                            <CopyButton text={point} />
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                {structuredData.insights_from_images &&
                  structuredData.insights_from_images.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Insights from Images
                      </label>
                      <ul className="space-y-2">
                        {structuredData.insights_from_images.map(
                          (insight, index) => (
                            <li key={index} className="flex space-x-2">
                              <Input
                                value={insight}
                                readOnly
                                className="flex-1"
                              />
                              <CopyButton text={insight} />
                            </li>
                          )
                        )}
                      </ul>
                    </div>
                  )}

                {/* Render any additional fields from the schema */}
                {Object.entries(structuredData).map(([key, value]) => {
                  // Skip the fields we've already rendered
                  if (
                    [
                      "title",
                      "summary",
                      "key_points",
                      "insights_from_images",
                    ].includes(key)
                  ) {
                    return null;
                  }

                  // Render arrays
                  if (Array.isArray(value) && value.length > 0) {
                    return (
                      <div key={key}>
                        <label className="block text-sm font-medium mb-1 capitalize">
                          {key.replace(/_/g, " ")}
                        </label>
                        <ul className="space-y-2">
                          {value.map((item, index) => (
                            <li key={index} className="flex space-x-2">
                              <Input value={item} readOnly className="flex-1" />
                              <CopyButton text={item} />
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  }

                  // Render string values
                  if (typeof value === "string" && value.trim() !== "") {
                    return (
                      <div key={key}>
                        <label
                          htmlFor={key}
                          className="block text-sm font-medium mb-1 capitalize"
                        >
                          {key.replace(/_/g, " ")}
                        </label>
                        <div className="flex space-x-2">
                          <Input
                            id={key}
                            value={value}
                            readOnly
                            className="flex-1"
                          />
                          <CopyButton text={value} />
                        </div>
                      </div>
                    );
                  }

                  return null;
                })}
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="images">
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Meaningful Images</h2>
            {images.length === 0 ? (
              <p className="text-muted-foreground">
                No meaningful images were found in the document.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {images.map((image, index) => (
                  <Card key={index} className="overflow-hidden">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">
                        Image {index + 1} - Page {image.page}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="relative aspect-video overflow-hidden bg-muted flex items-center justify-center">
                        <Image
                          src={image.image_data}
                          alt={`Extracted image ${index + 1}`}
                          className="object-contain"
                          fill
                          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                        />
                      </div>
                    </CardContent>
                    <CardFooter className="flex justify-between pt-4">
                      <div className="text-sm text-muted-foreground truncate max-w-[180px]">
                        {image.width && image.height
                          ? `${image.width}×${image.height}`
                          : image.filename}
                      </div>
                      <Button
                        size="sm"
                        onClick={() =>
                          downloadImage(image.image_data, image.filename)
                        }
                      >
                        <Download className="h-4 w-4 mr-1" /> Download
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="pages">
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">PDF Pages</h2>
            {processedPages.length === 0 ? (
              <p className="text-muted-foreground">
                No page images were extracted from the document.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4">
                {processedPages.map((page, index) => (
                  <Card key={index} className="overflow-hidden">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-base">
                        Page {page.page}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="relative aspect-auto overflow-hidden bg-muted flex items-center justify-center">
                        {page.image_data ? (
                          <Image
                            src={page.image_data}
                            alt={`Page ${page.page}`}
                            className="object-contain"
                            fill
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw"
                            loading="lazy"
                          />
                        ) : (
                          <div className="p-10 text-center text-muted-foreground flex flex-col items-center justify-center">
                            {loadingPages[index] ? (
                              <>
                                <Loader2 className="h-8 w-8 mb-2 animate-spin text-primary" />
                                <p>Loading page...</p>
                              </>
                            ) : (
                              <Button
                                variant="outline"
                                onClick={() => {
                                  setLoadingPages((prev) => ({
                                    ...prev,
                                    [index]: true,
                                  }));
                                  fetchPageImage(page.path, index).finally(
                                    () => {
                                      setLoadingPages((prev) => {
                                        const updated = { ...prev };
                                        delete updated[index];
                                        return updated;
                                      });
                                    }
                                  );
                                }}
                              >
                                Load Page
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    </CardContent>
                    <CardFooter className="flex justify-between pt-4">
                      <div className="text-sm text-muted-foreground truncate max-w-[180px]">
                        {page.width && page.height
                          ? `${page.width}×${page.height}`
                          : page.filename}
                      </div>
                      {page.image_data && (
                        <Button
                          size="sm"
                          onClick={() => {
                            if (page.image_data) {
                              downloadImage(
                                page.image_data,
                                `page_${page.page}.png`
                              );
                            }
                          }}
                        >
                          <Download className="h-4 w-4 mr-1" /> Download
                        </Button>
                      )}
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
