import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart3, RefreshCw, Lightbulb, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import ConnectionScreen from './components/ConnectionScreen';
import SchemaVisualizer from './components/SchemaVisualizer';
import ResultsDisplay from './components/ResultsDisplay';
import QueryInterface from './components/QueryInterface';

import type { QueryResponse, GraphData } from './types';

const API_BASE = "https://autoquery-cm17.onrender.com/api";

const containerVariants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.15 } }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
};

export default function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [queryLoading, setQueryLoading] = useState(false);
  
  const [query, setQuery] = useState('');
  const [provider, setProvider] = useState('groq');
  
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);

  // New states for the Insights feature
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [dbInsights, setDbInsights] = useState<string | null>(null);

  const handleConnect = async (dbUrl: string) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/connect-db`, { database_url: dbUrl });
      setIsConnected(true);
      fetchSchema();
    } catch (err) {
      alert("Connection failed. Check console for details.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSchema = async () => {
    try {
      const res = await axios.get(`${API_BASE}/schema-graph`);
      setGraphData(res.data);
    } catch (err) {
      console.error("Failed to load schema", err);
    }
  };

  const handleQuery = async () => {
    if (!query) return;
    setQueryLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/query`, {
        query,
        provider,
        optimize: true,
        explain: true,
        visualize: true
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Query failed. Ensure it matches your schema.");
    } finally {
      setQueryLoading(false);
    }
  };

  const resetSandbox = async () => {
    try {
      await axios.post(`${API_BASE}/reset-sandbox`);
      alert("Sandbox successfully reset to production state.");
    } catch (err) {
      console.error(err);
    }
  };

  const fetchInsights = async () => {
    if (dbInsights) {
      setDbInsights(null); // Toggle off if already open
      return;
    }
    
    setInsightsLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/insights`, { provider, data: result.data });
      // Assuming backend returns {"insights": "text..."}
      setDbInsights(res.data.insights || JSON.stringify(res.data)); 
    } catch (err) {
      console.error(err);
      alert("Failed to load insights.");
    } finally {
      setInsightsLoading(false);
    }
  };





  if (!isConnected) {
    return <ConnectionScreen onConnect={handleConnect} loading={loading} />;
  }

  return (
    <div className="min-h-screen text-slate-200 font-sans selection:bg-indigo-500/30">
      
      {/* Top Navigation */}
      <motion.nav 
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="border-b border-slate-800 p-4 flex flex-wrap justify-between items-center bg-slate-900/70 backdrop-blur-md sticky top-0 z-50 shadow-sm gap-4"
      >
        <div className="flex items-center gap-3">
          <div className="p-1 bg-white rounded-lg shadow-inner">
            <img src="/logo.jpeg" alt="AutoQuery Logo" className="w-8 h-8 object-contain" />
          </div>
          <span className="font-bold text-white tracking-tight text-lg">AutoQuery <span className="text-indigo-400">AI</span></span>
        </div>
        
        <div className="flex items-center gap-3 flex-wrap">
          {/* Insights Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={fetchInsights}
            disabled={insightsLoading}
            className="flex items-center gap-2 text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-4 py-2 rounded-lg hover:bg-amber-500/20 transition-colors font-semibold"
          >
            <Lightbulb className={`w-3.5 h-3.5 ${insightsLoading ? 'animate-pulse' : ''}`} />
            {insightsLoading ? "Analyzing..." : "DB Insights"}
          </motion.button>

          <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-lg p-1 shadow-inner">
            <span className="text-xs text-slate-500 pl-2 uppercase font-bold">LLM</span>
            <select 
              className="bg-transparent border-none text-sm text-white focus:ring-0 cursor-pointer outline-none custom-scrollbar"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
            >
              <option value="groq" className="bg-slate-900">Groq (Llama 3)</option>
              <option value="gemini" className="bg-slate-900">Gemini Pro</option>
              <option value="gpt" className="bg-slate-900">OpenAI GPT-4</option>
              <option value="local" className="bg-slate-900">Fine Tuned llama</option>
            </select>
          </div>

          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={resetSandbox}
            className="flex items-center gap-2 text-xs bg-red-500/10 text-red-400 border border-red-500/20 px-4 py-2 rounded-lg hover:bg-red-500/20 transition-colors font-semibold"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reset Sandbox
          </motion.button>
        </div>
      </motion.nav>

      {/* Expandable Insights Banner */}
      <AnimatePresence>
        {dbInsights && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-b border-amber-500/20 bg-gradient-to-r from-amber-500/10 to-orange-500/5 overflow-hidden"
          >
            <div className="max-w-7xl mx-auto p-6 relative">
              <button onClick={() => setDbInsights(null)} className="absolute top-4 right-4 text-amber-500/50 hover:text-amber-400 transition-colors">
                <X className="w-5 h-5" />
              </button>
              <h3 className="text-amber-400 font-bold mb-2 flex items-center gap-2">
                <Lightbulb className="w-4 h-4" /> AI Database Insights
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed max-w-4xl whitespace-pre-wrap">
                {dbInsights}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.main 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="max-w-7xl mx-auto p-6 grid grid-cols-12 gap-6"
      >
        <div className="col-span-12 lg:col-span-8 space-y-6 overflow-hidden">
          <motion.div variants={itemVariants}>
            <QueryInterface 
              query={query} 
              setQuery={setQuery} 
              handleQuery={handleQuery} 
              loading={queryLoading} 
            />
          </motion.div>

          {result && (
             <motion.div variants={itemVariants}>
               {/* Updated to pass query and provider down to the Results Display */}
               <ResultsDisplay result={result} query={query} provider={provider} />
             </motion.div>
          )}
        </div>

        <motion.div variants={itemVariants} className="col-span-12 lg:col-span-4 space-y-6">
          <div className="bg-slate-900/80 backdrop-blur-sm border border-slate-800 rounded-2xl p-6 shadow-xl sticky top-24">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-md font-semibold text-white flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-400" /> Schema Introspection
              </h3>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Dynamically extracted schema provided to the LLM for context-aware query generation.
            </p>
            <SchemaVisualizer graphData={graphData} />
          </div>
        </motion.div>
      </motion.main>
    </div>
  );
}