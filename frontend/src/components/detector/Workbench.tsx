import React, { useState, useRef, useEffect } from 'react';
import type { AnalysisResult } from '../../types';
import { analyzeImage, PRESET_SAMPLES } from '../../services/api';
import { HologramScanner } from '../3d/HologramScanner';
import { GradCamViewer } from './GradCamViewer';
import { 
  UploadCloud, 
  FileText, 
  ShieldCheck, 
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface WorkbenchProps {
  currentAnalysis: AnalysisResult | null;
  onAnalysisComplete: (result: AnalysisResult) => void;
  className?: string;
}

export const Workbench: React.FC<WorkbenchProps> = ({
  currentAnalysis,
  onAnalysisComplete,
  className = '',
}) => {
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [dragOver, setDragOver] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [timerActive, setTimerActive] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Timer simulation like aiornot.com
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (timerActive) {
      interval = setInterval(() => {
        setElapsedSeconds(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [timerActive]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `[00:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}]`;
  };

  const handleFileUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload a valid image file (PNG, JPG, WebP, GIF).');
      return;
    }

    setIsScanning(true);
    setTimerActive(true);
    setElapsedSeconds(0);

    try {
      const result = await analyzeImage(file);
      onAnalysisComplete(result);

      if (!result.is_ai_generated) {
        // Authentic celebration confetti
        confetti({
          particleCount: 45,
          spread: 60,
          origin: { y: 0.7 },
          colors: ['#96E071', '#38bdf8', '#ffffff']
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsScanning(false);
      setTimerActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const activeResult = currentAnalysis || PRESET_SAMPLES[0];

  // Calculations for circular gauges (radius = 48, circumference = ~301.6)
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const rawConf = typeof activeResult.confidence_percentage === 'number' 
    ? activeResult.confidence_percentage 
    : parseFloat(String(activeResult.confidence_percentage).replace('%', '')) || 95;
  const aiScore = Math.max(1, Math.min(99, activeResult.is_ai_generated ? rawConf : (100 - rawConf)));
  const aiStrokeDashoffset = circumference - (aiScore / 100) * circumference;

  const deepfakeProb = activeResult.generator_attribution?.family_probabilities?.['GAN/StyleGAN'];
  const deepfakeScore = typeof deepfakeProb === 'number'
    ? Math.round(deepfakeProb * 100)
    : activeResult.is_ai_generated ? Math.max(12, Math.round(aiScore * 0.45)) : 3;
  const deepfakeStrokeDashoffset = circumference - (deepfakeScore / 100) * circumference;

  return (
    <div className={`w-full max-w-[1280px] mx-auto flex flex-col gap-8 ${className}`}>
      {/* Workbench Container Matching obsidian card */}
      <div className="relative w-full border border-[#2A2E3B] bg-[#12141C] shadow-2xl rounded-xl overflow-hidden">
        {/* Top Workbench Tabs Bar */}
        <div className="h-[48px] border-b border-[#2A2E3B] px-5 flex items-center justify-between bg-[#171924]">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 text-xs font-mono font-bold bg-[#252836] text-[#96E071] border border-[#96E071]/30 rounded-md">
              IMAGE INSPECTION WORKBENCH
            </span>
            <span className="text-gray-400 font-mono text-xs hidden sm:inline">
              // NEURAL BACKBONE: ConvNeXt-Tiny + Platt Calibrated
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 font-mono text-xs text-gray-300">
              <span className={`w-2.5 h-2.5 rounded-full ${isScanning ? 'bg-yellow-400 animate-ping' : 'bg-[#96E071]'}`} />
              <span className="hidden sm:inline font-semibold">
                {isScanning ? 'PROCESSING INFERENCE...' : 'SYSTEM READY'}
              </span>
            </div>
          </div>
        </div>

        {/* Workbench Body: Two-Column Split Grid */}
        <div className="w-full flex flex-col lg:flex-row min-h-[540px]">
          {/* ========================================================================= */}
          {/* LEFT COLUMN: UPLOAD & DROPZONE WITH 3D SCANNER                            */}
          {/* ========================================================================= */}
          <div className="w-full lg:w-[50%] p-6 md:p-8 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-[#2A2E3B] bg-[#0F1117]">
            {/* Drag & Drop Area */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative w-full h-[320px] md:h-[360px] border-2 border-dashed rounded-xl transition-all flex flex-col items-center justify-center p-6 cursor-pointer overflow-hidden group ${
                dragOver
                  ? 'border-[#96E071] bg-[#96E071]/5 glow-green'
                  : 'border-[#2A2E3B] hover:border-[#96E071]/60 bg-[#141620]'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => {
                  if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
                }}
                className="hidden"
              />

              {/* Background Cyber Grid */}
              <div className="absolute inset-0 cyber-grid opacity-20 pointer-events-none" />

              {/* 3D Holographic Scanner Plane when active */}
              {isScanning ? (
                <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black/85 backdrop-blur-sm">
                  <HologramScanner isScanning={true} className="w-full h-[260px]" />
                  <div className="font-mono text-xs text-[#96E071] mt-2 flex items-center gap-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>DEEP SCANNING LATENT PIXEL ANOMALIES...</span>
                  </div>
                </div>
              ) : activeResult.preview_url ? (
                /* Show current preview with scanlines */
                <div className="relative w-full h-full flex items-center justify-center">
                  <img
                    src={activeResult.preview_url}
                    alt="Active Preview"
                    className="max-w-full max-h-full object-contain rounded"
                  />
                  <div className="absolute inset-0 scanlines opacity-20 pointer-events-none" />
                  
                  {/* Subtle 3D Holographic Overlay on hover */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 backdrop-blur-xs flex flex-col items-center justify-center pointer-events-none">
                    <UploadCloud className="w-10 h-10 text-[#96E071] mb-2 animate-bounce" />
                    <span className="font-mono text-xs text-white font-semibold">Drop or Click to Inspect New Image</span>
                    <span className="font-mono text-[10px] text-gray-400 mt-1">PNG, JPG, WEBP up to 50MB</span>
                  </div>
                </div>
              ) : (
                /* Initial Clean Drop Prompt */
                <div className="relative z-10 flex flex-col items-center text-center gap-3">
                  <div className="w-14 h-14 rounded-full bg-[#20232c] border border-white/10 flex items-center justify-center text-[#96E071] group-hover:scale-110 transition-transform">
                    <UploadCloud className="w-7 h-7" />
                  </div>
                  <div>
                    <p className="font-sans font-medium text-white text-base">
                      Drag and drop image here, or <span className="text-[#96E071] underline">browse</span>
                    </p>
                    <p className="font-mono text-[11px] text-gray-400 mt-1">
                      Supports: JPG, PNG, WEBP, GIF, TIFF
                    </p>
                  </div>
                </div>
              )}

              {/* Format Badge Bar inside dropzone */}
              <div className="absolute top-2.5 left-2.5 flex flex-col gap-0.5 font-mono text-[9px] text-gray-400 bg-black/60 backdrop-blur-sm px-2 py-1 rounded border border-white/5 pointer-events-none">
                <span>FORMAT: MULTI-RESOLUTION</span>
                <span>CHANNELS: RGB / HIGH-FREQUENCY EXAMINER</span>
              </div>
            </div>

            {/* Quick Test Preset Thumbnails Gallery */}
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-[11px] text-gray-400 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-[#96E071]" />
                  <span>TRY SAMPLE BENCHMARK IMAGES:</span>
                </span>
                <span className="font-mono text-[10px] text-gray-500">1-CLICK TEST</span>
              </div>

              <div className="grid grid-cols-6 gap-2">
                {PRESET_SAMPLES.map((preset, idx) => (
                  <button
                    key={preset.id || idx}
                    onClick={() => onAnalysisComplete(preset)}
                    className={`relative h-14 rounded overflow-hidden border transition-all group ${
                      activeResult.id === preset.id
                        ? 'border-[#96E071] ring-2 ring-[#96E071]/40'
                        : 'border-[#333] hover:border-gray-400'
                    }`}
                    title={preset.image_name}
                  >
                    <img
                      src={preset.preview_url}
                      alt={preset.image_name}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform"
                    />
                    <div className="absolute inset-0 bg-black/30 group-hover:bg-transparent transition-colors" />
                    <span
                      className={`absolute bottom-0.5 right-0.5 w-2 h-2 rounded-full ${
                        preset.is_ai_generated ? 'bg-red-500' : 'bg-[#96E071]'
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>

            {/* Bottom Telemetry HUD Bar */}
            <div className="mt-4 pt-3 border-t border-[#2A2A2A] flex items-center justify-between font-mono text-xs text-gray-400">
              <div className="flex items-center gap-2">
                <span className="text-red-400 font-bold">{formatTimer(elapsedSeconds)}</span>
                <span>{isScanning ? 'Scanning tensor layers...' : 'Analysis Complete.'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500 text-[11px]">FILE:</span>
                <span className="text-white text-[11px] max-w-[140px] truncate">{activeResult.image_name}</span>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* RIGHT COLUMN: GAUGES, BREAKDOWN & FORENSICS                               */}
          {/* ========================================================================= */}
          <div className="w-full lg:w-[50%] p-4 md:p-6 flex flex-col justify-between bg-[#14151C]">
            {/* Top Twin Circular Gauges */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {/* Gauge 1: AI Likelihood */}
              <div className="relative bg-[#1A1C24] border border-[#3A3A3A] p-3.5 rounded flex flex-col items-center justify-center">
                <div className="relative w-28 h-28 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
                    {/* Background Track Circle */}
                    <circle
                      cx="60"
                      cy="60"
                      r={radius}
                      stroke="#2C2E38"
                      strokeWidth="8"
                      fill="none"
                    />
                    {/* Dynamic Progress Arc */}
                    <circle
                      cx="60"
                      cy="60"
                      r={radius}
                      stroke={activeResult.is_ai_generated ? '#FF4D4D' : '#96E071'}
                      strokeWidth="8"
                      strokeDasharray={circumference}
                      strokeDashoffset={aiStrokeDashoffset}
                      strokeLinecap="round"
                      fill="none"
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  {/* Metric Readout in Center */}
                  <div className="absolute flex flex-col items-center text-center">
                    <span className="font-mono text-xl font-bold text-white leading-none">
                      {Math.round(aiScore)}%
                    </span>
                    <span className="font-mono text-[10px] text-gray-400 mt-0.5">
                      {activeResult.is_ai_generated ? 'AI LIKELY' : 'AUTHENTIC'}
                    </span>
                  </div>
                </div>
                <span className="font-mono text-[11px] font-semibold text-gray-300 mt-2">
                  AI PROBABILITY
                </span>
              </div>

              {/* Gauge 2: Deepfake & Synthetic Risk */}
              <div className="relative bg-[#1A1C24] border border-[#3A3A3A] p-3.5 rounded flex flex-col items-center justify-center">
                <div className="relative w-28 h-28 flex items-center justify-center">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
                    <circle
                      cx="60"
                      cy="60"
                      r={radius}
                      stroke="#2C2E38"
                      strokeWidth="8"
                      fill="none"
                    />
                    <circle
                      cx="60"
                      cy="60"
                      r={radius}
                      stroke={deepfakeScore > 50 ? '#FF4D4D' : '#38BDF8'}
                      strokeWidth="8"
                      strokeDasharray={circumference}
                      strokeDashoffset={deepfakeStrokeDashoffset}
                      strokeLinecap="round"
                      fill="none"
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center text-center">
                    <span className="font-mono text-xl font-bold text-white leading-none">
                      {deepfakeScore}%
                    </span>
                    <span className="font-mono text-[10px] text-gray-400 mt-0.5">
                      {deepfakeScore > 50 ? 'HIGH RISK' : 'LOW RISK'}
                    </span>
                  </div>
                </div>
                <span className="font-mono text-[11px] font-semibold text-gray-300 mt-2">
                  DEEPFAKE RISK
                </span>
              </div>
            </div>

            {/* Generator Family Breakdown Bars */}
            <div className="bg-[#181B26] border border-[#2A2E3B] p-5 rounded-xl mb-6 shadow-md">
              <div className="flex justify-between items-center mb-3">
                <span className="font-mono text-xs font-bold text-white tracking-wider">
                  DATA BREAKDOWN // GENERATOR ATTRIBUTION
                </span>
                <span className="font-mono text-[10px] text-[#96E071] font-semibold bg-[#96E071]/10 px-2 py-0.5 rounded border border-[#96E071]/20">
                  TOP: {activeResult.generator_attribution?.attributed_family || 'Evaluated Architecture'}
                </span>
              </div>

              <div className="space-y-3 font-mono text-[11px]">
                {/* FLUX.1 / Black Forest Labs */}
                <div>
                  <div className="flex justify-between text-gray-300 mb-1">
                    <span>FLUX.1 / Rectified Flow</span>
                    <span className="font-bold text-white">
                      {Math.round((activeResult.generator_attribution?.family_probabilities?.['FLUX.1'] || 0) * 100)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-[#252834] rounded-full overflow-hidden">
                    <div
                      style={{
                        width: `${(activeResult.generator_attribution?.family_probabilities?.['FLUX.1'] || 0) * 100}%`,
                      }}
                      className="h-full bg-[#96E071] transition-all duration-700"
                    />
                  </div>
                </div>

                {/* Midjourney v6 */}
                <div>
                  <div className="flex justify-between text-gray-300 mb-1">
                    <span>Midjourney v6.1</span>
                    <span className="font-bold text-white">
                      {Math.round((activeResult.generator_attribution?.family_probabilities?.['Midjourney'] || 0) * 100)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-[#252834] rounded-full overflow-hidden">
                    <div
                      style={{
                        width: `${(activeResult.generator_attribution?.family_probabilities?.['Midjourney'] || 0) * 100}%`,
                      }}
                      className="h-full bg-cyan-400 transition-all duration-700"
                    />
                  </div>
                </div>

                {/* DALL-E 3 / OpenAI */}
                <div>
                  <div className="flex justify-between text-gray-300 mb-1">
                    <span>DALL·E 3</span>
                    <span className="font-bold text-white">
                      {Math.round((activeResult.generator_attribution?.family_probabilities?.['DALL-E 3'] || 0) * 100)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-[#252834] rounded-full overflow-hidden">
                    <div
                      style={{
                        width: `${(activeResult.generator_attribution?.family_probabilities?.['DALL-E 3'] || 0) * 100}%`,
                      }}
                      className="h-full bg-yellow-400 transition-all duration-700"
                    />
                  </div>
                </div>

                {/* Authentic Physical Camera */}
                <div>
                  <div className="flex justify-between text-gray-300 mb-1">
                    <span>Authentic Camera Sensor</span>
                    <span className="font-bold text-white">
                      {Math.round((activeResult.generator_attribution?.family_probabilities?.['Authentic/Camera'] || (activeResult.is_ai_generated ? 0 : 0.98)) * 100)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-[#252834] rounded-full overflow-hidden">
                    <div
                      style={{
                        width: `${(activeResult.generator_attribution?.family_probabilities?.['Authentic/Camera'] || (activeResult.is_ai_generated ? 0 : 0.98)) * 100}%`,
                      }}
                      className="h-full bg-emerald-400 transition-all duration-700"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Embedded Grad-CAM Heatmap Viewer */}
            <div className="mb-6">
              <GradCamViewer
                originalImage={activeResult.preview_url || ''}
                heatmapImage={activeResult.gradcam_heatmap}
                isAi={activeResult.is_ai_generated}
              />
            </div>

            {/* Forensic Explanation Box */}
            <div className="bg-[#181B26] border border-[#2A2E3B] p-5 rounded-xl shadow-md">
              <div className="flex items-center gap-2 font-mono text-xs font-bold text-gray-200 mb-2">
                <FileText className="w-4 h-4 text-[#96E071]" />
                <span>EXPLAINABLE AI EVIDENCE SUMMARY</span>
              </div>
              <p className="font-sans text-xs text-gray-300 leading-relaxed">
                {activeResult.explanation}
              </p>

              {/* Provenance & EXIF Tag pill */}
              <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap items-center justify-between gap-3 font-mono text-[11px]">
                <div className="flex items-center gap-1.5">
                  <ShieldCheck className={`w-4 h-4 ${activeResult.metadata_provenance?.c2pa_manifest_found ? 'text-[#96E071]' : 'text-gray-500'}`} />
                  <span className="text-gray-400">C2PA CREDENTIALS:</span>
                  <span className="text-white font-bold">
                    {activeResult.metadata_provenance?.c2pa_manifest_found ? 'VERIFIED CRYPTOGRAPHIC MANIFEST' : 'NOT DETECTED'}
                  </span>
                </div>
                {activeResult.metadata_provenance?.exif_details?.make && (
                  <span className="text-gray-400 font-semibold">
                    HARDWARE: {activeResult.metadata_provenance.exif_details.make} {activeResult.metadata_provenance.exif_details.model || ''}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
