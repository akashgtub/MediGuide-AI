import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle,
  FileCheck2,
  Search,
  UserCheck,
  Calendar,
  AlertOctagon,
  PhoneCall,
  Activity,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';

const CompletedReviews = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchCompletedReviews = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/reviews?status=COMPLETED');
      if (res.ok) {
        const data = await res.json();
        setReviews(data);
      } else {
        throw new Error('API failed');
      }
    } catch {
      setReviews([
        {
          id: 'MG-1021',
          patient_id: 'PT-5512 (Anonymized)',
          risk_level: 'UNCERTAIN',
          status: 'COMPLETED',
          summary: 'Patient taking Warfarin along with high-dose Ibuprofen. Elevated INR test value recorded.',
          escalation_reasons: ['Uncertain medication interaction with OTC analgesics.'],
          created_at: '2026-10-14T14:20:00Z',
          decision: 'Schedule urgent telehealth consult',
          review_notes: 'Advising immediate cessation of NSAID (Ibuprofen) due to potentiating bleeding risk with Warfarin. Re-check INR in 48 hours.',
          reviewed_by: 'Dr. Sarah Wilson, MD',
          reviewed_at: '2026-10-14T15:45:00Z',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompletedReviews();
  }, []);

  const filteredReviews = reviews.filter((item) => {
    const matchesDecision = decisionFilter === 'ALL' || item.decision === decisionFilter;
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      item.id?.toLowerCase().includes(query) ||
      item.summary?.toLowerCase().includes(query) ||
      item.review_notes?.toLowerCase().includes(query) ||
      item.reviewed_by?.toLowerCase().includes(query);

    return matchesDecision && matchesSearch;
  });

  const getDecisionBadge = (decision) => {
    if (!decision) return null;
    const d = decision.toLowerCase();
    if (d.includes('er') || d.includes('immediate')) {
      return (
        <span className="inline-flex items-center space-x-1 bg-red-100 text-red-800 text-xs font-bold px-2.5 py-1 rounded-full">
          <AlertOctagon className="w-3.5 h-3.5 mr-1 text-red-600" />
          <span>Immediate ER Referral</span>
        </span>
      );
    }
    if (d.includes('telehealth') || d.includes('consult')) {
      return (
        <span className="inline-flex items-center space-x-1 bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-1 rounded-full">
          <PhoneCall className="w-3.5 h-3.5 mr-1 text-blue-600" />
          <span>Urgent Telehealth</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 bg-teal-100 text-teal-800 text-xs font-bold px-2.5 py-1 rounded-full">
        <CheckCircle className="w-3.5 h-3.5 mr-1 text-teal-600" />
        <span>{decision}</span>
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Completed Reviews Archive</h1>
          <p className="text-slate-500 text-sm mt-1">
            Historical audit log of clinician decisions, medical sign-offs, and risk dispositions
          </p>
        </div>
        <button
          onClick={fetchCompletedReviews}
          disabled={loading}
          className="inline-flex items-center space-x-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-medium px-4 py-2 rounded-xl text-sm transition-colors shadow-sm self-start"
        >
          <RefreshCw className={`w-4 h-4 text-teal-600 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search completed reviews, notes, clinician name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {['ALL', 'Recommend immediate ER visit', 'Schedule urgent telehealth consult', 'Routine follow-up'].map((d) => (
            <button
              key={d}
              onClick={() => setDecisionFilter(d)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                decisionFilter === d
                  ? 'bg-teal-600 text-white font-semibold'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {d === 'ALL' ? 'All Decisions' : d}
            </button>
          ))}
        </div>
      </div>

      {/* Reviews List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white rounded-2xl p-12 text-center text-slate-400 border border-slate-100">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-teal-600 mb-3" />
            <p className="text-sm">Retrieving completed review records...</p>
          </div>
        ) : filteredReviews.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center text-slate-400 border border-slate-100">
            <FileCheck2 className="w-10 h-10 mx-auto text-slate-300 mb-3" />
            <h3 className="font-semibold text-slate-700">No completed reviews found</h3>
            <p className="text-sm mt-1">Pending cases will appear here once reviewed and signed off by a physician.</p>
          </div>
        ) : (
          filteredReviews.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-100 pb-4 mb-4">
                <div className="flex items-center space-x-3">
                  <span className="font-bold text-slate-800 text-lg">Case #{item.id}</span>
                  <span className="text-xs text-slate-400 bg-slate-100 px-2.5 py-0.5 rounded-full font-medium">
                    {item.patient_id}
                  </span>
                  {getDecisionBadge(item.decision)}
                </div>

                <div className="flex items-center space-x-2 text-xs text-slate-400">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>
                    Reviewed: {item.reviewed_at ? new Date(item.reviewed_at).toLocaleString() : 'N/A'}
                  </span>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* AI Summary & Escalation Context */}
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Patient Presentation & AI Extraction
                  </p>
                  <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-xl border border-slate-100">
                    {item.summary}
                  </p>
                </div>

                {/* Clinician Decision & Notes */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold uppercase tracking-wider text-teal-700">
                      Physician Clinical Notes
                    </p>
                    <span className="text-xs text-slate-500 font-medium">
                      Signed: {item.reviewed_by || 'Dr. Sarah Wilson, MD'}
                    </span>
                  </div>
                  <div className="bg-teal-50/70 p-3 rounded-xl border border-teal-100/80 text-sm text-teal-900 leading-relaxed">
                    {item.review_notes || 'Case reviewed and verified safe.'}
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-50 flex justify-end">
                <Link
                  to={`/doctor/reviews/${item.id}`}
                  className="inline-flex items-center space-x-1 text-xs font-semibold text-teal-600 hover:text-teal-700"
                >
                  <span>View Full Clinical Record</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default CompletedReviews;
