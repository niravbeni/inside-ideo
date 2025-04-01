import React from "react";

export function DebugInfo() {
  return (
    <div
      style={{
        position: "fixed",
        bottom: "10px",
        right: "10px",
        backgroundColor: "rgba(0,0,0,0.7)",
        color: "white",
        padding: "8px",
        borderRadius: "4px",
        fontSize: "12px",
        zIndex: 9999,
      }}
    >
      API URL: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
    </div>
  );
}
