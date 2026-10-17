import { useState, useEffect } from 'react';
import { useAuth, apiFetch } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { mockStats, mockReports } from '../../data/mockData';
import StatCard from '../../components/StatCard';
import {
  FileText,
  CheckCircle2,
  Clock,
  Calendar,
  Upload,
  Heart,
  Activity,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Stethoscope,
  ChevronRight,
  Droplets,
  Thermometer,
  Wind,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const PatientDashboard = () => {
  const { user } = useAuth();
  const { t } = useLanguage();

  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(mockStats.patient);

  useEffect(() => {
    const fetchPatientData = async () => {
      setLoading(true);
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
      } catch (e) {
        console.warn('Session storage read error:', e);
      }

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
              measurements: r.measurements || [],
            },
          }));
        }
      } catch (err) {
        console.warn('Could not fetch backend reports:', err);
      }

      // Merge real reports
      const combined = [...dbReports];
      sessionReports.forEach((s) => {
        if (!combined.some((c) => c.id === s.id)) combined.push(s);
      });
      mockReports.forEach((m) => {
        if (!combined.some((c) => c.id === m.id)) combined.push(m);
      });

      setReports(combined);

      // Compute dynamic stats
      const uploadedCount = combined.length;
      const analyzedCount = combined.filter((r) => r.status === 'Analyzed').length;
      const pendingCount = combined.filter((r) => r.status === 'Review Required' || r.risk === 'High').length;

      setStats({
        uploaded: uploadedCount,
        analyzed: analyzedCount,
        pending: pendingCount,
        prep: 2,
      });

      setLoading(false);
    };

    fetchPatientData();
  }, []);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('dashboard.greetingMorning', 'Good morning');
    if (hour < 17) return t('dashboard.greetingAfternoon', 'Good afternoon');
    return t('dashboard.greetingEvening', 'Good evening');
  };

  const recentReports = reports.slice(0, 4);

  return (
    <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-200">
      {/* Header & Welcome Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#172033] tracking-tight">
              {getGreeting()}, {user?.name ? user.name.split(' ')[0] : 'Alex'} 👋
            </h1>
          </div>
          <p className="text-slate-500 mt-1 text-xs sm:text-sm">
            {t('dashboard.subtitle', "Here's an overview of your health records and diagnostic progress.")}
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <Link
            to="/patient/upload"
            className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs sm:text-sm px-4 py-2.5 rounded-xl shadow-sm hover:shadow-teal-600/20 transition-all"
          >
            <Upload className="w-4 h-4" />
            <span>{t('nav.uploadReport', 'Upload Report')}</span>
          </Link>
          <Link
            to="/patient/assistant"
            className="inline-flex items-center space-x-2 bg-white hover:bg-slate-50 border border-[#E5EDF5] text-slate-700 font-semibold text-xs sm:text-sm px-4 py-2.5 rounded-xl shadow-xs transition-all"
          >
            <Sparkles className="w-4 h-4 text-teal-600" />
            <span className="hidden sm:inline">Ask AI</span>
          </Link>
        </div>
      </div>

      {/* Featured Upcoming Doctor Consultation Banner (Inspired by Reference 5 "Hourglass") */}
      <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-teal-700 via-teal-800 to-[#14213D] text-white p-6 sm:p-7 shadow-lg shadow-teal-900/10">
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md text-teal-100 text-xs font-semibold">
              <Calendar className="w-3.5 h-3.5 text-teal-300" />
              <span>Next Upcoming Consultation</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white">
              Dr. Sarah Wilson, MD • Cardiology
            </h2>
            <p className="text-teal-100 text-xs sm:text-sm max-w-xl">
              Appointment scheduled for routine cardiovascular review and blood pressure panel checkup.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-2 text-xs font-medium text-teal-200">
              <span className="bg-white/10 px-3 py-1 rounded-lg">📅 Monday, 26 Oct 2026 • 10:30 AM</span>
              <span className="bg-white/10 px-3 py-1 rounded-lg">🏥 Clinic Room A-03 • Station 4</span>
            </div>
          </div>

          <div className="flex sm:flex-col gap-2.5 shrink-0 w-full sm:w-auto">
            <Link
              to="/patient/appointment"
              className="inline-flex items-center justify-center space-x-2 bg-white text-teal-800 hover:bg-teal-50 px-5 py-3 rounded-xl font-bold text-xs sm:text-sm transition-all shadow-md text-center"
            >
              <span>Prepare Questions</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* Summary Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        <StatCard
          title={t('dashboard.statsUploaded', 'Reports Uploaded')}
          value={stats.uploaded}
          icon={<FileText className="w-6 h-6" />}
          color="blue"
          trend="+2 this month"
          trendUp={true}
        />
        <StatCard
          title={t('dashboard.statsAnalyzed', 'Reports Analyzed')}
          value={stats.analyzed}
          icon={<CheckCircle2 className="w-6 h-6" />}
          color="teal"
          trend="100% processed"
          trendUp={true}
        />
        <StatCard
          title={t('dashboard.statsPending', 'Reviews Pending')}
          value={stats.pending}
          icon={<Clock className="w-6 h-6" />}
          color="amber"
          subtitle={stats.pending > 0 ? 'Requires clinician look' : 'All clear'}
        />
        <StatCard
          title={t('dashboard.statsPrep', 'Appointments Prepared')}
          value={stats.prep}
          icon={<Calendar className="w-6 h-6" />}
          color="indigo"
          subtitle="Doctor questions ready"
        />
      </div>

      {/* Vitals Overview Widget (Inspired by Reference 2 & 4 "Medivora" & "Medi") */}
      <div className="bg-white rounded-3xl p-6 border border-[#E5EDF5] shadow-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-100 gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center border border-teal-100">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-extrabold text-[#172033]">Patient Vitals & Health Indicator</h2>
              <p className="text-xs text-slate-400">Recorded clinical biomarkers from verified laboratory panels</p>
            </div>
          </div>
          <div className="inline-flex items-center space-x-2 bg-emerald-50 text-emerald-700 px-3.5 py-1.5 rounded-full border border-emerald-100 text-xs font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Overall Health Score: 94/100 (Optimal)</span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-5">
          {/* Heart Rate */}
          <div className="bg-[#F6F9FC] p-4 rounded-2xl border border-slate-100 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center space-x-1.5">
                <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500/20" />
                <span>Heart Rate</span>
              </span>
              <span className="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px] font-bold">Normal</span>
            </div>
            <p className="text-2xl font-black text-[#172033]">72 <span className="text-xs font-medium text-slate-400">bpm</span></p>
            <p className="text-[11px] text-slate-400">Ref range: 60 - 100 bpm</p>
          </div>

          {/* Blood Pressure */}
          <div className="bg-[#F6F9FC] p-4 rounded-2xl border border-slate-100 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center space-x-1.5">
                <Droplets className="w-3.5 h-3.5 text-blue-500" />
                <span>Blood Pressure</span>
              </span>
              <span className="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px] font-bold">Normal</span>
            </div>
            <p className="text-2xl font-black text-[#172033]">120/80 <span className="text-xs font-medium text-slate-400">mmHg</span></p>
            <p className="text-[11px] text-slate-400">Ref range: &lt;120/80 mmHg</p>
          </div>

          {/* Oxygen Level */}
          <div className="bg-[#F6F9FC] p-4 rounded-2xl border border-slate-100 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center space-x-1.5">
                <Wind className="w-3.5 h-3.5 text-cyan-500" />
                <span>Oxygen SpO2</span>
              </span>
              <span className="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px] font-bold">Optimal</span>
            </div>
            <p className="text-2xl font-black text-[#172033]">98% <span className="text-xs font-medium text-slate-400">SpO2</span></p>
            <p className="text-[11px] text-slate-400">Ref range: 95% - 100%</p>
          </div>

          {/* Temperature */}
          <div className="bg-[#F6F9FC] p-4 rounded-2xl border border-slate-100 space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold">
              <span className="flex items-center space-x-1.5">
                <Thermometer className="w-3.5 h-3.5 text-amber-500" />
                <span>Core Temp</span>
              </span>
              <span className="text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded text-[10px] font-bold">Normal</span>
            </div>
            <p className="text-2xl font-black text-[#172033]">36.6 <span className="text-xs font-medium text-slate-400">°C</span></p>
            <p className="text-[11px] text-slate-400">Ref range: 36.5 - 37.5 °C</p>
          </div>
        </div>
      </div>

      {/* Main Grid: Recent Reports & Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Left Column (2/3): Recent Reports List */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-[#E5EDF5] shadow-card">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold text-[#172033]">
                  {t('dashboard.recentReports', 'Recent Diagnostic Reports')}
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Extracted biomarkers and clinical plain-language interpretations
                </p>
              </div>
              <Link
                to="/patient/reports"
                className="text-xs font-bold text-teal-600 hover:text-teal-700 inline-flex items-center space-x-1 hover:underline"
              >
                <span>View all</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {loading ? (
              <div className="py-12 text-center text-slate-400">
                <div className="w-7 h-7 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-xs">Loading medical reports...</p>
              </div>
            ) : recentReports.length === 0 ? (
              <div className="py-12 text-center text-slate-400">
                <FileText className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                <p className="text-sm font-semibold text-slate-700">No medical reports found</p>
                <p className="text-xs mt-1">Upload a lab report or prescription to see your insights.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {recentReports.map((report) => {
                  const isHighRisk = report.risk === 'High' || report.status === 'Review Required';

                  return (
                    <div
                      key={report.id}
                      className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/70 rounded-xl px-2 transition-colors"
                    >
                      <div className="flex items-center space-x-3.5">
                        <div className="p-3 bg-teal-50 text-teal-600 rounded-2xl border border-teal-100 shrink-0">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="font-bold text-[#172033] text-sm">{report.type}</p>
                          <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
                            <span className="font-mono">Ref #{report.id}</span>
                            <span>•</span>
                            <span>{report.date}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 self-end sm:self-center">
                        <span
                          className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                            isHighRisk
                              ? 'bg-rose-50 text-rose-700 border border-rose-100'
                              : 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isHighRisk ? 'bg-rose-500' : 'bg-emerald-500'
                            }`}
                          />
                          <span>
                            {isHighRisk
                              ? t('dashboard.statusPending', 'Review Required')
                              : t('dashboard.statusAnalyzed', 'Analyzed')}
                          </span>
                        </span>

                        <Link
                          to={`/patient/reports/${report.id}`}
                          state={{ report: report.reportData }}
                          className="inline-flex items-center space-x-1 text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100/80 px-3 py-1.5 rounded-xl font-bold text-xs transition-colors"
                        >
                          <span>{t('common.view', 'View')}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Health Tips Card (Inspired by Reference 5 "Hourglass") */}
          <div className="bg-white rounded-3xl p-6 border border-[#E5EDF5] shadow-card">
            <h2 className="text-base font-bold text-[#172033] mb-4">Daily Health Tips & Wellness Guidelines</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-4 rounded-2xl bg-[#F6F9FC] border border-slate-100 space-y-1.5">
                <span className="font-bold text-[#172033] block">💧 Stay Hydrated</span>
                <p className="text-slate-500 leading-relaxed">
                  Drink 2.5 liters of clean water daily to assist renal kidney filtration and electrolyte stability.
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-[#F6F9FC] border border-slate-100 space-y-1.5">
                <span className="font-bold text-[#172033] block">🚶 Move Every Hour</span>
                <p className="text-slate-500 leading-relaxed">
                  Take a 5-minute walk after desk work to support venous circulation and reduce cardiovascular strain.
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-[#F6F9FC] border border-slate-100 space-y-1.5">
                <span className="font-bold text-[#172033] block">🥗 Balanced Micronutrients</span>
                <p className="text-slate-500 leading-relaxed">
                  Include fiber-rich greens with lunch to stabilize glycemic spikes and promote optimal gut health.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (1/3): Action Widgets */}
        <div className="space-y-6">
          {/* Prominent Upload Medical Report Card */}
          <div className="bg-gradient-to-br from-teal-600 via-teal-700 to-teal-800 rounded-3xl shadow-md p-6 text-white relative overflow-hidden">
            <div className="absolute top-[-20%] right-[-20%] w-40 h-40 bg-white/10 rounded-full blur-xl pointer-events-none" />
            <div className="w-12 h-12 rounded-2xl bg-white/15 flex items-center justify-center text-teal-100 mb-4 border border-white/20">
              <Upload className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-black mb-1.5 text-white">
              {t('dashboard.uploadCtaTitle', 'Upload Medical Report')}
            </h2>
            <p className="text-teal-100 text-xs mb-5 leading-relaxed">
              {t('dashboard.uploadCtaDesc', 'Upload lab reports, prescriptions, or clinical summaries for automated patient-friendly translation.')}
            </p>
            <Link
              to="/patient/upload"
              className="block w-full text-center bg-white text-teal-800 font-bold py-3 rounded-xl hover:bg-slate-50 transition-colors text-xs sm:text-sm shadow-md"
            >
              {t('dashboard.uploadCtaBtn', 'Upload Now')}
            </Link>
          </div>

          {/* AI Insight Card */}
          <div className="bg-white rounded-3xl shadow-card border border-[#E5EDF5] p-6 space-y-4">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 bg-teal-50 text-teal-600 rounded-xl">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-extrabold text-[#172033]">
                  {t('dashboard.aiInsightTitle', 'AI Clinical Insight')}
                </h2>
                <p className="text-[11px] text-slate-400">
                  {t('dashboard.aiInsightSubtitle', 'Continuous safety & terminology check')}
                </p>
              </div>
            </div>

            <ul className="space-y-2.5 text-xs text-slate-600">
              <li className="flex items-center space-x-2.5 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t('dashboard.aiExtracted', 'Biomarker ranges extracted')}</span>
              </li>
              <li className="flex items-center space-x-2.5 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t('dashboard.aiSummary', 'Plain-English summary active')}</span>
              </li>
              <li className="flex items-center space-x-2.5 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t('dashboard.aiMultilingual', '6 Indian languages supported')}</span>
              </li>
            </ul>

            <Link
              to="/patient/assistant"
              className="w-full inline-flex items-center justify-center space-x-1.5 py-2.5 rounded-xl bg-slate-50 hover:bg-teal-50 text-slate-700 hover:text-teal-700 text-xs font-bold transition-colors border border-slate-200"
            >
              <span>Ask AI About Your Vitals</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Find a Doctor Specialty Directory (Inspired by Reference 5 "Hourglass") */}
          <div className="bg-white rounded-3xl shadow-card border border-[#E5EDF5] p-6">
            <div className="flex items-center justify-between mb-3.5">
              <h2 className="text-sm font-extrabold text-[#172033]">Medical Specialties</h2>
              <span className="text-[11px] text-teal-600 font-bold cursor-pointer hover:underline">
                Find Doctor
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs font-semibold">
              <div className="p-2.5 bg-slate-50 hover:bg-teal-50 rounded-xl border border-slate-100 transition-colors flex items-center space-x-2">
                <Heart className="w-3.5 h-3.5 text-rose-500" />
                <span>Cardiology</span>
              </div>
              <div className="p-2.5 bg-slate-50 hover:bg-teal-50 rounded-xl border border-slate-100 transition-colors flex items-center space-x-2">
                <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
                <span>General Health</span>
              </div>
              <div className="p-2.5 bg-slate-50 hover:bg-teal-50 rounded-xl border border-slate-100 transition-colors flex items-center space-x-2">
                <Wind className="w-3.5 h-3.5 text-cyan-600" />
                <span>Pulmonology</span>
              </div>
              <div className="p-2.5 bg-slate-50 hover:bg-teal-50 rounded-xl border border-slate-100 transition-colors flex items-center space-x-2">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                <span>Diagnostics</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientDashboard;
