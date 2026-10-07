import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, FileText, Upload, Calendar, Settings, Home, Users, Stethoscope } from 'lucide-react';

const Sidebar = () => {
  const { user } = useAuth();
  
  const getLinks = () => {
    if (user?.role === 'patient') {
      return [
        { name: 'Dashboard', path: '/patient', icon: <Home className="w-5 h-5" /> },
        { name: 'Upload Report', path: '/patient/upload', icon: <Upload className="w-5 h-5" /> },
        { name: 'My Reports', path: '/patient/reports', icon: <FileText className="w-5 h-5" /> },
        { name: 'AI Assistant', path: '/patient/assistant', icon: <Activity className="w-5 h-5" /> },
        { name: 'Appointment Prep', path: '/patient/appointment', icon: <Calendar className="w-5 h-5" /> }
      ];
    }
    if (user?.role === 'doctor') {
      return [
        { name: 'Dashboard', path: '/doctor', icon: <Home className="w-5 h-5" /> },
        { name: 'Review Requests', path: '/doctor/reviews', icon: <FileText className="w-5 h-5" /> },
        { name: 'Completed Reviews', path: '/doctor/completed', icon: <Activity className="w-5 h-5" /> }
      ];
    }
    if (user?.role === 'admin') {
      return [
        { name: 'Dashboard', path: '/admin', icon: <Home className="w-5 h-5" /> },
        { name: 'Users', path: '/admin/users', icon: <Users className="w-5 h-5" /> },
        { name: 'Doctors', path: '/admin/doctors', icon: <Stethoscope className="w-5 h-5" /> },
        { name: 'System Monitoring', path: '/admin/monitoring', icon: <Activity className="w-5 h-5" /> }
      ];
    }
    return [];
  };

  return (
    <div className="w-64 bg-white border-r border-slate-200 shadow-sm flex flex-col">
      <div className="p-4 border-b border-slate-100 flex items-center space-x-2">
        <Activity className="text-teal-600 w-6 h-6" />
        <span className="font-bold text-xl text-slate-800">MediGuide AI</span>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {getLinks().map(link => (
          <Link key={link.name} to={link.path} className="flex items-center space-x-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-50 hover:text-teal-600 transition-colors">
            {link.icon}
            <span className="font-medium">{link.name}</span>
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-100">
        <Link to="#" className="flex items-center space-x-3 px-3 py-2 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors">
          <Settings className="w-5 h-5" />
          <span className="font-medium">Settings</span>
        </Link>
      </div>
    </div>
  );
};

export default Sidebar;
