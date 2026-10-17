import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import {
  Activity,
  Mail,
  Lock,
  Eye,
  EyeOff,
  User,
  Stethoscope,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  Shield,
  Heart,
  Loader2,
} from 'lucide-react';
import { motion } from 'framer-motion';

const Login = () => {
  const { login, quickLogin } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [role, setRole] = useState('patient');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Email address cannot be empty.');
      return;
    }
    if (!password.trim()) {
      setError('Password cannot be empty.');
      return;
    }

    setError('');
    setIsLoading(true);
    try {
      const authUser = await login(email, password);
      navigate(`/${authUser.role || role}`);
    } catch (err) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (selectedRole) => {
    setError('');
    setIsLoading(true);
    setRole(selectedRole);
    try {
      const authUser = await quickLogin(selectedRole);
      navigate(`/${authUser.role || selectedRole}`);
    } catch (err) {
      setError(err.message || 'Quick login failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F6F9FC] flex flex-col md:flex-row text-[#172033]">
      {/* Left Column: Teal-to-Blue Gradient Branding */}
      <div className="w-full md:w-1/2 bg-gradient-to-br from-[#0D9488] via-[#0F766E] to-[#2563EB] text-white p-8 sm:p-12 lg:p-16 flex flex-col justify-between relative overflow-hidden select-none">
        {/* Subtle decorative mesh / background shapes */}
        <div className="absolute top-[-15%] left-[-15%] w-96 h-96 bg-white/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-80 h-80 bg-teal-300/10 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center space-x-3 group">
            <div className="w-11 h-11 rounded-2xl bg-white text-teal-600 flex items-center justify-center font-bold shadow-lg shadow-teal-900/20 transition-transform group-hover:scale-105">
              <Activity className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <span className="font-extrabold text-2xl tracking-tight text-white block leading-tight">
                MediGuide <span className="text-teal-200">AI</span>
              </span>
              <span className="text-[10px] tracking-widest text-teal-100 uppercase font-semibold">
                Clinical Health Intelligence
              </span>
            </div>
          </Link>
        </div>

        {/* Central Graphic & Value Prop */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10 my-10 lg:my-14 space-y-6"
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md text-teal-100 text-xs font-semibold border border-white/20">
            <Sparkles className="w-3.5 h-3.5 text-teal-300" />
            <span>Trusted Healthcare AI Platform</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black leading-tight tracking-tight text-white">
            Healthcare information, <br />
            <span className="text-teal-200 underline decoration-teal-300/40 underline-offset-8">
              made clearer.
            </span>
          </h1>

          <p className="text-teal-50 text-sm sm:text-base max-w-lg leading-relaxed font-normal">
            Understand complex laboratory reports, get plain-language biomarker explanations in your native language, and connect with clinical experts for physician sign-off.
          </p>

          {/* Interactive Telemetry Card Preview inside Left Branding */}
          <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-4 max-w-md shadow-xl text-white space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-teal-400/20 flex items-center justify-center text-teal-200">
                  <Heart className="w-4 h-4 fill-teal-200" />
                </div>
                <div>
                  <p className="text-xs font-bold">Biomarker Health Vitals</p>
                  <p className="text-[10px] text-teal-100">Live Clinical Reference Ranges</p>
                </div>
              </div>
              <span className="text-[10px] font-bold bg-emerald-400/20 text-emerald-200 px-2 py-0.5 rounded-full border border-emerald-300/30">
                100% Safe Bounds
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center pt-1 text-xs">
              <div className="bg-white/10 rounded-xl p-2">
                <span className="text-[10px] text-teal-100 block">Resting HR</span>
                <span className="font-bold text-white">72 bpm</span>
              </div>
              <div className="bg-white/10 rounded-xl p-2">
                <span className="text-[10px] text-teal-100 block">BP Index</span>
                <span className="font-bold text-white">120/80</span>
              </div>
              <div className="bg-white/10 rounded-xl p-2">
                <span className="text-[10px] text-teal-100 block">Oxygen SpO2</span>
                <span className="font-bold text-white">98%</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Security Badges at Bottom */}
        <div className="relative z-10 flex flex-wrap items-center gap-4 text-xs text-teal-100 pt-6 border-t border-white/20">
          <span className="flex items-center space-x-1.5">
            <Shield className="w-4 h-4 text-teal-200" />
            <span>HIPAA Compliant</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <Lock className="w-4 h-4 text-teal-200" />
            <span>AES-256 Encryption</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <CheckCircle2 className="w-4 h-4 text-teal-200" />
            <span>Clinician Triage Safe</span>
          </span>
        </div>
      </div>

      {/* Right Column: Centered White Authentication Card */}
      <div className="w-full md:w-1/2 flex items-center justify-center p-6 sm:p-10 lg:p-14 bg-[#F6F9FC]">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="w-full max-w-md"
        >
          <div className="bg-white rounded-3xl shadow-xl shadow-slate-200/50 border border-[#E5EDF5] p-7 sm:p-9">
            {/* Header */}
            <div className="mb-6">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#172033] tracking-tight">
                Welcome back
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">
                Sign in to access your MediGuide AI portal
              </p>
            </div>

            {/* Error Message Banner */}
            {error && (
              <div className="bg-rose-50 border border-rose-200 text-rose-700 p-3.5 rounded-xl flex items-start space-x-2.5 mb-5 text-xs font-medium animate-in fade-in">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span className="flex-1">{error}</span>
              </div>
            )}

            {/* Role Selector Tabs */}
            <div className="mb-5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Select Portal Role
              </label>
              <div className="grid grid-cols-3 gap-2 bg-slate-50 p-1 rounded-2xl border border-slate-200">
                <button
                  type="button"
                  onClick={() => setRole('patient')}
                  className={`flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl text-xs font-bold transition-all ${
                    role === 'patient'
                      ? 'bg-white text-teal-700 shadow-sm border border-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <User className="w-3.5 h-3.5 text-teal-600" />
                  <span>Patient</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRole('doctor')}
                  className={`flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl text-xs font-bold transition-all ${
                    role === 'doctor'
                      ? 'bg-white text-teal-700 shadow-sm border border-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
                  <span>Doctor</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRole('admin')}
                  className={`flex items-center justify-center space-x-1.5 py-2 px-3 rounded-xl text-xs font-bold transition-all ${
                    role === 'admin'
                      ? 'bg-white text-teal-700 shadow-sm border border-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                  <span>Admin</span>
                </button>
              </div>
            </div>

            {/* Login Form */}
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50/70 border border-slate-200 rounded-xl text-xs sm:text-sm text-[#172033] focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all placeholder:text-slate-400"
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
                    Password
                  </label>
                  <span className="text-[11px] text-teal-600 hover:text-teal-700 font-semibold cursor-pointer">
                    Forgot password?
                  </span>
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-10 pr-11 py-2.5 bg-slate-50/70 border border-slate-200 rounded-xl text-xs sm:text-sm text-[#172033] focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-all placeholder:text-slate-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full inline-flex items-center justify-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 rounded-xl transition-all shadow-md shadow-teal-600/25 disabled:opacity-70 mt-2 text-sm"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Quick Demo Access Divider */}
            <div className="my-6 flex items-center justify-center">
              <div className="border-t border-[#E5EDF5] w-full" />
              <span className="px-3 text-slate-400 text-[11px] font-bold uppercase tracking-wider bg-white whitespace-nowrap">
                Or Quick 1-Click Demo
              </span>
              <div className="border-t border-[#E5EDF5] w-full" />
            </div>

            {/* Quick Demo Login Pills */}
            <div className="space-y-2.5">
              <button
                type="button"
                onClick={() => handleDemoLogin('patient')}
                disabled={isLoading}
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-teal-50 hover:border-teal-300 text-slate-700 hover:text-teal-900 transition-all text-xs font-semibold group"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="w-7 h-7 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center">
                    <User className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <span className="block font-bold">Alex Morgan</span>
                    <span className="text-[10px] text-slate-400">alex@example.com</span>
                  </div>
                </div>
                <span className="text-[11px] font-bold text-teal-700 bg-teal-100/70 px-2 py-0.5 rounded-md">
                  Patient Portal &rarr;
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoLogin('doctor')}
                disabled={isLoading}
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-teal-50 hover:border-teal-300 text-slate-700 hover:text-teal-900 transition-all text-xs font-semibold group"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center">
                    <Stethoscope className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <span className="block font-bold">Dr. Sarah Wilson</span>
                    <span className="text-[10px] text-slate-400">sarah@example.com</span>
                  </div>
                </div>
                <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded-md">
                  Doctor Queue &rarr;
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleDemoLogin('admin')}
                disabled={isLoading}
                className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-blue-50 hover:border-blue-300 text-slate-700 hover:text-blue-900 transition-all text-xs font-semibold group"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="w-7 h-7 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <span className="block font-bold">System Admin</span>
                    <span className="text-[10px] text-slate-400">admin@example.com</span>
                  </div>
                </div>
                <span className="text-[11px] font-bold text-blue-700 bg-blue-100/70 px-2 py-0.5 rounded-md">
                  Admin System &rarr;
                </span>
              </button>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-100 text-center">
              <Link to="/" className="text-xs text-slate-500 hover:text-teal-600 font-medium">
                &larr; Back to public homepage
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Login;
