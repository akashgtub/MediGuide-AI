import { useEffect, useState } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import {
  ShieldAlert,
  CheckCircle,
  ArrowLeft,
  FileText,
  AlertTriangle,
  Info,
  Eye,
  Globe,
  Loader2,
  Activity,
  Calendar,
  CheckCircle2,
} from 'lucide-react';
import { apiFetch } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { SUPPORTED_LANGUAGES } from '../../i18n/translations';

const ReportAnalysis = () => {
  const { id } = useParams();
  const location = useLocation();
  const { language, t } = useLanguage();

  const [report, setReport] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [showRawText, setShowRawText] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [explanationLang, setExplanationLang] = useState(language || 'en');
  const [isTranslating, setIsTranslating] = useState(false);

  // Sync explanation language when global language changes
  useEffect(() => {
    if (language) {
      setExplanationLang(language);
    }
  }, [language]);

  useEffect(() => {
    // 1. Check React Router navigation state
    if (location.state?.report) {
      setReport(location.state.report);
      if (location.state.previewUrl) {
        setPreviewUrl(location.state.previewUrl);
      }
      return;
    }

    // 2. Check session storage cache for page refresh
    if (id) {
      const cached = sessionStorage.getItem(`mediguide_report_${id}`);
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          setReport(parsed);
          const cachedPreview = sessionStorage.getItem(`mediguide_preview_${id}`);
          if (cachedPreview) {
            setPreviewUrl(cachedPreview);
          }
          return;
        } catch {
          // fallback to backend
        }
      }

      // 3. Fallback: Query backend SQLite persistence
      setIsLoading(true);
      apiFetch(`/api/reports/${id}?lang=${explanationLang}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            setReport({
              report_id: data.id,
              filename: data.filename,
              created_at: data.created_at,
              summary: data.summary,
              guidance: data.guidance || [],
              risk_assessment: {
                risk_level: data.risk_level,
                is_high_risk: data.is_high_risk,
                uncertainty_flag: data.uncertainty_flag,
                reasons: data.risk_reasons || [],
              },
              extracted_info: {
                symptoms: (data.entities || []).filter((e) => e.label === 'Symptom').map((e) => e.word),
                medications: (data.entities || []).filter((e) => e.label === 'Medication').map((e) => e.word),
                test_names: (data.measurements || []).map((m) => m.test_name),
                test_values: (data.measurements || []).map((m) => m.value),
                units: (data.measurements || []).map((m) => m.unit),
                reference_ranges: (data.measurements || []).map((m) => m.reference_range || '—'),
                observations: (data.entities || []).filter((e) => !['Symptom', 'Medication'].includes(e.label)).map((e) => e.word),
              },
              timings: data.timings || {},
              disclaimer: data.disclaimer || "MediGuide AI is an educational informational aid and is NOT a substitute for professional medical advice, clinical diagnosis, or treatment. Always consult a qualified physician.",
            });
          }
        })
        .catch((e) => console.warn('Could not fetch report from backend:', e))
        .finally(() => setIsLoading(false));
    }
  }, [id, location.state]);

  // Translate summary and guidance when explanationLang changes
  useEffect(() => {
    if (!report?.report_id) return;

    let isMounted = true;
    setIsTranslating(true);

    apiFetch(`/api/reports/${report.report_id}/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_language: explanationLang }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && isMounted) {
          setReport((prev) => ({
            ...prev,
            summary: data.summary || prev.summary,
            guidance: data.guidance || prev.guidance,
            disclaimer: data.disclaimer || prev.disclaimer,
          }));
        }
      })
      .catch((e) => console.warn('Translation request failed:', e))
      .finally(() => {
        if (isMounted) setIsTranslating(false);
      });

    return () => {
      isMounted = false;
    };
  }, [explanationLang, report?.report_id]);

  if (!report) {
    return (
      <div className="max-w-2xl mx-auto my-12 bg-white rounded-xl shadow-sm border border-slate-100 p-8 text-center">
        <div className="w-16 h-16 bg-slate-100 text-slate-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <FileText className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-800 mb-2">No Analysis Available</h2>
        <p className="text-slate-500 text-sm mb-6 max-w-md mx-auto">
          No report analysis data found for reference #{id}. Please upload a medical document to generate real-time AI extraction and summarization.
        </p>
        <Link
          to="/patient/upload"
          className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-medium px-5 py-2.5 rounded-lg transition-colors shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Upload a Report</span>
        </Link>
      </div>
    );
  }

  const { extracted_info, summary, risk_assessment, guidance, disclaimer, extracted_text, filename, created_at } = report;
  const isHighRisk = risk_assessment?.is_high_risk;
  const isUncertain = risk_assessment?.uncertainty_flag;

  // Build verified measurements list from extracted data
  const measurements = [];
  if (report.measurements && Array.isArray(report.measurements) && report.measurements.length > 0) {
    report.measurements.forEach((m) => {
      measurements.push({
        name: m.test_name || m.name || '—',
        value: m.value != null ? String(m.value) : '—',
        unit: m.unit || '—',
        referenceRange: m.reference_range || m.referenceRange || '—',
        status: m.status || (isHighRisk ? 'High Risk' : isUncertain ? 'Caution' : 'Normal'),
      });
    });
  } else if (extracted_info?.test_names?.length || extracted_info?.test_values?.length) {
    const names = extracted_info.test_names || [];
    const vals = extracted_info.test_values || [];
    const units = extracted_info.units || [];
    const ranges = extracted_info.reference_ranges || [];
    const count = Math.max(names.length, vals.length);

    for (let i = 0; i < count; i++) {
      const testName = names[i] || '—';
      const val = vals[i] != null ? String(vals[i]) : '—';
      const unit = units[i] || '—';
      const range = ranges[i] || '—';

      // Status: strictly from verified risk_assessment, never guess or invent based on numbers!
      let status = '—';
      if (isHighRisk) {
        const isMentionedInReasons = risk_assessment?.reasons?.some((r) =>
          r.toLowerCase().includes(testName.toLowerCase()) ||
          (testName.toLowerCase().includes('blood pressure') && r.toLowerCase().includes('blood pressure')) ||
          (testName.toLowerCase().includes('hemoglobin') && r.toLowerCase().includes('hemoglobin'))
        );
        status = isMentionedInReasons ? 'High Risk' : 'Flagged';
      } else if (isUncertain) {
        status = 'Caution / Review';
      } else if (risk_assessment && risk_assessment.is_high_risk === false && !risk_assessment.uncertainty_flag) {
        status = 'Normal';
      }

      measurements.push({
        name: testName,
        value: val,
        unit: unit,
        referenceRange: range,
        status: status,
      });
    }
  }

  const reportDate = created_at ? created_at.slice(0, 10) : (extracted_info?.dates?.[0] || '—');

  return (
    <div className="flex flex-col h-full space-y-5">
      {/* SECTION A: Report Header */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <Link to="/patient/upload" className="text-slate-400 hover:text-slate-600 text-xs flex items-center font-medium">
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> {t('report.back')}
            </Link>
            <span className="text-slate-300">•</span>
            <span className="text-xs font-mono bg-slate-100 text-slate-700 font-semibold px-2.5 py-0.5 rounded-md border border-slate-200">
              {report.report_id}
            </span>
            <div className="flex items-center text-xs text-slate-500 font-medium">
              <Calendar className="w-3.5 h-3.5 mr-1 text-slate-400" />
              <span>{reportDate}</span>
            </div>
            {report.timings?.total_seconds && (
              <span className="text-[11px] text-slate-400 font-mono">[{report.timings.total_seconds}s]</span>
            )}
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
            {filename || t('report.title')}
          </h1>
        </div>

        {/* Status Badge & Language Selector */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Status Badge: Professional Healthcare Palette */}
          {isHighRisk ? (
            <span className="bg-rose-50 text-rose-800 border border-rose-200 px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-semibold flex items-center shadow-2xs">
              <ShieldAlert className="w-4 h-4 mr-1.5 text-rose-600 shrink-0" />
              {t('report.riskHigh')}
            </span>
          ) : isUncertain ? (
            <span className="bg-amber-50 text-amber-800 border border-amber-200 px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-semibold flex items-center shadow-2xs">
              <AlertTriangle className="w-4 h-4 mr-1.5 text-amber-600 shrink-0" />
              {t('report.riskUncertain')}
            </span>
          ) : (
            <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-semibold flex items-center shadow-2xs">
              <CheckCircle className="w-4 h-4 mr-1.5 text-emerald-600 shrink-0" />
              {t('report.riskStandard')}
            </span>
          )}

          {/* Explanation Language Selector */}
          <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl shadow-2xs">
            <Globe className="w-3.5 h-3.5 text-teal-600 shrink-0" />
            <span className="text-xs text-slate-500 font-medium">{t('report.languageSelectorLabel')}</span>
            <select
              value={explanationLang}
              onChange={(e) => setExplanationLang(e.target.value)}
              className="text-xs bg-transparent text-slate-800 outline-none font-semibold cursor-pointer"
            >
              {SUPPORTED_LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.nativeName} ({l.name})
                </option>
              ))}
            </select>
            {isTranslating && <Loader2 className="w-3.5 h-3.5 text-teal-600 animate-spin" />}
          </div>
        </div>
      </div>

      {/* SECTION B: Key Measurements Grid */}
      {measurements.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center">
              <Activity className="w-3.5 h-3.5 text-teal-600 mr-1.5" />
              Key Measurements Overview
            </h2>
            <span className="text-xs text-slate-400 font-medium">{measurements.length} test(s) extracted</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {measurements.map((m, idx) => {
              const isFlagged = m.status === 'High Risk' || m.status === 'Flagged';
              const isCaution = m.status === 'Caution / Review' || m.status === 'Caution';
              const isNormal = m.status === 'Normal';

              return (
                <div
                  key={idx}
                  className="bg-white rounded-xl border border-slate-200/80 p-3.5 flex flex-col justify-between space-y-2 shadow-2xs hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-semibold text-slate-800 truncate" title={m.name}>
                      {m.name}
                    </p>
                    {m.status !== '—' && (
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border shrink-0 ${
                          isFlagged
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : isCaution
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : isNormal
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-slate-50 text-slate-600 border-slate-200'
                        }`}
                      >
                        {m.status}
                      </span>
                    )}
                  </div>

                  <div className="flex items-baseline space-x-1.5">
                    <span className="text-xl font-bold font-mono text-slate-900 tracking-tight">
                      {m.value}
                    </span>
                    <span className="text-xs font-medium text-slate-500 font-mono">
                      {m.unit !== '—' ? m.unit : ''}
                    </span>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                    <span>Reference Range:</span>
                    <span className="font-mono font-medium text-slate-700">{m.referenceRange}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Analysis Body: Grid of Left Column (Preview/OCR) & Right Column (Table + Summary) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Left Column: Original Document / OCR Text (5 cols) */}
        <div className="lg:col-span-5 bg-slate-100/90 rounded-2xl border border-slate-200 p-4 flex flex-col min-h-[460px]">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center">
              <FileText className="w-3.5 h-3.5 text-slate-500 mr-1.5" />
              {showRawText ? t('report.ocrText') : t('report.originalDoc')}
            </span>
            <button
              type="button"
              onClick={() => setShowRawText(!showRawText)}
              className="text-xs font-medium text-teal-700 bg-white border border-slate-300 hover:bg-slate-50 px-2.5 py-1 rounded-md flex items-center space-x-1 shadow-2xs transition-colors"
            >
              <Eye className="w-3.5 h-3.5 mr-1" />
              <span>{showRawText ? t('report.showVisual') : t('report.viewOcrText')}</span>
            </button>
          </div>

          <div className="flex-1 flex items-center justify-center bg-white rounded-xl border border-slate-200 p-4 overflow-auto shadow-inner">
            {showRawText ? (
              <pre className="text-xs text-slate-800 font-mono whitespace-pre-wrap leading-relaxed w-full h-full select-all">
                {extracted_text || 'No raw OCR text available.'}
              </pre>
            ) : previewUrl ? (
              <img
                src={previewUrl}
                alt="Uploaded Report"
                className="max-h-[500px] max-w-full object-contain rounded shadow-xs"
              />
            ) : (
              <div className="text-center p-6 space-y-2">
                <FileText className="w-14 h-14 text-slate-300 mx-auto" />
                <p className="text-sm font-semibold text-slate-700">{filename || 'Medical Document'}</p>
                <p className="text-xs text-slate-400 max-w-xs mx-auto">
                  Original extracted medical text preserved via OCR engine. Toggle above to view extracted text.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Detailed Table + Patient-Friendly Summary (7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl shadow-xs border border-slate-200/80 p-6 overflow-y-auto space-y-6">
          {/* Safe metrics notice banner */}
          <div className="text-[11px] bg-sky-50 border border-sky-100 text-sky-900 px-3.5 py-2 rounded-xl flex items-center space-x-2">
            <Info className="w-4 h-4 text-sky-600 shrink-0" />
            <span>{t('report.originalNotice')}</span>
          </div>

          {/* SECTION C: Detailed Results Table */}
          <div className="space-y-2.5">
            <h2 className="text-sm font-bold text-slate-800 tracking-tight flex items-center">
              <Activity className="w-4 h-4 text-teal-600 mr-2" />
              Detailed Results Table
            </h2>

            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-2xs">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600">
                    <th className="py-2.5 px-3 font-semibold w-[32%] min-w-[140px]">Test / Measurement</th>
                    <th className="py-2.5 px-3 font-semibold text-right w-[20%] min-w-[90px]">Recorded Value</th>
                    <th className="py-2.5 px-3 font-semibold w-[14%] min-w-[60px]">Unit</th>
                    <th className="py-2.5 px-3 font-semibold text-center w-[18%] min-w-[100px]">Reference Range</th>
                    <th className="py-2.5 px-3 font-semibold text-center w-[16%] min-w-[90px]">Existing Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {measurements.length > 0 ? (
                    measurements.map((m, idx) => {
                      const isFlagged = m.status === 'High Risk' || m.status === 'Flagged';
                      const isCaution = m.status === 'Caution / Review' || m.status === 'Caution';
                      const isNormal = m.status === 'Normal';

                      return (
                        <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                          <td className="py-2.5 px-3 font-medium text-slate-800 break-words">
                            {m.name}
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                            {m.value}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-slate-500">
                            {m.unit}
                          </td>
                          <td className="py-2.5 px-3 text-center font-mono text-slate-600">
                            {m.referenceRange}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            {m.status !== '—' ? (
                              <span
                                className={`inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                                  isFlagged
                                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                                    : isCaution
                                    ? 'bg-amber-50 text-amber-700 border-amber-200'
                                    : isNormal
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                    : 'bg-slate-50 text-slate-600 border-slate-200'
                                }`}
                              >
                                {m.status}
                              </span>
                            ) : (
                              <span className="text-slate-400 font-mono">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-4 text-center text-slate-400 italic">
                        No individual numeric laboratory measurements were identified in this document.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* SECTION D: Patient-Friendly Summary */}
          <div className="bg-sky-50/50 p-4 rounded-xl border border-sky-100/90 space-y-2">
            <div className="flex items-center justify-between pb-1 border-b border-sky-100">
              <h3 className="font-bold text-slate-900 text-sm flex items-center">
                <Info className="w-4 h-4 mr-1.5 text-sky-600" />
                {t('report.summaryTitle')}
              </h3>
              {isTranslating && (
                <span className="text-xs text-sky-700 flex items-center font-normal">
                  <Loader2 className="w-3 h-3 animate-spin mr-1 text-sky-600" />
                  {t('report.translating')}
                </span>
              )}
            </div>
            <p className="text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">
              {summary || 'No summary available for this document.'}
            </p>
          </div>

          {/* Structured Clinical Observations & Context */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div className="border border-slate-200/70 bg-slate-50/50 rounded-xl p-3">
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">{t('report.symptomsTitle')}</p>
              <p className="font-medium text-slate-800 mt-1 text-xs">
                {extracted_info?.symptoms?.length ? extracted_info.symptoms.join(', ') : t('common.noneDetected')}
              </p>
            </div>

            <div className="border border-slate-200/70 bg-slate-50/50 rounded-xl p-3">
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">{t('report.medicationsTitle')}</p>
              <p className="font-medium text-slate-800 mt-1 text-xs">
                {extracted_info?.medications?.length ? extracted_info.medications.join(', ') : t('common.noneListed')}
              </p>
            </div>
          </div>

          {/* Observations if available */}
          {extracted_info?.observations?.length > 0 && (
            <div className="border border-slate-200/70 rounded-xl p-3.5 bg-slate-50/30 space-y-1">
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide">{t('report.observationsTitle')}</p>
              <ul className="text-xs text-slate-700 list-disc pl-5 space-y-1">
                {extracted_info.observations.map((obs, idx) => (
                  <li key={idx}>{obs}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggested Next Steps / Guidance */}
          <div className="space-y-2">
            <h3 className="font-bold text-slate-800 text-xs uppercase tracking-wider flex items-center">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 mr-1.5" />
              {t('report.nextStepsTitle')}
            </h3>
            <ul className="text-xs text-slate-600 space-y-1.5 pl-5 list-disc leading-relaxed">
              {guidance?.length > 0 ? (
                guidance.map((step, idx) => <li key={idx}>{step}</li>)
              ) : (
                <li>Bring this document to your next doctor consultation.</li>
              )}
            </ul>
          </div>

          {/* Flagged Review Factors (if flagged by risk engine) */}
          {risk_assessment?.reasons?.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 text-xs text-amber-900 space-y-1">
              <p className="font-bold flex items-center">
                <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-600" />
                {t('report.flaggedFactors')}
              </p>
              <ul className="list-disc pl-5 space-y-0.5">
                {risk_assessment.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Mandatory Clinical Disclaimer */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-500 leading-relaxed">
            <strong className="text-slate-600">{t('report.disclaimerTitle')}</strong> {disclaimer}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportAnalysis;
