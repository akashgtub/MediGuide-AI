import { useParams, Link } from 'react-router-dom';
import { ShieldAlert, CheckCircle } from 'lucide-react';

const ReviewCase = () => {
  const { id } = useParams();

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Review Case #{id}</h1>
          <p className="text-slate-500">Patient anonymized • Submitted 2 hours ago</p>
        </div>
        <Link to="/doctor" className="text-teal-600 font-medium hover:underline">Back to Dashboard</Link>
      </div>

      <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg flex items-start space-x-3">
        <ShieldAlert className="w-6 h-6 shrink-0 mt-0.5" />
        <div>
          <h3 className="font-bold">Reason for Escalation</h3>
          <p className="text-sm mt-1">The AI engine flagged this case because the patient reported "severe chest pain" and "shortness of breath", which are high-risk indicators.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h2 className="font-bold text-slate-800 border-b pb-2 mb-4">Extracted Information</h2>
          <div className="space-y-3 text-sm">
            <p><span className="font-semibold text-slate-600 w-32 inline-block">Symptoms:</span> Chest pain, shortness of breath</p>
            <p><span className="font-semibold text-slate-600 w-32 inline-block">Medications:</span> Aspirin</p>
            <p><span className="font-semibold text-slate-600 w-32 inline-block">Dates:</span> 2023-10-12</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h2 className="font-bold text-slate-800 border-b pb-2 mb-4">AI Summary</h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            Patient reports severe chest pain and shortness of breath. Patient is taking Aspirin. 
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 border-t-4 border-t-teal-500">
        <h2 className="text-lg font-bold text-slate-800 mb-1">Clinical Review Panel</h2>
        <p className="text-sm text-slate-500 mb-6 italic">The healthcare professional makes the final clinical decision.</p>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Review Notes</label>
            <textarea rows="4" className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none" placeholder="Enter clinical notes..."></textarea>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Decision / Status</label>
            <select className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-teal-500 outline-none">
              <option>Recommend immediate ER visit</option>
              <option>Schedule urgent telehealth consult</option>
              <option>Routine follow-up</option>
              <option>Information safe, no action needed</option>
            </select>
          </div>
          <button className="bg-teal-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-teal-700 transition-colors flex items-center">
            <CheckCircle className="w-5 h-5 mr-2" /> Submit Review
          </button>
        </div>
      </div>
    </div>
  );
};
export default ReviewCase;
