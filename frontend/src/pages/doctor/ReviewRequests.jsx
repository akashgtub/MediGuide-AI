import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Clock,
  CheckCircle,
  Search,
  Filter,
  ArrowRight,
  ShieldAlert,
  RefreshCw,
  FileText,
  Activity,
  UserCheck,
} from 'lucide-react';
import { apiFetch } from '../../context/AuthContext';

const ReviewRequests = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterRisk, setFilterRisk] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('PENDING_REVIEW');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const res = await apiFetch('/api/reviews');
      if (res.ok) {
        const data = await res.json();
        setReviews(data);
      } else {
        throw new Error('API request failed');
      }
    } catch {
      // Fallback local initial state if backend is offline
      setReviews([
        {
          id: 'MG-1024',
          patient_id: 'PT-8821 (Anonymized)',
          risk_level: 'HIGH',
          status: 'PENDING_REVIEW',
          summary: 'Patient reports severe chest pain and shortness of breath for 4 hours. Taking Aspirin 81mg. Blood pressure elevated at 145/95 mmHg.',
          escalation_reasons: ['Reported severe chest pain and shortness of breath.'],
          created_at: '2026-10-15T09:30:00Z',
        },
        {
          id: 'MG-1025',
          patient_id: 'PT-3419 (Anonymized)',
          risk_level: 'HIGH',
          status: 'PENDING_REVIEW',
          summary: 'Routine vitals recorded blood pressure of 180/110 mmHg with accompanying occipital headache.',
          escalation_reasons: ['Extremely elevated blood pressure (180/110 mmHg).'],
          created_at: '2026-10-15T10:15:00Z',
        },
        {
          id: 'MG-1021',
          patient_id: 'PT-5512 (Anonymized)',
          risk_level: 'UNCERTAIN',
          status: 'COMPLETED',
          summary: 'Patient taking Warfarin along with high-dose Ibuprofen. Elevated INR test value recorded.',
          escalation_reasons: ['Uncertain medication interaction with OTC analgesics.'],
          created_at: '2026-10-14T14:20:00Z',
          decision: 'Schedule urgent telehealth consult',
          reviewed_by: 'Dr. Sarah Wilson, MD',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const filteredReviews = reviews.filter((item) => {
    const matchesRisk = filterRisk === 'ALL' || item.risk_level === filterRisk;
    const matchesStatus = filterStatus === 'ALL' || item.status === filterStatus;
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      item.id?.toLowerCase().includes(query) ||
      item.summary?.toLowerCase().includes(query) ||
      item.escalation_reasons?.some((r) => r.toLowerCase().includes(query)) ||
      item.patient_id?.toLowerCase().includes(query);

    return matchesRisk && matchesStatus && matchesSearch;
  });

  const pendingCount = reviews.filter((r) => r.status === 'PENDING_REVIEW').length;
  const highRiskCount = reviews.filter((r) => r.risk_level === 'HIGH' && r.status === 'PENDING_REVIEW').length;
  const completedCount = reviews.filter((r) => r.status === 'COMPLETED').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Clinical Review Queue</h1>
          <p className="text-slate-500 text-sm mt-1">
            Cases escalated by MediGuide-AI risk evaluation for expert clinician sign-off
          </p>
        </div>
        <button
          onClick={fetchReviews}
          disabled={loading}
          className="inline-flex items-center space-x-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-medium px-4 py-2 rounded-xl text-sm transition-colors shadow-sm self-start"
        >
          <RefreshCw className={`w-4 h-4 text-teal-600 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Pending Review</p>
            <p className="text-2xl font-bold text-slate-800">{pendingCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-rose-50 text-rose-600 rounded-xl">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">High Risk Escalations</p>
            <p className="text-2xl font-bold text-rose-600">{highRiskCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-teal-50 text-teal-600 rounded-xl">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Completed Reviews</p>
            <p className="text-2xl font-bold text-teal-700">{completedCount}</p>
          </div>
        </div>
      </div>

      {/* Controls & Filter Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Case ID, symptom, or escalation reason..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        {/* Filter Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center space-x-1 text-xs text-slate-400 mr-2">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter:</span>
          </div>

          <button
            onClick={() => setFilterStatus(filterStatus === 'PENDING_REVIEW' ? 'ALL' : 'PENDING_REVIEW')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filterStatus === 'PENDING_REVIEW'
                ? 'bg-amber-100 text-amber-800 font-semibold'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Pending Only
          </button>

          <button
            onClick={() => setFilterRisk(filterRisk === 'HIGH' ? 'ALL' : 'HIGH')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filterRisk === 'HIGH'
                ? 'bg-rose-100 text-rose-800 font-semibold'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            High Risk Only
          </button>

          {(filterRisk !== 'ALL' || filterStatus !== 'ALL' || searchQuery) && (
            <button
              onClick={() => {
                setFilterRisk('ALL');
                setFilterStatus('ALL');
                setSearchQuery('');
              }}
              className="text-xs text-slate-400 hover:text-slate-600 underline px-2 py-1"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Cases Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-teal-600 mb-3" />
            <p className="text-sm">Loading clinical cases...</p>
          </div>
        ) : filteredReviews.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <FileText className="w-10 h-10 mx-auto text-slate-300 mb-3" />
            <h3 className="font-semibold text-slate-700">No matching cases found</h3>
            <p className="text-sm mt-1">Try adjusting your search criteria or filter tags.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {filteredReviews.map((item) => {
              const isHighRisk = item.risk_level === 'HIGH';
              const isCompleted = item.status === 'COMPLETED';

              return (
                <div
                  key={item.id}
                  className="p-6 hover:bg-slate-50/70 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="font-bold text-slate-800 text-base">Case #{item.id}</span>
                      <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2.5 py-0.5 rounded-full">
                        {item.patient_id}
                      </span>
                      {isHighRisk ? (
                        <span className="inline-flex items-center space-x-1 bg-rose-100 text-rose-800 text-xs font-bold px-2.5 py-0.5 rounded-full">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-600"></span>
                          <span>HIGH RISK</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-0.5 rounded-full">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>
                          <span>{item.risk_level}</span>
                        </span>
                      )}

                      {isCompleted ? (
                        <span className="inline-flex items-center space-x-1 bg-emerald-100 text-emerald-800 text-xs font-semibold px-2 py-0.5 rounded-full">
                          <CheckCircle className="w-3 h-3" />
                          <span>REVIEWED</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 bg-sky-50 text-sky-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                          <Clock className="w-3 h-3" />
                          <span>AWAITING SIGN-OFF</span>
                        </span>
                      )}
                    </div>

                    {/* Escalation alert */}
                    {item.escalation_reasons && item.escalation_reasons.length > 0 && (
                      <div className="flex items-start space-x-2 text-rose-700 bg-rose-50/80 px-3 py-1.5 rounded-lg border border-rose-100 text-xs">
                        <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                        <span className="font-medium">{item.escalation_reasons.join(', ')}</span>
                      </div>
                    )}

                    {/* Summary snippet */}
                    <p className="text-slate-600 text-sm line-clamp-2 leading-relaxed">
                      {item.summary}
                    </p>

                    <p className="text-xs text-slate-400">
                      Logged {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>

                  <div className="flex items-center space-x-3 shrink-0 self-end md:self-center">
                    <Link
                      to={`/doctor/reviews/${item.id}`}
                      className={`inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all shadow-sm ${
                        isCompleted
                          ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                          : 'bg-teal-600 hover:bg-teal-700 text-white hover:shadow-teal-600/20'
                      }`}
                    >
                      <span>{isCompleted ? 'View Sign-Off' : 'Review Case'}</span>
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewRequests;
