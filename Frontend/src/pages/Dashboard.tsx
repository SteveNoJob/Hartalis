'use client';
import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from "../context/AuthContext";

export default function AuthenticatedDashboard() {
  const { user, loading, refreshUser } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate('/');
    }
  }, [user, loading, navigate]);

  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [mainTask, setMainTask] = useState('Demand Prediction');
  const [isTaskMenuOpen, setIsTaskMenuOpen] = useState(false); 

  const [useContextEnrichment, setUseContextEnrichment] = useState(false);
  const [useReorderRec, setUseReorderRec] = useState(false);
  
  // State for the two-step upload process
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleMainTaskChange = (value: string) => {
    setMainTask(value);
    setIsTaskMenuOpen(false); 
    
    if (value === 'Inventory Optimization') {
      setUseContextEnrichment(false);
      setUseReorderRec(false);
    }
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  // Step 1: Handle file selection and display the UI pill
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const removeSelectedFile = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering the outer div click
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = ''; // Reset the input so they can re-select the same file
    }
  };

  // Step 2: Actually send the data to the FastAPI backend
  const handleProcessSubmit = async () => {
    if (!selectedFile) {
      alert("Please select a file using the + button first!");
      return;
    }

    const formData = new FormData();
    formData.append('sales', selectedFile); 
    formData.append('stock', ''); 
    
    // Optional: Send your UI state to the backend as well
    formData.append('task', mainTask);
    formData.append('use_context_enrichment', useContextEnrichment.toString());
    formData.append('use_reorder_rec', useReorderRec.toString());

    setIsUploading(true);

    try {
      const response = await fetch('http://localhost:8000/inventory/upload', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'accept': 'application/json',
          // Note: browser automatically sets Content-Type for FormData!
        },
        body: formData,
      });

      const data = await response.json();
      console.log('Success:', data);
      alert(`File processed successfully! Check console for results.`);
      
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file. Is the backend running?');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("http://localhost:8000/auth/logout", {
        method: "POST",
        credentials: "include", 
      });

      await refreshUser();
      navigate('/');
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  const taskOptions = ['Demand Prediction', 'Inventory Optimization'];

  useEffect(() => {
    if (!user) {
      refreshUser();
    }
  }, [user, refreshUser]);

  return (
    <>
      <div className="min-h-screen animate-bg flex flex-col text-white font-sans relative">
        
        {/* HEADER */}
        <header className="h-24 flex justify-between items-center px-6 w-full relative z-[1000]">
          <div className="font-bold text-xl tracking-wider cursor-pointer flex items-center gap-2" onClick={() => navigate('/dashboard')}>
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
              <span className="font-bold text-white text-sm">Z</span>
            </div>
            <span>Z.AI Hub</span>
          </div>
          
          <div className="relative">
            <button 
              onClick={() => setIsProfileMenuOpen(!isProfileMenuOpen)}
              className="flex items-center justify-center w-11 h-11 rounded-full bg-gradient-to-tr from-blue-500 to-purple-600 border-2 border-white/20 hover:border-white/60 transition-all shadow-lg relative z-50"
            >
              {user?.profile_image ? (
                <img
                  src={`http://localhost:8000${user.profile_image}`}
                  alt="avatar"
                  className="w-full h-full object-cover rounded-full"
                />
              ) : (
                <span className="font-bold text-sm tracking-widest">
                  {user?.username?.slice(0, 2) || "?"}
                </span>
              )}
            </button>

            {isProfileMenuOpen && (
              <div className="absolute right-0 mt-3 w-56 bg-[#0f172a]/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col py-2 transition-all z-50">
                <div className="px-4 py-3 border-b border-white/10 mb-1 bg-white/5">
                  <p className="text-xs text-blue-400 font-medium mb-1">Signed in as</p>
                  <p className="text-sm font-semibold truncate text-gray-200">{user ? user.email: "Loading..."}</p>
                </div>
                <button onClick={() => { navigate('/profile'); setIsProfileMenuOpen(false); }} className="px-4 py-2.5 text-left text-sm text-gray-300 hover:bg-white/10 hover:text-white transition-colors">Profile</button>
                <button onClick={() => { navigate('/usage'); setIsProfileMenuOpen(false); }} className="px-4 py-2.5 text-left text-sm text-gray-300 hover:bg-white/10 hover:text-white transition-colors">Usage Settings</button>
                <button onClick={() => { navigate('/subscriptions'); setIsProfileMenuOpen(false); }} className="px-4 py-2.5 text-left text-sm text-gray-300 hover:bg-white/10 hover:text-white transition-colors">Subscription Plan</button>
                <div className="border-t border-white/10 mt-1 pt-1">
                  <button onClick={handleLogout} className="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors">Log out</button>
                </div>
              </div>
            )}
          </div>
        </header>

        <main className="flex-grow flex flex-col items-center justify-center px-4 w-full max-w-5xl mx-auto -mt-10 relative">
          
          <h1 className="text-4xl md:text-6xl font-extrabold mb-4 text-center tracking-tight relative z-10">
            Welcome back, <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">{user ? user.username : "Loading..."}</span>
          </h1>
          <p className="text-gray-400 text-lg md:text-xl mb-10 text-center font-light tracking-wide relative z-10">
            Select your optimization model parameters below.
          </p>

          {isTaskMenuOpen && (
            <div className="fixed inset-0 z-[900]" onClick={() => setIsTaskMenuOpen(false)}></div>
          )}

          {/* MAIN SEARCH / UPLOAD BAR */}
          <div className={`w-full max-w-3xl relative flex items-center bg-[#0f172a]/80 backdrop-blur-xl border border-white/10 rounded-full p-2 shadow-2xl transition-all hover:border-blue-500/50 focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/20 ${isTaskMenuOpen ? 'z-[999]' : 'z-40'}`}>
            
            <input type="file" ref={fileInputRef} onChange={handleFileSelect} accept=".csv, .xlsx, .xls, .json" className="hidden" />

            {/* The "+" Button to open file dialog */}
            <button 
              onClick={handleFileClick} 
              className="p-3.5 bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 rounded-full transition-all ml-1 shrink-0 relative z-10 flex items-center justify-center" 
              title="Upload File"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" /></svg>
            </button>

            {/* File Name Indicator Pill */}
            {selectedFile && (
              <div className="ml-3 flex items-center bg-blue-500/20 border border-blue-500/40 text-blue-300 text-sm font-medium px-3 py-1.5 rounded-full shrink-0 animate-fade-in">
                <svg className="w-4 h-4 mr-1.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                <span className="truncate max-w-[120px] sm:max-w-[200px]">{selectedFile.name}</span>
                <button onClick={removeSelectedFile} className="ml-2 text-blue-400 hover:text-white transition-colors focus:outline-none">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
              </div>
            )}

            {/* Custom Dropdown */}
            <div className="relative flex-1 ml-2 mr-2">
              <button 
                onClick={() => setIsTaskMenuOpen(!isTaskMenuOpen)}
                className="w-full bg-transparent text-white font-semibold text-lg px-4 py-4 outline-none text-left flex justify-between items-center group relative z-10"
              >
                <span className="truncate">{mainTask}</span>
                <svg 
                  className={`w-5 h-5 text-gray-400 group-hover:text-white transition-transform duration-300 ${isTaskMenuOpen ? 'rotate-180 text-blue-400' : ''}`} 
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Options List */}
              {isTaskMenuOpen && (
                <div className="absolute top-full left-0 mt-3 w-full bg-[#0f172a]/95 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_20px_50px_-10px_rgba(0,0,0,0.7)] py-2 z-[1000] overflow-hidden">
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
              )}
            </div>

            {/* The Submit / Send Button */}
            <button 
              onClick={handleProcessSubmit} 
              disabled={isUploading}
              className={`p-4 rounded-full transition-all shadow-lg mr-1 shrink-0 relative z-10 flex items-center justify-center ${
                isUploading 
                ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white hover:shadow-blue-500/25'
              }`}
            >
              {isUploading ? (
                <svg className="w-6 h-6 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
              )}
            </button>
          </div>

          {/* Optional Toggles Area */}
          {mainTask === 'Demand Prediction' && (
            <div className="w-full max-w-3xl flex flex-col sm:flex-row items-center justify-center gap-4 mt-6 relative z-30">
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
          )}

          <div className="mt-40 max-w-2xl text-center px-6 mb-8 w-full relative z-10">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative bg-[#0f172a]/80 ring-1 ring-white/10 p-6 rounded-2xl backdrop-blur-md shadow-xl">
                <div className="flex items-center justify-center gap-2 mb-3">
                  <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  <strong className="text-white text-base tracking-wide">Hackathon 2026: Economic Empowerment</strong>
                </div>
                <p className="text-gray-400 text-sm leading-relaxed">
                  This platform addresses fragmented data by leveraging the <span className="text-blue-400 font-semibold">Z.AI GLM</span>. By applying context-aware reasoning to structured metrics and unstructured signals, it empowers workers and merchants to optimize decision-making and maximize economic outcomes.
                </p>
              </div>
            </div>
          </div>
        </main>

        {isProfileMenuOpen && <div className="fixed inset-0 z-[900]" onClick={() => setIsProfileMenuOpen(false)}></div>}
      </div>
    </>
  );
}