import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Download,
  FileText,
  Image as ImageIcon,
  Clock,
  Loader2,
  RefreshCcw,
  RotateCcw,
  Edit,
  Check,
  X,
  ChevronDown,
  ChevronUp,
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
import { EditableField } from "@/components/ui/EditableField";
import { EditableArrayField } from "@/components/ui/EditableArrayField";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StructuredData } from "@/api/pdfService";
import Image from "next/image";
import IdeoLoader from "./IdeoLoader";
import { cn } from "@/lib/utils";

interface ImageData {
  filename: string;
  page: number;
  ocr_text: string;
  image_data: string;
  image_description?: string;
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

interface EditableFieldProps {
  fieldId: string;
  label: string;
  value: string;
  isTextArea?: boolean;
  rows?: number;
  onChange: (value: string) => void;
  onFocus: (fieldId: string) => void;
  onBlur: () => void;
  onReset: () => void;
}

// Component to handle showing/hiding long image descriptions
function ImageDescription({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  // If text is short enough, just show it
  const isShort = text.length < 100;

  if (isShort) {
    return (
      <>
        <strong>Image Content:</strong> {text}
      </>
    );
  }

  return (
    <div>
      <strong>Image Content:</strong>{" "}
      {expanded ? text : text.substring(0, 100) + "..."}
      <button
        onClick={() => setExpanded(!expanded)}
        className="ml-1 text-primary inline-flex items-center"
      >
        {expanded ? (
          <>
            Show less <ChevronUp className="h-3 w-3 ml-1" />
          </>
        ) : (
          <>
            Show more <ChevronDown className="h-3 w-3 ml-1" />
          </>
        )}
      </button>
    </div>
  );
}

export function ResultsSection({
  structuredData,
  images,
  pages = [],
  isLoading,
  processingStep = { step: 0, message: "" },
}: ResultsSectionProps) {
  const [activeTab, setActiveTab] = useState("structured");
  const [activeStructuredTab, setActiveStructuredTab] = useState("summary");
  const [processedPages, setProcessedPages] = useState<PageData[]>([]);
  const [loadingPages, setLoadingPages] = useState<Record<number, boolean>>({});
  const [editableData, setEditableData] = useState<StructuredData | null>(null);
  const [originalData, setOriginalData] = useState<StructuredData | null>(null);

  const [focusedField, setFocusedField] = useState<string | null>(null);

  const titleRef = useRef<HTMLInputElement>(null);
  const summaryRef = useRef<HTMLTextAreaElement>(null);
  const keyPointsRef = useRef<HTMLTextAreaElement>(null);
  const insightsRef = useRef<HTMLTextAreaElement>(null);
  const otherFieldRefs = useRef<
    Record<string, HTMLInputElement | HTMLTextAreaElement | null>
  >({});

  const [rawKeyPoints, setRawKeyPoints] = useState<string>("");
  const [rawInsights, setRawInsights] = useState<string>("");

  // Add a state to track raw text values for other array fields
  const [otherRawFields, setOtherRawFields] = useState<Record<string, string>>(
    {}
  );

  useEffect(() => {
    if (structuredData) {
      setEditableData(JSON.parse(JSON.stringify(structuredData)));
      setOriginalData(JSON.parse(JSON.stringify(structuredData)));

      // Initialize raw text values
      if (structuredData.key_points) {
        setRawKeyPoints(structuredData.key_points.join("\n"));
      }
      if (structuredData.insights) {
        setRawInsights(structuredData.insights.join("\n"));
      }

      // Initialize other raw fields
      const newRawFields: Record<string, string> = {};
      Object.entries(structuredData).forEach(([key, value]) => {
        if (
          Array.isArray(value) &&
          value.length > 0 &&
          typeof value[0] === "string"
        ) {
          newRawFields[key] = value.join("\n");
        }
      });
      setOtherRawFields(newRawFields);
    }
  }, [structuredData]);

  useEffect(() => {
    if (pages && pages.length > 0) {
      const pagesCopy = pages.map((page) => ({
        ...page,
        isLoading: false,
      }));

      setProcessedPages(pagesCopy);
    } else {
      setProcessedPages([]);
    }
  }, [pages]);

  const loadVisiblePages = useCallback(() => {
    const pagesToLoad = processedPages
      .map((page, index) => ({ page, index }))
      .filter(({ page }) => !page.image_data && page.path);

    const batchSize = 3;
    const batch = pagesToLoad.slice(0, batchSize);

    const newLoadingState: Record<number, boolean> = {};
    batch.forEach(({ index }) => {
      newLoadingState[index] = true;
    });
    setLoadingPages({ ...loadingPages, ...newLoadingState });

    batch.forEach(({ page, index }) => {
      fetchPageImage(page.path, index).finally(() => {
        setLoadingPages((prev) => {
          const updated = { ...prev };
          delete updated[index];
          return updated;
        });
      });
    });
  }, [processedPages, loadingPages]);

  useEffect(() => {
    if (activeTab === "pages") {
      loadVisiblePages();
    }
  }, [activeTab, loadVisiblePages]);

  useEffect(() => {
    if (activeTab === "pages" && Object.keys(loadingPages).length === 0) {
      const hasUnloadedPages = processedPages.some(
        (page) => !page.image_data && page.path
      );

      if (hasUnloadedPages) {
        const timer = setTimeout(() => {
          loadVisiblePages();
        }, 100);

        return () => clearTimeout(timer);
      }
    }
  }, [activeTab, loadingPages, processedPages, loadVisiblePages]);

  const handleResetToOriginal = () => {
    if (originalData) {
      setEditableData(JSON.parse(JSON.stringify(originalData)));

      // Reset raw text values
      if (originalData.key_points) {
        setRawKeyPoints(originalData.key_points.join("\n"));
      }
      if (originalData.insights) {
        setRawInsights(originalData.insights.join("\n"));
      }

      // Reset other raw fields
      const newRawFields: Record<string, string> = {};
      Object.entries(originalData).forEach(([key, value]) => {
        if (
          Array.isArray(value) &&
          value.length > 0 &&
          typeof value[0] === "string"
        ) {
          newRawFields[key] = value.join("\n");
        }
      });
      setOtherRawFields(newRawFields);

      setFocusedField(null);
    }
  };

  const handleResetField = (field: string, index?: number) => {
    if (!originalData || !editableData) return;

    if (
      index !== undefined &&
      Array.isArray(originalData[field]) &&
      Array.isArray(editableData[field])
    ) {
      const newArray = [...editableData[field]];
      newArray[index] = originalData[field][index];

      setEditableData({
        ...editableData,
        [field]: newArray,
      });
    } else if (originalData[field] !== undefined) {
      setEditableData({
        ...editableData,
        [field]: originalData[field],
      });

      // Update raw text fields when resetting
      if (field === "key_points" && originalData.key_points) {
        setRawKeyPoints(originalData.key_points.join("\n"));
      } else if (field === "insights" && originalData.insights) {
        setRawInsights(originalData.insights.join("\n"));
      } else if (
        field in originalData &&
        Array.isArray(originalData[field]) &&
        originalData[field].length > 0 &&
        typeof originalData[field][0] === "string"
      ) {
        // Type assertion since we've checked it's an array of strings
        const stringArray = originalData[field] as string[];
        setOtherRawFields((prev) => ({
          ...prev,
          [field]: stringArray.join("\n"),
        }));
      }
    }
  };

  const handleKeyPointsChange = (
    rawValue: string,
    processedArray: string[]
  ) => {
    setRawKeyPoints(rawValue);

    if (editableData && editableData.key_points) {
      setEditableData({
        ...editableData,
        key_points: processedArray,
      });
    }
  };

  const handleInsightsChange = (rawValue: string, processedArray: string[]) => {
    setRawInsights(rawValue);

    if (editableData && editableData.insights) {
      setEditableData({
        ...editableData,
        insights: processedArray,
      });
    }
  };

  const handleStringFieldChange = (field: string, value: string) => {
    if (editableData) {
      setEditableData({
        ...editableData,
        [field]: value,
      });
    }
  };

  const handleArrayFieldChange = (
    field: string,
    rawValue: string,
    processedArray: string[]
  ) => {
    if (editableData) {
      // Update raw text state
      setOtherRawFields((prev) => ({
        ...prev,
        [field]: rawValue,
      }));

      // Update array in editable data
      setEditableData({
        ...editableData,
        [field]: processedArray,
      });
    }
  };

  const handleFieldFocus = (fieldId: string) => {
    setFocusedField(fieldId);
  };

  const handleFieldBlur = () => {
    setFocusedField(null);
  };

  // Force EditableArrayField to exit edit mode when switching tabs
  useEffect(() => {
    setFocusedField(null);
  }, [activeTab, activeStructuredTab]);

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
      // Extract session_id and filename from the path
      // Path format: output/SESSION_ID/pages/FILENAME
      const pathParts = path.split("/");
      const filename = pathParts.pop() || "";
      const session_id = pathParts[pathParts.indexOf("output") + 1] || "";

      if (!session_id) {
        console.error("Could not extract session_id from path:", path);
        throw new Error("Invalid path format");
      }

      const response = await fetch(
        `http://localhost:8000/api/pages/${session_id}/${filename}`
      );

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
          <TabsTrigger value="images">Images ({images.length})</TabsTrigger>
          <TabsTrigger value="pages">
            PDF Pages ({processedPages.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="structured">
          {editableData && (
            <div className="space-y-6">
              <Tabs
                defaultValue="summary"
                className="w-full"
                value={activeStructuredTab}
                onValueChange={setActiveStructuredTab}
              >
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="summary">PDF Summary</TabsTrigger>
                  <TabsTrigger value="insideideo">Inside IDEO</TabsTrigger>
                </TabsList>

                <TabsContent value="summary" className="space-y-4">
                  {editableData.summary && (
                    <EditableField
                      fieldId="summary"
                      label="Summary"
                      value={editableData.summary}
                      isTextArea={true}
                      rows={4}
                      onChange={(value) =>
                        handleStringFieldChange("summary", value)
                      }
                      onFocus={handleFieldFocus}
                      onBlur={handleFieldBlur}
                      onReset={() => handleResetField("summary")}
                    />
                  )}

                  {editableData.key_points &&
                    editableData.key_points.length > 0 && (
                      <EditableArrayField
                        fieldId="key_points"
                        label="Key Points"
                        value={editableData.key_points}
                        rawValue={rawKeyPoints}
                        rows={6}
                        placeholder="Enter key points, one per line"
                        onChange={handleKeyPointsChange}
                        onFocus={handleFieldFocus}
                        onBlur={handleFieldBlur}
                        onReset={() => handleResetField("key_points")}
                      />
                    )}

                  {editableData.insights &&
                    editableData.insights.length > 0 && (
                      <EditableArrayField
                        fieldId="insights"
                        label="Insights"
                        value={editableData.insights}
                        rawValue={rawInsights}
                        rows={6}
                        placeholder="Enter insights, one per line"
                        onChange={handleInsightsChange}
                        onFocus={handleFieldFocus}
                        onBlur={handleFieldBlur}
                        onReset={() => handleResetField("insights")}
                      />
                    )}
                </TabsContent>

                <TabsContent value="insideideo" className="space-y-4">
                  {editableData && (
                    <>
                      <EditableField
                        fieldId="inside_ideo_client"
                        label="Client"
                        value={
                          typeof editableData.inside_ideo_client === "string"
                            ? editableData.inside_ideo_client
                            : ""
                        }
                        isTextArea={false}
                        onChange={(value) =>
                          handleStringFieldChange("inside_ideo_client", value)
                        }
                        onFocus={handleFieldFocus}
                        onBlur={handleFieldBlur}
                        onReset={() => handleResetField("inside_ideo_client")}
                      />

                      <EditableField
                        fieldId="inside_ideo_title"
                        label="Title"
                        value={
                          typeof editableData.inside_ideo_title === "string"
                            ? editableData.inside_ideo_title
                            : ""
                        }
                        isTextArea={true}
                        rows={2}
                        onChange={(value) =>
                          handleStringFieldChange("inside_ideo_title", value)
                        }
                        onFocus={handleFieldFocus}
                        onBlur={handleFieldBlur}
                        onReset={() => handleResetField("inside_ideo_title")}
                      />

                      <EditableField
                        fieldId="inside_ideo_tagline"
                        label="Tagline"
                        value={
                          typeof editableData.inside_ideo_tagline === "string"
                            ? editableData.inside_ideo_tagline
                            : ""
                        }
                        isTextArea={false}
                        onChange={(value) =>
                          handleStringFieldChange("inside_ideo_tagline", value)
                        }
                        onFocus={handleFieldFocus}
                        onBlur={handleFieldBlur}
                        onReset={() => handleResetField("inside_ideo_tagline")}
                      />

                      <EditableField
                        fieldId="inside_ideo_challenge"
                        label="The Challenge"
                        value={
                          typeof editableData.inside_ideo_challenge === "string"
                            ? editableData.inside_ideo_challenge
                            : ""
                        }
                        isTextArea={true}
                        rows={4}
                        onChange={(value) =>
                          handleStringFieldChange(
                            "inside_ideo_challenge",
                            value
                          )
                        }
                        onFocus={handleFieldFocus}
                        onBlur={handleFieldBlur}
                        onReset={() =>
                          handleResetField("inside_ideo_challenge")
                        }
                      />

                      <EditableField
                        fieldId="inside_ideo_design"
                        label="The Design/Work"
                        value={
                          typeof editableData.inside_ideo_design === "string"
                            ? editableData.inside_ideo_design
                            : ""
                        }
                        isTextArea={true}
                        rows={4}
                        onChange={(value) =>
                          handleStringFieldChange("inside_ideo_design", value)
                        }
                        onFocus={handleFieldFocus}
                        onBlur={handleFieldBlur}
                        onReset={() => handleResetField("inside_ideo_design")}
                      />

                      <EditableField
                        fieldId="inside_ideo_impact"
                        label="The Outcome/Impact"
                        value={
                          typeof editableData.inside_ideo_impact === "string"
                            ? editableData.inside_ideo_impact
                            : ""
                        }
                        isTextArea={true}
                        rows={4}
                        onChange={(value) =>
                          handleStringFieldChange("inside_ideo_impact", value)
                        }
                        onFocus={handleFieldFocus}
                        onBlur={handleFieldBlur}
                        onReset={() => handleResetField("inside_ideo_impact")}
                      />
                    </>
                  )}
                </TabsContent>
              </Tabs>
            </div>
          )}
        </TabsContent>

        <TabsContent value="images">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {images.map((image, index) => (
              <Card key={index} className="overflow-hidden">
                <CardHeader className="p-4 pb-2">
                  <CardTitle className="text-sm flex justify-between items-center">
                    <span>
                      Page {image.page + 1}{" "}
                      {/* Use a shorter title or just page number */}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="ml-2 h-8 w-8 p-0"
                      onClick={() =>
                        image.image_data &&
                        downloadImage(
                          image.image_data,
                          `image-page-${image.page + 1}.png`
                        )
                      }
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-2">
                  {image.image_data ? (
                    <div className="relative aspect-video">
                      <Image
                        src={image.image_data}
                        alt={`Image from page ${image.page + 1}`}
                        className="object-contain"
                        fill
                      />
                    </div>
                  ) : (
                    <div className="flex items-center justify-center p-12">
                      <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                    </div>
                  )}
                </CardContent>
                <CardFooter className="block p-4 pt-0">
                  <div className="text-xs text-gray-500 mt-2">
                    {image.image_description ? (
                      <ImageDescription text={image.image_description} />
                    ) : (
                      <>
                        <strong>OCR Text:</strong>{" "}
                        {image.ocr_text || "No text detected in image"}
                      </>
                    )}
                  </div>
                </CardFooter>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="pages">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {processedPages.map((page, index) => (
              <Card key={index} className="overflow-hidden">
                <CardHeader className="p-4 pb-2">
                  <CardTitle className="text-sm flex justify-between items-center">
                    <span>Page {index + 1}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="ml-2 h-8 w-8 p-0"
                      onClick={() =>
                        page.image_data &&
                        downloadImage(page.image_data, `page-${index + 1}.png`)
                      }
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 pt-2">
                  {page.image_data ? (
                    <div className="relative w-full" style={{ height: "40vh" }}>
                      <Image
                        src={page.image_data}
                        alt={`Page ${index + 1}`}
                        className="object-contain"
                        fill
                      />
                    </div>
                  ) : (
                    <div className="flex items-center justify-center p-12">
                      {loadingPages[index] ? (
                        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                      ) : (
                        <Button onClick={loadVisiblePages}>Load Image</Button>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
