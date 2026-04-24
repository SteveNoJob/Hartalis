'use client';
import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token");

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // validation
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setError("");

    try {
      const res = await fetch("http://localhost:8000/auth/reset-confirm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token,
          new_password: password,
        }),
      });

      if (!res.ok) {
        throw new Error("Reset failed");
      }

      alert("Password reset successful!");
      navigate("/"); // back to login

    } catch (err) {
      console.error(err);
      setError("Invalid or expired token");
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

          <h2 className="text-2xl font-bold text-center mb-2">
            Reset Password
          </h2>

          <p className="text-gray-400 text-center mb-6 text-sm">
            Enter your new password below
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* New Password */}
            <div>
              <label className="text-sm text-gray-400">New Password</label>
              <div className="relative mt-1">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter new password"
                  required
                  className="w-full px-4 py-3 pr-12 bg-white/5 border border-white/10 rounded-lg 
                  focus:outline-none focus:ring-2 focus:ring-blue-500/40 
                  focus:border-blue-500/40 transition text-white placeholder-gray-500"
                />
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="text-sm text-gray-400">Confirm Password</label>
              <div className="relative mt-1">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  required
                  className="w-full px-4 py-3 pr-12 bg-white/5 border border-white/10 rounded-lg 
                  focus:outline-none focus:ring-2 focus:ring-blue-500/40 
                  focus:border-blue-500/40 transition text-white placeholder-gray-500"
                />

                {/* Show/Hide toggle */}
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-gray-400 hover:text-white text-sm"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            {/* Error message */}
            {error && (
              <p className="text-red-400 text-sm text-center">{error}</p>
            )}

            {/* Submit */}
            <button
              type="submit"
              className="w-full py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 
              hover:from-blue-500 hover:to-purple-500 transition-all shadow-lg 
              hover:shadow-blue-500/25 font-semibold"
            >
              Reset Password
            </button>
          </form>

          {/* Back to login */}
          <button
            onClick={() => navigate('/')}
            className="mt-4 text-sm text-gray-400 hover:text-white w-full text-center"
          >
            ← Back to login
          </button>

        </div>
      </div>
    </div>
  );
}