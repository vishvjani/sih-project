import React, { useState, useEffect } from 'react';
import type { ActiveTab } from '../../types';
import { Shield, Sparkles, Terminal, Activity, Layers, Sliders, ExternalLink, Menu, X } from 'lucide-react';

interface HeaderProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  backendOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  backendOnline,
}) => {
  const [isScrolled, setIsScrolled] = useState<boolean>(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
    { id: 'workbench', label: 'Workbench', icon: <Sparkles className="w-3.5 h-3.5" /> },
    { id: 'batch', label: '3D Batch Deck', icon: <Layers className="w-3.5 h-3.5" /> },
    { id: 'robustness', label: 'Robustness Lab', icon: <Sliders className="w-3.5 h-3.5" /> },
    { id: 'provenance', label: 'EXIF / C2PA', icon: <Shield className="w-3.5 h-3.5" /> },
    { id: 'benchmarks', label: 'Model Benchmarks', icon: <Activity className="w-3.5 h-3.5" /> },
  ];

  return (
    <header
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-200 ${
        isScrolled
          ? 'bg-[#0C0D11]/90 backdrop-blur-md border-b border-white/10 shadow-lg'
          : 'bg-transparent border-b border-transparent'
      }`}
    >
      <div className="max-w-[1440px] mx-auto h-[64px] px-4 md:px-8 flex items-center justify-between">
        {/* Logo & Status Badge */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setActiveTab('workbench')}
            className="flex items-center gap-2.5 group text-left"
          >
            <div className="w-8 h-8 rounded bg-[#161822] border border-[#96E071]/50 flex items-center justify-center text-[#96E071] group-hover:glow-green transition-all">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-sans font-bold text-white tracking-tight text-lg">SignalScope</span>
                <span className="font-mono text-[9px] px-1.5 py-0.2 bg-[#96E071]/15 text-[#96E071] border border-[#96E071]/30 rounded">
                  v2.4
                </span>
              </div>
              <p className="font-mono text-[9px] text-gray-500 tracking-wider">AI MEDIA AUTHENTICITY</p>
            </div>
          </button>

          {/* Live Backend Status Pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#161820] border border-white/5 font-mono text-[10px]">
            <span
              className={`w-2 h-2 rounded-full ${
                backendOnline ? 'bg-[#96E071] animate-pulse' : 'bg-yellow-400'
              }`}
            />
            <span className={backendOnline ? 'text-[#96E071]' : 'text-yellow-400'}>
              {backendOnline ? 'API :8000 LIVE' : 'CLIENT-SIDE RUNTIME'}
            </span>
          </div>
        </div>

        {/* Center Desktop Navigation Tabs */}
        <nav className="hidden lg:flex items-center gap-1 bg-[#13151D] p-1 rounded-md border border-white/5">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono transition-all ${
                activeTab === item.id
                  ? 'bg-[#96E071] text-black font-bold shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <span className={activeTab === item.id ? 'text-black' : 'text-[#96E071]'}>/</span>
              {item.label}
            </button>
          ))}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#1A1C25] hover:bg-[#232634] text-gray-300 hover:text-white font-mono text-xs border border-white/10 transition-colors"
          >
            <Terminal className="w-3.5 h-3.5 text-[#96E071]" />
            <span>FastAPI Docs</span>
            <ExternalLink className="w-3 h-3 text-gray-500" />
          </a>

          <button
            onClick={() => setActiveTab('batch')}
            className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 bg-[#96E071] hover:bg-[#a9f583] text-black font-sans font-semibold text-xs rounded transition-all glow-green"
          >
            <span>Batch Upload</span>
          </button>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 text-gray-400 hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-[#0F1117] border-b border-white/10 px-4 py-3 space-y-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded text-xs font-mono text-left ${
                activeTab === item.id
                  ? 'bg-[#96E071] text-black font-bold'
                  : 'text-gray-300 hover:bg-white/5'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </header>
  );
};
