import React, { useEffect, useRef, useState } from "react";

interface IdeoLoaderProps {
  size?: "small" | "medium" | "large";
}

const IdeoLoader: React.FC<IdeoLoaderProps> = ({ size = "medium" }) => {
  const [letters, setLetters] = useState(["I", "D", "E", "O"]);
  const letterQueue = useRef(["I", "D", "E", "O"]);
  const tileRef = useRef<HTMLDivElement | null>(null);

  // Size configuration based on the size prop
  const sizeConfig = {
    small: {
      container: { min: 30, max: 45 },
      tile: { size: 16, fontSize: 10 },
    },
    medium: {
      container: { min: 40, max: 60 },
      tile: { size: 21, fontSize: 14 },
    },
    large: {
      container: { min: 60, max: 90 },
      tile: { size: 31, fontSize: 20 },
    },
  };

  const { container, tile } = sizeConfig[size];

  useEffect(() => {
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
  }, []);

  return (
    <>
      <div className="ideo-loader">
        {letters.map((letter, i) => (
          <div
            key={i}
            className={`ideo-tile ideo-tile-${i + 1}`}
            ref={i === 0 ? tileRef : null}
          >
            {letter}
          </div>
        ))}
      </div>

      <style>{`
        .ideo-loader {
          position: relative;
          width: ${container.min}px;
          height: ${container.min}px;
          animation: ideo-grow-shrink 1.5s infinite cubic-bezier(0.3,1,0,1);
          margin: 0 auto;
        }

        .ideo-tile {
          position: absolute;
          width: ${tile.size}px;
          height: ${tile.size}px;
          background: black;
          color: white;
          font-weight: bold;
          font-family: sans-serif;
          font-size: ${tile.fontSize}px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        @keyframes ideo-grow-shrink {
          0%   { width: ${container.min}px; height: ${container.min}px; }
          33%, 66% { width: ${container.max}px; height: ${container.max}px; }
          100% { width: ${container.min}px; height: ${container.min}px; }
        }

        @keyframes ideo-move1 {
          0%, 33%   { top: 0; left: 0; }
          66%, 100% { top: 0; left: calc(100% - ${tile.size}px); }
        }
        @keyframes ideo-move2 {
          0%, 33%   { top: 0; left: calc(100% - ${tile.size}px); }
          66%, 100% { top: calc(100% - ${tile.size}px); left: calc(100% - ${tile.size}px); }
        }
        @keyframes ideo-move3 {
          0%, 33%   { top: calc(100% - ${tile.size}px); left: calc(100% - ${tile.size}px); }
          66%, 100% { top: calc(100% - ${tile.size}px); left: 0; }
        }
        @keyframes ideo-move4 {
          0%, 33%   { top: calc(100% - ${tile.size}px); left: 0; }
          66%, 100% { top: 0; left: 0; }
        }

        .ideo-tile-1 { animation: ideo-move1 1.5s infinite cubic-bezier(0.3,1,0,1); }
        .ideo-tile-2 { animation: ideo-move2 1.5s infinite cubic-bezier(0.3,1,0,1); }
        .ideo-tile-3 { animation: ideo-move3 1.5s infinite cubic-bezier(0.3,1,0,1); }
        .ideo-tile-4 { animation: ideo-move4 1.5s infinite cubic-bezier(0.3,1,0,1); }
      `}</style>
    </>
  );
};

export default IdeoLoader;