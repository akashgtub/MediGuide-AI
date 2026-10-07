import { UploadCloud } from 'lucide-react';

const UploadReport = () => {
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Upload Medical Report</h1>
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-10">
        <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 flex flex-col items-center justify-center text-center hover:bg-slate-50 transition-colors cursor-pointer">
          <UploadCloud className="w-12 h-12 text-teal-500 mb-4" />
          <h3 className="text-lg font-bold text-slate-800 mb-1">Click or drag file to this area</h3>
          <p className="text-slate-500 text-sm mb-6">Support for a single or bulk upload. Strictly prohibit from uploading company data or other band files.</p>
          <div className="bg-teal-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-teal-700">
            Select File
          </div>
          <p className="text-xs text-slate-400 mt-4">Supported formats: PDF, JPG, PNG (Max 10MB)</p>
        </div>
      </div>
    </div>
  );
};
export default UploadReport;
