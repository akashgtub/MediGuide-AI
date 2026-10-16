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
  FileText,
  Activity,
  ExternalLink,
} from 'lucide-react';
import { useAuth, apiFetch } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { SUPPORTED_LANGUAGES } from '../../i18n/translations';

const PatientAssistant = () => {
  const { user } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const messagesEndRef = useRef(null);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [targetLanguage, setTargetLanguage] = useState(language || 'en');

  const [messages, setMessages] = useState([
    {
      id: 'm-1',
      sender: 'assistant',
      text: t('assistant.welcome'),
      guidance: [t('assistant.initialGuidance')],
      disclaimer: t('assistant.initialDisclaimer'),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  // Keep targetLanguage synchronized with LanguageContext
  useEffect(() => {
    if (language) {
      setTargetLanguage(language);
    }
  }, [language]);

  // Refresh default welcome message if only greeting is present when language switches
  useEffect(() => {
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].id === 'm-1') {
        return [
          {
            id: 'm-1',
            sender: 'assistant',
            text: t('assistant.welcome'),
            guidance: [t('assistant.initialGuidance')],
            disclaimer: t('assistant.initialDisclaimer'),
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          },
        ];
      }
      return prev;
    });
  }, [language, t]);

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
      // Gather recent message history for multi-turn context
      const historyPayload = messages.slice(-6).map((m) => ({
        sender: m.sender,
        text: m.text,
      }));

      const queryParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
      const activeReportId = queryParams ? (queryParams.get('reportId') || queryParams.get('report_id')) : null;

      const res = await apiFetch('/api/process-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: query,
          target_language: targetLanguage,
          report_id: activeReportId || undefined,
          conversation_history: historyPayload,
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
        disclaimer: data.disclaimer || '',
        reportList: data.report_list || null,
        metricData: data.metric_data || null,
        intent: data.intent || null,
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
    t('assistant.prompt0'),
    t('assistant.prompt1'),
    t('assistant.prompt2'),
    t('assistant.prompt3'),
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-7.5rem)] max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">{t('assistant.title')}</h1>
          <p className="text-slate-500 text-xs">
            {t('assistant.subtitle')}
          </p>
        </div>

        {/* Language selector */}
        <div className="flex items-center space-x-1.5 bg-white border border-slate-200 px-3 py-1.5 rounded-xl shadow-sm">
          <Globe className="w-3.5 h-3.5 text-teal-600" />
          <select
            value={targetLanguage}
            onChange={(e) => {
              setTargetLanguage(e.target.value);
              setLanguage(e.target.value);
            }}
            className="text-xs bg-transparent text-slate-700 outline-none font-semibold cursor-pointer"
          >
            {SUPPORTED_LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.nativeName} ({l.name})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Safety Notice Banner */}
      <div className="bg-amber-50/90 border border-amber-200/80 text-amber-900 px-4 py-2.5 rounded-2xl flex items-center space-x-2.5 mb-3 text-xs shrink-0 shadow-sm">
        <Shield className="w-4 h-4 text-amber-600 shrink-0" />
        <span className="font-medium">
          {t('assistant.banner')}
        </span>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-100 p-5 overflow-y-auto space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === 'user';

          return (
            <div key={m.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-2xl p-4 space-y-2.5 text-sm shadow-sm ${
                  isUser
                    ? 'bg-teal-600 text-white rounded-br-none'
                    : 'bg-slate-50 border border-slate-200/80 text-slate-800 rounded-tl-none'
                }`}
              >
                <div className="flex items-center justify-between space-x-2 text-[11px] opacity-75 mb-1">
                  <span className="font-semibold">{isUser ? 'You' : 'MediGuide Assistant'}</span>
                  <span className="font-mono">{m.timestamp}</span>
                </div>

                <p className="leading-relaxed whitespace-pre-wrap">{m.text}</p>

                {/* Metric Highlight Card */}
                {m.metricData && (
                  <div className="mt-2.5 p-3 bg-white border border-teal-200 rounded-xl space-y-1 shadow-2xs">
                    <div className="flex items-center justify-between text-teal-900 font-semibold text-xs">
                      <span className="flex items-center">
                        <Activity className="w-3.5 h-3.5 text-teal-600 mr-1.5" />
                        {m.metricData.metric}
                      </span>
                      {m.metricData.date && (
                        <span className="text-[10px] text-slate-400 font-mono">{m.metricData.date}</span>
                      )}
                    </div>
                    <div className="flex items-baseline space-x-1.5 py-0.5">
                      <span className="text-xl font-bold font-mono text-slate-900">
                        {m.metricData.value}
                      </span>
                      <span className="text-xs text-slate-500 font-mono font-medium">
                        {m.metricData.unit}
                      </span>
                    </div>
                    {m.metricData.filename && (
                      <p className="text-[10px] text-slate-400 truncate">
                        Source: {m.metricData.filename}
                      </p>
                    )}
                  </div>
                )}

                {/* Compact Interactive Report List */}
                {m.reportList && m.reportList.length > 0 && (
                  <div className="mt-2.5 pt-2 border-t border-slate-200/80 space-y-2">
                    <p className="text-[11px] font-bold text-slate-600 uppercase tracking-wider flex items-center">
                      <FileText className="w-3.5 h-3.5 text-teal-600 mr-1" />
                      Uploaded Reports ({m.reportList.length})
                    </p>
                    <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                      {m.reportList.map((r, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between bg-white border border-slate-200 hover:border-teal-400 p-2 rounded-xl transition-all shadow-2xs text-xs"
                        >
                          <div className="truncate pr-2">
                            <p className="font-semibold text-slate-800 truncate">{r.filename}</p>
                            <p className="text-[10px] text-slate-400">{r.created_at || 'Recent'}</p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleSend(`Summarize my ${r.filename}`)}
                            className="bg-teal-50 hover:bg-teal-600 text-teal-700 hover:text-white px-2.5 py-1 rounded-lg text-[11px] font-medium transition-colors shrink-0"
                          >
                            Summarize
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Guidance items (only when non-empty) */}
                {m.guidance && m.guidance.length > 0 && (
                  <div className={`mt-2 pt-2 border-t text-xs ${isUser ? 'border-teal-500/50' : 'border-slate-200'} space-y-1`}>
                    <p className="font-semibold flex items-center space-x-1">
                      <Sparkles className="w-3.5 h-3.5 mr-1" />
                      <span>{t('assistant.nextSteps')}</span>
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
                      <span className="font-bold">{t('assistant.highRiskFlag')}</span>
                      <p className="mt-0.5 text-rose-700">
                        {m.reviewRequest.escalation_reasons?.join(', ')}
                      </p>
                    </div>
                  </div>
                )}

                {/* Non-diagnostic disclaimer (only when non-empty) */}
                {m.disclaimer && m.disclaimer.trim().length > 0 && (
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
              <span>{t('assistant.thinking')}</span>
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
            placeholder={t('assistant.placeholder')}
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
