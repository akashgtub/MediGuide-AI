import { useAuth } from '../../context/AuthContext';
import { useLanguage } from '../../context/LanguageContext';
import { mockStats, mockReports } from '../../data/mockData';
import StatCard from '../../components/StatCard';
import LanguageSelector from '../../components/LanguageSelector';
import { FileText, CheckCircle, Clock, Calendar, Upload, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';

const PatientDashboard = () => {
  const { user } = useAuth();
  const { t } = useLanguage();
  const stats = mockStats.patient;

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return t('dashboard.greetingMorning', 'Good morning');
    if (hour < 17) return t('dashboard.greetingAfternoon', 'Good afternoon');
    return t('dashboard.greetingEvening', 'Good evening');
  };

  return (
    <div className="space-y-6">
      {/* Welcome Bar with Language Selector */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-800">
            {getGreeting()}, {user?.name ? user.name.split(' ')[0] : 'there'}
          </h1>
          <p className="text-slate-500 mt-1 text-sm">
            {t('dashboard.subtitle', "Here's an overview of your MediGuide journey.")}
          </p>
        </div>

        {/* Dashboard Language Selector */}
        <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-xl border border-slate-200 shadow-xs">
          <span className="text-xs font-medium text-slate-500 hidden sm:inline">
            {t('common.language', 'Language')}:
          </span>
          <LanguageSelector />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title={t('dashboard.statsUploaded', 'Reports Uploaded')} value={stats.uploaded} icon={<FileText />} color="blue" />
        <StatCard title={t('dashboard.statsAnalyzed', 'Reports Analyzed')} value={stats.analyzed} icon={<CheckCircle />} color="teal" />
        <StatCard title={t('dashboard.statsPending', 'Reviews Pending')} value={stats.pending} icon={<Clock />} color="amber" />
        <StatCard title={t('dashboard.statsPrep', 'Appointments Prepared')} value={stats.prep} icon={<Calendar />} color="indigo" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Recent Reports List */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-xs border border-slate-100 p-6">
            <h2 className="text-lg font-bold text-slate-800 mb-4">
              {t('dashboard.recentReports', 'Recent Reports')}
            </h2>
            <div className="space-y-3">
              {mockReports.map((report) => (
                <div key={report.id} className="flex items-center justify-between p-3.5 border border-slate-100 rounded-lg hover:bg-slate-50/80 transition-colors">
                  <div className="flex items-center space-x-3.5">
                    <div className="p-2.5 bg-teal-50 text-teal-600 rounded-lg">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800 text-sm">{report.type}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{report.date}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      report.status === 'Analyzed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {report.status === 'Analyzed' ? t('dashboard.statusAnalyzed', 'Analyzed') : t('dashboard.statusPending', 'Review Required')}
                    </span>
                    <Link
                      to={`/patient/reports/${report.id}`}
                      className="text-teal-600 hover:text-teal-800 font-semibold text-xs bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded-md transition-colors"
                    >
                      {t('common.view', 'View')}
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Action Widgets */}
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-teal-600 to-teal-800 rounded-xl shadow-sm p-6 text-white">
            <div className="flex justify-between items-start mb-3">
              <Upload className="w-7 h-7 text-teal-100" />
            </div>
            <h2 className="text-lg font-bold mb-1.5">
              {t('dashboard.uploadCtaTitle', 'Upload Medical Report')}
            </h2>
            <p className="text-teal-100 text-xs mb-5 leading-relaxed">
              {t('dashboard.uploadCtaDesc', 'Upload your latest medical documents for AI-assisted simplification.')}
            </p>
            <Link
              to="/patient/upload"
              className="block w-full text-center bg-white text-teal-700 font-semibold py-2.5 rounded-lg hover:bg-slate-50 transition-colors text-sm shadow-xs"
            >
              {t('dashboard.uploadCtaBtn', 'Upload Now')}
            </Link>
          </div>

          <div className="bg-white rounded-xl shadow-xs border border-slate-100 p-5">
            <h2 className="text-base font-bold text-slate-800 mb-1">
              {t('dashboard.aiInsightTitle', 'AI Insight')}
            </h2>
            <p className="text-xs text-slate-500 mb-3.5">
              {t('dashboard.aiInsightSubtitle', 'Your latest report has been processed.')}
            </p>
            <ul className="space-y-2 text-xs text-slate-700">
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t('dashboard.aiExtracted', 'Information extracted')}</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t('dashboard.aiSummary', 'Summary available')}</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{t('dashboard.aiMultilingual', 'Multilingual support active')}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientDashboard;
