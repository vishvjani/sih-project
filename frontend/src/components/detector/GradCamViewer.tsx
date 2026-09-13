import React, { useState, useRef } from 'react';
import { Layers, Split, Image as ImageIcon, Sparkles } from 'lucide-react';

interface GradCamViewerProps {
  originalImage: string;
  heatmapImage: string;
  isAi?: boolean;
  className?: string;
}

export const GradCamViewer: React.FC<GradCamViewerProps> = ({
  originalImage,
  heatmapImage,
  className = '',
}) => {
  const [viewMode, setViewMode] = useState<'overlay' | 'original' | 'split' | 'heatmap'>('overlay');
  const [splitPos, setSplitPos] = useState<number>(50); // 0 to 100%
  const containerRef = useRef<HTMLDivElement>(null);
  const isDraggingRef = useRef<boolean>(false);

  const handlePointerDown = () => {
    isDraggingRef.current = true;
  };

  const handlePointerUp = () => {
    isDraggingRef.current = false;
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDraggingRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    setSplitPos((x / rect.width) * 100);
  };

  return (
    <div className={`flex flex-col rounded-lg border border-[rgba(255,255,255,0.08)] bg-[#14151b] overflow-hidden ${className}`}>
      {/* View Mode Switcher Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/5 bg-[#101217]">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#96E071]" />
          <span className="font-mono text-xs font-semibold text-gray-200">
            GRAD-CAM EXPLAINABILITY VIEWER
          </span>
        </div>

        <div className="flex items-center gap-1 bg-[#181a22] p-0.5 rounded border border-white/5">
          <button
            onClick={() => setViewMode('overlay')}
            className={`px-2 py-1 text-[11px] font-mono rounded flex items-center gap-1 transition-all ${
              viewMode === 'overlay'
                ? 'bg-[#96E071] text-black font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
            title="Blended Heatmap Overlay"
          >
            <Layers className="w-3 h-3" />
            <span>Overlay</span>
          </button>

          <button
            onClick={() => setViewMode('split')}
            className={`px-2 py-1 text-[11px] font-mono rounded flex items-center gap-1 transition-all ${
              viewMode === 'split'
                ? 'bg-[#96E071] text-black font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
            title="Split-Slider Comparison"
          >
            <Split className="w-3 h-3" />
            <span>Split Curtain</span>
          </button>

          <button
            onClick={() => setViewMode('heatmap')}
            className={`px-2 py-1 text-[11px] font-mono rounded flex items-center gap-1 transition-all ${
              viewMode === 'heatmap'
                ? 'bg-[#96E071] text-black font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
            title="Pure Heatmap Activations"
          >
            <Sparkles className="w-3 h-3" />
            <span>Pure Heat</span>
          </button>

          <button
            onClick={() => setViewMode('original')}
            className={`px-2 py-1 text-[11px] font-mono rounded flex items-center gap-1 transition-all ${
              viewMode === 'original'
                ? 'bg-[#96E071] text-black font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
            title="Original Image"
          >
            <ImageIcon className="w-3 h-3" />
            <span>Original</span>
          </button>
        </div>
      </div>

      {/* Main Image Stage */}
      <div
        ref={containerRef}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerMove={handlePointerMove}
        className="relative w-full h-[260px] md:h-[320px] bg-black overflow-hidden select-none"
      >
        {/* Under layer: Original Image */}
        <img
          src={originalImage}
          alt="Original"
          className="absolute inset-0 w-full h-full object-contain pointer-events-none"
        />

        {/* Overlay Mode */}
        {viewMode === 'overlay' && (
          <img
            src={heatmapImage}
            alt="Grad-CAM Overlay"
            className="absolute inset-0 w-full h-full object-contain mix-blend-screen opacity-85 pointer-events-none transition-opacity"
          />
        )}

        {/* Pure Heatmap Mode */}
        {viewMode === 'heatmap' && (
          <img
            src={heatmapImage}
            alt="Pure Grad-CAM"
            className="absolute inset-0 w-full h-full object-contain bg-black pointer-events-none"
          />
        )}

        {/* Split Screen Slider Mode */}
        {viewMode === 'split' && (
          <>
            {/* Right side reveal (Heatmap overlay clipped) */}
            <div
              style={{ clipPath: `polygon(${splitPos}% 0, 100% 0, 100% 100%, ${splitPos}% 100%)` }}
              className="absolute inset-0 w-full h-full pointer-events-none"
            >
              <img
                src={originalImage}
                alt="Original Base"
                className="w-full h-full object-contain"
              />
              <img
                src={heatmapImage}
                alt="Heatmap Overlay"
                className="absolute inset-0 w-full h-full object-contain mix-blend-screen opacity-90"
              />
              <div className="absolute top-2 right-2 bg-black/80 backdrop-blur-sm px-2 py-0.5 rounded font-mono text-[10px] text-[#96E071] border border-[#96E071]/30">
                GRAD-CAM HEATMAP
              </div>
            </div>

            {/* Left side label */}
            <div className="absolute top-2 left-2 bg-black/80 backdrop-blur-sm px-2 py-0.5 rounded font-mono text-[10px] text-gray-300 border border-white/10 pointer-events-none">
              ORIGINAL SOURCE
            </div>

            {/* Draggable Divider Line & Handle */}
            <div
              style={{ left: `${splitPos}%` }}
              className="absolute inset-y-0 w-0.5 bg-[#96E071] shadow-[0_0_10px_#96E071] pointer-events-none"
            >
              <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-[#96E071] text-black flex items-center justify-center cursor-ew-resize pointer-events-auto shadow-lg">
                <Split className="w-3.5 h-3.5" />
              </div>
            </div>
          </>
        )}

        {/* Scanline decoration */}
        <div className="absolute inset-0 scanlines opacity-20 pointer-events-none" />
      </div>

      {/* Heatmap Legend Bar */}
      <div className="flex items-center justify-between px-3 py-2 bg-[#0d0e12] border-t border-white/5 font-mono text-[10px]">
        <span className="text-gray-400">ACTIVATION INTENSITY:</span>
        <div className="flex items-center gap-2">
          <span className="text-blue-400">Low (Pristine)</span>
          <div className="w-28 h-2 rounded-full bg-gradient-to-r from-blue-500 via-emerald-400 via-yellow-400 to-red-500" />
          <span className="text-red-400 font-bold">High (Synthetic Anomaly)</span>
        </div>
      </div>
    </div>
  );
};
