import React, { useState, useEffect, useRef } from 'react';
import type { AnalysisResult, PaginationMode } from '../../types';
import { 
  ChevronLeft, 
  ChevronRight, 
  Layers, 
  Rotate3d, 
  Activity, 
  Eye, 
  Sparkles,
  LayoutGrid,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';

interface Creative3DPaginationProps {
  items: AnalysisResult[];
  currentIndex: number;
  onSelectIndex: (index: number) => void;
  onInspectItem?: (item: AnalysisResult) => void;
  className?: string;
}

export const Creative3DPagination: React.FC<Creative3DPaginationProps> = ({
  items,
  currentIndex,
  onSelectIndex,
  onInspectItem,
  className = '',
}) => {
  const [mode, setMode] = useState<PaginationMode>('cylinder');
  const [isAutoPlay, setIsAutoPlay] = useState<boolean>(false);
  const [dragStartX, setDragStartX] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const total = items.length;

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) return;

      if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
        onSelectIndex((currentIndex + 1) % total);
      } else if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
        onSelectIndex((currentIndex - 1 + total) % total);
      } else if (e.key >= '1' && e.key <= '9') {
        const num = parseInt(e.key, 10) - 1;
        if (num < total) onSelectIndex(num);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentIndex, total, onSelectIndex]);

  // Auto-play timer
  useEffect(() => {
    if (!isAutoPlay || total <= 1 || mode === 'grid') return;
    const interval = setInterval(() => {
      onSelectIndex((currentIndex + 1) % total);
    }, 4200);
    return () => clearInterval(interval);
  }, [isAutoPlay, currentIndex, total, onSelectIndex, mode]);

  // Drag handlers for 3D gesture
  const handleMouseDown = (e: React.MouseEvent) => setDragStartX(e.clientX);
  const handleMouseUp = (e: React.MouseEvent) => {
    if (dragStartX === null) return;
    const delta = e.clientX - dragStartX;
    if (delta > 45) {
      onSelectIndex((currentIndex - 1 + total) % total);
    } else if (delta < -45) {
      onSelectIndex((currentIndex + 1) % total);
    }
    setDragStartX(null);
  };

  const handleTouchStart = (e: React.TouchEvent) => setDragStartX(e.touches[0].clientX);
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (dragStartX === null) return;
    const delta = e.changedTouches[0].clientX - dragStartX;
    if (delta > 40) {
      onSelectIndex((currentIndex - 1 + total) % total);
    } else if (delta < -40) {
      onSelectIndex((currentIndex + 1) % total);
    }
    setDragStartX(null);
  };

  if (total === 0) return null;

  return (
    <div className={`relative flex flex-col items-center w-full select-none ${className}`}>
      {/* Top HUD Control Bar */}
      <div className="w-full flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 bg-[#12141C] border border-[#2A2E3B] rounded-t-xl">
        {/* Title & Mode Indicators */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#96E071] animate-pulse" />
            <span className="font-mono text-xs text-[#96E071] font-bold tracking-wider uppercase">
              Forensic Deck Engine
            </span>
          </div>
          <span className="text-gray-600 font-mono text-xs">|</span>
          <span className="font-mono text-xs text-gray-300">
            ITEM <span className="text-white font-bold">{String(currentIndex + 1).padStart(2, '0')}</span> / {String(total).padStart(2, '0')}
          </span>
        </div>

        {/* Mode Selector Buttons */}
        <div className="flex items-center gap-1.5 bg-[#181B26] p-1 rounded-lg border border-white/5">
          <button
            onClick={() => setMode('cylinder')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
              mode === 'cylinder'
                ? 'bg-[#96E071] text-black font-bold shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
            title="3D Orbit Cylinder Mode"
          >
            <Rotate3d className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Orbit Cylinder</span>
          </button>

          <button
            onClick={() => setMode('stack')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
              mode === 'stack'
                ? 'bg-[#96E071] text-black font-bold shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
            title="3D Isometric Stack Mode"
          >
            <Layers className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Layer Stack</span>
          </button>

          <button
            onClick={() => setMode('scrubber')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
              mode === 'scrubber'
                ? 'bg-[#96E071] text-black font-bold shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
            title="Radar Wave Scrubber Mode"
          >
            <Activity className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Radar Wave</span>
          </button>

          <button
            onClick={() => setMode('grid')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded-md transition-all ${
              mode === 'grid'
                ? 'bg-[#96E071] text-black font-bold shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
            title="Forensic Table View"
          >
            <LayoutGrid className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Table Grid</span>
          </button>

          {mode !== 'grid' && (
            <button
              onClick={() => setIsAutoPlay(!isAutoPlay)}
              className={`px-2.5 py-1 text-xs font-mono rounded-md ml-1 transition-all flex items-center gap-1 ${
                isAutoPlay ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-gray-500 hover:text-gray-300'
              }`}
              title="Toggle auto orbit"
            >
              <Sparkles className="w-3 h-3" />
              <span>{isAutoPlay ? 'Auto ON' : 'Auto'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Visual Stage */}
      <div
        ref={containerRef}
        onMouseDown={mode !== 'grid' ? handleMouseDown : undefined}
        onMouseUp={mode !== 'grid' ? handleMouseUp : undefined}
        onTouchStart={mode !== 'grid' ? handleTouchStart : undefined}
        onTouchEnd={mode !== 'grid' ? handleTouchEnd : undefined}
        className={`relative w-full ${
          mode === 'grid' ? 'min-h-[380px] p-6' : 'h-[390px] md:h-[450px]'
        } bg-gradient-to-b from-[#0F1117] via-[#0C0D12] to-[#0A0B0E] border-x border-b border-[#2A2E3B] overflow-hidden flex items-center justify-center ${
          mode !== 'grid' ? 'cursor-grab active:cursor-grabbing perspective-1000' : ''
        }`}
      >
        {/* Subtle Cyber Radial Backdrop */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_40%,rgba(150,224,113,0.05),transparent_70%)] pointer-events-none" />
        <div className="absolute inset-0 cyber-grid opacity-20 pointer-events-none" />

        {/* ========================================================================= */}
        {/* MODE 1: 3D CYLINDER ORBIT (FIXED SPACING & NO CARD OVERLAPPING)           */}
        {/* ========================================================================= */}
        {mode === 'cylinder' && (
          <div className="relative w-full h-full flex items-center justify-center preserve-3d">
            {items.map((item, idx) => {
              let offset = idx - currentIndex;
              if (offset > total / 2) offset -= total;
              if (offset < -total / 2) offset += total;

              // Only render items within safe field of view (-2 to +2) to eliminate cluttered back-cards
              const isVisible = Math.abs(offset) <= 2;
              if (!isVisible) return null;

              // Calculated with generous separation so 310px cards never collide with each other
              const translateX = offset * 330; // 330px step > 300px card width ensures clean gap
              const translateZ = 160 - Math.abs(offset) * 85;
              const rotateY = offset * 22; // subtle angle
              const scale = 1 - Math.abs(offset) * 0.12;
              const opacity = 1 - Math.abs(offset) * 0.35;
              const isActive = idx === currentIndex;

              const isAi = Boolean(item.is_ai_generated);
              const conf = typeof item.confidence_percentage === 'number' ? item.confidence_percentage : 95;
              const attrName = item.generator_attribution?.attributed_family || (isAi ? 'Diffusion / Latent AI' : 'Authentic Camera Sensor');

              return (
                <div
                  key={item.id || idx}
                  onClick={() => onSelectIndex(idx)}
                  style={{
                    transform: `translateX(${translateX}px) translateZ(${translateZ}px) rotateY(${rotateY}deg) scale(${scale})`,
                    opacity: Math.max(0.18, opacity),
                    zIndex: 50 - Math.abs(offset) * 10,
                    transition: 'all 0.45s cubic-bezier(0.2, 0.8, 0.2, 1)',
                  }}
                  className={`absolute w-[280px] md:w-[310px] h-[345px] rounded-xl border bg-[#141620]/95 backdrop-blur-md p-4 shadow-2xl flex flex-col justify-between cursor-pointer overflow-hidden transition-all ${
                    isActive
                      ? 'border-[#96E071] ring-2 ring-[#96E071]/30 glow-green'
                      : 'border-white/10 hover:border-white/25 hover:bg-[#181B26]'
                  }`}
                >
                  {/* Card Header */}
                  <div className="flex items-center justify-between border-b border-white/5 pb-2.5">
                    <div className="flex items-center gap-1.5 truncate max-w-[170px]">
                      <span className="font-mono text-[11px] text-[#96E071] font-bold">#{idx + 1}</span>
                      <span className="font-mono text-xs text-white truncate font-medium">{item.image_name}</span>
                    </div>
                    <span
                      className={`font-mono text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                        isAi
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : 'bg-[#96E071]/20 text-[#96E071] border border-[#96E071]/30'
                      }`}
                    >
                      {isAi ? 'Synthetic' : 'Authentic'}
                    </span>
                  </div>

                  {/* Card Image Preview */}
                  <div className="relative w-full h-[155px] bg-[#0A0B0E] rounded-lg border border-white/5 overflow-hidden my-2 group">
                    <img
                      src={item.preview_url}
                      alt={item.image_name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    
                    {/* Confidence pill */}
                    <div className="absolute bottom-2 right-2 bg-black/85 backdrop-blur-md px-2.5 py-0.5 rounded font-mono text-xs font-bold text-white border border-white/10 shadow-sm">
                      {conf}%
                    </div>
                  </div>

                  {/* Card Metadata Details */}
                  <div className="space-y-1.5 font-mono text-[11px] py-1">
                    <div className="flex justify-between text-gray-400">
                      <span>Attribution:</span>
                      <span className="text-white truncate max-w-[150px] font-semibold text-right">
                        {attrName}
                      </span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Signal Verdict:</span>
                      <span className={`font-semibold ${isAi ? 'text-red-400' : 'text-[#96E071]'}`}>
                        {isAi ? 'Artifacts Flagged' : 'Passed Verified'}
                      </span>
                    </div>
                  </div>

                  {/* Card Action Button */}
                  {isActive ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onInspectItem?.(item);
                      }}
                      className="mt-1 w-full py-2 bg-[#96E071] hover:bg-[#a9f583] text-black font-mono font-bold text-xs rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-md cursor-pointer"
                    >
                      <Eye className="w-4 h-4" />
                      <span>Inspect in Workbench</span>
                    </button>
                  ) : (
                    <div className="text-center font-mono text-[11px] text-gray-500 py-1.5 bg-black/30 rounded border border-white/5">
                      Click to Focus
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODE 2: 3D ISOMETRIC LAYER STACK                                         */}
        {/* ========================================================================= */}
        {mode === 'stack' && (
          <div className="relative w-full h-full flex items-center justify-center preserve-3d">
            {items.map((item, idx) => {
              const offset = idx - currentIndex;
              // Show up to 5 cards in isometric depth
              if (offset < 0 || offset > 4) return null;

              const translateX = offset * 28;
              const translateY = offset * -14;
              const translateZ = -offset * 65;
              const rotateY = -18;
              const rotateX = 12;
              const opacity = 1 - offset * 0.18;
              const isActive = offset === 0;

              return (
                <div
                  key={item.id || idx}
                  onClick={() => onSelectIndex(idx)}
                  style={{
                    transform: `translateX(${translateX}px) translateY(${translateY}px) translateZ(${translateZ}px) rotateY(${rotateY}deg) rotateX(${rotateX}deg)`,
                    opacity,
                    zIndex: 50 - offset,
                    transition: 'all 0.5s cubic-bezier(0.25, 1, 0.5, 1)',
                  }}
                  className={`absolute w-[270px] md:w-[310px] h-[330px] rounded-lg border bg-[#14161d]/95 backdrop-blur-md p-4 shadow-2xl flex flex-col justify-between cursor-pointer ${
                    isActive
                      ? 'border-[#96E071] ring-2 ring-[#96E071]/30 glow-green'
                      : 'border-white/15 hover:border-white/40'
                  }`}
                >
                  <div className="flex justify-between items-center border-b border-white/10 pb-2">
                    <span className="font-mono text-xs font-bold text-white">
                      STACK LAYER #{idx + 1}
                    </span>
                    <span
                      className={`font-mono text-[10px] px-2 py-0.5 rounded font-bold ${
                        item.is_ai_generated ? 'text-red-400 bg-red-500/20' : 'text-[#96E071] bg-[#96E071]/20'
                      }`}
                    >
                      {item.prediction}
                    </span>
                  </div>

                  <div className="relative w-full h-[160px] bg-black rounded overflow-hidden my-2">
                    <img
                      src={item.preview_url}
                      alt={item.image_name}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-sm px-2 py-0.5 rounded font-mono text-[10px] text-gray-300">
                      {item.generator_attribution.attributed_family}
                    </div>
                  </div>

                  <div className="space-y-1 font-mono text-[11px] text-gray-300">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Calibrated Conf:</span>
                      <span className="font-bold text-[#96E071]">{item.confidence_percentage}%</span>
                    </div>
                    <p className="text-gray-400 text-[10px] line-clamp-1 italic">
                      {item.explanation}
                    </p>
                  </div>

                  {isActive ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onInspectItem?.(item);
                      }}
                      className="w-full py-1.5 bg-[#96E071] hover:bg-[#a9f583] text-black font-mono font-bold text-xs rounded transition-colors flex items-center justify-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect Active Layer</span>
                    </button>
                  ) : (
                    <div className="text-center font-mono text-[10px] text-gray-500">
                      Click to bring to top
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODE 3: RADAR WAVEFORM SCRUBBER                                           */}
        {/* ========================================================================= */}
        {mode === 'scrubber' && (
          <div className="relative w-full h-full flex flex-col items-center justify-center px-6">
            {/* Center Focus Card */}
            {items[currentIndex] && (
              <div className="relative w-[300px] md:w-[360px] h-[260px] rounded-lg border border-[#96E071] bg-[#14161d]/90 p-4 shadow-2xl flex flex-col justify-between mb-4">
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs text-[#96E071] font-bold">
                    RADAR TARGET: {items[currentIndex].image_name}
                  </span>
                  <span className="font-mono text-xs text-white font-bold">
                    {items[currentIndex].confidence_percentage}% CONF
                  </span>
                </div>

                <div className="flex gap-3 my-2 h-[130px]">
                  <div className="relative w-1/2 h-full rounded overflow-hidden border border-white/10">
                    <img
                      src={items[currentIndex].preview_url}
                      alt={items[currentIndex].image_name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="relative w-1/2 h-full rounded overflow-hidden border border-white/10 bg-black">
                    <img
                      src={items[currentIndex].gradcam_heatmap}
                      alt="Heatmap"
                      className="w-full h-full object-cover opacity-80"
                    />
                    <span className="absolute bottom-1 right-1 bg-black/80 text-[8px] font-mono px-1 rounded text-[#96E071]">
                      GRAD-CAM
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => onInspectItem?.(items[currentIndex])}
                  className="w-full py-1.5 bg-[#96E071] hover:bg-[#a9f583] text-black font-mono font-bold text-xs rounded transition-colors flex items-center justify-center gap-1.5"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect in Workbench</span>
                </button>
              </div>
            )}

            {/* Interactive Waveform Radar Scrubber Bar */}
            <div className="w-full max-w-xl flex flex-col gap-2">
              <div className="flex justify-between font-mono text-[10px] text-gray-400">
                <span>RADAR TIMELINE SCAN</span>
                <span>SCRUB TO JUMP</span>
              </div>
              <div className="relative w-full h-10 bg-[#161822] rounded border border-white/10 flex items-center px-2">
                {/* Audio/Frequency Bars visualization */}
                <div className="absolute inset-0 flex items-center justify-between px-3 opacity-30 pointer-events-none">
                  {Array.from({ length: 40 }).map((_, i) => (
                    <div
                      key={i}
                      style={{
                        height: `${20 + Math.sin(i * 0.5) * 60}%`,
                      }}
                      className="w-0.5 bg-[#96E071]"
                    />
                  ))}
                </div>

                {/* Radar Pips for each item */}
                <div className="relative w-full flex justify-between items-center z-10">
                  {items.map((it, idx) => (
                    <button
                      key={idx}
                      onClick={() => onSelectIndex(idx)}
                      className={`relative w-7 h-7 rounded-full flex items-center justify-center font-mono text-xs font-bold transition-all ${
                        idx === currentIndex
                          ? 'bg-[#96E071] text-black ring-4 ring-[#96E071]/30 scale-125'
                          : it.is_ai_generated
                          ? 'bg-red-500/40 text-red-300 hover:bg-red-500/70 border border-red-500/50'
                          : 'bg-emerald-500/40 text-emerald-300 hover:bg-emerald-500/70 border border-emerald-500/50'
                      }`}
                    >
                      {idx + 1}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* MODE 4: FORENSIC TABLE GRID VIEW (PROFESSIONAL AUDIT LIST)                */}
        {/* ========================================================================= */}
        {mode === 'grid' && (
          <div className="w-full overflow-x-auto">
            <table className="w-full border-collapse font-sans text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-gray-400 font-mono text-[11px] uppercase tracking-wider">
                  <th className="py-3 px-3">#</th>
                  <th className="py-3 px-3">Preview</th>
                  <th className="py-3 px-3">File Name</th>
                  <th className="py-3 px-3">Verdict</th>
                  <th className="py-3 px-3">Confidence</th>
                  <th className="py-3 px-3">Attribution</th>
                  <th className="py-3 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono">
                {items.map((item, idx) => {
                  const isSelected = idx === currentIndex;
                  return (
                    <tr
                      key={item.id || idx}
                      onClick={() => onSelectIndex(idx)}
                      className={`transition-colors cursor-pointer ${
                        isSelected ? 'bg-[#96E071]/10 text-white' : 'hover:bg-white/5 text-gray-300'
                      }`}
                    >
                      <td className="py-3 px-3 font-bold text-[#96E071]">
                        {String(idx + 1).padStart(2, '0')}
                      </td>
                      <td className="py-2 px-3">
                        <div className="w-10 h-10 rounded-md overflow-hidden bg-black border border-white/10">
                          <img
                            src={item.preview_url}
                            alt={item.image_name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      </td>
                      <td className="py-3 px-3 font-medium text-white max-w-[180px] truncate">
                        {item.image_name}
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                            item.is_ai_generated
                              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                              : 'bg-[#96E071]/20 text-[#96E071] border border-[#96E071]/30'
                          }`}
                        >
                          {item.is_ai_generated ? (
                            <AlertTriangle className="w-3 h-3" />
                          ) : (
                            <ShieldCheck className="w-3 h-3" />
                          )}
                          <span>{item.prediction}</span>
                        </span>
                      </td>
                      <td className="py-3 px-3 font-bold">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-[#252834] rounded-full overflow-hidden">
                            <div
                              style={{ width: `${item.confidence_percentage}%` }}
                              className={`h-full ${item.is_ai_generated ? 'bg-red-400' : 'bg-[#96E071]'}`}
                            />
                          </div>
                          <span>{item.confidence_percentage}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-gray-400 text-[11px] truncate max-w-[160px]">
                        {item.generator_attribution?.attributed_family || 'Standard Model'}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onInspectItem?.(item);
                          }}
                          className="px-3 py-1.5 rounded-md bg-[#1C1F2B] hover:bg-[#96E071] text-[#96E071] hover:text-black border border-[#96E071]/30 font-semibold text-[11px] transition-all inline-flex items-center gap-1 cursor-pointer"
                        >
                          <Eye className="w-3 h-3" />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* 3D Stage Navigation Chevrons */}
        {mode !== 'grid' && (
          <>
            <button
              onClick={() => onSelectIndex((currentIndex - 1 + total) % total)}
              className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/70 hover:bg-[#96E071] text-white hover:text-black border border-white/15 hover:border-[#96E071] flex items-center justify-center transition-all z-40 backdrop-blur-md cursor-pointer shadow-lg"
              title="Previous Item (Left Arrow / A)"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => onSelectIndex((currentIndex + 1) % total)}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/70 hover:bg-[#96E071] text-white hover:text-black border border-white/15 hover:border-[#96E071] flex items-center justify-center transition-all z-40 backdrop-blur-md cursor-pointer shadow-lg"
              title="Next Item (Right Arrow / D)"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </>
        )}
      </div>

      {/* Bottom Interactive Pagination Bar */}
      <div className="w-full flex flex-wrap items-center justify-between gap-4 px-5 py-3.5 bg-[#12141C] border-x border-b border-[#2A2E3B] rounded-b-xl">
        {/* Quick Page Jump Buttons */}
        <div className="flex items-center gap-2 overflow-x-auto py-1">
          <button
            onClick={() => onSelectIndex((currentIndex - 1 + total) % total)}
            className="px-3 py-1.5 rounded-md bg-[#181B26] hover:bg-[#232736] text-gray-300 hover:text-white font-mono text-xs border border-white/10 flex items-center gap-1 transition-all cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span>PREV</span>
          </button>

          {items.map((_, idx) => (
            <button
              key={idx}
              onClick={() => onSelectIndex(idx)}
              className={`w-8 h-8 rounded-md font-mono text-xs font-bold transition-all cursor-pointer ${
                idx === currentIndex
                  ? 'bg-[#96E071] text-black shadow-md scale-105'
                  : 'bg-[#181B26] hover:bg-[#232736] text-gray-400 hover:text-white border border-white/5'
              }`}
            >
              {String(idx + 1).padStart(2, '0')}
            </button>
          ))}

          <button
            onClick={() => onSelectIndex((currentIndex + 1) % total)}
            className="px-3 py-1.5 rounded-md bg-[#181B26] hover:bg-[#232736] text-gray-300 hover:text-white font-mono text-xs border border-white/10 flex items-center gap-1 transition-all cursor-pointer"
          >
            <span>NEXT</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Keyboard Hotkeys Legend */}
        <div className="hidden lg:flex items-center gap-2 font-mono text-[11px] text-gray-400">
          <span>HOTKEYS:</span>
          <kbd className="px-2 py-0.5 bg-[#181B26] border border-white/10 rounded text-gray-300 font-semibold">← / A</kbd>
          <kbd className="px-2 py-0.5 bg-[#181B26] border border-white/10 rounded text-gray-300 font-semibold">→ / D</kbd>
          <kbd className="px-2 py-0.5 bg-[#181B26] border border-white/10 rounded text-gray-300 font-semibold">1-9</kbd>
        </div>
      </div>
    </div>
  );
};
