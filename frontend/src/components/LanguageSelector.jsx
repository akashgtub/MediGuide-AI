import { Globe } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

const LanguageSelector = ({ compact = false, className = '' }) => {
  const { language, setLanguage, supportedLanguages } = useLanguage();

  return (
    <div
      className={`inline-flex items-center space-x-1.5 bg-white border border-slate-200 text-slate-700 rounded-xl shadow-xs px-2.5 py-1.5 transition-colors hover:border-slate-300 ${className}`}
    >
      <Globe className="w-3.5 h-3.5 text-teal-600 shrink-0" />
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        aria-label="Select Preferred Language"
        className="bg-transparent text-xs font-semibold text-slate-700 outline-none cursor-pointer pr-1"
      >
        {supportedLanguages.map((lang) => (
          <option key={lang.code} value={lang.code} className="text-slate-800 bg-white py-1">
            {lang.nativeName} ({lang.name})
          </option>
        ))}
      </select>
    </div>
  );
};

export default LanguageSelector;
