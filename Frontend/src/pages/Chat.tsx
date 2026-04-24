'use client';
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

interface Message {
  id: number;
  role: string;
  content: string;
}

interface ChatHistoryItem {
  id: string;
  title: string;
}

export default function ChatInterface() {
  const navigate = useNavigate();
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // --- SESSION MANAGEMENT ---
  // Generate a unique session ID when this component mounts so the backend can group these messages.
  const currentSessionId = useRef(`session_${Date.now()}`);

  // --- CHAT STATE ---
  const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);

  // --- FILE UPLOAD STATE ---
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [attachedFile, setAttachedFile] = useState<string | null>(null);
  const [isUploadingFile, setIsUploadingFile] = useState(false);

  // --- 1. FETCH CHAT HISTORY ON MOUNT ---
  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const response = await fetch('http://localhost:8000/inventory/history', {
          method: 'GET',
          headers: {
            'accept': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}` // Uncomment if your API is secured!
          }
        });

        if (!response.ok) throw new Error('Failed to fetch history');

        const data = await response.json();
        
        // Map the backend data to guarantee our UI has the fields it needs
        const formattedHistory = data.map((item: any, index: number) => ({
          id: item.session_id || item.id || `fallback-id-${index}`,
          title: item.title || item.topic || `Analysis Session ${index + 1}`
        }));

        setChatHistory(formattedHistory);

      } catch (error) {
        console.error("Error fetching chat history:", error);
        setChatHistory([]); // Fail silently if server is offline
      }
    };

    fetchChatHistory();
  }, []);

  // --- 2. HANDLE FILE UPLOAD ---
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploadingFile(true);
    
    // We use FormData to send files to the backend
    const formData = new FormData();
    formData.append('file', file); // Make sure 'file' is the exact key the API expects
    formData.append('session_id', currentSessionId.current); 

    try {
      const response = await fetch('http://localhost:8000/inventory/upload', {
        method: 'POST',
        // Do NOT set Content-Type header manually when sending FormData
        // headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        body: formData
      });

      if (!response.ok) throw new Error('Upload failed');
      
      const data = await response.json();
      
      // Save the filename to state so we can show it in the UI and send it with chats
      setAttachedFile(data.filename || file.name); 

    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Failed to upload file. Please try again.");
    } finally {
      setIsUploadingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = ''; // Reset input
    }
  };

  // --- 3. HANDLE SENDING MESSAGES ---
  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage = { 
      id: Date.now(), 
      role: 'user', 
      content: inputText 
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/inventory/chat', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${localStorage.getItem('token')}` 
        },
        body: JSON.stringify({
          session_id: currentSessionId.current, 
          message: userMessage.content,
          conversation_history: messages.map(m => ({
            role: m.role,
            content: m.content
          })),
          // Send the attached file context, or a default string if empty
          data_context: attachedFile || "none" 
        })
      });

      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response || data.message || data.content || "Task completed." 
      }]);

    } catch (error) {
      console.error("Error communicating with backend:", error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: "⚠️ Connection error. Could not reach the Hartalis.AI server."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-[#070b14] text-white font-sans overflow-hidden">
      
      {/* --- SIDEBAR (History) --- */}
      <aside className="w-72 bg-[#0a0f1c] border-r border-white/5 flex flex-col hidden md:flex">
        <div className="p-6 flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
            <span className="font-bold text-white text-sm">Z</span>
          </div>
          <span className="font-bold text-xl tracking-wider">Z.AI Hub</span>
        </div>

        <div className="px-4 mb-6">
          <button 
            onClick={() => {
              currentSessionId.current = `session_${Date.now()}`;
              setMessages([]);
              setAttachedFile(null); // Clear file on new session
              navigate('/dashboard'); 
            }}
            className="w-full flex items-center justify-between bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl p-3 transition-colors text-sm font-medium"
          >
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
              New Analysis
            </div>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 pb-4 custom-scrollbar">
          {chatHistory.length > 0 && (
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 ml-2">Recent</p>
          )}
          <div className="space-y-1">
            {chatHistory.map((chat) => (
              <button key={chat.id} className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-white/5 text-gray-300 hover:text-white transition-colors text-sm truncate group flex items-center gap-3">
                <svg className="w-4 h-4 text-gray-500 group-hover:text-blue-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                <span className="truncate">{chat.title}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-white/5 bg-[#0a0f1c]">
          <button onClick={() => navigate('/profile')} className="w-full flex items-center gap-3 hover:bg-white/5 p-2 rounded-xl transition-colors text-left">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center shrink-0">
              <span className="font-bold text-xs tracking-widest">CX</span>
            </div>
            <div className="flex-1 truncate">
              <p className="text-sm font-semibold text-white truncate">Chenxuan</p>
              <p className="text-xs text-blue-400 truncate">Monthly Pro Plan</p>
            </div>
          </button>
        </div>
      </aside>

      {/* --- MAIN CHAT AREA --- */}
      <main className="flex-1 flex flex-col relative bg-gradient-to-br from-[#0f172a] to-[#070b14]">
        
        <header className="md:hidden flex justify-between items-center p-4 border-b border-white/5 bg-[#0f172a]/80 backdrop-blur-md">
          <div className="font-bold text-lg tracking-wider flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"><span className="font-bold text-white text-[10px]">Z</span></div>
            Z.AI Hub
          </div>
          <button onClick={() => {
            currentSessionId.current = `session_${Date.now()}`;
            setMessages([]);
            setAttachedFile(null);
          }} className="text-sm text-blue-400">New</button>
        </header>

        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scroll-smooth custom-scrollbar">
          <div className="max-w-4xl mx-auto w-full space-y-8">
            
            {messages.length === 0 && !isLoading && (
               <div className="flex flex-col items-center justify-center h-full text-center mt-20 opacity-50">
                 <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 border border-white/10 flex items-center justify-center mb-4">
                   <span className="font-bold text-2xl text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Z</span>
                 </div>
                 <h2 className="text-xl font-bold mb-2">How can I help you analyze your data today?</h2>
                 <p className="text-sm text-gray-400">Upload a dataset or enter a query below to start.</p>
               </div>
            )}

            {messages.map((msg) => (
              msg.role === 'user' ? (
                <div key={msg.id} className="flex flex-col items-end gap-2">
                  <div className="flex items-center gap-2 text-gray-400 mb-1 mr-1">
                    <span className="text-sm font-medium text-white">You</span>
                    <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center"><span className="font-bold text-[8px] tracking-widest text-white">CX</span></div>
                  </div>
                  <div className="bg-[#1e293b]/80 border border-white/10 rounded-2xl rounded-tr-sm p-5 max-w-[85%] shadow-lg">
                    <p className="text-gray-200 whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ) : (
                <div key={msg.id} className="flex flex-col items-start gap-2">
                  <div className="flex items-center gap-2 text-gray-400 mb-1 ml-1">
                    <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg"><span className="font-bold text-white text-[10px]">Z</span></div>
                    <span className="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Hartalis.AI</span>
                  </div>
                  <div className="bg-transparent text-gray-300 leading-relaxed max-w-[90%] md:max-w-[85%] space-y-4">
                    <div className="bg-white/5 border border-white/10 rounded-xl p-5 shadow-lg">
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                </div>
              )
            ))}

            {isLoading && (
              <div className="flex flex-col items-start gap-2">
                <div className="flex items-center gap-2 text-gray-400 mb-1 ml-1">
                  <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg animate-pulse"><span className="font-bold text-white text-[10px]">Z</span></div>
                  <span className="text-sm font-bold text-gray-500 animate-pulse">Analyzing context...</span>
                </div>
              </div>
            )}

          </div>
        </div>

        {/* --- FIXED BOTTOM INPUT AREA --- */}
        <div className="p-4 md:p-6 bg-gradient-to-t from-[#070b14] via-[#070b14] to-transparent flex flex-col items-center">
          
          {/* File Uploading Spinner */}
          {isUploadingFile && (
            <div className="w-full max-w-4xl mb-2 flex justify-start">
               <span className="text-xs text-blue-400 flex items-center gap-2 bg-blue-500/10 px-3 py-1.5 rounded-full border border-blue-500/20">
                 <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                 Uploading...
               </span>
            </div>
          )}
          
          {/* Attached File Badge */}
          {attachedFile && !isUploadingFile && (
            <div className="w-full max-w-4xl mb-2 flex justify-start">
              <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 text-green-400 text-xs px-3 py-1.5 rounded-full shadow-sm">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                {attachedFile}
                <button onClick={() => setAttachedFile(null)} className="ml-1 hover:text-white transition-colors" title="Remove file">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>
            </div>
          )}

          <div className={`w-full max-w-4xl relative flex items-end bg-[#1e293b]/60 backdrop-blur-xl border ${isLoading ? 'border-blue-500/30' : 'border-white/10'} rounded-3xl p-2 shadow-2xl focus-within:border-blue-500/50 transition-colors`}>
            
            {/* Hidden File Input */}
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept=".csv,.xlsx,.xls,.json" 
            />

            {/* Upload Button */}
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploadingFile || isLoading}
              className="p-3 text-gray-400 hover:text-white rounded-full transition-colors mb-1 disabled:opacity-50"
              title="Upload Data Context"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
            </button>

            <textarea 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder={isLoading ? "Please wait..." : "Ask a follow up question or request a different strategy..."}
              className="flex-1 bg-transparent text-white placeholder-gray-500 px-4 py-4 outline-none resize-none max-h-32 min-h-[56px] custom-scrollbar disabled:opacity-50"
              rows={1}
            />

            <button 
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isLoading}
              className={`p-3 rounded-full transition-all mb-1 mr-1 ${(inputText.trim() && !isLoading) ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25' : 'bg-white/5 text-gray-500 cursor-not-allowed'}`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
            </button>
          </div>
          <p className="text-center text-xs text-gray-500 mt-3">
            Z.AI GLM can make mistakes. Consider verifying important decisions.
          </p>
        </div>

      </main>
    </div>
  );
}