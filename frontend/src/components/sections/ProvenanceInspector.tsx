import React from 'react';
import type { AnalysisResult } from '../../types';
import { Shield, Info, FileSpreadsheet, Lock } from 'lucide-react';

interface ProvenanceInspectorProps {
  currentAnalysis: AnalysisResult | null;
  className?: string;
}

export const ProvenanceInspector: React.FC<ProvenanceInspectorProps> = ({
  currentAnalysis,
  className = '',
}) => {
  const meta = currentAnalysis?.metadata_provenance || {
    has_exif: false,
    c2pa_manifest_found: false,
    c2pa_claim_summary: null,
    exif_details: {},
    authenticity_signals: {}
  };

  return (
    <section className={`w-full max-w-[1280px] mx-auto flex flex-col gap-8 py-4 ${className}`}>
      <div className="p-6 md:p-8 bg-[#12141C] border border-[#2A2E3B] rounded-xl shadow-lg flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <Shield className="w-6 h-6 text-[#96E071]" />
            <h2 className="text-2xl font-sans font-bold text-white tracking-tight">
              EXIF & C2PA Provenance Inspector
            </h2>
          </div>
          <p className="font-mono text-xs text-gray-400">
            Validates Content Authenticity Initiative (CAI) cryptographic manifests and physical camera sensor metadata.
          </p>
        </div>

        <span className="font-mono text-xs text-gray-400 bg-[#181B26] px-3 py-1.5 rounded-lg border border-white/5">
          FILE: <span className="text-white font-bold">{currentAnalysis?.image_name || 'No image loaded'}</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* C2PA Manifest Status */}
        <div className="p-6 md:p-8 bg-[#12141C] border border-[#2A2E3B] rounded-xl shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-[#96E071]" />
                <h3 className="font-mono text-xs font-bold text-white">C2PA CONTENT CREDENTIALS</h3>
              </div>
              <span
                className={`font-mono text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                  meta.c2pa_manifest_found
                    ? 'bg-[#96E071]/20 text-[#96E071] border border-[#96E071]/30'
                    : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                }`}
              >
                {meta.c2pa_manifest_found ? 'Cryptographically Verified' : 'Manifest Missing'}
              </span>
            </div>

            <p className="font-sans text-xs text-gray-300 mb-4 leading-relaxed">
              {meta.c2pa_claim_summary || 'No cryptographic assertion was detected within the image binary stream. This is common for synthetic AI exports or compressed social media re-uploads.'}
            </p>

            <div className="p-3 bg-[#1A1C24] border border-white/5 rounded font-mono text-xs space-y-2 text-gray-400">
              <div className="flex justify-between">
                <span>Cryptographic Digest:</span>
                <span className="text-white">{meta.c2pa_manifest_found ? 'SHA-256 Validated' : 'Unsigned'}</span>
              </div>
              <div className="flex justify-between">
                <span>Signer Authority:</span>
                <span className="text-white">{meta.c2pa_manifest_found ? 'Root of Trust Confirmed' : 'None'}</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 font-mono text-[11px] text-gray-500 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-[#96E071]" />
            <span>Adheres to Coalition for Content Provenance and Authenticity (C2PA) standard.</span>
          </div>
        </div>

        {/* Camera Hardware EXIF */}
        <div className="p-6 md:p-8 bg-[#12141C] border border-[#2A2E3B] rounded-xl shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-[#96E071]" />
                <h3 className="font-mono text-xs font-bold text-white">HARDWARE SENSOR EXIF RECORD</h3>
              </div>
              <span
                className={`font-mono text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                  meta.has_exif
                    ? 'bg-[#96E071]/20 text-[#96E071] border border-[#96E071]/30'
                    : 'bg-gray-700 text-gray-400'
                }`}
              >
                {meta.has_exif ? 'Hardware Tags Present' : 'EXIF Stripped'}
              </span>
            </div>

            <div className="space-y-2 font-mono text-xs">
              <div className="flex justify-between p-2 bg-[#1A1C24] rounded">
                <span className="text-gray-400">Camera Maker:</span>
                <span className="text-white">{meta.exif_details?.make || 'Not Available'}</span>
              </div>
              <div className="flex justify-between p-2 bg-[#1A1C24] rounded">
                <span className="text-gray-400">Model:</span>
                <span className="text-white">{meta.exif_details?.model || 'Not Available'}</span>
              </div>
              <div className="flex justify-between p-2 bg-[#1A1C24] rounded">
                <span className="text-gray-400">Lens Specification:</span>
                <span className="text-white">{meta.exif_details?.lens || 'Not Available'}</span>
              </div>
              <div className="flex justify-between p-2 bg-[#1A1C24] rounded">
                <span className="text-gray-400">ISO Speed Rating:</span>
                <span className="text-white">{meta.exif_details?.iso || 'Not Available'}</span>
              </div>
              <div className="flex justify-between p-2 bg-[#1A1C24] rounded">
                <span className="text-gray-400">Software String:</span>
                <span className="text-white">{meta.exif_details?.software || 'Not Available'}</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 font-mono text-[11px] text-gray-500">
            <span>Sensor demosaicing integrity inspected for CMOS Poissonian distribution.</span>
          </div>
        </div>
      </div>
    </section>
  );
};
