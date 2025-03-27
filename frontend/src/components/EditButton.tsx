import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Pencil, X } from "lucide-react";

interface EditButtonProps {
  text: string;
  className?: string;
  size?: "sm" | "lg" | "icon" | "default";
  onSave: (newText: string) => void;
  inputRef?: React.RefObject<HTMLInputElement | HTMLTextAreaElement>;
  onEditingChange?: (isEditing: boolean) => void;
}

export function EditButton({
  text,
  className,
  size = "sm",
  onSave,
  inputRef,
  onEditingChange,
}: EditButtonProps) {
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    // Notify parent component when editing state changes
    if (onEditingChange) {
      onEditingChange(isEditing);
    }

    // Focus the input when entering edit mode
    if (isEditing && inputRef?.current) {
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 0);
    }
  }, [isEditing, onEditingChange, inputRef]);

  const handleEditToggle = () => {
    if (isEditing) {
      // We're canceling
      setIsEditing(false);
      return;
    }

    setIsEditing(true);
  };

  return isEditing ? (
    <div className="flex space-x-1">
      <Button
        variant="outline"
        size={size}
        className={className}
        onClick={handleEditToggle}
        title="Cancel editing"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  ) : (
    <Button
      variant="outline"
      size={size}
      className={className}
      onClick={handleEditToggle}
      title="Edit text"
    >
      <Pencil className="h-4 w-4" />
    </Button>
  );
}
