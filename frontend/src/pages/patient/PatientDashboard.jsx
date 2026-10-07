import { useAuth } from '../../context/AuthContext';
import { mockStats, mockReports } from '../../data/mockData';
import StatCard from '../../components/StatCard';
import { FileText, CheckCircle, Clock, Calendar, Upload } from 'lucide-react';
import { Link } from 'react-router-dom';

const PatientDashboard = () => {
  const { user } = useAuth();
  const stats = mockStats.patient;

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800">Good morning, {user?.name.split(' ')[0]}</h1>
        <p className="text-slate-500 mt-1">Here's an overview of your MediGuide journey.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Reports Uploaded" value={stats.uploaded} icon={<FileText />} color="blue" />
        <StatCard title="Reports Analyzed" value={stats.analyzed} icon={<CheckCircle />} color="teal" />
        <StatCard title="Reviews Pending" value={stats.pending} icon={<Clock />} color="amber" />
        <StatCard title="Appointments Prepared" value={stats.prep} icon={<Calendar />} color="indigo" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Recent Reports</h2>
            <div className="space-y-4">
              {mockReports.map(report => (
                <div key={report.id} className="flex items-center justify-between p-4 border border-slate-100 rounded-lg hover:bg-slate-50">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-teal-50 text-teal-600 rounded-lg">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-800">{report.type}</p>
                      <p className="text-sm text-slate-500">{report.date}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${report.status === 'Analyzed' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                      {report.status}
                    </span>
                    <Link to={`/patient/reports/${report.id}`} className="text-teal-600 hover:text-teal-800 font-medium text-sm">View</Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-gradient-to-br from-teal-500 to-teal-700 rounded-xl shadow-md p-6 text-white">
            <div className="flex justify-between items-start mb-4">
              <Upload className="w-8 h-8 text-teal-100" />
            </div>
            <h2 className="text-xl font-bold mb-2">Upload Medical Report</h2>
            <p className="text-teal-100 text-sm mb-6">Upload your latest medical documents for AI-assisted simplification.</p>
            <Link to="/patient/upload" className="block w-full text-center bg-white text-teal-700 font-medium py-2 rounded-lg hover:bg-slate-50 transition-colors">
              Upload Now
            </Link>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
            <h2 className="text-lg font-bold text-slate-800 mb-2">AI Insight</h2>
            <p className="text-sm text-slate-500 mb-4">Your latest report has been processed.</p>
            <ul className="space-y-2 text-sm text-slate-700">
              <li className="flex items-center space-x-2"><CheckCircle className="w-4 h-4 text-green-500" /> <span>Information extracted</span></li>
              <li className="flex items-center space-x-2"><CheckCircle className="w-4 h-4 text-green-500" /> <span>Summary available</span></li>
              <li className="flex items-center space-x-2"><CheckCircle className="w-4 h-4 text-green-500" /> <span>Translation available</span></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
export default PatientDashboard;
