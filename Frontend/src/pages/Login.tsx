'use client';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [showReset, setShowReset] = useState(false);
  const [email, setEmail] = useState('');
  const navigate = useNavigate();

  const handleReset = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    alert(`Password reset link sent to ${email}`);
    setShowReset(false);
  };

  const [password, setPassword] = useState('');

  const { refreshUser } = useAuth();
  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include", // 🔥 VERY IMPORTANT (for cookies)
        body: JSON.stringify({
          email: email, // backend expects username
          password: password,
          remember_me: true // For now default to true, CHANGE THIS PLS
        }),
      });

      if (!res.ok) {
        throw new Error("Login failed");
      }

      const data = await res.json();
      console.log(data);

      // IMPORTANT: sync auth state
      
      await refreshUser();

      // now navigate
      navigate("/dashboard");

    } catch (err) {
      console.error(err);
      alert("Login failed");
    }
  };

  return (
    <div className="min-h-screen animate-bg flex items-center justify-center text-white font-sans px-4">
      
      {/* Glow background */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 blur-3xl opacity-30"></div>

      <div className="relative w-full max-w-md">
        
        {/* Outer glow */}
        <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-25"></div>

        {/* Glass card */}
        <div className="relative bg-[#0f172a]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">

          {!showReset ? (
            <>
              {/* LOGIN VIEW */}
              <h2 className="text-3xl font-extrabold text-center mb-2 tracking-tight">
                Welcome to{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
                  Z.AI Hub
                </span>
              </h2>

              <p className="text-gray-400 text-center mb-8 text-sm">
                Sign in to continue optimizing your data
              </p>

              <form onSubmit={handleLogin} className="space-y-5">

                {/* Email */}
                <div>
                  <label className="text-sm text-gray-400">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="w-full mt-1 px-4 py-3 bg-white/5 border border-white/10 rounded-lg 
                    focus:outline-none focus:ring-2 focus:ring-blue-500/40 
                    focus:border-blue-500/40 transition text-white placeholder-gray-500"
                  />
                </div>

                {/* Password */}
                <div>
                  <label className="text-sm text-gray-400">Password</label>
                  <div className="relative mt-1">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="w-full px-4 py-3 pr-12 bg-white/5 border border-white/10 rounded-lg 
                      focus:outline-none focus:ring-2 focus:ring-blue-500/40 
                      focus:border-blue-500/40 transition text-white placeholder-gray-500"
                    />

                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3 text-gray-400 hover:text-white text-sm"
                    >
                      {showPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </div>

                {/* Forgot Password */}
                <div className="text-right">
                  <button
                    type="button"
                    onClick={() => setShowReset(true)}
                    className="text-sm text-blue-400 hover:text-blue-300"
                  >
                    Forgot password?
                  </button>
                </div>

                {/* Login Button */}
                <button
                  type="submit"
                  className="w-full py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 
                  hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg 
                  hover:shadow-blue-500/25 font-semibold"
                >
                  Sign In
                </button>
              </form>

              <div className="mt-6 text-center text-sm text-gray-400">
                Don’t have an account?{" "}
                <span
                  onClick={() => navigate('/register')}
                  className="text-blue-400 hover:text-blue-300 cursor-pointer"
                >
                  Sign up
                </span>
              </div>
            </>
          ) : (
            <>
              {/* RESET VIEW */}
              <h2 className="text-2xl font-bold text-center mb-2">
                Reset Password
              </h2>

              <p className="text-gray-400 text-center mb-6 text-sm">
                Enter your email and we’ll send you a reset link
              </p>

              <form onSubmit={handleReset} className="space-y-5">
                <div>
                  <label className="text-sm text-gray-400">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full mt-1 px-4 py-3 bg-white/5 border border-white/10 rounded-lg 
                    focus:outline-none focus:ring-2 focus:ring-blue-500/40 
                    focus:border-blue-500/40 transition text-white placeholder-gray-500"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 
                  hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg 
                  hover:shadow-blue-500/25 font-semibold"
                >
                  Send Reset Link
                </button>
              </form>

              <button
                onClick={() => setShowReset(false)}
                className="mt-4 text-sm text-gray-400 hover:text-white w-full text-center"
              >
                ← Back to login
              </button>
            </>
          )}

        </div>
      </div>
    </div>
  );
}