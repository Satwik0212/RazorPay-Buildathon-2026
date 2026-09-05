import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { apiClient } from '../../api/client';
import { Layers, Scan, Cpu, Activity } from 'lucide-react';

const IntelligenceVisual = () => (
  <div className="relative w-full aspect-[16/9] max-h-[380px] rounded-xl overflow-hidden bg-[#05050A] shadow-2xl flex items-center justify-center border border-white/10">
    {/* Grid Background */}
    <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff04_1px,transparent_1px),linear-gradient(to_bottom,#ffffff04_1px,transparent_1px)] bg-[size:24px_24px]"></div>

    {/* Ambient Glows */}
    <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-[#6C2BD9]/15 rounded-full blur-[80px]"></div>
    <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-[#2DD4BF]/10 rounded-full blur-[80px]"></div>

    {/* Central Hub */}
    <div className="relative z-10 flex items-center justify-between w-full h-full p-6 sm:p-10 gap-4">

       {/* Left: Source Catalogue */}
       <div className="hidden sm:flex flex-col gap-3 w-[30%] animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <div className="text-[10px] uppercase tracking-[0.2em] text-[#667085] font-bold flex items-center gap-2">
             <Layers className="w-3.5 h-3.5" /> Source
          </div>
          <div className="p-4 rounded-xl border border-white/10 bg-[#ffffff05] backdrop-blur-md">
             <div className="w-full aspect-square rounded-lg bg-[#ffffff08] mb-4 flex items-center justify-center border border-white/5">
                <Scan className="w-8 h-8 text-white/20" />
             </div>
             <div className="h-2 w-3/4 bg-white/20 rounded mb-2.5"></div>
             <div className="h-2 w-1/2 bg-white/10 rounded mb-6"></div>
             <div className="flex justify-between items-center text-[10px] font-mono border-t border-white/5 pt-3">
                <span className="text-[#8b95a5]">SKU_09X</span>
                <span className="text-white font-medium">₹2,499</span>
             </div>
          </div>
       </div>

       {/* Center: Processing / AI Lens */}
       <div className="relative flex flex-col items-center justify-center flex-1 h-full max-w-[200px]">
          {/* Vertical axis line */}
          <div className="absolute h-full w-px bg-gradient-to-b from-transparent via-[#6C2BD9]/50 to-transparent"></div>

          {/* Horizontal Scanning Line */}
          <div className="absolute w-full h-px bg-gradient-to-r from-transparent via-[#22D3EE] to-transparent animate-scan shadow-[0_0_10px_#22D3EE]"></div>

          {/* Core Lens Node */}
          <div className="relative z-10 bg-[#0B0B14] border border-[#6C2BD9]/40 rounded-2xl p-4 shadow-[0_0_30px_rgba(108,43,217,0.2)] flex flex-col items-center gap-2">
             <div className="w-10 h-10 rounded-full bg-[#6C2BD9]/20 flex items-center justify-center border border-[#6C2BD9]/30">
               <Cpu className="w-5 h-5 text-[#8B5CF6]" />
             </div>
             <span className="text-[9px] uppercase tracking-[0.2em] text-[#8B5CF6] font-bold">Buyer Agent</span>
          </div>

          {/* Rotating Rings */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[150px] h-[150px] border border-dashed border-[#6C2BD9]/25 rounded-full animate-spin-slow"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[190px] h-[190px] border border-[#22D3EE]/15 rounded-full animate-spin-reverse-slow"></div>
       </div>

       {/* Right: Evaluation / Decisions */}
       <div className="flex flex-col gap-3 w-full sm:w-[35%] animate-slide-up" style={{ animationDelay: '0.4s' }}>
          <div className="text-[10px] uppercase tracking-[0.2em] text-[#2DD4BF] font-bold flex items-center gap-2">
             <Activity className="w-3.5 h-3.5" /> Signals
          </div>
          <div className="flex flex-col gap-2.5">
             {[
               { label: 'BUDGET_MATCH', color: 'text-[#2DD4BF]', border: 'border-[#2DD4BF]/25', bg: 'bg-[#2DD4BF]/10', dot: 'bg-[#2DD4BF]' },
               { label: 'SLA_VERIFIED', color: 'text-[#2DD4BF]', border: 'border-[#2DD4BF]/25', bg: 'bg-[#2DD4BF]/10', dot: 'bg-[#2DD4BF]' },
               { label: 'TRUST_SCORE', color: 'text-[#22D3EE]', border: 'border-[#22D3EE]/25', bg: 'bg-[#22D3EE]/10', dot: 'bg-[#22D3EE]' },
               { label: 'FRICTION_DETECTED', color: 'text-[#F59E0B]', border: 'border-[#F59E0B]/25', bg: 'bg-[#F59E0B]/10', dot: 'bg-[#F59E0B]' },
             ].map((signal, i) => (
                <div key={signal.label} className={`flex items-center justify-between p-2.5 rounded-lg border ${signal.border} ${signal.bg} backdrop-blur-sm shadow-sm`} style={{ animation: `fade-in 0.5s ease-out ${0.6 + i*0.2}s backwards` }}>
                   <span className={`text-[9px] font-mono ${signal.color} uppercase tracking-widest`}>{signal.label}</span>
                   <div className={`w-1.5 h-1.5 rounded-full ${signal.dot} shadow-[0_0_8px_currentColor]`}></div>
                </div>
             ))}
          </div>
       </div>

    </div>

    <style>{`
      @keyframes scan {
        0% { top: 0%; opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { top: 100%; opacity: 0; }
      }
      .animate-scan {
        animation: scan 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
      }
      @keyframes fade-in {
        0% { opacity: 0; transform: translateY(15px); }
        100% { opacity: 1; transform: translateY(0); }
      }
      .animate-slide-up {
        animation: fade-in 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      }
      @keyframes spin-slow {
        100% { transform: translate(-50%, -50%) rotate(360deg); }
      }
      .animate-spin-slow {
        animation: spin-slow 20s linear infinite;
      }
      @keyframes spin-reverse-slow {
        100% { transform: translate(-50%, -50%) rotate(-360deg); }
      }
      .animate-spin-reverse-slow {
        animation: spin-reverse-slow 25s linear infinite;
      }
    `}</style>
  </div>
);

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.post('/auth/login', {
        email: email.trim(),
        password
      });
      localStorage.setItem('access_token', response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user_profile', JSON.stringify(response.data.user));
      }

      const userRole = response.data.user?.role || response.data.role;
      if (userRole === 'CUSTOMER') {
        localStorage.setItem('buyer_token', response.data.access_token);
        navigate('/buyer');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      const errData = err.response?.data;
      const validationErrors = errData?.error?.details?.errors || (Array.isArray(errData?.detail) ? errData.detail : null);
      let validationMsg: string | null = null;
      if (Array.isArray(validationErrors) && validationErrors.length > 0) {
        const first = validationErrors[0];
        const field = first?.loc?.slice(-1)[0];
        validationMsg = field ? `${field}: ${first?.msg}` : first?.msg;
      }

      setError(
        validationMsg ||
        errData?.error?.message ||
        (typeof errData?.detail === 'string' ? errData.detail : null) ||
        errData?.message ||
        (err.code === 'ERR_NETWORK' || !err.response
          ? 'Unable to connect to backend server. Please verify backend is running on port 8000.'
          : 'Login failed. Please check your credentials and try again.')
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#FFFFFF] font-sans antialiased selection:bg-[#6C2BD9] selection:text-white">
      {/* LEFT PANEL - PRODUCT STORY */}
      <div className="w-full lg:w-[55%] xl:w-[60%] bg-[#020205] text-white flex flex-col justify-between p-8 sm:p-12 lg:p-16 xl:p-24 relative overflow-hidden">
        {/* Subtle background mesh/gradient */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(108,43,217,0.12),transparent_40%)] pointer-events-none"></div>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,rgba(45,212,191,0.06),transparent_50%)] pointer-events-none"></div>

        {/* Brand */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center">
             <span className="text-[#020205] font-black text-lg leading-none tracking-tighter">G</span>
          </div>
          <span className="font-bold text-xl tracking-tight">GraahakLens</span>
        </div>

        {/* Story */}
        <div className="relative z-10 max-w-2xl mt-16 mb-12 lg:my-auto">
          <h1 className="text-[2.5rem] sm:text-5xl lg:text-6xl leading-[1.05] font-semibold tracking-[-0.02em] mb-6">
            See how AI buyers <br className="hidden sm:block"/>see your catalogue.
          </h1>
          <p className="text-[#8b95a5] text-lg sm:text-xl font-medium tracking-tight max-w-[500px] mb-12 leading-relaxed">
            Simulate autonomous evaluation, uncover hidden friction, and optimize for the era of agentic commerce.
          </p>

          {/* ANIMATED VISUALIZATION - Hidden on mobile to keep login highly accessible */}
          <div className="hidden lg:block relative w-full">
            <IntelligenceVisual />
          </div>
        </div>

        {/* Footer */}
        <div className="hidden lg:flex relative z-10 items-center justify-between text-[11px] uppercase tracking-[0.2em] font-bold text-[#667085]">
          <span>Razorpay Buildathon 2026</span>
          <span className="flex items-center gap-2.5 text-[#2DD4BF]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#2DD4BF] opacity-60"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#2DD4BF]"></span>
            </span>
            Intelligence Active
          </span>
        </div>
      </div>

      {/* RIGHT PANEL - LOGIN */}
      <div className="w-full lg:w-[45%] xl:w-[40%] bg-white flex flex-col justify-center px-6 sm:px-16 lg:px-20 xl:px-28 relative min-h-[60vh] lg:min-h-screen border-l border-[#E5E5EA]">
        <div className="w-full max-w-[380px] mx-auto relative z-10">

          <div className="mb-10 text-left">
            <div className="lg:hidden w-10 h-10 bg-[#020205] rounded-md shadow-md flex items-center justify-center mb-6">
              <span className="text-white font-black text-xl leading-none tracking-tighter">G</span>
            </div>
            <h2 className="text-[2rem] font-bold text-[#111118] tracking-tight mb-2">Sign in</h2>
            <p className="text-[#667085] text-sm font-medium">Access your intelligence workspace.</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            {error && (
              <div className="p-4 text-sm text-[#D92D20] bg-[#FEF3F2] rounded-xl border border-[#FEE4E2] flex items-start shadow-sm">
                <span className="block font-medium leading-relaxed">{error}</span>
              </div>
            )}

            <div className="space-y-5">
              <div>
                <label className="block text-[11px] font-bold text-[#111118] uppercase tracking-widest mb-2">Work Email</label>
                <Input
                  type="email"
                  placeholder="merchant@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="h-12 bg-[#F7F7FA] border-[#E5E5EA] text-[#111118] text-base placeholder:text-[#98A2B3] focus:border-[#6C2BD9] focus:ring-1 focus:ring-[#6C2BD9] focus:bg-white shadow-sm rounded-xl transition-all w-full"
                />
              </div>

              <div className="relative">
                <label className="block text-[11px] font-bold text-[#111118] uppercase tracking-widest mb-2">Password</label>
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-12 bg-[#F7F7FA] border-[#E5E5EA] text-[#111118] text-base placeholder:text-[#98A2B3] focus:border-[#6C2BD9] focus:ring-1 focus:ring-[#6C2BD9] focus:bg-white shadow-sm rounded-xl transition-all pr-16 w-full"
                />
                <button
                  type="button"
                  className="absolute right-3 top-[28px] text-xs font-bold text-[#667085] hover:text-[#111118] transition-colors h-12 px-2 flex items-center justify-center focus:outline-none"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <Button type="submit" className="w-full h-12 bg-[#6C2BD9] hover:bg-[#5b24b8] text-white text-[15px] font-semibold shadow-[0_4px_14px_0_rgba(108,43,217,0.39)] hover:shadow-[0_6px_20px_rgba(108,43,217,0.23)] rounded-xl transition-all" isLoading={loading}>
                Continue to Workspace
              </Button>
            </div>

            <div className="text-center mt-8 pt-6 border-t border-[#E5E5EA]/60">
              <span className="text-sm text-[#667085] font-medium">Don't have an account? </span>
              <Link to="/register" className="text-sm font-bold text-[#111118] hover:text-[#6C2BD9] transition-colors">
                Create an account
              </Link>
            </div>
          </form>
        </div>

        {/* Trust Signal Bottom */}
        <div className="hidden lg:block absolute bottom-8 left-0 right-0 text-center text-[10px] font-bold text-[#98A2B3] tracking-[0.2em] uppercase">
          GraahakLens &bull; AI-Commerce Platform
        </div>
      </div>
    </div>
  );
};
