import { useParams } from 'react-router-dom';
import { ShieldAlert, CheckCircle, ArrowRight } from 'lucide-react';

const ReportAnalysis = () => {
  const { id } = useParams();

  return (
    <div className="flex flex-col h-full space-y-4">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-2xl font-bold text-slate-800">Report Analysis</h1>
        <div className="flex space-x-2">
          <span className="bg-amber-100 text-amber-800 px-3 py-1 rounded-full text-sm font-medium flex items-center">
            <ShieldAlert className="w-4 h-4 mr-1" />
            Additional professional review recommended
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        <div className="bg-slate-200 rounded-xl border border-slate-300 flex items-center justify-center min-h-[500px]">
          <p className="text-slate-500 font-medium">Original Document Preview Placeholder</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 overflow-y-auto">
          <h2 className="text-lg font-bold text-slate-800 mb-4">Information identified from the uploaded report</h2>
          
          <div className="space-y-6">
            <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
              <h3 className="font-bold text-slate-700 mb-2">Simple Summary</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                This is a summary of the provided document. Please note this is not a diagnosis or clinical recommendation. Reported symptoms include headache and nausea. Mentioned medications include ibuprofen. Tests mentioned include blood pressure and heart rate.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="border border-slate-100 rounded-lg p-3">
                <p className="text-xs font-semibold text-slate-500 uppercase">Symptoms</p>
                <p className="font-medium text-slate-800 mt-1">Headache, Nausea</p>
              </div>
              <div className="border border-slate-100 rounded-lg p-3">
                <p className="text-xs font-semibold text-slate-500 uppercase">Medications</p>
                <p className="font-medium text-slate-800 mt-1">Ibuprofen</p>
              </div>
              <div className="border border-slate-100 rounded-lg p-3">
                <p className="text-xs font-semibold text-slate-500 uppercase">Tests & Values</p>
                <p className="font-medium text-slate-800 mt-1">130/85 mmHg, 88 bpm</p>
              </div>
              <div className="border border-slate-100 rounded-lg p-3">
                <p className="text-xs font-semibold text-slate-500 uppercase">Dates</p>
                <p className="font-medium text-slate-800 mt-1">2023-10-12</p>
              </div>
            </div>

            <div>
              <h3 className="font-bold text-slate-700 mb-2 flex items-center"><CheckCircle className="w-4 h-4 text-teal-500 mr-2" /> Suggested Next Steps</h3>
              <ul className="text-sm text-slate-600 space-y-2 pl-6 list-disc">
                <li>Discuss the elevated blood pressure with your provider.</li>
                <li>Report the ongoing headaches.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ReportAnalysis;
