import { mockStats } from '../../data/mockData';
import StatCard from '../../components/StatCard';
import { Users, Stethoscope, FileText, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Mon', reports: 120 },
  { name: 'Tue', reports: 150 },
  { name: 'Wed', reports: 180 },
  { name: 'Thu', reports: 140 },
  { name: 'Fri', reports: 200 },
  { name: 'Sat', reports: 90 },
  { name: 'Sun', reports: 70 },
];

const AdminDashboard = () => {
  const stats = mockStats.admin;

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800">System Administrator Dashboard</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Total Users" value={stats.users} icon={<Users />} color="blue" />
        <StatCard title="Registered Doctors" value={stats.doctors} icon={<Stethoscope />} color="teal" />
        <StatCard title="Reports Processed" value={stats.reports} icon={<FileText />} color="indigo" />
        <StatCard title="Pending Reviews" value={stats.pending} icon={<Activity />} color="amber" />
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mt-8">
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-6">Processing Volume</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b'}} />
                <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                <Bar dataKey="reports" fill="#0d9488" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4">System Status</h2>
          <div className="space-y-4">
            {['AI Processing Engine', 'Document Parsing Service', 'Human Review Queue', 'Authentication System'].map((sys, i) => (
              <div key={i} className="flex justify-between items-center p-3 border border-slate-100 rounded-lg">
                <span className="font-medium text-slate-700">{sys}</span>
                <span className="flex items-center text-sm font-bold text-green-600 bg-green-50 px-3 py-1 rounded-full">
                  <div className="w-2 h-2 rounded-full bg-green-500 mr-2"></div> Operational
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
export default AdminDashboard;
