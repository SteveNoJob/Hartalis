'use client';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function ChatInterface() {
  const navigate = useNavigate();
  const [inputText, setInputText] = useState('');

  // Mock data for previous conversations
  const chatHistory = [
    { id: 1, title: 'Shopee Q3 Inventory Forecast', date: 'Today' },
    { id: 2, title: 'Grab Fleet Route Optimization', date: 'Yesterday' },
    { id: 3, title: 'Weekend Surge Pricing Calc', date: 'Previous 7 Days' },
    { id: 4, title: 'Supplier Cost Analysis', date: 'Previous 30 Days' },
  ];

  return (
    <div className="flex h-screen bg-[#070b14] text-white font-sans overflow-hidden">
      
      {/* --- SIDEBAR (History) --- */}
      <aside className="w-72 bg-[#0a0f1c] border-r border-white/5 flex flex-col hidden md:flex">
        {/* Brand Header */}
        <div className="p-6 flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
            <span className="font-bold text-white text-sm">Z</span>
          </div>
          <span className="font-bold text-xl tracking-wider">Z.AI Hub</span>
        </div>

        {/* New Chat Button */}
        <div className="px-4 mb-6">
          <button 
            onClick={() => navigate('/dashboard')}
            className="w-full flex items-center justify-between bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl p-3 transition-colors text-sm font-medium"
          >
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
              New Analysis
            </div>
          </button>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto px-4 pb-4 custom-scrollbar">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 ml-2">Recent</p>
          <div className="space-y-1">
            {chatHistory.map((chat) => (
              <button key={chat.id} className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-white/5 text-gray-300 hover:text-white transition-colors text-sm truncate group flex items-center gap-3">
                <svg className="w-4 h-4 text-gray-500 group-hover:text-blue-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                <span className="truncate">{chat.title}</span>
              </button>
            ))}
          </div>
        </div>

        {/* User Mini Profile */}
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
        
        {/* Mobile Header (Hidden on Desktop) */}
        <header className="md:hidden flex justify-between items-center p-4 border-b border-white/5 bg-[#0f172a]/80 backdrop-blur-md">
          <div className="font-bold text-lg tracking-wider flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"><span className="font-bold text-white text-[10px]">Z</span></div>
            Z.AI Hub
          </div>
          <button onClick={() => navigate('/dashboard')} className="text-sm text-blue-400">New</button>
        </header>

        {/* Chat Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 scroll-smooth custom-scrollbar">
          
          <div className="max-w-4xl mx-auto w-full space-y-8">
            
            {/* 1. USER MESSAGE BLOCK */}
            <div className="flex flex-col items-end gap-2">
              <div className="flex items-center gap-2 text-gray-400 mb-1 mr-1">
                <span className="text-sm font-medium text-white">You</span>
                <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center"><span className="font-bold text-[8px] tracking-widest text-white">CX</span></div>
              </div>
              
              <div className="bg-[#1e293b]/80 border border-white/10 rounded-2xl rounded-tr-sm p-5 max-w-[85%] shadow-lg">
                <p className="text-gray-200 mb-4">Analyze my sales data and predict inventory needs for the next 30 days. Factor in local holidays.</p>
                
                {/* Visualizer for the parameters they picked on the dashboard */}
                <div className="flex flex-wrap gap-2 mb-3">
                  <span className="bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs px-2.5 py-1 rounded-md font-medium flex items-center gap-1.5">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                    Demand Prediction
                  </span>
                  <span className="bg-purple-500/20 border border-purple-500/30 text-purple-300 text-xs px-2.5 py-1 rounded-md font-medium">
                    + Context Enrichment
                  </span>
                  <span className="bg-purple-500/20 border border-purple-500/30 text-purple-300 text-xs px-2.5 py-1 rounded-md font-medium">
                    + Reorder Recommendations
                  </span>
                </div>

                {/* Visualizer for the uploaded file */}
                <div className="bg-black/40 border border-white/5 rounded-xl p-3 flex items-center gap-3 w-max pr-8">
                  <div className="bg-green-500/20 p-2 rounded-lg">
                    <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-200">shopee_q2_data.csv</p>
                    <p className="text-xs text-gray-500">2.4 MB • 14,020 rows</p>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. AI RESPONSE BLOCK */}
            <div className="flex flex-col items-start gap-2">
              <div className="flex items-center gap-2 text-gray-400 mb-1 ml-1">
                <div className="w-6 h-6 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg"><span className="font-bold text-white text-[10px]">Z</span></div>
                <span className="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Hartalis.AI</span>
              </div>
              
              <div className="bg-transparent text-gray-300 leading-relaxed max-w-[90%] md:max-w-[85%] space-y-4">
                <p>Based on the <code className="text-blue-300 bg-blue-500/10 px-1.5 py-0.5 rounded">shopee_q2_data.csv</code> dataset and applying context enrichment for local market conditions, here is your 30-day economic optimization strategy.</p>
                
                <div className="bg-white/5 border border-white/10 rounded-xl p-5 shadow-lg">
                  <h4 className="text-white font-bold mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                    Demand Prediction Insights
                  </h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span><strong className="text-white">Trend Alert:</strong> Electronics category shows a 42% historical spike approaching the upcoming public holiday.</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">•</span>
                      <span><strong className="text-white">Underperforming Asset:</strong> "Basic T-Shirts" have plateaued. Recommend dynamic price reduction of 8% to clear inventory before end-of-month storage fees apply.</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-white/5 border border-white/10 rounded-xl p-5 shadow-lg">
                  <h4 className="text-white font-bold mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
                    Reorder Recommendations
                  </h4>
                  <p className="text-sm mb-2">To prevent stockouts while maintaining healthy cash flow, issue the following purchase orders immediately:</p>
                  <div className="overflow-x-auto rounded-lg border border-white/10">
                    <table className="w-full text-sm text-left">
                      <thead className="bg-black/40 text-gray-400">
                        <tr>
                          <th className="px-4 py-2 font-medium">SKU</th>
                          <th className="px-4 py-2 font-medium">Suggested Qty</th>
                          <th className="px-4 py-2 font-medium">Confidence</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        <tr className="hover:bg-white/5">
                          <td className="px-4 py-2 text-gray-200">SKU-892 (Wireless Earbuds)</td>
                          <td className="px-4 py-2 text-green-400 font-mono">+1,200 units</td>
                          <td className="px-4 py-2 text-blue-300">94%</td>
                        </tr>
                        <tr className="hover:bg-white/5">
                          <td className="px-4 py-2 text-gray-200">SKU-104 (Powerbank 20k)</td>
                          <td className="px-4 py-2 text-green-400 font-mono">+850 units</td>
                          <td className="px-4 py-2 text-blue-300">89%</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* THE TOKEN USAGE BADGE */}
                <div className="flex justify-start pt-2">
                  <div className="flex items-center gap-1.5 bg-orange-500/10 border border-orange-500/20 text-orange-400 text-xs px-2.5 py-1.5 rounded-md font-mono tracking-wide shadow-sm" title="Tokens consumed for this inference">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    -1,450 Tokens
                  </div>
                </div>

              </div>
            </div>

          </div>
        </div>

        {/* --- FIXED BOTTOM INPUT AREA --- */}
        <div className="p-4 md:p-6 bg-gradient-to-t from-[#070b14] via-[#070b14] to-transparent">
          <div className="max-w-4xl mx-auto relative flex items-end bg-[#1e293b]/60 backdrop-blur-xl border border-white/10 rounded-3xl p-2 shadow-2xl focus-within:border-blue-500/50 transition-colors">
            
            <button className="p-3 text-gray-400 hover:text-white rounded-full transition-colors mb-1">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"/></svg>
            </button>

            <textarea 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask a follow up question or request a different strategy..."
              className="flex-1 bg-transparent text-white placeholder-gray-500 px-4 py-4 outline-none resize-none max-h-32 min-h-[56px] custom-scrollbar"
              rows={1}
            />

            <button className={`p-3 rounded-full transition-all mb-1 mr-1 ${inputText.trim() ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25' : 'bg-white/5 text-gray-500 cursor-not-allowed'}`}>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
            </button>
          </div>
          <p className="text-center text-xs text-gray-500 mt-3">
            Z.AI GLM can make mistakes. Consider verifying important economic decisions.
          </p>
        </div>

      </main>
      
    </div>
  );
}