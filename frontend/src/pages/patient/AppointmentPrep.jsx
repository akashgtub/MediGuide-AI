import { useState } from 'react';
import {
  CheckCircle,
  FileText,
  Info,
  Printer,
  Plus,
  Trash2,
  Calendar,
  HelpCircle,
  Clock,
  Sparkles,
} from 'lucide-react';

const defaultQuestions = [
  { id: '1', text: 'Are my blood pressure readings of 130/85 mmHg within an acceptable target range?', checked: false },
  { id: '2', text: 'Could my severe headaches and nausea be side effects of ibuprofen or related to blood pressure?', checked: false },
  { id: '3', text: 'What lifestyle adjustments or diagnostic follow-ups do you recommend for the reported fatigue?', checked: false },
];

const defaultDocs = [
  { id: 'd1', text: 'Recent Diagnostic Lab Report (PDF / hardcopy)', checked: true },
  { id: 'd2', text: 'Complete list of current prescription and OTC medications with dosages', checked: true },
  { id: 'd3', text: 'Government Photo ID and Health Insurance Card', checked: false },
];

const AppointmentPrep = () => {
  const [questions, setQuestions] = useState(defaultQuestions);
  const [docs, setDocs] = useState(defaultDocs);
  const [newQuestion, setNewQuestion] = useState('');
  const [symptomNotes, setSymptomNotes] = useState(
    'Headaches started 4 days ago, primarily in the mornings. Taking 400mg Ibuprofen with partial relief.'
  );

  const toggleQuestion = (id) => {
    setQuestions((prev) =>
      prev.map((q) => (q.id === id ? { ...q, checked: !q.checked } : q))
    );
  };

  const toggleDoc = (id) => {
    setDocs((prev) =>
      prev.map((d) => (d.id === id ? { ...d, checked: !d.checked } : d))
    );
  };

  const handleAddQuestion = (e) => {
    e.preventDefault();
    if (!newQuestion.trim()) return;

    setQuestions([
      ...questions,
      { id: String(Date.now()), text: newQuestion.trim(), checked: false },
    ]);
    setNewQuestion('');
  };

  const removeQuestion = (id) => {
    setQuestions((prev) => prev.filter((q) => q.id !== id));
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Appointment Preparation</h1>
          <p className="text-slate-500 text-sm mt-1">
            Personalized consultation checklist and clinical question builder for your next doctor visit
          </p>
        </div>
        <button
          onClick={handlePrint}
          className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-medium px-4 py-2.5 rounded-xl text-sm transition-all shadow-sm hover:shadow-teal-600/20 self-start"
        >
          <Printer className="w-4 h-4" />
          <span>Print / Export Summary</span>
        </button>
      </div>

      {/* Questions to Ask Doctor */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-teal-600" />
            <h2 className="text-lg font-bold text-slate-800">
              Questions for Your Healthcare Professional
            </h2>
          </div>
          <span className="text-xs text-slate-400">
            {questions.filter((q) => q.checked).length} of {questions.length} asked
          </span>
        </div>

        <ul className="space-y-2.5">
          {questions.map((q) => (
            <li
              key={q.id}
              className={`flex items-start justify-between p-3 rounded-xl border transition-colors ${
                q.checked
                  ? 'bg-teal-50/50 border-teal-200 text-slate-400 line-through'
                  : 'bg-slate-50/70 border-slate-100 text-slate-700'
              }`}
            >
              <label className="flex items-start space-x-3 cursor-pointer flex-1 mr-3">
                <input
                  type="checkbox"
                  checked={q.checked}
                  onChange={() => toggleQuestion(q.id)}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <span className="text-sm font-medium leading-relaxed">{q.text}</span>
              </label>

              <button
                onClick={() => removeQuestion(q.id)}
                className="text-slate-300 hover:text-rose-500 transition-colors p-1"
                title="Remove Question"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </li>
          ))}
        </ul>

        {/* Add custom question */}
        <form onSubmit={handleAddQuestion} className="flex items-center space-x-2 pt-2">
          <input
            type="text"
            placeholder="Add your own question to ask the doctor..."
            value={newQuestion}
            onChange={(e) => setNewQuestion(e.target.value)}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
          <button
            type="submit"
            disabled={!newQuestion.trim()}
            className="inline-flex items-center space-x-1.5 bg-slate-100 hover:bg-teal-50 text-slate-700 hover:text-teal-700 font-semibold px-4 py-2 rounded-xl text-sm transition-colors disabled:opacity-40"
          >
            <Plus className="w-4 h-4" />
            <span>Add</span>
          </button>
        </form>
      </div>

      {/* Documents & Symptom Notes Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Documents to bring */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-4">
          <h2 className="text-lg font-bold text-slate-800 flex items-center space-x-2 border-b border-slate-100 pb-3">
            <FileText className="w-5 h-5 text-blue-600" />
            <span>Documents to Bring</span>
          </h2>

          <ul className="space-y-2.5">
            {docs.map((d) => (
              <li
                key={d.id}
                className="flex items-center space-x-3 p-3 bg-slate-50/70 border border-slate-100 rounded-xl"
              >
                <input
                  type="checkbox"
                  checked={d.checked}
                  onChange={() => toggleDoc(d.id)}
                  className="h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <span className={`text-sm ${d.checked ? 'text-slate-800 font-medium' : 'text-slate-500'}`}>
                  {d.text}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* Symptoms Timeline & Observations */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-4">
          <h2 className="text-lg font-bold text-slate-800 flex items-center space-x-2 border-b border-slate-100 pb-3">
            <Info className="w-5 h-5 text-amber-500" />
            <span>Symptom Timeline to Mention</span>
          </h2>

          <p className="text-xs text-slate-400">
            Jot down onset date, frequency, severity scale (1-10), and triggers:
          </p>

          <textarea
            rows={4}
            value={symptomNotes}
            onChange={(e) => setSymptomNotes(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>
      </div>
    </div>
  );
};

export default AppointmentPrep;
