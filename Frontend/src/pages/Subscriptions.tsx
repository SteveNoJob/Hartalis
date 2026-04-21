'use client';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SubscriptionPlans() {
  const navigate = useNavigate();
  
  // Payment Flow States
  const [selectedPlan, setSelectedPlan] = useState<{name: string, price: string} | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Form Input States
  const [cardName, setCardName] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvc, setCvc] = useState('');

  // Developer Override State
  const [devOverrideActive, setDevOverrideActive] = useState(false);

  // --- THE HIDDEN DEVELOPER BYPASS LISTENER ---
  useEffect(() => {
    const overrideSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a', 'Enter'];
    let currentSequence: string[] = [];

    const handleKeyDown = (e: KeyboardEvent) => {
      const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
      currentSequence.push(key);

      if (currentSequence.length > overrideSequence.length) {
        currentSequence.shift();
      }

      if (currentSequence.join(',') === overrideSequence.join(',')) {
        setDevOverrideActive(true); // Trigger Professional Override
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // --- FORMATTING LOGIC ---
  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '');
    value = value.substring(0, 16);
    value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
    setCardNumber(value);
  };

  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '');
    value = value.substring(0, 4);
    if (value.length >= 3) {
      value = `${value.substring(0, 2)}/${value.substring(2, 4)}`;
    }
    setExpiry(value);
  };

  const handleCvcChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').substring(0, 4);
    setCvc(value);
  };

  const handlePayment = (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);
    
    setTimeout(() => {
      setIsProcessing(false);
      setIsSuccess(true);
      
      setTimeout(() => {
        setIsSuccess(false);
        setSelectedPlan(null);
        setCardName('');
        setCardNumber('');
        setExpiry('');
        setCvc('');
        navigate('/dashboard');
      }, 3000);
    }, 2000);
  };

  return (
    <>

      <div className="min-h-screen animate-bg-warm flex flex-col text-white font-sans pb-12 relative">
        
        <header className="flex justify-between items-center p-6 w-full">
          <button 
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors bg-black/20 px-4 py-2 rounded-full backdrop-blur-md border border-white/10"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Dashboard
          </button>
          <div className="font-bold text-xl tracking-wider">Z.AI Hub</div>
        </header>

        <main className="flex-grow flex flex-col items-center justify-center px-4 w-full max-w-6xl mx-auto mt-8">
          <h1 className="text-4xl md:text-5xl font-extrabold mb-4 text-center">
            Unlock True <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-yellow-300">Decision Intelligence</span>
          </h1>
          <p className="text-gray-300 mb-12 text-center max-w-2xl text-lg bg-black/20 p-4 rounded-xl backdrop-blur-sm border border-white/10">
            Power your business optimizations with Z.AI GLM tokens. Choose the plan that fits your data volume.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full">
            
            {/* Free Plan */}
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-8 flex flex-col hover:bg-white/10 transition-all shadow-xl">
              <h2 className="text-2xl font-bold text-gray-200">Starter</h2>
              <div className="mt-4 mb-6">
                <span className="text-4xl font-extrabold">RM 0</span><span className="text-gray-400"> / forever</span>
              </div>
              <ul className="flex-grow space-y-4 mb-8 text-gray-300">
                <li className="flex items-center gap-3"><span className="text-orange-400">✓</span> 1,000 Z.AI Tokens / month</li>
                <li className="flex items-center gap-3"><span className="text-orange-400">✓</span> Basic Data Parsing</li>
              </ul>
              <button className="w-full py-3 rounded-xl border border-white/20 text-gray-500 cursor-not-allowed font-semibold">
                Current Plan
              </button>
            </div>

            {/* Monthly Pro Plan */}
            <div className="bg-gradient-to-b from-white/15 to-white/5 backdrop-blur-xl border-2 border-orange-400/50 rounded-3xl p-8 flex flex-col transform md:-translate-y-4 shadow-2xl relative">
              <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gradient-to-r from-orange-500 to-pink-500 px-4 py-1 rounded-full text-sm font-bold shadow-lg">
                Most Popular
              </div>
              <h2 className="text-2xl font-bold text-orange-300">Monthly Pro</h2>
              <div className="mt-4 mb-6">
                <span className="text-4xl font-extrabold">RM 49</span><span className="text-gray-300"> / month</span>
              </div>
              <ul className="flex-grow space-y-4 mb-8 text-gray-100">
                <li className="flex items-center gap-3"><span className="text-yellow-400 text-xl">★</span> 50,000 Z.AI Tokens</li>
                <li className="flex items-center gap-3"><span className="text-yellow-400 text-xl">★</span> Advanced Trade-Offs</li>
              </ul>
              <button 
                onClick={() => setSelectedPlan({ name: 'Monthly Pro', price: 'RM 49' })}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-orange-500 to-pink-600 hover:from-orange-400 hover:to-pink-500 transition-colors font-bold shadow-lg text-white"
              >
                Upgrade to Pro
              </button>
            </div>

            {/* Yearly Pro Plan */}
            <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-3xl p-8 flex flex-col hover:bg-white/10 transition-all shadow-xl">
              <h2 className="text-2xl font-bold text-gray-200">Yearly Pro</h2>
              <div className="mt-4 mb-6">
                <span className="text-4xl font-extrabold">RM 399</span><span className="text-gray-400"> / year</span>
              </div>
              <ul className="flex-grow space-y-4 mb-8 text-gray-300">
                <li className="flex items-center gap-3"><span className="text-orange-400">✓</span> 750,000 Z.AI Tokens</li>
                <li className="flex items-center gap-3"><span className="text-orange-400">✓</span> Save RM 189 annually</li>
              </ul>
              <button 
                onClick={() => setSelectedPlan({ name: 'Yearly Pro', price: 'RM 399' })}
                className="w-full py-3 rounded-xl border border-white/20 hover:bg-white/10 transition-colors font-semibold"
              >
                Go Yearly
              </button>
            </div>
          </div>
        </main>

        {/* --- PROFESSIONAL DEVELOPER OVERRIDE OVERLAY --- */}
        {devOverrideActive && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md px-4">
            <div className="bg-[#0f172a] border border-blue-500/30 rounded-3xl w-full max-w-md p-8 shadow-2xl text-center relative overflow-hidden">
              {/* Subtle top accent bar */}
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-600"></div>

              <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-blue-500/20">
                <svg className="w-8 h-8 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
              </div>
              
              <h3 className="text-2xl font-bold text-white mb-2">
                Developer Environment
              </h3>
              <p className="text-gray-400 mb-8 text-sm leading-relaxed">
                Local testing detected. Subscription enforcement has been disabled and token restrictions are lifted for QA testing.
              </p>
              
              <button 
                onClick={() => {
                  setDevOverrideActive(false);
                  navigate('/dashboard');
                }}
                className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 transition-colors font-semibold text-white shadow-lg"
              >
                Acknowledge & Continue
              </button>
            </div>
          </div>
        )}

        {/* --- STANDARD PAYMENT MODAL OVERLAY --- */}
        {selectedPlan && !devOverrideActive && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm px-4">
            <div className="bg-gray-900 border border-white/10 rounded-3xl w-full max-w-md p-8 shadow-2xl relative overflow-hidden">
              
              {!isProcessing && !isSuccess && (
                <button onClick={() => setSelectedPlan(null)} className="absolute top-4 right-4 text-gray-400 hover:text-white">
                  ✕
                </button>
              )}

              {isSuccess ? (
                <div className="text-center py-8">
                  <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">Payment Successful!</h3>
                  <p className="text-gray-400">Your account has been upgraded.<br/>Redirecting to dashboard...</p>
                </div>
              ) : (
                <>
                  <h3 className="text-2xl font-bold text-white mb-1">Checkout</h3>
                  <p className="text-gray-400 mb-6">You are upgrading to <span className="text-orange-400 font-bold">{selectedPlan.name}</span></p>

                  <form onSubmit={handlePayment} className="space-y-4">
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Name on Card</label>
                      <input 
                        required 
                        type="text" 
                        value={cardName}
                        onChange={(e) => setCardName(e.target.value)}
                        placeholder="Chenxuan" 
                        className="w-full bg-black/50 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-orange-500" 
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-400 mb-1">Card Number</label>
                      <input 
                        required 
                        type="text" 
                        value={cardNumber}
                        onChange={handleCardNumberChange}
                        placeholder="•••• •••• •••• 4242" 
                        className="w-full bg-black/50 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-orange-500 tracking-wider" 
                      />
                    </div>
                    <div className="flex gap-4">
                      <div className="w-1/2">
                        <label className="block text-sm text-gray-400 mb-1">Expiry</label>
                        <input 
                          required 
                          type="text" 
                          value={expiry}
                          onChange={handleExpiryChange}
                          placeholder="MM/YY" 
                          className="w-full bg-black/50 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-orange-500 tracking-widest" 
                        />
                      </div>
                      <div className="w-1/2">
                        <label className="block text-sm text-gray-400 mb-1">CVC</label>
                        <input 
                          required 
                          type="text" 
                          value={cvc}
                          onChange={handleCvcChange}
                          placeholder="123" 
                          className="w-full bg-black/50 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-orange-500 tracking-widest" 
                        />
                      </div>
                    </div>
                    
                    <button 
                      type="submit" 
                      disabled={isProcessing}
                      className="w-full mt-6 py-4 rounded-xl bg-gradient-to-r from-orange-500 to-pink-600 hover:from-orange-400 hover:to-pink-500 transition-all font-bold shadow-lg text-white flex justify-center items-center gap-2 disabled:opacity-50"
                    >
                      {isProcessing ? (
                        <>
                          <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24" fill="none">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Processing...
                        </>
                      ) : (
                        `Pay ${selectedPlan.price}`
                      )}
                    </button>
                  </form>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}