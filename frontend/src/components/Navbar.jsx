import { useAuth } from '../context/AuthContext';
import { Bell, Search, User, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-white border-b border-slate-200 h-16 flex items-center justify-between px-6">
      <div className="flex items-center text-slate-400 bg-slate-50 rounded-full px-3 py-1.5 w-64 border border-slate-100">
        <Search className="w-4 h-4 mr-2" />
        <input type="text" placeholder="Search..." className="bg-transparent border-none outline-none text-sm text-slate-700 w-full" />
      </div>
      
      <div className="flex items-center space-x-4">
        <button className="text-slate-400 hover:text-slate-600 relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-0 right-0 w-2 h-2 bg-amber-500 rounded-full"></span>
        </button>
        <div className="flex items-center space-x-2 border-l pl-4 border-slate-200">
          <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center font-bold">
            {user?.name?.charAt(0)}
          </div>
          <span className="text-sm font-medium text-slate-700 hidden md:block">{user?.name}</span>
          <button onClick={handleLogout} className="text-slate-400 hover:text-red-500 ml-2">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
