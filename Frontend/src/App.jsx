import React, { useState, useEffect } from 'react';
import ChatTerminal from './components/ChatTerminal';
import DataPortal from './components/DataPortal';
import { Terminal, Database, Shield, Zap, Globe, Cpu, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [activeTab, setActiveTab] = useState('terminal');
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoaded(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-carbon flex flex-col items-center justify-center font-mono">
        <div className="w-64 h-1 bg-neon-cyan/20 relative overflow-hidden">
          <motion.div 
            initial={{ left: '-100%' }}
            animate={{ left: '100%' }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
            className="absolute top-0 bottom-0 w-1/2 bg-neon-cyan shadow-[0_0_15px_#00ffff]"
          />
        </div>
        <p className="mt-4 text-[10px] tracking-[0.5em] text-neon-cyan animate-pulse">BOOTING_VORTEX_OS...</p>
      </div>
    );
  }

  return (
    <div className="h-[100dvh] w-full bg-carbon text-neon-cyan font-mono relative overflow-hidden flex flex-col selection:bg-neon-pink selection:text-white">
      {/* ── CRT & ATMOSPHERE ── */}
      <div className="scanline"></div>
      <div className="scanline-moving"></div>
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,255,255,0.05)_0%,transparent_70%)] pointer-events-none"></div>

      {/* ── TOP DECORATIVE BAR ── */}
      <div className="h-1 bg-gradient-to-r from-neon-cyan via-neon-pink to-neon-cyan bg-[length:200%_100%] animate-[gradient_5s_linear_infinite] opacity-50 shrink-0"></div>

      {/* ── MAIN HEADER ── */}
      <header className="border-b border-neon-cyan/20 px-4 md:px-6 py-4 flex flex-col md:flex-row md:justify-between items-center gap-4 bg-carbon/40 backdrop-blur-xl z-20 shrink-0">
        <div className="flex items-center gap-4 group">
          <div className="relative">
            <div className="absolute inset-0 bg-neon-cyan blur-md opacity-20 group-hover:opacity-40 transition-opacity"></div>
            <div className="p-2.5 border-2 border-neon-cyan relative bg-carbon shadow-[inset_0_0_10px_rgba(0,255,255,0.2)]">
              <Zap className="text-neon-cyan group-hover:scale-110 transition-transform" size={24} />
            </div>
          </div>
          <div>
            <h1 className="font-orbitron text-2xl tracking-[0.2em] neon-text-cyan flex items-center gap-2">
              VORTEX <span className="text-xs bg-neon-cyan text-carbon px-1 tracking-normal font-bold">RAG</span>
            </h1>
            <div className="flex items-center gap-2 text-[9px] text-neon-pink tracking-widest uppercase mt-0.5">
              <Activity size={10} className="animate-pulse" /> NEURAL_LINK_ESTABLISHED
            </div>
          </div>
        </div>

        <nav className="flex items-center bg-carbon/60 p-1 border border-neon-cyan/20 rounded-sm w-full md:w-auto justify-center">
          <button 
            onClick={() => setActiveTab('terminal')}
            className={`px-4 md:px-6 py-2 flex items-center gap-2 font-orbitron text-xs transition-all duration-300 relative overflow-hidden flex-1 md:flex-none justify-center ${
              activeTab === 'terminal' ? 'text-carbon' : 'text-neon-cyan hover:text-white'
            }`}
          >
            {activeTab === 'terminal' && (
              <motion.div layoutId="nav-bg" className="absolute inset-0 bg-neon-cyan" transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }} />
            )}
            <span className="relative z-10 flex items-center gap-2">
              <Terminal size={14} /> CORE_TERMINAL
            </span>
          </button>
          <button 
            onClick={() => setActiveTab('portal')}
            className={`px-4 md:px-6 py-2 flex items-center gap-2 font-orbitron text-xs transition-all duration-300 relative overflow-hidden flex-1 md:flex-none justify-center ${
              activeTab === 'portal' ? 'text-carbon' : 'text-neon-pink hover:text-white'
            }`}
          >
            {activeTab === 'portal' && (
              <motion.div layoutId="nav-bg" className="absolute inset-0 bg-neon-pink" transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }} />
            )}
            <span className="relative z-10 flex items-center gap-2">
              <Database size={14} /> DATA_INJECTOR
            </span>
          </button>
        </nav>

        <div className="hidden xl:flex items-center gap-6 text-[10px] tracking-tighter uppercase shrink-0">
          <div className="flex flex-col items-end">
            <span className="text-neon-cyan opacity-40">UPLINK_STATUS</span>
            <span className="text-neon-cyan font-bold flex items-center gap-1">
               <Globe size={10} className="text-green-500" /> ONLINE_ENCRYPTED
            </span>
          </div>
          <div className="w-px h-8 bg-neon-cyan/20"></div>
          <div className="flex flex-col items-end">
            <span className="text-neon-pink opacity-40">CPU_LOAD</span>
            <span className="text-neon-pink font-bold flex items-center gap-1">
               <Cpu size={10} /> 12.4%_STABLE
            </span>
          </div>
        </div>
      </header>

      {/* ── BREADCRUMB / STATUS BAR ── */}
      <div className="bg-neon-cyan/5 px-6 py-1.5 border-b border-neon-cyan/10 flex items-center gap-4 text-[9px] text-neon-cyan/60 uppercase italic uppercase shrink-0 whitespace-nowrap overflow-x-auto scrollbar-none">
        <span className="flex items-center gap-1"><Zap size={10} /> SYS.PROMPT_LOADED: TUTOR_V2</span>
        <span className="opacity-20 shrink-0">|</span>
        <span className="flex items-center gap-1"><Shield size={10} /> SSRF_PROTECTION: ACTIVE</span>
        <span className="ml-auto font-mono not-italic tracking-widest shrink-0">{new Date().toLocaleTimeString()}</span>
      </div>

      {/* ── MAIN VIEWPORT ── */}
      <main className="flex-1 relative overflow-hidden p-4 md:p-10 flex flex-col min-h-0">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, scale: 0.98, filter: 'blur(10px)' }}
            animate={{ opacity: 1, scale: 1, filter: 'blur(0px)' }}
            exit={{ opacity: 0, scale: 1.02, filter: 'blur(10px)' }}
            transition={{ duration: 0.4, ease: "circOut" }}
            className="flex-1 h-full min-h-0 flex flex-col"
          >
            {activeTab === 'terminal' ? <ChatTerminal /> : <DataPortal />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* ── ANALYTICS FOOTER ── */}
      <footer className="border-t border-neon-cyan/10 bg-carbon/60 p-2 flex justify-between items-center px-6 text-[8px] tracking-[0.3em] opacity-40 select-none">
        <div className="flex gap-4">
          <span>QDRANT_NODES: 01</span>
          <span>REDIS_SHARDS: ALLOWED</span>
        </div>
        <div className="flex gap-4">
          <span>MEM: 14.2GB / 32GB</span>
          <span>FRAME: 60FPS</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
