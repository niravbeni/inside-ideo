import React, { useEffect, useRef, useState } from "react";

interface IdeoLoaderCursorProps {
  isLoading?: boolean;
}

const IdeoLoaderCursor: React.FC<IdeoLoaderCursorProps> = ({
  isLoading = false,
}) => {
  const [letters, setLetters] = useState(["I", "D", "E", "O"]);
  const letterQueue = useRef(["I", "D", "E", "O"]);
  const tileRef = useRef<HTMLDivElement | null>(null);
  const cursorRef = useRef<HTMLDivElement | null>(null);
  const [position, setPosition] = useState({ x: -100, y: -100 });

  // Handle letter rotation - use the same approach as the original
  useEffect(() => {
    if (!isLoading) return;

    const handleAnim = () => {
      // Rotate letters for *next* cycle, right at the START of the new loop
      const lastLetter = letterQueue.current.pop();
      if (lastLetter) {
        letterQueue.current.unshift(lastLetter);
        setLetters([...letterQueue.current]); // update after full cycle
      }
    };

    const tile = tileRef.current;
    if (tile) {
      tile.addEventListener("animationiteration", handleAnim);
      return () => tile.removeEventListener("animationiteration", handleAnim);
    }

    return undefined;
  }, [isLoading]);

  // Handle cursor position updates
  useEffect(() => {
    if (!isLoading) return;

    const updatePosition = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };

    document.addEventListener("mousemove", updatePosition);
    return () => {
      document.removeEventListener("mousemove", updatePosition);
    };
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <div
      ref={cursorRef}
      className="ideo-loader-cursor"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
      }}
    >
      <div className="ideo-loader-cursor-container">
        {letters.map((letter, i) => (
          <div
            key={i}
            className={`ideo-cursor-tile ideo-cursor-tile-${i + 1}`}
            ref={i === 0 ? tileRef : null}
          >
            {letter}
          </div>
        ))}
      </div>

      <style jsx>{`
        .ideo-loader-cursor {
          position: fixed;
          pointer-events: none;
          z-index: 9999;
          transform: translate(-50%, -50%);
        }

        .ideo-loader-cursor-container {
          position: relative;
          width: 25px;
          height: 25px;
          animation: ideo-cursor-grow-shrink 1.5s infinite
            cubic-bezier(0.3, 1, 0, 1);
          margin: 0 auto;
        }

        .ideo-cursor-tile {
          position: absolute;
          width: 14px;
          height: 14px;
          background: black;
          color: white;
          font-weight: bold;
          font-family: sans-serif;
          font-size: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        @keyframes ideo-cursor-grow-shrink {
          0% {
            width: 25px;
            height: 25px;
          }
          33%,
          66% {
            width: 38px;
            height: 38px;
          }
          100% {
            width: 25px;
            height: 25px;
          }
        }

        @keyframes ideo-cursor-move1 {
          0%,
          33% {
            top: 0;
            left: 0;
          }
          66%,
          100% {
            top: 0;
            left: calc(100% - 14px);
          }
        }
        @keyframes ideo-cursor-move2 {
          0%,
          33% {
            top: 0;
            left: calc(100% - 14px);
          }
          66%,
          100% {
            top: calc(100% - 14px);
            left: calc(100% - 14px);
          }
        }
        @keyframes ideo-cursor-move3 {
          0%,
          33% {
            top: calc(100% - 14px);
            left: calc(100% - 14px);
          }
          66%,
          100% {
            top: calc(100% - 14px);
            left: 0;
          }
        }
        @keyframes ideo-cursor-move4 {
          0%,
          33% {
            top: calc(100% - 14px);
            left: 0;
          }
          66%,
          100% {
            top: 0;
            left: 0;
          }
        }

        .ideo-cursor-tile-1 {
          animation: ideo-cursor-move1 1.5s infinite cubic-bezier(0.3, 1, 0, 1);
        }
        .ideo-cursor-tile-2 {
          animation: ideo-cursor-move2 1.5s infinite cubic-bezier(0.3, 1, 0, 1);
        }
        .ideo-cursor-tile-3 {
          animation: ideo-cursor-move3 1.5s infinite cubic-bezier(0.3, 1, 0, 1);
        }
        .ideo-cursor-tile-4 {
          animation: ideo-cursor-move4 1.5s infinite cubic-bezier(0.3, 1, 0, 1);
        }
      `}</style>

      {/* Additional global styles to hide default cursor when loader is active */}
      <style jsx global>{`
        ${isLoading
          ? "body { cursor: none !important; } button, a, input, .cursor-pointer { cursor: none !important; }"
          : ""}
      `}</style>
    </div>
  );
};

export default IdeoLoaderCursor;
