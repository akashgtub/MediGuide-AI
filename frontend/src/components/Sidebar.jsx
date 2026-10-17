import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import {
  Activity,
  FileText,
  Upload,
  Calendar,
  Settings,
  LayoutDashboard,
  Users,
  Stethoscope,
  Sparkles,
  ClipboardList,
  CheckCircle2,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';

const Sidebar = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();

  const getLinks = () => {
    if (user?.role === 'patient') {
      return [
        { name: t('nav.dashboard', 'Dashboard'), path: '/patient', icon: <LayoutDashboard className="w-5 h-5" /> },
        { name: t('nav.uploadReport', 'Upload Report'), path: '/patient/upload', icon: <Upload className="w-5 h-5" /> },
        { name: t('nav.myReports', 'My Reports'), path: '/patient/reports', icon: <FileText className="w-5 h-5" /> },
        { name: t('nav.aiAssistant', 'AI Assistant'), path: '/patient/assistant', icon: <Activity className="w-5 h-5" />, badge: 'Live' },
        { name: t('nav.appointmentPrep', 'Appointment Prep'), path: '/patient/appointment', icon: <Calendar className="w-5 h-5" /> },
      ];
    }
    if (user?.role === 'doctor') {
      return [
        { name: 'Dashboard', path: '/doctor', icon: <LayoutDashboard className="w-5 h-5" /> },
        { name: 'Review Requests', path: '/doctor/reviews', icon: <ClipboardList className="w-5 h-5" />, badge: 'Active' },
        { name: 'Completed Reviews', path: '/doctor/completed', icon: <CheckCircle2 className="w-5 h-5" /> },
      ];
    }
    if (user?.role === 'admin') {
      return [
        { name: 'Dashboard', path: '/admin', icon: <LayoutDashboard className="w-5 h-5" /> },
        { name: 'Users', path: '/admin/users', icon: <Users className="w-5 h-5" /> },
        { name: 'Doctors', path: '/admin/doctors', icon: <Stethoscope className="w-5 h-5" /> },
        { name: 'System Monitoring', path: '/admin/monitoring', icon: <ShieldCheck className="w-5 h-5" /> },
      ];
    }
    return [];
  };

  const isActive = (path) => {
    if (path === '/patient' || path === '/doctor' || path === '/admin') {
      return location.pathname === path;
    }
    return location.pathname.startsWith(path);
  };

  return (
    <aside className="w-64 bg-white border-r border-[#E5EDF5] flex flex-col justify-between shrink-0 select-none shadow-xs">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-[#E5EDF5] flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-teal-500 text-white flex items-center justify-center shadow-md shadow-teal-500/20">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <span className="font-extrabold text-lg tracking-tight text-[#14213D] block leading-tight">
              MediGuide <span className="text-teal-600">AI</span>
            </span>
            <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
              Clinical Platform
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <div className="p-4">
          <p className="px-3 text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
            {user?.role === 'doctor' ? 'Clinical Navigation' : 'Patient Portal'}
          </p>
          <nav className="space-y-1">
            {getLinks().map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all duration-150 ${
                    active
                      ? 'bg-teal-50 text-teal-700 font-semibold shadow-xs'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className={active ? 'text-teal-600' : 'text-slate-400'}>{link.icon}</span>
                    <span>{link.name}</span>
                  </div>
                  {link.badge && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-100 text-teal-700">
                      {link.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Bottom Section: AI Assistant Widget & Settings */}
      <div className="p-4 border-t border-[#E5EDF5] space-y-3">
        {/* AI Health Assistant Teaser (Inspired by reference image 2) */}
        <div className="bg-gradient-to-br from-[#0B132B] to-[#14213D] text-white p-3.5 rounded-2xl shadow-sm border border-slate-700/40 relative overflow-hidden">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-bold text-white flex items-center">
              <Sparkles className="w-3.5 h-3.5 text-teal-400 mr-1.5" />
              AI Assistant
            </span>
            <span className="inline-flex items-center text-[9px] font-medium text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded-full border border-emerald-500/20">
              <span className="w-1 h-1 rounded-full bg-emerald-400 mr-1 animate-pulse"></span>
              Online
            </span>
          </div>
          <p className="text-[11px] text-slate-300 mb-2.5 leading-snug">
            {user?.role === 'doctor'
              ? 'Analyze recent patient test labs or clinical criteria.'
              : 'Ask medical questions or explain complex symptoms.'}
          </p>
          <Link
            to={user?.role === 'doctor' ? '/doctor/reviews' : '/patient/assistant'}
            className="w-full inline-flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold transition-all shadow-xs"
          >
            <span>{user?.role === 'doctor' ? 'Review Cases' : 'Chat with AI'}</span>
            <ChevronRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Settings Link */}
        <Link
          to="#"
          className="flex items-center space-x-3 px-3 py-2 rounded-xl text-slate-500 hover:bg-slate-50 hover:text-slate-800 transition-colors text-xs sm:text-sm font-medium"
        >
          <Settings className="w-4 h-4 text-slate-400" />
          <span>{user?.role === 'patient' ? t('nav.settings', 'Settings') : 'Settings'}</span>
        </Link>
      </div>
    </aside>
  );
};

export default Sidebar;
