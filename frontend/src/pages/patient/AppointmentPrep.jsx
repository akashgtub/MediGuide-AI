import { CheckCircle, FileText, Info } from 'lucide-react';

const AppointmentPrep = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Appointment Preparation</h1>
      
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
        <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center">
          <CheckCircle className="w-5 h-5 text-teal-500 mr-2" />
          Questions to ask your healthcare professional
        </h2>
        <ul className="space-y-3 text-slate-600">
          <li className="flex items-start"><span className="mr-2 text-teal-500">•</span> Are my blood pressure readings of 130/85 mmHg a concern?</li>
          <li className="flex items-start"><span className="mr-2 text-teal-500">•</span> Could my severe headaches and nausea be side effects of ibuprofen or related to blood pressure?</li>
          <li className="flex items-start"><span className="mr-2 text-teal-500">•</span> What can I do to address the fatigue noted in my report?</li>
        </ul>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center">
            <FileText className="w-5 h-5 text-blue-500 mr-2" />
            Documents to bring
          </h2>
          <ul className="space-y-3 text-slate-600">
            <li className="flex items-start"><span className="mr-2 text-blue-500">•</span> General Health Report (Oct 12)</li>
            <li className="flex items-start"><span className="mr-2 text-blue-500">•</span> List of current medications</li>
          </ul>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center">
            <Info className="w-5 h-5 text-amber-500 mr-2" />
            Information to mention
          </h2>
          <ul className="space-y-3 text-slate-600">
            <li className="flex items-start"><span className="mr-2 text-amber-500">•</span> Frequency and duration of headaches.</li>
            <li className="flex items-start"><span className="mr-2 text-amber-500">•</span> Exact dosage of ibuprofen you are taking.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
export default AppointmentPrep;
