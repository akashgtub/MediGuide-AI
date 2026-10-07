import { mockReports } from '../../data/mockData';
import { FileText } from 'lucide-react';

const MyReports = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">My Reports</h1>
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              <th className="p-4 text-sm font-semibold text-slate-600">Report Type</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Date</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Status</th>
              <th className="p-4 text-sm font-semibold text-slate-600">Risk Assessment</th>
            </tr>
          </thead>
          <tbody>
            {mockReports.map(report => (
              <tr key={report.id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="p-4 flex items-center space-x-3">
                  <FileText className="text-teal-500 w-5 h-5" />
                  <span className="font-medium text-slate-800">{report.type}</span>
                </td>
                <td className="p-4 text-slate-600">{report.date}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${report.status === 'Analyzed' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                    {report.status}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${report.risk === 'Low' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {report.risk}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
export default MyReports;
