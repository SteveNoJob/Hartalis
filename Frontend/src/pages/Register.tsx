'use client';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function RegisterPage() {

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
  e.preventDefault();

  // basic validation
  if (password !== confirmPassword) {
    setError("Passwords do not match");
    return;
  }

  try {
    const res = await fetch("http://localhost:8000/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        username,
        password,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      setError(data.detail || "Registration failed");
      return;
    }

    // success
    alert("Account created!");
    navigate('/'); // go to login

  } catch (err) {
    console.error(err);
    setError("Something went wrong");
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

          {/* Title */}
          <h2 className="text-3xl font-extrabold text-center mb-2 tracking-tight">
            Create your{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
              account
            </span>
          </h2>

          <p className="text-gray-400 text-center mb-8 text-sm">
            Join Z.AI Hub and start optimizing your data
          </p>

          {/* Form */}
          <form onSubmit={handleRegister} className="space-y-5">

            {/* Name */}
            <div>
              <label className="text-sm text-gray-400">Full Name</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)} 
                placeholder="King Boshua"
                className="w-full mt-1 px-4 py-3 bg-white/5 border border-white/10 rounded-lg 
                focus:outline-none focus:ring-2 focus:ring-blue-500/40 
                focus:border-blue-500/40 transition text-white placeholder-gray-500"
              />
            </div>

            {/* Email */}
            <div>
              <label className="text-sm text-gray-400">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e)=>setEmail(e.target.value)}
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
                  placeholder="Create a password"
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

            {/* Confirm Password */}
            <div>
              <label className="text-sm text-gray-400">Confirm Password</label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                className="w-full mt-1 px-4 py-3 bg-white/5 border border-white/10 rounded-lg 
                focus:outline-none focus:ring-2 focus:ring-blue-500/40 
                focus:border-blue-500/40 transition text-white placeholder-gray-500"
              />
            </div>

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
              Create Account
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center text-sm text-gray-400">
            Already have an account?{" "}
            <span
              onClick={() => navigate('/')}
              className="text-blue-400 hover:text-blue-300 cursor-pointer"
            >
              Sign in
            </span>
          </div>

        </div>
      </div>
    </div>
  );
}