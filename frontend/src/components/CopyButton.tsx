import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Check, Copy } from "lucide-react";
import { copyToClipboard } from "@/lib/utils";

interface CopyButtonProps {
  text: string;
  className?: string;
  size?: "sm" | "lg" | "icon" | "default";
}

export function CopyButton({ text, className, size = "sm" }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Button
      variant="outline"
      size={size}
      className={className}
      onClick={handleCopy}
      title={copied ? "Copied!" : "Copy to clipboard"}
    >
      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
    </Button>
  );
}
