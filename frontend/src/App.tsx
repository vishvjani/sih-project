import React, { useState, useEffect } from 'react';
import type { AnalysisResult, ActiveTab } from './types';
import { PRESET_SAMPLES } from './services/api';
import { Header } from './components/sections/Header';
import { Hero } from './components/sections/Hero';
import { Workbench } from './components/detector/Workbench';
import { TrustTicker } from './components/sections/TrustTicker';
import { BatchStudio } from './components/sections/BatchStudio';
import { RobustnessLab } from './components/sections/RobustnessLab';
import { ProvenanceInspector } from './components/sections/ProvenanceInspector';
import { MetricsView } from './components/sections/MetricsView';
import { Footer } from './components/sections/Footer';
import { Creative3DPagination } from './components/pagination/Creative3DPagination';
import { Layers, ArrowRight, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('workbench');
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult>(PRESET_SAMPLES[0]);
  const [backendOnline, setBackendOnline] = useState<boolean>(false);
  const [showNotification, setShowNotification] = useState<string | null>(null);

  // Check FastAPI backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/v1/health', { method: 'GET' });
        if (res.ok) {
          setBackendOnline(true);
        } else {
          setBackendOnline(false);
        }
      } catch (err) {
        setBackendOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setCurrentAnalysis(result);
    setShowNotification(`Analysis complete for: ${result.image_name}`);
    setTimeout(() => setShowNotification(null), 4000);
  };

  const handleInspectFromPagination = (item: AnalysisResult) => {
    setCurrentAnalysis(item);
    setActiveTab('workbench');
    window.scrollTo({ top: 320, behavior: 'smooth' });
    setShowNotification(`Loaded ${item.image_name} into workbench.`);
    setTimeout(() => setShowNotification(null), 3500);
  };

  return (
    <div className="min-h-screen bg-[#0C0D10] text-[#E0E2EC] flex flex-col font-sans selection:bg-[#96E071] selection:text-black">
      {/* Toast Notification */}
      {showNotification && (
        <div className="fixed bottom-6 right-6 z-50 bg-[#161822] border border-[#96E071] text-white px-4 py-2.5 rounded shadow-2xl font-mono text-xs flex items-center gap-2 animate-bounce">
          <Sparkles className="w-4 h-4 text-[#96E071]" />
          <span>{showNotification}</span>
        </div>
      )}

      {/* Global Cyber Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendOnline={backendOnline}
      />

      {/* Main Content Body */}
      <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        {activeTab === 'workbench' && (
          <div className="space-y-12">
            <Hero />
            
            {/* Core Detector Workbench */}
            <Workbench
              currentAnalysis={currentAnalysis}
              onAnalysisComplete={handleAnalysisComplete}
            />

            <TrustTicker />

            {/* Feature Showcase: 3D Creative Pagination Section right on Homepage */}
            <section className="p-6 md:p-8 bg-[#111319] border border-[#2A2E3B] rounded-xl shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-4 mb-8 pb-4 border-b border-white/5">
                <div>
                  <div className="flex items-center gap-2.5">
                    <Layers className="w-5 h-5 text-[#96E071]" />
                    <h2 className="text-xl font-sans font-bold text-white tracking-tight">
                      3D Forensic Deck & Creative Pagination
                    </h2>
                  </div>
                  <p className="font-mono text-xs text-gray-400 mt-1.5">
                    Explore forensic benchmark cases using our custom 3D Cylinder Orbit, Isometric Layer Stack, and Radar Timeline.
                  </p>
                </div>

                <button
                  onClick={() => {
                    setActiveTab('batch');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-[#1C1F2B] hover:bg-[#25293A] text-[#96E071] border border-[#96E071]/30 hover:border-[#96E071] font-mono text-xs font-semibold transition-all shadow-sm"
                >
                  <span>Open Full 3D Batch Studio</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Live Interactive 3D Pagination Deck */}
              <Creative3DPagination
                items={PRESET_SAMPLES}
                currentIndex={PRESET_SAMPLES.findIndex(p => p.id === currentAnalysis.id) >= 0 ? PRESET_SAMPLES.findIndex(p => p.id === currentAnalysis.id) : 0}
                onSelectIndex={(idx) => setCurrentAnalysis(PRESET_SAMPLES[idx])}
                onInspectItem={handleInspectFromPagination}
              />
            </section>

            {/* Model Benchmarks Summary */}
            <div className="pt-4">
              <MetricsView />
            </div>
          </div>
        )}

        {activeTab === 'batch' && (
          <BatchStudio onInspectItem={handleInspectFromPagination} />
        )}

        {activeTab === 'robustness' && (
          <RobustnessLab currentAnalysis={currentAnalysis} />
        )}

        {activeTab === 'provenance' && (
          <ProvenanceInspector currentAnalysis={currentAnalysis} />
        )}

        {activeTab === 'benchmarks' && (
          <MetricsView />
        )}
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default App;
