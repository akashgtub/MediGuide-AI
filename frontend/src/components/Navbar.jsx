import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import LanguageSelector from './LanguageSelector';
import { Bell, Search, User, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Navbar = () => {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6">
      <div className="flex items-center text-slate-400 bg-slate-50 rounded-full px-3 py-1.5 w-64 border border-slate-100">
        <Search className="w-4 h-4 mr-2" />
        <input
          type="text"
          placeholder={t('common.search', 'Search...')}
          className="bg-transparent border-none outline-none text-sm text-slate-700 w-full"
        />
      </div>

      <div className="flex items-center space-x-3">
        {/* Language selector for patients */}
        {user?.role === 'patient' && (
          <LanguageSelector compact={true} />
        )}

        <button className="text-slate-400 hover:text-slate-600 relative p-1.5">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-amber-500 rounded-full"></span>
        </button>

        <div className="flex items-center space-x-2 border-l pl-3 border-slate-200">
          <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-sm">
            {user?.name?.charAt(0)}
          </div>
          <span className="text-sm font-medium text-slate-700 hidden md:block">{user?.name}</span>
          <button
            onClick={handleLogout}
            title={t('common.logout', 'Logout')}
            className="text-slate-400 hover:text-red-500 ml-1 p-1"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
