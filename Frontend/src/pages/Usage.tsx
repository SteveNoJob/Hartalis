'use client';
import { useNavigate } from 'react-router-dom';

export default function UsageSettings() {
  const navigate = useNavigate();

  // Fake data to make the dashboard look active for the judges
  const planLimit = 50000;
  const tokensUsed = 38450;
  const usagePercentage = Math.round((tokensUsed / planLimit) * 100);

  // Fake recent activity logs
  const activityLogs = [
    { id: 1, action: "Market Sentiment Analysis (Shopee Data)", tokens: 1250, date: "Today, 10:42 AM" },
    { id: 2, action: "Dynamic Pricing Optimization (JSON)", tokens: 840, date: "Today, 09:15 AM" },
    { id: 3, action: "Route Weather Calculation", tokens: 320, date: "Yesterday, 04:30 PM" },
    { id: 4, action: "Gig Worker Surge Prediction", tokens: 4100, date: "Yesterday, 11:20 AM" },
  ];

  return (
    <div className="min-h-screen animate-bg flex flex-col text-white font-sans pb-12 relative">
      
      {/* Top Navigation Bar */}
      <header className="flex justify-between items-center p-6 w-full relative z-50">
        <button 
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors bg-white/5 px-4 py-2 rounded-full backdrop-blur-md border border-white/10 hover:bg-white/10"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </button>
        <div className="font-bold text-xl tracking-wider flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
            <span className="font-bold text-white text-sm">Z</span>
          </div>
          <span>Z.AI Hub</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow flex flex-col items-center px-4 w-full max-w-5xl mx-auto mt-8 relative z-10">
        
        <div className="w-full mb-10">
          <h1 className="text-3xl md:text-4xl font-extrabold mb-2 tracking-tight">Usage & Telemetry</h1>
          <p className="text-gray-400 text-lg">Monitor your Z.AI GLM token consumption and API activity.</p>
        </div>

        {/* Top Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-8">
          
          {/* Card 1: Tokens Used */}
          <div className="bg-[#0f172a]/60 backdrop-blur-xl border border-white/10 rounded-3xl p-6 shadow-xl flex flex-col">
            <span className="text-gray-400 text-sm font-medium mb-2 uppercase tracking-wider">Tokens Used</span>
            <span className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">
              {tokensUsed.toLocaleString()}
            </span>
            <span className="text-gray-500 text-xs mt-2">This billing cycle</span>
          </div>

          {/* Card 2: Tokens Remaining */}
          <div className="bg-[#0f172a]/60 backdrop-blur-xl border border-white/10 rounded-3xl p-6 shadow-xl flex flex-col">
            <span className="text-gray-400 text-sm font-medium mb-2 uppercase tracking-wider">Tokens Remaining</span>
            <span className="text-4xl font-black text-white">
              {(planLimit - tokensUsed).toLocaleString()}
            </span>
            <span className="text-gray-500 text-xs mt-2">Resets in 12 days</span>
          </div>

          {/* Card 3: Current Plan */}
          <div className="bg-gradient-to-br from-purple-900/40 to-blue-900/40 backdrop-blur-xl border border-purple-500/30 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
            <div>
              <span className="text-purple-300 text-sm font-medium mb-1 block uppercase tracking-wider">Current Plan</span>
              <span className="text-2xl font-bold text-white">Monthly Pro</span>
            </div>
            <button 
              onClick={() => navigate('/subscriptions')}
              className="mt-4 w-full py-2 bg-purple-500/20 hover:bg-purple-500/40 text-purple-200 rounded-xl text-sm font-semibold transition-colors border border-purple-500/30"
            >
              Manage Plan
            </button>
          </div>
        </div>

        {/* Progress Bar Section */}
        <div className="w-full bg-[#0f172a]/60 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-xl mb-8">
          <div className="flex justify-between items-end mb-4">
            <div>
              <h3 className="text-xl font-bold text-white mb-1">Monthly Limit Overview</h3>
              <p className="text-gray-400 text-sm">{usagePercentage}% of total capacity used</p>
            </div>
            <span className="text-gray-400 text-sm font-mono">{tokensUsed.toLocaleString()} / {planLimit.toLocaleString()}</span>
          </div>
          
          {/* The Visual Bar */}
          <div className="w-full bg-gray-800 rounded-full h-4 overflow-hidden shadow-inner">
            <div 
              className={`h-full rounded-full transition-all duration-1000 ${usagePercentage > 85 ? 'bg-gradient-to-r from-orange-500 to-red-500' : 'bg-gradient-to-r from-blue-500 to-purple-500'}`}
              style={{ width: `${usagePercentage}%` }}
            ></div>
          </div>
          
          {usagePercentage > 75 && (
            <p className="text-orange-400 text-sm mt-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
              You are approaching your monthly limit.
            </p>
          )}
        </div>

        {/* Activity Log Table */}
        <div className="w-full bg-[#0f172a]/60 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-xl overflow-hidden">
          <h3 className="text-xl font-bold text-white mb-6">Recent AI Requests</h3>
          
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-gray-400 text-sm tracking-wider uppercase">
                  <th className="pb-4 font-medium pl-2">Task / File Processed</th>
                  <th className="pb-4 font-medium">Date & Time</th>
                  <th className="pb-4 font-medium text-right pr-2">Tokens Used</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {activityLogs.map((log) => (
                  <tr key={log.id} className="border-b border-white/5 hover:bg-white/5 transition-colors group">
                    <td className="py-4 pl-2 text-gray-200 flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-blue-500 group-hover:shadow-[0_0_8px_#3b82f6]"></div>
                      {log.action}
                    </td>
                    <td className="py-4 text-gray-500">{log.date}</td>
                    <td className="py-4 text-right pr-2 font-mono text-blue-300">-{log.tokens}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

      </main>
    </div>
  );
}