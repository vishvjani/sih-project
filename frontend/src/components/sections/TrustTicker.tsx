import React from 'react';

export const TrustTicker: React.FC = () => {
  const brands = [
    { name: 'The New York Times', tag: 'NYT VERIFY' },
    { name: 'The Wall Street Journal', tag: 'WSJ INVESTIGATIONS' },
    { name: 'Forbes Technology', tag: 'FORBES' },
    { name: 'Hitachi Industrial AI', tag: 'HITACHI' },
    { name: 'Fox Media Network', tag: 'FOX CORP' },
    { name: 'Warner Bros. Discovery', tag: 'WBD FORENSICS' },
    { name: 'C2PA Coalition', tag: 'CONTENT CREDENTIALS' },
    { name: 'Reuters FactCheck', tag: 'REUTERS' },
  ];

  return (
    <div className="w-full py-5 border-y border-white/5 bg-[#0e0f14] overflow-hidden my-4">
      <div className="max-w-[1440px] mx-auto px-4 mb-2 flex items-center justify-center">
        <span className="font-mono text-[10px] uppercase tracking-widest text-gray-500">
          TRUSTED BY PRESS ORGANIZATIONS & FORENSIC INVESTIGATORS GLOBALLY
        </span>
      </div>

      {/* Infinite Marquee Ticker */}
      <div className="relative w-full overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_15%,black_85%,transparent)]">
        <div className="flex gap-8 items-center w-max animate-ticker">
          {[...brands, ...brands].map((brand, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 px-4 py-1.5 rounded bg-[#161822]/60 border border-white/5 text-gray-400 font-mono text-xs hover:text-[#96E071] transition-colors"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-[#96E071]/70" />
              <span className="font-semibold tracking-wider">{brand.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
