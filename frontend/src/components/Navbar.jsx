import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import LanguageSelector from './LanguageSelector';
import { Bell, Search, LogOut, CheckCircle2, AlertTriangle, Shield, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Navbar = () => {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const notifications = [
    {
      id: 1,
      title: 'Lab Report Analysis Complete',
      desc: 'Complete Blood Count report was summarized into plain language.',
      time: '12m ago',
      type: 'success',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
    },
    {
      id: 2,
      title: user?.role === 'doctor' ? 'Urgent Review Requested' : 'Physician Sign-Off Update',
      desc: user?.role === 'doctor' ? 'Case #MG-1024 escalated due to reported chest discomfort.' : 'Dr. Sarah Wilson signed off on your latest cardiology questions.',
      time: '1h ago',
      type: 'alert',
      icon: <AlertTriangle className="w-4 h-4 text-amber-500" />,
    },
    {
      id: 3,
      title: 'AI Medical Knowledge Sync',
      desc: 'Knowledge base updated with latest MedlinePlus clinical standards.',
      time: '3h ago',
      type: 'info',
      icon: <Sparkles className="w-4 h-4 text-teal-500" />,
    },
  ];

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-[#E5EDF5] h-16 flex items-center justify-between px-4 sm:px-6 sticky top-0 z-30 transition-all">
      {/* Global Search */}
      <div className="flex items-center text-slate-400 bg-[#F6F9FC] rounded-xl px-3.5 py-2 w-56 sm:w-80 border border-[#E5EDF5] focus-within:border-teal-500 focus-within:bg-white focus-within:ring-2 focus-within:ring-teal-500/15 transition-all">
        <Search className="w-4 h-4 mr-2.5 text-slate-400 shrink-0" />
        <input
          type="text"
          placeholder={t('common.search', 'Search patients, records, tests...')}
          className="bg-transparent border-none outline-none text-xs sm:text-sm text-[#172033] w-full placeholder:text-slate-400"
        />
        <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-semibold text-slate-400 bg-white border border-slate-200 rounded shadow-xs">
          ⌘K
        </kbd>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-2 sm:space-x-3.5">
        {/* Language selector for patients & global */}
        <LanguageSelector compact={true} />

        {/* Notifications */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            aria-label="Notifications"
            className="text-slate-500 hover:text-teal-600 hover:bg-slate-50 relative p-2 rounded-xl transition-colors border border-transparent hover:border-slate-200"
          >
            <Bell className="w-4 h-4 sm:w-5 sm:h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-white animate-pulse"></span>
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-xl border border-[#E5EDF5] py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="px-4 py-2.5 border-b border-slate-100 flex items-center justify-between">
                <span className="font-bold text-sm text-[#172033]">Notifications</span>
                <span className="text-[11px] font-medium text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full">
                  3 New
                </span>
              </div>
              <div className="divide-y divide-slate-50 max-h-80 overflow-y-auto">
                {notifications.map((n) => (
                  <div key={n.id} className="p-3.5 hover:bg-slate-50 transition-colors flex items-start space-x-3">
                    <div className="mt-0.5 p-1.5 bg-slate-50 rounded-lg shrink-0 border border-slate-100">
                      {n.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-[#172033] truncate">{n.title}</p>
                      <p className="text-xs text-slate-500 line-clamp-2 mt-0.5">{n.desc}</p>
                      <span className="text-[10px] text-slate-400 mt-1 block">{n.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile & Role */}
        <div className="flex items-center space-x-2 pl-2 sm:pl-3 border-l border-slate-200">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-600 to-teal-400 text-white flex items-center justify-center font-bold text-xs sm:text-sm shadow-xs uppercase">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <div className="hidden md:flex flex-col text-left">
            <span className="text-xs font-bold text-[#172033] leading-tight truncate max-w-[120px]">
              {user?.name || 'User'}
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-teal-600">
              {user?.role === 'doctor' ? 'Clinician' : (user?.role === 'admin' ? 'Administrator' : 'Patient')}
            </span>
          </div>
          <button
            onClick={handleLogout}
            title={t('common.logout', 'Logout')}
            className="text-slate-400 hover:text-rose-600 hover:bg-rose-50 p-2 rounded-xl transition-colors ml-1"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
