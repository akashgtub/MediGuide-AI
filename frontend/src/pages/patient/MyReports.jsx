import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Search,
  Filter,
  ArrowRight,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Calendar,
} from 'lucide-react';
import { mockReports } from '../../data/mockData';
import { apiFetch } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';

const MyReports = () => {
  const { t } = useLanguage();
  const [reports, setReports] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');

  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadReports = async () => {
      setIsLoading(true);
      const sessionReports = [];
      try {
        for (let i = 0; i < sessionStorage.length; i++) {
          const key = sessionStorage.key(i);
          if (key && key.startsWith('mediguide_report_')) {
            const raw = sessionStorage.getItem(key);
            if (raw) {
              const parsed = JSON.parse(raw);
              sessionReports.push({
                id: parsed.report_id,
                type: parsed.filename || 'Uploaded Medical Document',
                date: new Date().toISOString().split('T')[0],
                status: parsed.risk_assessment?.is_high_risk ? 'Review Required' : 'Analyzed',
                risk: parsed.risk_assessment?.is_high_risk ? 'High' : 'Low',
                reportData: parsed,
              });
            }
          }
        }
      } catch {
        // ignore parsing errors
      }

      // Fetch persistent reports from SQLite via backend API
      let dbReports = [];
      try {
        const res = await apiFetch('/api/reports');
        if (res.ok) {
          const data = await res.json();
          dbReports = data.map((r) => ({
            id: r.id,
            type: r.filename || 'Diagnostic Report',
            date: r.uploaded_at ? r.uploaded_at.split('T')[0] : new Date().toISOString().split('T')[0],
            status: r.is_high_risk ? 'Review Required' : 'Analyzed',
            risk: r.is_high_risk ? 'High' : (r.risk_level === 'MEDIUM' ? 'Medium' : 'Low'),
            reportData: {
              report_id: r.id,
              filename: r.filename,
              summary: r.summary,
              risk_assessment: {
                risk_level: r.risk_level,
                is_high_risk: r.is_high_risk,
                triggered_rules: r.risk_reasons || [],
              },
              extracted_entities: r.entities || [],
              structured_findings: {
                measurements: r.measurements || [],
              },
              timings: r.timings || {},
            },
          }));
        }
      } catch (e) {
        console.warn('Could not fetch reports from backend:', e);
      }

      // Merge: backend reports first, then session reports, then mock reports
      const combined = [...dbReports];
      sessionReports.forEach((s) => {
        if (!combined.some((c) => c.id === s.id)) {
          combined.push(s);
        }
      });
      mockReports.forEach((m) => {
        if (!combined.some((c) => c.id === m.id)) {
          combined.push(m);
        }
      });

      setReports(combined);
      setIsLoading(false);
    };

    loadReports();
  }, []);

  const filteredReports = reports.filter((r) => {
    const matchesRisk = riskFilter === 'ALL' || r.risk?.toUpperCase() === riskFilter.toUpperCase();
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      r.type.toLowerCase().includes(query) ||
      r.id.toLowerCase().includes(query) ||
      r.status.toLowerCase().includes(query);

    return matchesRisk && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">{t('myReports.title')}</h1>
          <p className="text-slate-500 text-sm mt-1">
            Access your processed diagnostic documents, AI summaries, and clinical safety reviews
          </p>
        </div>
        <Link
          to="/patient/upload"
          className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-medium px-4 py-2.5 rounded-xl text-sm transition-all shadow-sm hover:shadow-teal-600/20 self-start"
        >
          <UploadCloud className="w-4 h-4" />
          <span>{t('nav.uploadReport')}</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder={t('common.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {['ALL', 'Low', 'High'].map((risk) => (
            <button
              key={risk}
              onClick={() => setRiskFilter(risk)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                riskFilter === risk
                  ? 'bg-teal-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {risk === 'ALL' ? 'All' : (risk === 'High' ? t('dashboard.riskHigh') : t('dashboard.riskLow'))}
            </button>
          ))}
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-100 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <th className="p-4 pl-6">{t('dashboard.tableType')}</th>
                <th className="p-4">{t('dashboard.tableDate')}</th>
                <th className="p-4">{t('dashboard.tableStatus')}</th>
                <th className="p-4">{t('dashboard.tableRisk')}</th>
                <th className="p-4 pr-6 text-right">{t('dashboard.tableAction')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {filteredReports.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center text-slate-400">
                    <FileText className="w-10 h-10 mx-auto text-slate-300 mb-2" />
                    <p className="font-semibold text-slate-700">{t('myReports.empty')}</p>
                  </td>
                </tr>
              ) : (
                filteredReports.map((report) => {
                  const isHighRisk = report.risk?.toLowerCase() === 'high';

                  return (
                    <tr key={report.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="p-4 pl-6">
                        <div className="flex items-center space-x-3">
                          <div className="p-2.5 bg-teal-50 text-teal-600 rounded-xl shrink-0">
                            <FileText className="w-5 h-5" />
                          </div>
                          <div>
                            <p className="font-semibold text-slate-800">{report.type}</p>
                            <p className="text-xs text-slate-400 font-mono">Ref #{report.id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-slate-500 text-xs">
                        <div className="flex items-center space-x-1.5">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          <span>{report.date}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span
                          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            report.status === 'Analyzed'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {report.status === 'Analyzed' ? (
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                          ) : (
                            <Clock className="w-3 h-3 mr-1" />
                          )}
                          <span>{report.status === 'Analyzed' ? t('dashboard.statusAnalyzed') : t('dashboard.statusPending')}</span>
                        </span>
                      </td>
                      <td className="p-4">
                        <span
                          className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            isHighRisk
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isHighRisk ? 'bg-rose-600' : 'bg-emerald-600'
                            }`}
                          ></span>
                          <span>{isHighRisk ? t('dashboard.riskHigh') : t('dashboard.riskLow')}</span>
                        </span>
                      </td>
                      <td className="p-4 pr-6 text-right">
                        <Link
                          to={`/patient/reports/${report.id}`}
                          state={{ report: report.reportData }}
                          className="inline-flex items-center space-x-1 bg-slate-100 hover:bg-teal-50 text-slate-700 hover:text-teal-700 px-3.5 py-1.5 rounded-xl text-xs font-medium transition-colors"
                        >
                          <span>{t('common.view')}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MyReports;
