import { useAuth } from '../../context/AuthContext';
import { mockStats } from '../../data/mockData';
import StatCard from '../../components/StatCard';
import { Users, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';

const DoctorDashboard = () => {
  const { user } = useAuth();
  const stats = mockStats.doctor;

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800">Good morning, {user?.name}</h1>
        <p className="text-slate-500 mt-1">You have {stats.pending} reviews pending today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Pending Reviews" value={stats.pending} icon={<Clock />} color="blue" />
        <StatCard title="High Priority" value={stats.highPriority} icon={<AlertTriangle />} color="red" />
        <StatCard title="Reviewed Today" value={stats.reviewedToday} icon={<CheckCircle />} color="teal" />
        <StatCard title="Completed Cases" value={stats.completed} icon={<Users />} color="indigo" />
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-bold text-slate-800 mb-4">Priority Review Queue</h2>
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <div>
              <h3 className="font-bold text-slate-800">Case #MG-1024</h3>
              <p className="text-sm text-slate-500">Submitted 2 hours ago • Patient anonymized</p>
            </div>
            <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">High Priority</span>
          </div>
          <div className="p-6">
            <p className="font-medium text-slate-800 mb-2">Reason for review:</p>
            <p className="text-slate-600 mb-6 bg-red-50 p-3 rounded-lg border border-red-100">Additional professional review recommended due to reported severe chest pain and shortness of breath.</p>
            <Link to="/doctor/reviews/MG-1024" className="bg-teal-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-teal-700 transition-colors inline-block">
              Review Case
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
export default DoctorDashboard;
