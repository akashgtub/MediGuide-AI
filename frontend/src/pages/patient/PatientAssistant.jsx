import { useState, useRef, useEffect } from 'react';
import {
  Shield,
  Send,
  Loader2,
  AlertCircle,
  HelpCircle,
  Globe,
  Sparkles,
  Bot,
  User,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const PatientAssistant = () => {
  const { user } = useAuth();
  const messagesEndRef = useRef(null);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [targetLanguage, setTargetLanguage] = useState('en');

  const [messages, setMessages] = useState([
    {
      id: 'm-1',
      sender: 'assistant',
      text: `Hello ${user?.name || 'there'}! I'm your MediGuide AI Health Information Assistant. I can help explain medical terms in your reports, summarize lab tests, or help you formulate clear questions for your physician.`,
      guidance: ['Ask any question about your symptoms, lab measurements, or doctor appointments.'],
      disclaimer: 'This system provides educational health information and does not diagnose, prescribe, or provide clinical treatments.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMsg = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/process-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: query,
          target_language: targetLanguage,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned error ${res.status}`);
      }

      const data = await res.json();
      const assistantMsg = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: data.translated_summary || 'I have analyzed the provided medical context.',
        guidance: data.guidance || [],
        reviewRequest: data.review_request,
        disclaimer: data.disclaimer || 'This system does not diagnose or prescribe.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      // Deterministic client fallback response if backend is offline or network fails
      const isCritical = query.toLowerCase().includes('chest pain') || query.toLowerCase().includes('shortness of breath');
      const fallbackMsg = {
        id: `asst-${Date.now()}`,
        sender: 'assistant',
        text: isCritical
          ? 'Warning: Severe symptoms detected. Please contact emergency medical services or go to the nearest emergency department immediately.'
          : `I have noted: "${query}". You can discuss these specific observations with your physician at your next appointment.`,
        guidance: isCritical
          ? ['Seek immediate emergency medical attention.']
          : ['Bring your current medication list and notes to your next consultation.'],
        disclaimer: 'This system provides informational assistance only and does not replace medical judgment.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setLoading(false);
    }
  };

  const samplePrompts = [
    'What does a Blood Pressure reading of 130/85 mmHg mean?',
    'What questions should I ask my doctor about fatigue?',
    'Can I take Ibuprofen with other medications?',
    'Explain Hemoglobin 12.5 g/dL in simple terms.',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)] max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">MediGuide Patient Assistant</h1>
          <p className="text-slate-500 text-xs">
            Interactive clinical translation & doctor consultation preparation
          </p>
        </div>

        {/* Language selector */}
        <div className="flex items-center space-x-1.5 bg-white border border-slate-200 px-3 py-1.5 rounded-xl shadow-sm">
          <Globe className="w-3.5 h-3.5 text-teal-600" />
          <select
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
            className="text-xs bg-transparent text-slate-700 outline-none font-medium cursor-pointer"
          >
            <option value="en">English (US)</option>
            <option value="es">Español (Spanish)</option>
            <option value="fr">Français (French)</option>
            <option value="de">Deutsch (German)</option>
            <option value="hi">हिंदी (Hindi)</option>
          </select>
        </div>
      </div>

      {/* Safety Notice Banner */}
      <div className="bg-amber-50/90 border border-amber-200/80 text-amber-900 px-4 py-2.5 rounded-2xl flex items-center space-x-2.5 mb-3 text-xs shrink-0 shadow-sm">
        <Shield className="w-4 h-4 text-amber-600 shrink-0" />
        <span className="font-medium">
          MediGuide AI provides patient educational guidance only. Never delay emergency care or modify prescriptions without consulting your physician.
        </span>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-100 p-5 overflow-y-auto space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === 'user';

          return (
            <div key={m.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-2xl p-4 space-y-2 text-sm shadow-sm ${
                  isUser
                    ? 'bg-teal-600 text-white rounded-br-none'
                    : 'bg-slate-50 border border-slate-100 text-slate-800 rounded-tl-none'
                }`}
              >
                <div className="flex items-center justify-between space-x-2 text-[11px] opacity-75 mb-1">
                  <span className="font-semibold">{isUser ? 'You' : 'MediGuide Assistant'}</span>
                  <span>{m.timestamp}</span>
                </div>

                <p className="leading-relaxed whitespace-pre-wrap">{m.text}</p>

                {/* Guidance items */}
                {m.guidance && m.guidance.length > 0 && (
                  <div className={`mt-2 pt-2 border-t text-xs ${isUser ? 'border-teal-500/50' : 'border-slate-200'} space-y-1`}>
                    <p className="font-semibold flex items-center space-x-1">
                      <Sparkles className="w-3.5 h-3.5 mr-1" />
                      <span>Next Steps & Preparation:</span>
                    </p>
                    <ul className="list-disc list-inside space-y-0.5 opacity-90 pl-1">
                      {m.guidance.map((g, idx) => (
                        <li key={idx}>{g}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* High Risk Flag */}
                {m.reviewRequest && (
                  <div className="mt-2 p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start space-x-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold">High Risk Escalation Flagged:</span>
                      <p className="mt-0.5 text-rose-700">
                        {m.reviewRequest.escalation_reasons?.join(', ')}
                      </p>
                    </div>
                  </div>
                )}

                {/* Non-diagnostic disclaimer */}
                {m.disclaimer && (
                  <p className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-100">
                    {m.disclaimer}
                  </p>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-50 border border-slate-100 text-slate-600 px-4 py-3 rounded-2xl rounded-tl-none text-xs flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-teal-600" />
              <span>Analyzing clinical context and formulating verified guidance...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts & Input Box */}
      <div className="bg-white p-3.5 border-t border-slate-100 rounded-b-2xl shadow-sm space-y-3 mt-2 shrink-0">
        {/* Quick prompt chips */}
        <div className="flex space-x-2 overflow-x-auto pb-1 scrollbar-none">
          {samplePrompts.map((prompt, i) => (
            <button
              key={i}
              type="button"
              disabled={loading}
              onClick={() => handleSend(prompt)}
              className="whitespace-nowrap bg-teal-50 hover:bg-teal-100/80 text-teal-800 border border-teal-100/80 px-3.5 py-1.5 rounded-full text-xs font-medium transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            placeholder="Ask questions about symptoms, medications, or lab measurements..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-teal-600 hover:bg-teal-700 text-white p-2.5 rounded-xl transition-all shadow-sm hover:shadow-teal-600/20 disabled:opacity-40"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
};

export default PatientAssistant;
