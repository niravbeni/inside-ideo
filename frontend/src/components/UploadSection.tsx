import React, { useCallback, useState } from "react";
import { useDropzone, FileRejection } from "react-dropzone";
import { Upload, AlertCircle, FileType } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatBytes } from "@/lib/utils";

interface FileWithPreview extends File {
  preview?: string;
}

interface UploadSectionProps {
  onFilesSelected: (files: File[]) => void;
  isLoading: boolean;
}

export function UploadSection({
  onFilesSelected,
  isLoading,
}: UploadSectionProps) {
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      if (isLoading) return;

      if (rejectedFiles.length > 0) {
        // Show error for the first rejected file
        const firstError = rejectedFiles[0].errors[0];
        if (firstError.code === "file-too-large") {
          setError("File is too large. Maximum size is 10MB.");
        } else if (firstError.code === "file-invalid-type") {
          setError("Only PDF files are allowed.");
        } else {
          setError(firstError.message);
        }
        return;
      }

      if (acceptedFiles.length > 5) {
        setError("Maximum 5 files allowed");
        return;
      }

      setError(null);
      const newFiles = acceptedFiles.map((file) =>
        Object.assign(file, {
          preview: URL.createObjectURL(file),
        })
      );
      setFiles(newFiles);
      onFilesSelected(newFiles);
    },
    [onFilesSelected, isLoading]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
    },
    maxSize: 50 * 1024 * 1024, // 10MB
    disabled: isLoading,
  });

  const removeFile = (index: number) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);
    onFilesSelected(newFiles);
  };

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isLoading
            ? "border-primary/30 bg-muted opacity-75 cursor-not-allowed"
            : isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/20"
        }`}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center justify-center space-y-4">
          <Upload className="h-10 w-10 text-muted-foreground" />
          <div>
            <p className="text-lg font-medium">
              {isLoading
                ? "Processing your PDFs..."
                : "Drag & drop your PDF files here"}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              {isLoading
                ? "Please wait while we extract the content"
                : "or click to browse files"}
            </p>
          </div>
          <Button disabled={isLoading} type="button">
            Select PDF files
          </Button>
          <p className="text-xs text-muted-foreground">
            Upload up to 5 PDF files (max 10MB each)
          </p>
        </div>
      </div>

      {error && !isLoading && (
        <div className="mt-4 p-3 bg-destructive/10 border border-destructive rounded-md flex items-center text-sm">
          <AlertCircle className="h-4 w-4 text-destructive mr-2" />
          <span>{error}</span>
        </div>
      )}

      {files.length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-medium">Selected Files</h3>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li
                key={index}
                className="flex items-center justify-between p-3 bg-muted/50 rounded-md"
              >
                <div className="flex items-center">
                  <FileType className="h-5 w-5 text-muted-foreground mr-2" />
                  <div>
                    <p className="text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatBytes(file.size)}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  disabled={isLoading}
                >
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
