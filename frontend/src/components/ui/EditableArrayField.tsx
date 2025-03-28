import React, { useState, useRef, useEffect } from "react";
import { Button } from "./button";
import { Textarea } from "./textarea";
import { RotateCcw, Edit, Check, Plus, X } from "lucide-react";
import { CopyButton } from "@/components/CopyButton";
import { Input } from "./input";

interface EditableArrayFieldProps {
  fieldId: string;
  label: string;
  value: string[];
  rawValue: string;
  rows?: number;
  placeholder?: string;
  onChange: (rawValue: string, processedArray: string[]) => void;
  onFocus?: (fieldId: string) => void;
  onBlur?: () => void;
  onReset?: () => void;
}

export function EditableArrayField({
  fieldId,
  label,
  value,
  rawValue,
  rows = 4,
  placeholder = "Enter items, one per line",
  onChange,
  onFocus,
  onBlur,
  onReset,
}: EditableArrayFieldProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [editItems, setEditItems] = useState<string[]>([]);
  const [newItem, setNewItem] = useState("");

  // Initialize the edit items when starting to edit
  useEffect(() => {
    if (isEditing) {
      setEditItems(value.length > 0 ? [...value] : [""]);
    }
  }, [isEditing, value]);

  const handleItemChange = (index: number, newValue: string) => {
    const updatedItems = [...editItems];
    updatedItems[index] = newValue;
    setEditItems(updatedItems);

    // Update parent component with raw text and processed array
    const newRawValue = updatedItems.join("\n");
    const filteredItems = updatedItems.filter((item) => item.trim() !== "");
    onChange(newRawValue, filteredItems);
  };

  const handleAddItem = () => {
    setEditItems([...editItems, ""]);
  };

  const handleRemoveItem = (index: number) => {
    const updatedItems = [...editItems];
    updatedItems.splice(index, 1);

    // Ensure we always have at least one item for editing
    if (updatedItems.length === 0) {
      updatedItems.push("");
    }

    setEditItems(updatedItems);

    // Update parent component
    const newRawValue = updatedItems.join("\n");
    const filteredItems = updatedItems.filter((item) => item.trim() !== "");
    onChange(newRawValue, filteredItems);
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    const processedArray = newValue
      .split("\n")
      .filter((line) => line.trim() !== "");
    onChange(newValue, processedArray);
  };

  const handleFocus = () => {
    setIsEditing(true);
    setIsFocused(true);
    if (onFocus) onFocus(fieldId);
  };

  const handleBlur = () => {
    // Don't blur/exit edit mode on regular field blur
    // We'll handle this explicitly with the Done button
    if (onBlur) onBlur();
  };

  const handleSaveChanges = () => {
    setIsEditing(false);
    setIsFocused(false);
    if (onBlur) onBlur();
  };

  const handleReset = () => {
    if (onReset) onReset();
    if (isEditing) {
      setIsEditing(false);
      setIsFocused(false);
    }
  };

  const toggleEdit = () => {
    if (!isEditing) {
      handleFocus();
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      handleSaveChanges();
    }
  };

  // Render bullet points for display mode
  const renderBulletPoints = () => (
    <div
      className={`flex-1 border rounded-md p-3 min-h-[5rem] cursor-text transition-all duration-150
        ${!isEditing ? "hover:border-primary" : ""}
        ${
          isFocused || isEditing
            ? "bg-primary/5 border-primary shadow-sm"
            : "bg-background"
        }
        relative group`}
      onClick={() => {
        handleFocus();
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
      <ul className="list-disc pl-5 space-y-1">
        {value.map((item, index) => (
          <li key={index} className="text-sm">
            {item}
          </li>
        ))}
        {value.length === 0 && (
          <li className="text-sm text-muted-foreground italic">
            Click to add items
          </li>
        )}
      </ul>
    </div>
  );

  // Render bulleted item editor
  const renderBulletEditor = () => (
    <div className="flex-1 border rounded-md p-3 bg-primary/5 border-primary shadow-sm">
      <div className="space-y-2">
        {editItems.map((item, index) => (
          <div key={index} className="flex items-center space-x-2">
            <div className="text-sm mr-1">•</div>
            <Input
              value={item}
              onChange={(e) => handleItemChange(index, e.target.value)}
              className="flex-1"
              placeholder="Enter item text"
              autoFocus={index === editItems.length - 1 && item === ""}
              onFocus={() => setIsFocused(true)}
            />
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => handleRemoveItem(index)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button
          variant="outline"
          size="sm"
          className="mt-2"
          onClick={handleAddItem}
        >
          <Plus className="h-4 w-4 mr-1" /> Add Item
        </Button>
      </div>
    </div>
  );

  return (
    <div>
      <label htmlFor={fieldId} className="block text-sm font-medium mb-1">
        {label}
      </label>
      <div className="flex space-x-2">
        {isEditing ? renderBulletEditor() : renderBulletPoints()}
        <div className="flex flex-col space-y-1 self-start">
          {isEditing ? (
            <Button
              variant="outline"
              size="sm"
              className="px-2"
              onClick={handleSaveChanges}
              title="Done editing"
            >
              <Check className="h-4 w-4" />
            </Button>
          ) : (
            <CopyButton text={rawValue} />
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

      {/* Hidden textarea to maintain compatibility with existing code */}
      <textarea
        ref={inputRef}
        className="sr-only"
        tabIndex={-1}
        aria-hidden="true"
      />
    </div>
  );
}
