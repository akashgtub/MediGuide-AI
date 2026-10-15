import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Activity, Mail, Lock, User, Stethoscope, ShieldCheck, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const Login = () => {
  const { login, quickLogin } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [role, setRole] = useState('patient');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Email cannot be empty.');
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
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Left side branding */}
      <div className="w-full md:w-1/2 bg-gradient-to-br from-teal-500 to-blue-600 text-white p-12 flex flex-col justify-center items-start">
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
          <div className="flex items-center space-x-3 mb-8">
            <div className="bg-white p-2 rounded-xl text-teal-600">
              <Activity className="w-8 h-8" />
            </div>
            <span className="font-bold text-3xl">MediGuide AI</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-6 leading-tight">Healthcare information, <br/>made clearer.</h1>
          <p className="text-teal-50 text-lg max-w-md leading-relaxed">
            Understand your medical information, prepare for appointments, and connect with professional review when needed.
          </p>
        </motion.div>
      </div>

      {/* Right side login */}
      <div className="w-full md:w-1/2 flex items-center justify-center p-8 bg-slate-50">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.2 }} className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
            <h2 className="text-2xl font-bold text-slate-800 mb-1">Welcome to MediGuide AI</h2>
            <p className="text-slate-500 mb-8">Sign in to continue</p>

            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-lg flex items-center mb-6 text-sm">
                <AlertCircle className="w-4 h-4 mr-2" />
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Mail className="w-5 h-5" />
                  </div>
                  <input 
                    type="email" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com" 
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-all" 
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-5 h-5" />
                  </div>
                  <input 
                    type="password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••" 
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none transition-all" 
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Role for this session</label>
                <select 
                  value={role} 
                  onChange={(e) => setRole(e.target.value)} 
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none bg-white"
                >
                  <option value="patient">Patient</option>
                  <option value="doctor">Doctor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <button type="submit" className="w-full bg-teal-600 text-white font-medium py-2.5 rounded-lg hover:bg-teal-700 transition-colors mt-2 shadow-md shadow-teal-500/20">
                Sign In
              </button>
            </form>

            <div className="mt-8 mb-6 flex items-center justify-center">
              <div className="border-t border-slate-200 w-full"></div>
              <span className="px-4 text-slate-400 text-sm font-medium bg-white">OR QUICK LOGIN</span>
              <div className="border-t border-slate-200 w-full"></div>
            </div>

            <div className="space-y-3">
              <button onClick={() => handleDemoLogin('patient')} className="w-full flex items-center justify-center space-x-2 border border-slate-200 bg-slate-50 text-slate-700 font-medium py-2.5 rounded-lg hover:bg-slate-100 hover:border-slate-300 transition-all">
                <User className="w-4 h-4 text-slate-500" />
                <span>Continue as Patient</span>
              </button>
              <button onClick={() => handleDemoLogin('doctor')} className="w-full flex items-center justify-center space-x-2 border border-slate-200 bg-slate-50 text-slate-700 font-medium py-2.5 rounded-lg hover:bg-slate-100 hover:border-slate-300 transition-all">
                <Stethoscope className="w-4 h-4 text-teal-600" />
                <span>Continue as Doctor</span>
              </button>
              <button onClick={() => handleDemoLogin('admin')} className="w-full flex items-center justify-center space-x-2 border border-slate-200 bg-slate-50 text-slate-700 font-medium py-2.5 rounded-lg hover:bg-slate-100 hover:border-slate-300 transition-all">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                <span>Continue as Admin</span>
              </button>
            </div>

            <p className="text-center text-xs text-slate-400 mt-6">
              Demo authentication — no real account required.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Login;
