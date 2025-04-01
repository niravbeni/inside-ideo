import React from "react";

export function DebugInfo() {
  return (
    <div
      style={{
        position: "fixed",
        bottom: "5px",
        right: "5px",
        backgroundColor: "rgba(0,0,0,0.4)",
        color: "rgba(255,255,255,0.7)",
        padding: "4px 6px",
        borderRadius: "3px",
        fontSize: "10px",
        zIndex: 9999,
        maxWidth: "200px",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}
    >
      api: {process.env.NEXT_PUBLIC_API_URL || "localhost:8000"}
    </div>
  );
}
