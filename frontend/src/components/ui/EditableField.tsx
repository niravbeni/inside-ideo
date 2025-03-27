import React, { useState, useRef, useEffect } from "react";
import { Input } from "./input";
import { Textarea } from "./textarea";
import { Button } from "./button";
import { RotateCcw, Edit, Check } from "lucide-react";
import { CopyButton } from "@/components/CopyButton";

interface EditableFieldProps {
  fieldId: string;
  label: string;
  value: string;
  initialValue?: string;
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
  initialValue,
  isTextArea = false,
  rows = 4,
  placeholder = "",
  onChange,
  onFocus,
  onBlur,
  onReset,
}: EditableFieldProps) {
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);
  const [isEditing, setIsEditing] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
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
      handleFocus();
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      handleBlur();
    }
  };

  // Render display mode
  const renderDisplayValue = () => {
    const displayValue = value || placeholder;
    const isEmpty = !value || value.trim() === "";

    return (
      <div
        className="flex-1 border rounded-md p-3 bg-background min-h-[2.5rem] cursor-text hover:border-primary transition-colors relative group"
        onClick={() => {
          handleFocus();
          setTimeout(() => inputRef.current?.focus(), 0);
        }}
      >
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
        {isTextArea ? (
          <div className="whitespace-pre-wrap text-sm">
            {isEmpty ? (
              <span className="text-muted-foreground italic">
                Click to add content
              </span>
            ) : (
              displayValue
            )}
          </div>
        ) : (
          <div className="text-sm">
            {isEmpty ? (
              <span className="text-muted-foreground italic">
                Click to add content
              </span>
            ) : (
              displayValue
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      <label htmlFor={fieldId} className="block text-sm font-medium mb-1">
        {label}
      </label>
      <div className="flex space-x-2">
        {isEditing ? (
          isTextArea ? (
            <Textarea
              id={fieldId}
              value={value}
              ref={inputRef as React.RefObject<HTMLTextAreaElement>}
              rows={rows}
              className="flex-1"
              onChange={handleChange}
              onFocus={handleFocus}
              onBlur={handleBlur}
              placeholder={placeholder}
            />
          ) : (
            <Input
              id={fieldId}
              value={value}
              ref={inputRef as React.RefObject<HTMLInputElement>}
              className="flex-1"
              onChange={handleChange}
              onFocus={handleFocus}
              onBlur={handleBlur}
              placeholder={placeholder}
            />
          )
        ) : (
          renderDisplayValue()
        )}
        <div
          className={`flex ${
            isTextArea ? "flex-col space-y-1 self-start" : "space-x-1"
          }`}
        >
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
