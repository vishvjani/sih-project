import React, { useState, useRef } from 'react';
import type { AnalysisResult } from '../../types';
import { Creative3DPagination } from '../pagination/Creative3DPagination';
import { PRESET_SAMPLES, analyzeBatch } from '../../services/api';
import { GradCamViewer } from '../detector/GradCamViewer';
import { 
  Layers, 
  Eye, 
  RotateCw, 
  Plus 
} from 'lucide-react';

interface BatchStudioProps {
  onInspectItem: (item: AnalysisResult) => void;
  className?: string;
}

export const BatchStudio: React.FC<BatchStudioProps> = ({
  onInspectItem,
  className = '',
}) => {
  const [items, setItems] = useState<AnalysisResult[]>(PRESET_SAMPLES);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleBatchUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const fileArray = Array.from(files).slice(0, 10);

    setIsProcessing(true);
    try {
      const batchRes = await analyzeBatch(fileArray);
      if (batchRes.results && batchRes.results.length > 0) {
        setItems(prev => [...batchRes.results, ...prev]);
        setSelectedIndex(0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const activeItem = items[selectedIndex] || items[0];
  const totalSynthetic = items.filter(i => i.is_ai_generated).length;
  const totalAuthentic = items.filter(i => !i.is_ai_generated).length;

  return (
    <section className={`w-full max-w-[1280px] mx-auto flex flex-col gap-8 py-4 ${className}`}>
      {/* Studio Header */}
      <div className="flex flex-wrap items-center justify-between gap-6 p-6 md:p-8 bg-[#12141C] border border-[#2A2E3B] rounded-xl shadow-lg">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <Layers className="w-6 h-6 text-[#96E071]" />
            <h2 className="text-2xl font-sans font-bold text-white tracking-tight">
              3D Batch Deck & Forensic Stream
            </h2>
          </div>
          <p className="font-mono text-xs text-gray-400">
            Browse and audit multiple media artifacts simultaneously using 3D Orbit Cylinder, Isometric Stack, Radar Scrubber, or Table Grid.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={(e) => handleBatchUpload(e.target.files)}
            className="hidden"
          />

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isProcessing}
            className="flex items-center gap-2.5 px-5 py-2.5 bg-[#96E071] hover:bg-[#a9f583] text-black font-sans font-semibold text-xs rounded-lg transition-all glow-green cursor-pointer shadow-md disabled:opacity-50"
          >
            {isProcessing ? (
              <>
                <RotateCw className="w-4 h-4 animate-spin" />
                <span>Analyzing Batch Stream...</span>
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                <span>Upload Batch Images (Up to 10)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Batch Overview KPI Pill Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-xs">
        <div className="p-4 bg-[#141620] border border-[#2A2E3B] rounded-xl flex items-center justify-between">
          <span className="text-gray-400">TOTAL ARTIFACTS IN DECK:</span>
          <span className="text-lg font-bold text-white">{items.length} Files</span>
        </div>
        <div className="p-4 bg-[#141620] border border-red-500/20 rounded-xl flex items-center justify-between">
          <span className="text-gray-400">FLAGGED SYNTHETIC / AI:</span>
          <span className="text-lg font-bold text-red-400">{totalSynthetic} Flagged</span>
        </div>
        <div className="p-4 bg-[#141620] border border-emerald-500/20 rounded-xl flex items-center justify-between">
          <span className="text-gray-400">VERIFIED AUTHENTIC CAMERA:</span>
          <span className="text-lg font-bold text-[#96E071]">{totalAuthentic} Passed</span>
        </div>
      </div>

      {/* Primary 3D Multi-Mode Creative Pagination Component */}
      {items.length > 0 ? (
        <Creative3DPagination
          items={items}
          currentIndex={selectedIndex}
          onSelectIndex={(idx) => setSelectedIndex(idx)}
          onInspectItem={(item) => onInspectItem(item)}
        />
      ) : (
        <div 
          onClick={() => fileInputRef.current?.click()}
          className="w-full py-16 border-2 border-dashed border-[#2A2E3B] hover:border-[#96E071] bg-[#12141C] rounded-xl flex flex-col items-center justify-center gap-3 cursor-pointer transition-all"
        >
          <Plus className="w-10 h-10 text-[#96E071] animate-bounce" />
          <p className="font-sans font-semibold text-white text-base">No batch images loaded yet</p>
          <p className="font-mono text-xs text-gray-400">Click to upload up to 10 images for instant forensic analysis</p>
        </div>
      )}

      {/* Selected Item Quick Inspection Panel */}
      {activeItem && items.length > 0 && (
        <div className="w-full grid grid-cols-1 lg:grid-cols-12 gap-8 p-6 md:p-8 bg-[#12141C] border border-[#2A2E3B] rounded-xl shadow-xl">
          {/* Left Grad-CAM View */}
          <div className="lg:col-span-7 flex flex-col justify-between">
            <div className="mb-2">
              <span className="font-mono text-[11px] text-[#96E071] uppercase tracking-wider font-semibold">
                LOCALIZED VISUAL EVIDENCE // FOCUS ITEM #{selectedIndex + 1}
              </span>
            </div>
            <GradCamViewer
              originalImage={activeItem.preview_url || ''}
              heatmapImage={activeItem.gradcam_heatmap}
              isAi={activeItem.is_ai_generated}
            />
          </div>

          {/* Right Forensic Breakdown */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex justify-between items-start border-b border-white/5 pb-3">
                <div>
                  <span className="font-mono text-[10px] text-gray-400">CURRENT TARGET FILE</span>
                  <h3 className="font-sans font-bold text-white text-lg truncate max-w-[280px]">
                    {activeItem.image_name}
                  </h3>
                </div>
                <span
                  className={`font-mono text-xs font-bold px-3 py-1 rounded-full ${
                    activeItem.is_ai_generated
                      ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                      : 'bg-[#96E071]/20 text-[#96E071] border border-[#96E071]/30'
                  }`}
                >
                  {activeItem.prediction}
                </span>
              </div>

              {/* Confidence Stat */}
              <div className="p-4 bg-[#181B26] border border-white/5 rounded-xl font-mono text-xs flex justify-between items-center">
                <span className="text-gray-400">Calibrated Likelihood:</span>
                <span className="text-xl font-bold text-white">{activeItem.confidence_percentage}%</span>
              </div>

              {/* Attribution */}
              <div className="p-4 bg-[#181B26] border border-white/5 rounded-xl font-mono text-xs space-y-1.5">
                <div className="flex justify-between text-gray-400">
                  <span>Attributed Family:</span>
                  <span className="text-white font-bold">{activeItem.generator_attribution?.attributed_family || 'Generic Model'}</span>
                </div>
                {activeItem.generator_attribution?.notes && (
                  <p className="text-[10px] text-gray-400 italic">
                    {activeItem.generator_attribution.notes}
                  </p>
                )}
              </div>

              {/* Explanation */}
              <div className="p-4 bg-[#181B26] border border-white/5 rounded-xl text-xs space-y-2">
                <span className="font-mono text-[10px] text-gray-400 font-semibold tracking-wider uppercase">
                  FORENSIC ARTIFACT EVIDENCE:
                </span>
                <p className="text-gray-300 leading-relaxed font-sans text-xs">
                  {activeItem.explanation}
                </p>
              </div>
            </div>

            <button
              onClick={() => onInspectItem(activeItem)}
              className="w-full py-3 bg-[#1E212D] hover:bg-[#96E071] text-[#96E071] hover:text-black border border-[#96E071]/30 hover:border-[#96E071] font-mono text-xs font-bold rounded-lg transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md"
            >
              <Eye className="w-4 h-4" />
              <span>Open in Full Workbench</span>
            </button>
          </div>
        </div>
      )}
    </section>
  );
};
