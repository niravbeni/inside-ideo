import React, { useState, useRef } from "react";
import { Button } from "./button";
import { Textarea } from "./textarea";
import { RotateCcw, Edit, Check } from "lucide-react";
import { CopyButton } from "@/components/CopyButton";

interface EditableFieldProps {
  fieldId: string;
  label: string;
  value: string;
  isTextArea?: boolean;
  rows?: number;
  placeholder?: string;
  onChange: (value: string) => void;
  onFocus?: (fieldId: string) => void;
  onBlur?: () => void;
  onReset?: () => void;
}

export function EditableField({
  fieldId,
  label,
  value,
  isTextArea = true,
  rows = 3,
  placeholder = "Enter text here",
  onChange,
  onFocus,
  onBlur,
  onReset,
}: EditableFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  const handleFocus = () => {
    setIsEditing(true);
    if (onFocus) onFocus(fieldId);
  };

  const handleBlur = () => {
    setIsEditing(false);
    if (onBlur) onBlur();
  };

  const handleReset = () => {
    if (onReset) onReset();
  };

  const toggleEdit = () => {
    if (!isEditing) {
      setIsEditing(true);
      if (onFocus) onFocus(fieldId);
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setIsEditing(false);
      if (onBlur) onBlur();
    }
  };

  return (
    <div>
      <label htmlFor={fieldId} className="block text-sm font-medium mb-1">
        {label}
      </label>
      <div className="flex space-x-2">
        <div
          className={`flex-1 border rounded-md p-3 bg-background ${
            !isEditing ? "hover:border-primary cursor-text" : ""
          } transition-colors relative group`}
          onClick={() => {
            if (!isEditing) {
              toggleEdit();
            }
          }}
        >
          {!isEditing && (
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleEdit();
                }}
              >
                <Edit className="h-4 w-4" />
              </Button>
            </div>
          )}
          {isEditing ? (
            <Textarea
              ref={inputRef}
              id={fieldId}
              value={value}
              rows={rows}
              placeholder={placeholder}
              onChange={handleChange}
              onBlur={handleBlur}
              className="w-full resize-none border-none p-0 focus-visible:ring-0 focus-visible:ring-offset-0"
              autoFocus
            />
          ) : (
            <div className="whitespace-pre-wrap text-sm min-h-[2.5rem]">
              {value || (
                <span className="text-muted-foreground italic">
                  Click to edit
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex flex-col space-y-1">
          {isEditing ? (
            <Button
              variant="outline"
              size="sm"
              className="px-2"
              onClick={toggleEdit}
              title="Done editing"
            >
              <Check className="h-4 w-4" />
            </Button>
          ) : (
            <CopyButton text={value} />
          )}
          <Button
            variant="outline"
            size="sm"
            className="px-2"
            onClick={handleReset}
            title="Reset this field"
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
