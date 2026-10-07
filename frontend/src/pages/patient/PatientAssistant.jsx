import { Shield, Send } from 'lucide-react';

const PatientAssistant = () => {
  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-slate-800">MediGuide Assistant</h1>
        <p className="text-slate-500 text-sm">Ask questions about your uploaded health information.</p>
      </div>

      <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-2 rounded-lg flex items-center space-x-2 mb-4 text-sm">
        <Shield className="w-4 h-4" />
        <span className="font-medium">MediGuide provides informational assistance and does not diagnose or prescribe.</span>
      </div>

      <div className="flex-1 bg-white rounded-t-xl shadow-sm border-x border-t border-slate-100 p-6 overflow-y-auto space-y-4">
        <div className="flex justify-start">
          <div className="bg-slate-100 text-slate-800 px-4 py-3 rounded-2xl rounded-tl-none max-w-[80%]">
            Hello Alex. I have reviewed your recent General Health Report. How can I help you understand it better today?
          </div>
        </div>
      </div>

      <div className="bg-white p-4 border border-slate-100 rounded-b-xl shadow-sm">
        <div className="flex space-x-2 mb-4 overflow-x-auto pb-2">
          {["What information is mentioned in my report?", "Help me prepare questions for my doctor.", "Explain this medical terminology."].map((prompt, i) => (
            <button key={i} className="whitespace-nowrap bg-teal-50 text-teal-700 border border-teal-100 px-4 py-1.5 rounded-full text-sm hover:bg-teal-100 transition-colors">
              {prompt}
            </button>
          ))}
        </div>
        <div className="flex items-center space-x-2">
          <input type="text" placeholder="Type your question..." className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-4 py-2 outline-none focus:border-teal-500" />
          <button className="bg-teal-600 text-white p-2.5 rounded-lg hover:bg-teal-700 transition-colors">
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};
export default PatientAssistant;
