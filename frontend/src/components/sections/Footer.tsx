import React from 'react';
import { Shield, Terminal, ExternalLink, Code2 } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-[#08090C] border-t border-[#2A2A2A] py-12 px-4 mt-12">
      <div className="max-w-[1440px] mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
        {/* Col 1: Brand */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-[#161822] border border-[#96E071]/50 flex items-center justify-center text-[#96E071]">
              <Shield className="w-3.5 h-3.5" />
            </div>
            <span className="font-sans font-bold text-white text-lg tracking-tight">SignalScope</span>
          </div>
          <p className="font-sans text-xs text-gray-400 leading-relaxed">
            Explainable AI media authenticity detection engine with localized Grad-CAM heatmaps, Platt calibration, and C2PA provenance.
          </p>
          <div className="font-mono text-[10px] text-gray-500">
            ENGINE: ConvNeXt-Tiny // PyTorch // FastAPI
          </div>
        </div>

        {/* Col 2: Endpoints */}
        <div className="space-y-2 font-mono text-xs">
          <h4 className="font-bold text-white uppercase tracking-wider mb-2">API Endpoints</h4>
          <p className="text-gray-400 hover:text-[#96E071] transition-colors">POST /api/v1/analyze</p>
          <p className="text-gray-400 hover:text-[#96E071] transition-colors">POST /api/v1/analyze-batch</p>
          <p className="text-gray-400 hover:text-[#96E071] transition-colors">POST /api/v1/inspect-metadata</p>
          <p className="text-gray-400 hover:text-[#96E071] transition-colors">POST /api/v1/test-robustness</p>
          <p className="text-gray-400 hover:text-[#96E071] transition-colors">GET /api/v1/metrics</p>
        </div>

        {/* Col 3: Research & Standards */}
        <div className="space-y-2 font-mono text-xs">
          <h4 className="font-bold text-white uppercase tracking-wider mb-2">Integrations</h4>
          <p className="text-gray-400">C2PA / CAI Standard</p>
          <p className="text-gray-400">Grad-CAM Localized Maps</p>
          <p className="text-gray-400">Platt Probability Calibration</p>
          <p className="text-gray-400">Rectified Flow Invariants</p>
          <p className="text-gray-400">Poissonian Sensor Noise</p>
        </div>

        {/* Col 4: Repository */}
        <div className="space-y-3 font-mono text-xs">
          <h4 className="font-bold text-white uppercase tracking-wider mb-2">Source & Documentation</h4>
          <a
            href="https://github.com/manankaba2007-lgtm/sih.git"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-gray-300 hover:text-[#96E071] transition-colors"
          >
            <Code2 className="w-4 h-4" />
            <span>GitHub Repository</span>
            <ExternalLink className="w-3 h-3 text-gray-500" />
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-gray-300 hover:text-[#96E071] transition-colors"
          >
            <Terminal className="w-4 h-4" />
            <span>Swagger Interactive API</span>
            <ExternalLink className="w-3 h-3 text-gray-500" />
          </a>
        </div>
      </div>

      {/* Responsible AI Disclaimer Banner */}
      <div className="max-w-[1440px] mx-auto pt-6 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-[11px] text-gray-500">
        <p>
          RESPONSIBLE AI: Predictions are probabilistic likelihoods to aid human experts, not absolute legal determinations.
        </p>
        <p className="flex items-center gap-1 text-gray-400">
          Built for SIH with <span className="text-[#96E071]">●</span> React, Three.js & FastAPI
        </p>
      </div>
    </footer>
  );
};
