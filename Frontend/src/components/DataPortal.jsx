import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Upload, Link as LinkIcon, Check, AlertCircle, Loader2, CloudUpload, FileText, Globe, Layers, Zap, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

const DataPortal = () => {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [deepScrape, setDeepScrape] = useState(false);
  const [status, setStatus] = useState({ type: null, message: '', jobId: null });
  const [jobProgress, setJobProgress] = useState(null);
  const notifyTimer = useRef(null);

  useEffect(() => {
    let interval;
    if (status.jobId) {
      interval = setInterval(async () => {
        try {
          const resp = await axios.get(`${API_BASE}/ingest/status/${status.jobId}`);
          setJobProgress(resp.data);
          if (resp.data.status === 'completed' || resp.data.status === 'failed') {
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Status poll error:', err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [status.jobId]);

  const notify = (type, message, jobId = null) => {
    // 1. Clear any pending auto-dismiss timer immediately
    if (notifyTimer.current) {
      clearTimeout(notifyTimer.current);
      notifyTimer.current = null;
    }

    // 2. Update status
    setStatus({ type, message, jobId });

    // 3. ONLY auto-dismiss if there's no active job (error or simple info)
    // If a jobId exists, we want the UI tracking to stay visible until manual dismissal or job completion.
    if (!jobId) {
      notifyTimer.current = setTimeout(() => {
        setStatus({ type: null, message: '', jobId: null });
        setJobProgress(null);
      }, 5000);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    notify('info', 'TRANSMITTING_LOCAL_DATA...');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const resp = await axios.post(`${API_BASE}/ingest/file`, formData);
      notify('success', 'PACKETS_QUEUED_FOR_INDEXING', resp.data.job_id);
      setFile(null);
    } catch (err) {
      notify('error', 'TX_FAILURE: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleUrlIngest = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    notify('info', 'REMOTE_CAPTURE_INITIATED...');
    try {
      const resp = await axios.post(`${API_BASE}/ingest/url`, { 
        url, 
        deep_scrape: deepScrape 
      });
      notify('success', 'URL_STREAM_REGISTERED', resp.data.job_id);
      setUrl('');
    } catch (err) {
      notify('error', 'LINK_FAILURE: ' + (err.response?.data?.error || err.message));
    }
  };

  return (
    <div className="h-full flex flex-col gap-8 max-w-5xl mx-auto overflow-y-auto pr-2">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* ── FILE INGESTION ── */}
        <motion.div initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="tech-card border-neon-cyan/20 group hover:border-neon-cyan/40 transition-colors">
          <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:opacity-100 transition-opacity">
            <FileText size={40} className="text-neon-cyan" />
          </div>
          <h3 className="font-orbitron flex items-center gap-2 mb-8 text-sm tracking-widest">
            <Layers size={16} className="text-neon-cyan" /> DOCUMENT_INDEXER
          </h3>
          <form onSubmit={handleFileUpload} className="space-y-6">
            <label className="block border border-neon-cyan/10 bg-neon-cyan/5 p-10 text-center hover:bg-neon-cyan/10 transition-all cursor-pointer group/upload relative overflow-hidden rounded-sm">
              <div className="absolute inset-0 bg-gradient-to-br from-neon-cyan/10 to-transparent opacity-0 group-hover/upload:opacity-100 transition-opacity"></div>
              <CloudUpload className="mx-auto mb-4 text-neon-cyan animate-bounce" size={40} />
              <p className="text-[10px] font-orbitron uppercase tracking-widest text-neon-cyan mb-1">
                {file ? file.name : 'Select Neural Seed File'}
              </p>
              <p className="text-[8px] opacity-40 uppercase">PDF, DOCX, TXT | MAX 10MB</p>
              <input type="file" className="hidden" onChange={(e) => setFile(e.target.files[0])} />
            </label>
            <button 
              type="submit" 
              disabled={!file}
              className="tech-btn w-full py-4 font-orbitron text-[10px] tracking-widest uppercase hover:tracking-[0.5em] transition-all"
            >
              INITIATE_UPLOAD_SEQUENCE
            </button>
          </form>
        </motion.div>

        {/* ── URL INGESTION ── */}
        <motion.div initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="tech-card border-neon-pink/20 hover:border-neon-pink/40 transition-colors">
          <div className="absolute top-0 right-0 p-2 opacity-10">
            <Globe size={40} className="text-neon-pink" />
          </div>
          <h3 className="font-orbitron flex items-center gap-2 mb-8 text-sm tracking-widest text-neon-pink">
            <Zap size={16} className="text-neon-pink" /> WEB_SCRAPER_NODE
          </h3>
          <form onSubmit={handleUrlIngest} className="space-y-6">
            <div className="relative">
              <input 
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="PROBE_URL: https://..."
                className="w-full bg-carbon border border-neon-pink/20 p-4 text-xs font-mono focus:border-neon-pink outline-none text-neon-pink placeholder:text-neon-pink/20 transition-all shadow-[inset_0_0_10px_rgba(255,0,255,0.05)]"
              />
              <div className="absolute top-0 right-0 h-full w-1 shadow-[0_0_10px_rgba(255,0,255,0.8)] bg-neon-pink opacity-50"></div>
            </div>
            
            <label className="flex items-center gap-3 cursor-pointer group">
              <div className={`w-4 h-4 border border-neon-pink flex items-center justify-center transition-all ${deepScrape ? 'bg-neon-pink' : 'bg-transparent'}`}>
                {deepScrape && <Check size={12} className="text-carbon font-bold" />}
              </div>
              <input 
                type="checkbox" 
                className="hidden"
                checked={deepScrape}
                onChange={(e) => setDeepScrape(e.target.checked)}
              />
              <span className="text-[9px] uppercase tracking-widest text-neon-pink/70 group-hover:text-neon-pink transition-colors">DEEP_SCAN_RECURSION (LVL_1)</span>
            </label>

            <button 
              type="submit" 
              disabled={!url}
              className="tech-btn w-full py-4 font-orbitron text-[10px] tracking-widest uppercase border-neon-pink text-neon-pink hover:bg-neon-pink hover:text-carbon hover:shadow-[0_0_30px_rgba(255,0,255,0.4)] transition-all"
               style={{ clipPath: 'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)' }}
            >
              EXECUTE_LINK_CAPTURE
            </button>
          </form>
        </motion.div>
      </div>

      {/* ── JOB STATUS CONSOLE ── */}
      <AnimatePresence>
        {status.type && (
          <motion.div 
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 50, opacity: 0 }}
            className={`p-6 border border-l-8 ${
              status.type === 'success' ? 'border-green-500 bg-green-500/5 text-green-500' :
              status.type === 'error' ? 'border-neon-pink bg-neon-pink/5 text-neon-pink' :
              'border-neon-cyan bg-neon-cyan/5 text-neon-cyan'
            } backdrop-blur-md tech-card`}
          >
            <div className="flex items-center justify-between gap-4 mb-4 font-orbitron text-xs tracking-[0.2em] font-bold">
              <div className="flex items-center gap-4">
                {status.type === 'info' && <Loader2 className="animate-spin" size={16} />}
                {status.type === 'success' && <Check size={16} />}
                {status.type === 'error' && <AlertCircle size={16} />}
                {status.message}
              </div>
              <button 
                onClick={() => {
                  setStatus({ type: null, message: '', jobId: null });
                  setJobProgress(null);
                }}
                className="opacity-40 hover:opacity-100 transition-opacity p-1"
              >
                <X size={14} />
              </button>
            </div>
            
            {jobProgress && (
              <div className="space-y-4 font-mono">
                <div className="flex justify-between items-center text-[9px] opacity-60">
                  <div className="flex flex-col">
                    <span>INDEX_ID: {status.jobId}</span>
                    <span>TARGET: URL_PROBE_01</span>
                  </div>
                  <div className="bg-neon-cyan/10 px-3 py-1 border border-neon-cyan/20 animate-pulse text-neon-cyan uppercase">
                    {jobProgress.status}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="h-0.5 bg-carbon border border-neon-cyan/10 relative overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: jobProgress.status === 'completed' ? '100%' : '40%' }}
                    className={`h-full ${jobProgress.status === 'failed' ? 'bg-neon-pink' : 'bg-neon-cyan'} shadow-[0_0_10px_currentColor]`}
                  />
                </div>

                {/* Logs Console */}
                {jobProgress.logs && jobProgress.logs.length > 0 && (
                  <div className="text-[9px] bg-black/40 p-3 h-32 overflow-y-auto font-mono text-neon-cyan/40 leading-relaxed scrollbar-thin">
                    <div className="mb-2 text-neon-cyan opacity-80 underline underline-offset-4">LOG_STREAM:</div>
                    {jobProgress.logs.map((log, i) => (
                      <div key={i} className="flex gap-2">
                        <span className="opacity-20">[{i}]</span>
                        <span className={log.toLowerCase().includes('failed') ? 'text-neon-pink' : ''}>{log}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default DataPortal;
