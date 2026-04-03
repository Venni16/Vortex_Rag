import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, User, Cpu, Loader2, Sparkles, Server, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const ChatTerminal = () => {
  const [messages, setMessages] = useState([
    { role: 'system', content: '>>> VORTEX_NEURAL_INTERFACE_READY. STANDING BY FOR INPUT.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const resp = await axios.post(`${API_BASE}/chat`, { question: input });
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: resp.data.answer,
        cached: resp.data.cached,
        sources: resp.data.sources,
        latency: resp.data.latency_ms
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: 'FATAL_ERROR: SIGNAL_LOST. RECONNECTING...' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full border border-neon-cyan/20 bg-carbon/40 backdrop-blur-xl rounded-sm shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden">
      {/* ── TERMINAL HEADER ── */}
      <div className="bg-neon-cyan/10 px-4 py-2 border-b border-neon-cyan/20 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[10px] font-orbitron tracking-widest uppercase">
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-neon-pink"></div>
            <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
            <div className="w-2 h-2 rounded-full bg-neon-cyan"></div>
          </div>
          Session: AI_TUTOR_001
        </div>
        <div className="text-[9px] opacity-40 animate-pulse">REC...</div>
      </div>

      {/* ── CONVERSATION AREA ── */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-none"
      >
        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 10, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className={`p-4 max-w-[90%] md:max-w-[75%] relative ${
                msg.role === 'user' 
                  ? 'bg-neon-pink/10 border-r-4 border-neon-pink text-neon-pink shadow-[0_0_20px_rgba(255,0,255,0.05)]' 
                  : msg.role === 'system'
                  ? 'bg-yellow-500/5 border border-yellow-500/20 text-yellow-500 font-bold italic'
                  : 'bg-neon-cyan/10 border-l-4 border-neon-cyan text-neon-cyan shadow-[0_0_20px_rgba(0,255,255,0.05)]'
              }`}>
                {/* ── MSG METADATA ── */}
                <div className="flex items-center gap-2 mb-2 text-[9px] uppercase tracking-tighter opacity-40 font-orbitron">
                  {msg.role === 'user' ? <User size={10} /> : (msg.role === 'system' ? <Info size={10} /> : <Cpu size={10} />)}
                  <span>{msg.role}_TRANSMISSION</span>
                  {msg.latency && <span className="ml-auto bg-neon-cyan/20 px-1">{msg.latency.toFixed(0)}MS</span>}
                  {msg.cached && <span className="ml-1 bg-neon-pink/20 px-1 text-neon-pink">CACHED</span>}
                </div>
                
                <div className="text-sm leading-relaxed whitespace-pre-wrap font-mono">
                  {msg.content}
                </div>

                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 pt-2 border-t border-neon-cyan/10 flex flex-wrap gap-2">
                    {msg.sources.map((s, i) => (
                      <span key={i} className="text-[8px] bg-carbon px-2 py-0.5 border border-neon-cyan/20 flex items-center gap-1">
                         <Server size={8} /> {s}
                      </span>
                    ))}
                  </div>
                )}
                
                {/* Decorative corner */}
                <div className={`absolute -bottom-1 -right-1 w-2 h-2 border-b-2 border-r-2 ${msg.role === 'user' ? 'border-neon-pink' : 'border-neon-cyan'} opacity-40`}></div>
              </div>
            </motion.div>
          ))}
          {loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="p-4 bg-neon-cyan/5 border-l-4 border-neon-cyan/50 text-neon-cyan flex items-center gap-4">
                <Loader2 className="animate-spin" size={18} />
                <div className="flex flex-col">
                  <span className="text-[10px] uppercase tracking-widest animate-pulse">Calculating_Response</span>
                  <div className="w-24 h-0.5 bg-neon-cyan/20 relative mt-1 overflow-hidden">
                     <motion.div animate={{ left: ['-100%', '100%'] }} transition={{ repeat: Infinity, duration: 1 }} className="absolute inset-0 bg-neon-cyan" />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── CMD PROMPT ── */}
      <div className="p-6 bg-carbon/60 border-t border-neon-cyan/10 relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-neon-cyan/20 to-transparent"></div>
        <form onSubmit={handleSend} className="max-w-3xl mx-auto relative group">
          <div className="absolute -inset-0.5 bg-neon-cyan rounded-sm opacity-10 group-focus-within:opacity-25 transition-opacity blur"></div>
          <div className="relative flex items-center bg-carbon border border-neon-cyan/30 focus-within:border-neon-cyan transition-colors">
             <div className="pl-4 pr-2 text-neon-cyan font-bold animate-pulse tracking-tighter">Vortex@Root:~$</div>
             <input 
               autoFocus
               value={input}
               onChange={(e) => setInput(e.target.value)}
               placeholder={loading ? 'NEURAL_LINK_BUSY...' : 'Input query for neural tutor...'}
               className="flex-1 bg-transparent py-4 text-sm outline-none text-neon-cyan placeholder:text-neon-cyan/10"
               disabled={loading}
             />
             <button 
               type="submit"
               disabled={loading || !input.trim()}
               className="px-6 h-full flex items-center justify-center text-neon-cyan hover:text-white hover:bg-neon-cyan transition-all disabled:opacity-10"
             >
               <Send size={18} />
             </button>
          </div>
        </form>
        <div className="mt-2 text-[8px] text-center text-neon-cyan/30 uppercase tracking-[0.5em]">
          End_To_End_Encrypted_Link_Node: vtx_42
        </div>
      </div>
    </div>
  );
};

export default ChatTerminal;
