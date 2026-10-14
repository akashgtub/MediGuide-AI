import { useEffect, useState } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import { ShieldAlert, CheckCircle, ArrowLeft, FileText, AlertTriangle, Info, Eye } from 'lucide-react';

const ReportAnalysis = () => {
  const { id } = useParams();
  const location = useLocation();

  const [report, setReport] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [showRawText, setShowRawText] = useState(false);

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
        } catch {
          setReport(null);
        }
      }
    }
  }, [id, location.state]);

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

  const { extracted_info, summary, risk_assessment, guidance, disclaimer, extracted_text, filename } = report;
  const isHighRisk = risk_assessment?.is_high_risk;
  const isUncertain = risk_assessment?.uncertainty_flag;

  const testValuesCombined = [];
  if (extracted_info?.test_names?.length || extracted_info?.test_values?.length) {
    const vals = extracted_info.test_values || [];
    const units = extracted_info.units || [];
    const names = extracted_info.test_names || [];

    if (vals.length > 0) {
      testValuesCombined.push(
        vals.map((v, i) => `${v} ${units[i] || ''}`.trim()).join(', ')
      );
    }
    if (names.length > 0 && vals.length === 0) {
      testValuesCombined.push(names.join(', '));
    }
  }

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-2">
        <div>
          <div className="flex items-center space-x-2">
            <Link to="/patient/upload" className="text-slate-400 hover:text-slate-600 text-sm flex items-center">
              <ArrowLeft className="w-4 h-4 mr-1" /> Back
            </Link>
            <span className="text-slate-300">•</span>
            <span className="text-xs font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
              {report.report_id}
            </span>
            {filename && (
              <span className="text-xs text-slate-500 font-medium">({filename})</span>
            )}
            {report.timings?.total_seconds && (
              <span className="text-xs text-slate-400 font-mono">[{report.timings.total_seconds}s]</span>
            )}
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mt-1">Report Analysis</h1>
        </div>

        {/* Dynamic Risk Badge */}
        <div className="flex flex-wrap items-center gap-2">
          {isHighRisk ? (
            <span className="bg-red-100 text-red-800 border border-red-200 px-3 py-1 rounded-full text-xs sm:text-sm font-semibold flex items-center shadow-sm">
              <ShieldAlert className="w-4 h-4 mr-1.5 text-red-600" />
              High Risk — Clinical Review Escalated
            </span>
          ) : isUncertain ? (
            <span className="bg-amber-100 text-amber-800 border border-amber-200 px-3 py-1 rounded-full text-xs sm:text-sm font-semibold flex items-center shadow-sm">
              <AlertTriangle className="w-4 h-4 mr-1.5 text-amber-600" />
              Additional Professional Review Recommended
            </span>
          ) : (
            <span className="bg-emerald-100 text-emerald-800 border border-emerald-200 px-3 py-1 rounded-full text-xs sm:text-sm font-semibold flex items-center shadow-sm">
              <CheckCircle className="w-4 h-4 mr-1.5 text-emerald-600" />
              Standard Report — Normal Routing
            </span>
          )}
        </div>
      </div>

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        {/* Left Column: Document Preview / OCR Raw Text */}
        <div className="bg-slate-100 rounded-xl border border-slate-200 p-4 flex flex-col min-h-[480px]">
          <div className="flex justify-between items-center mb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              {showRawText ? 'Extracted OCR Text' : 'Original Document'}
            </span>
            <button
              onClick={() => setShowRawText(!showRawText)}
              className="text-xs font-medium text-teal-700 bg-white border border-slate-300 hover:bg-slate-50 px-2.5 py-1 rounded-md flex items-center space-x-1 shadow-2xs"
            >
              <Eye className="w-3.5 h-3.5 mr-1" />
              <span>{showRawText ? 'Show Visual' : 'View OCR Text'}</span>
            </button>
          </div>

          <div className="flex-1 flex items-center justify-center bg-white rounded-lg border border-slate-200 p-4 overflow-auto">
            {showRawText ? (
              <pre className="text-xs text-slate-700 font-mono whitespace-pre-wrap leading-relaxed w-full h-full">
                {extracted_text || 'No raw text available.'}
              </pre>
            ) : previewUrl ? (
              <img
                src={previewUrl}
                alt="Uploaded Report"
                className="max-h-[520px] max-w-full object-contain rounded shadow-xs"
              />
            ) : (
              <div className="text-center p-6">
                <FileText className="w-16 h-16 text-slate-300 mx-auto mb-3" />
                <p className="text-sm font-semibold text-slate-700">{filename || 'Document'}</p>
                <p className="text-xs text-slate-400 mt-1">
                  Text extracted via PaddleOCR engine.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Structured AI Findings */}
        <div className="bg-white rounded-xl shadow-xs border border-slate-100 p-6 overflow-y-auto space-y-6">
          <h2 className="text-lg font-bold text-slate-800">Information Identified from Report</h2>

          {/* Simple Summary */}
          <div className="bg-teal-50/50 p-4 rounded-xl border border-teal-100">
            <h3 className="font-bold text-teal-900 text-sm mb-1.5 flex items-center">
              <Info className="w-4 h-4 mr-1.5 text-teal-600" /> Patient-Friendly Summary
            </h3>
            <p className="text-slate-700 text-sm leading-relaxed">
              {summary || 'No summary available for this document.'}
            </p>
          </div>

          {/* Extracted Clinical Metrics Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="border border-slate-100 bg-slate-50/40 rounded-xl p-3.5">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">Reported Symptoms</p>
              <p className="font-medium text-slate-800 mt-1 text-sm">
                {extracted_info?.symptoms?.length ? extracted_info.symptoms.join(', ') : 'None detected'}
              </p>
            </div>

            <div className="border border-slate-100 bg-slate-50/40 rounded-xl p-3.5">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">Medications</p>
              <p className="font-medium text-slate-800 mt-1 text-sm">
                {extracted_info?.medications?.length ? extracted_info.medications.join(', ') : 'None listed'}
              </p>
            </div>

            <div className="border border-slate-100 bg-slate-50/40 rounded-xl p-3.5">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">Tests & Measurements</p>
              <p className="font-medium text-slate-800 mt-1 text-sm">
                {testValuesCombined.length > 0
                  ? testValuesCombined.join(', ')
                  : (extracted_info?.test_names?.length ? extracted_info.test_names.join(', ') : 'None detected')}
              </p>
            </div>

            <div className="border border-slate-100 bg-slate-50/40 rounded-xl p-3.5">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide">Dates Recorded</p>
              <p className="font-medium text-slate-800 mt-1 text-sm">
                {extracted_info?.dates?.length ? extracted_info.dates.join(', ') : 'None noted'}
              </p>
            </div>
          </div>

          {/* Observations */}
          {extracted_info?.observations?.length > 0 && (
            <div className="border border-slate-100 rounded-xl p-3.5 bg-slate-50/30">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1">Clinical Observations</p>
              <ul className="text-sm text-slate-700 list-disc pl-5 space-y-1">
                {extracted_info.observations.map((obs, idx) => (
                  <li key={idx}>{obs}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggested Next Steps / Guidance */}
          <div>
            <h3 className="font-bold text-slate-800 mb-2 flex items-center text-sm">
              <CheckCircle className="w-4 h-4 text-teal-600 mr-2" /> Suggested Next Steps
            </h3>
            <ul className="text-sm text-slate-600 space-y-2 pl-6 list-disc">
              {guidance?.length > 0 ? (
                guidance.map((step, idx) => <li key={idx}>{step}</li>)
              ) : (
                <li>Bring this document to your next doctor consultation.</li>
              )}
            </ul>
          </div>

          {/* Escalation Reasons if Flagged */}
          {risk_assessment?.reasons?.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 text-xs text-amber-800">
              <p className="font-bold mb-1">Flagged Review Factors:</p>
              <ul className="list-disc pl-4 space-y-0.5">
                {risk_assessment.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Mandatory Clinical Disclaimer */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 leading-relaxed">
            <strong>Clinical Safety Disclaimer:</strong> {disclaimer}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportAnalysis;
