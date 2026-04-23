'use client';
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LandingPage() {

  const navigate = useNavigate();

  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, loading, navigate]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  
  
  const [mainTask, setMainTask] = useState('Demand Prediction');
  const [isTaskMenuOpen, setIsTaskMenuOpen] = useState(false); 

  const [useContextEnrichment, setUseContextEnrichment] = useState(false);
  const [useReorderRec, setUseReorderRec] = useState(false);

  const handleMainTaskChange = (value: string) => {
    setMainTask(value);
    setIsTaskMenuOpen(false);
    
    if (value === 'Inventory Optimization') {
      setUseContextEnrichment(false);
    }
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      alert(`Selected file: ${file.name} - We will send this to Python later!`);
    }
  };

  const taskOptions = ['Demand Prediction', 'Inventory Optimization'];

  return (
    <>
      <div className="min-h-screen animate-bg flex flex-col text-white font-sans">
        
        {/* FIXED HEIGHT HEADER: h-24 and px-6 instead of p-6 */}
        <header className="h-24 flex justify-between items-center px-6 w-full relative z-50">
          <div className="font-bold text-xl tracking-wider cursor-pointer flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
              <span className="font-bold text-white text-sm">Z</span>
            </div>
            <span>Z.AI Hub</span>
          </div>
          
          <button onClick={() => navigate('/login')} className="flex items-center gap-2 bg-white/10 hover:bg-white/20 transition-all px-5 py-2.5 rounded-full border border-white/20 backdrop-blur-md shadow-lg">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            <span className="font-semibold text-sm tracking-wide">Sign in</span>
          </button>
        </header>

        <main className="flex-grow flex flex-col items-center justify-center px-4 w-full max-w-5xl mx-auto -mt-10 relative z-10">
          
          <h1 className="text-4xl md:text-6xl font-extrabold mb-4 text-center tracking-tight">
            Experience <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">Hartalis.AI</span>
          </h1>
          <p className="text-gray-400 text-lg md:text-xl mb-10 text-center font-light tracking-wide">
            Your decision intelligence engine.
          </p>

          <div className="w-full max-w-3xl relative flex items-center bg-[#0f172a]/80 backdrop-blur-xl border border-white/10 rounded-full p-2 shadow-2xl transition-all hover:border-blue-500/50 focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/20">
            
            <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".csv, .xlsx, .xls, .json" className="hidden" />

            <button onClick={handleFileClick} className="p-3.5 bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 rounded-full transition-all ml-1 shrink-0" title="Upload CSV, Excel, or JSON">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" /></svg>
            </button>

            {/* Custom Dropdown */}
            <div className="relative flex-1 ml-2 mr-2">
              <button 
                onClick={() => setIsTaskMenuOpen(!isTaskMenuOpen)}
                className="w-full bg-transparent text-white font-semibold text-lg px-4 py-4 outline-none text-left flex justify-between items-center group"
              >
                <span className="truncate">{mainTask}</span>
                <svg 
                  className={`w-5 h-5 text-gray-400 group-hover:text-white transition-transform duration-300 ${isTaskMenuOpen ? 'rotate-180 text-blue-400' : ''}`} 
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isTaskMenuOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setIsTaskMenuOpen(false)}></div>
                  <div className="absolute top-full left-0 mt-3 w-full bg-[#0f172a]/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.5)] py-2 z-50 overflow-hidden transform opacity-100 scale-100 transition-all">
                    {taskOptions.map((option) => (
                      <button
                        key={option}
                        onClick={() => handleMainTaskChange(option)}
                        className={`w-full text-left px-5 py-3 transition-colors flex justify-between items-center ${
                          mainTask === option 
                            ? 'bg-blue-500/10 text-blue-400 font-bold' 
                            : 'text-gray-300 hover:bg-white/5 hover:text-white font-medium'
                        }`}
                      >
                        {option}
                        {mainTask === option && (
                          <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            <button onClick={() => navigate('/dashboard')} className="p-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-full transition-all shadow-lg hover:shadow-blue-500/25 mr-1 shrink-0">
              <svg className="w-6 h-6 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
            </button>
          </div>

          <div className="w-full max-w-3xl flex flex-col sm:flex-row items-center justify-center gap-4 mt-6">
            {mainTask === 'Demand Prediction' && (
              <button
                onClick={() => setUseContextEnrichment(!useContextEnrichment)}
                className={`flex items-center gap-3 px-5 py-2.5 rounded-full border transition-all duration-300 ${
                  useContextEnrichment
                    ? 'bg-blue-500/20 border-blue-500/50 text-blue-300 shadow-[0_0_15px_rgba(59,130,246,0.15)]'
                    : 'bg-black/40 border-white/10 text-gray-400 hover:border-white/30 hover:text-gray-200'
                }`}
              >
                <div className={`w-5 h-5 rounded-md flex items-center justify-center border transition-colors ${useContextEnrichment ? 'bg-blue-500 border-blue-400' : 'border-gray-600 bg-black/50'}`}>
                  {useContextEnrichment && <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/></svg>}
                </div>
                <span className="text-sm font-semibold tracking-wide">Context Enrichment</span>
              </button>
            )}

            <button
              onClick={() => setUseReorderRec(!useReorderRec)}
              className={`flex items-center gap-3 px-5 py-2.5 rounded-full border transition-all duration-300 ${
                useReorderRec
                  ? 'bg-purple-500/20 border-purple-500/50 text-purple-300 shadow-[0_0_15px_rgba(168,85,247,0.15)]'
                  : 'bg-black/40 border-white/10 text-gray-400 hover:border-white/30 hover:text-gray-200'
              }`}
            >
              <div className={`w-5 h-5 rounded-md flex items-center justify-center border transition-colors ${useReorderRec ? 'bg-purple-500 border-purple-400' : 'border-gray-600 bg-black/50'}`}>
                {useReorderRec && <svg className="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"/></svg>}
              </div>
              <span className="text-sm font-semibold tracking-wide">Reorder Recommendations</span>
            </button>
          </div>

          <div className="mt-20 max-w-2xl text-center px-6 mb-8 w-full">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative bg-[#0f172a]/80 ring-1 ring-white/10 p-6 rounded-2xl backdrop-blur-md shadow-xl">
                <div className="flex items-center justify-center gap-2 mb-3">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  <strong className="text-white text-base tracking-wide">Hackathon 2026: Economic Empowerment Domain</strong>
                </div>
                <p className="text-gray-400 text-sm leading-relaxed">
                  This platform addresses fragmented data by leveraging the <span className="text-blue-400 font-semibold">Z.AI GLM</span>. By applying context-aware reasoning to structured metrics and unstructured signals, it empowers workers and merchants to optimize decision-making and maximize economic outcomes.
                </p>
              </div>
            </div>
          </div>

        </main>
      </div>
    </>
  );
}