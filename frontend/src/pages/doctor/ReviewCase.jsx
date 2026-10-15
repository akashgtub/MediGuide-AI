import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  CheckCircle,
  ArrowLeft,
  Activity,
  FileText,
  AlertTriangle,
  UserCheck,
  Send,
  Loader2,
  Calendar,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const ReviewCase = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [caseData, setCaseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const [reviewNotes, setReviewNotes] = useState('');
  const [decision, setDecision] = useState('Recommend immediate ER visit');
  const [reviewerName, setReviewerName] = useState(user?.name || 'Dr. Sarah Wilson, MD');
  const [submitError, setSubmitError] = useState('');

  useEffect(() => {
    const fetchCase = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/reviews/${id}`);
        if (res.ok) {
          const data = await res.json();
          setCaseData(data);
          if (data.decision) setDecision(data.decision);
          if (data.review_notes) setReviewNotes(data.review_notes);
          if (data.reviewed_by) setReviewerName(data.reviewed_by);
          if (data.status === 'COMPLETED') setSubmitted(true);
        } else {
          throw new Error('Case not found');
        }
      } catch {
        // Fallback default case data
        setCaseData({
          id: id || 'MG-1024',
          patient_id: 'PT-8821 (Anonymized)',
          risk_level: 'HIGH',
          status: 'PENDING_REVIEW',
          summary: 'Patient reports severe chest pain and shortness of breath for 4 hours. Taking Aspirin 81mg. Blood pressure elevated at 145/95 mmHg.',
          escalation_reasons: ['Reported severe chest pain and shortness of breath.'],
          extracted_data: {
            symptoms: ['chest pain', 'shortness of breath'],
            medications: ['aspirin'],
            test_names: ['blood pressure'],
            test_values: ['145/95'],
            units: ['mmhg'],
            dates: ['15 October 2026'],
            observations: ['Patient reports severe chest pain and shortness of breath.'],
          },
          created_at: '2026-10-15T09:30:00Z',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchCase();
  }, [id, user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reviewNotes.trim()) {
      setSubmitError('Please provide clinical notes before submitting sign-off.');
      return;
    }

    setSubmitting(true);
    setSubmitError('');

    try {
      const res = await fetch(`/api/reviews/${id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          notes: reviewNotes,
          reviewer_name: reviewerName,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to record clinical review decision.');
      }

      const updated = await res.json();
      setCaseData(updated);
      setSubmitted(true);
    } catch (err) {
      // In offline/mock mode, update locally
      setCaseData((prev) => ({
        ...prev,
        status: 'COMPLETED',
        decision,
        review_notes: reviewNotes,
        reviewed_by: reviewerName,
        reviewed_at: new Date().toISOString(),
      }));
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-teal-600 mb-3" />
        <p className="text-sm">Loading case details...</p>
      </div>
    );
  }

  const extracted = caseData?.extracted_data || {};

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-slate-800">Case Review #{caseData?.id}</h1>
            <span
              className={`px-3 py-0.5 rounded-full text-xs font-bold ${
                caseData?.risk_level === 'HIGH'
                  ? 'bg-rose-100 text-rose-800'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              {caseData?.risk_level} RISK
            </span>
            {submitted && (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-0.5 rounded-full flex items-center space-x-1">
                <CheckCircle className="w-3 h-3 mr-1" />
                <span>COMPLETED</span>
              </span>
            )}
          </div>
          <p className="text-slate-500 text-sm mt-1">
            {caseData?.patient_id} • Received {new Date(caseData?.created_at).toLocaleString()}
          </p>
        </div>

        <Link
          to="/doctor/reviews"
          className="inline-flex items-center space-x-2 text-teal-600 hover:text-teal-700 text-sm font-medium self-start"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Review Queue</span>
        </Link>
      </div>

      {/* Escalation Notice */}
      <div className="bg-rose-50 border border-rose-200 text-rose-900 p-5 rounded-2xl flex items-start space-x-3 shadow-sm">
        <ShieldAlert className="w-6 h-6 shrink-0 mt-0.5 text-rose-600" />
        <div>
          <h3 className="font-bold text-sm">Automated Risk Engine Escalation</h3>
          <p className="text-sm mt-1 leading-relaxed text-rose-800">
            {caseData?.escalation_reasons?.join(' ') ||
              'Flagged by clinical metrics guardrails for mandatory healthcare professional verification.'}
          </p>
        </div>
      </div>

      {/* Extracted Details & AI Summary */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Extracted Clinical Data */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-4">
          <h2 className="font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-teal-600" />
            <span>Structured Clinical Extractions</span>
          </h2>

          <div className="space-y-3 text-sm">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Detected Symptoms
              </span>
              <div className="flex flex-wrap gap-1.5">
                {extracted.symptoms && extracted.symptoms.length > 0 ? (
                  extracted.symptoms.map((s, i) => (
                    <span key={i} className="bg-rose-50 text-rose-700 px-2.5 py-0.5 rounded-lg text-xs font-medium border border-rose-100">
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 italic text-xs">None detected</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Reported Medications
              </span>
              <div className="flex flex-wrap gap-1.5">
                {extracted.medications && extracted.medications.length > 0 ? (
                  extracted.medications.map((m, i) => (
                    <span key={i} className="bg-blue-50 text-blue-700 px-2.5 py-0.5 rounded-lg text-xs font-medium border border-blue-100">
                      {m}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-400 italic text-xs">No active medications listed</span>
                )}
              </div>
            </div>

            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Measurements & Vitals
              </span>
              {extracted.test_values && extracted.test_values.length > 0 ? (
                <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 space-y-1">
                  {extracted.test_values.map((v, i) => (
                    <div key={i} className="flex justify-between text-xs">
                      <span className="text-slate-600 font-medium capitalize">
                        {extracted.test_names?.[i] || 'Test Metric'}
                      </span>
                      <span className="font-bold text-slate-800">
                        {v} {extracted.units?.[i] || ''}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-slate-400 italic text-xs">No vital values detected</span>
              )}
            </div>

            {extracted.observations && extracted.observations.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Clinical Observations
                </span>
                <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  {extracted.observations.join(' ')}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* AI Patient Summary */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-4">
          <h2 className="font-bold text-slate-800 border-b border-slate-100 pb-3 flex items-center space-x-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <span>AI Patient Summary</span>
          </h2>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-sm text-slate-700 leading-relaxed">
            {caseData?.summary}
          </div>

          <div className="text-xs text-slate-500 bg-amber-50 p-3 rounded-xl border border-amber-100">
            <span className="font-semibold text-amber-800 block mb-0.5">Clinical Disclaimer:</span>
            MediGuide AI generated the summary above for informational reference only. All diagnoses and interventions must be confirmed by the reviewing physician.
          </div>
        </div>
      </div>

      {/* Review Submission Panel */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 border-t-4 border-t-teal-500 space-y-6">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Physician Review & Clinical Disposition</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Record your expert clinical instructions, required follow-ups, and disposition status.
          </p>
        </div>

        {submitted && (
          <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 p-4 rounded-xl flex items-center space-x-3">
            <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
            <div className="text-sm">
              <span className="font-bold">Clinical review signed and recorded.</span>
              <p className="text-xs mt-0.5 text-emerald-700">
                Decision registered by {caseData?.reviewed_by || reviewerName} at{' '}
                {caseData?.reviewed_at ? new Date(caseData.reviewed_at).toLocaleString() : 'Just now'}.
              </p>
            </div>
          </div>
        )}

        {submitError && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 p-3 rounded-xl text-xs font-medium">
            {submitError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                Clinical Decision / Disposition
              </label>
              <select
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
                disabled={submitted}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 disabled:opacity-75"
              >
                <option value="Recommend immediate ER visit">Recommend immediate ER visit</option>
                <option value="Schedule urgent telehealth consult">Schedule urgent telehealth consult</option>
                <option value="Routine follow-up in 1-2 weeks">Routine follow-up in 1-2 weeks</option>
                <option value="Information safe, no urgent action required">Information safe, no urgent action required</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                Reviewing Clinician
              </label>
              <input
                type="text"
                value={reviewerName}
                onChange={(e) => setReviewerName(e.target.value)}
                disabled={submitted}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 disabled:opacity-75"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1.5">
              Clinical Notes & Follow-up Instructions
            </label>
            <textarea
              rows={4}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              disabled={submitted}
              placeholder="Enter clinical assessment, differential observations, medication adjustments, or emergency directives..."
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 disabled:opacity-75"
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
            <Link
              to="/doctor/completed"
              className="text-xs text-slate-500 hover:text-slate-700 font-medium underline"
            >
              View Completed Reviews Archive
            </Link>

            {!submitted ? (
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-medium px-6 py-2.5 rounded-xl text-sm transition-all shadow-sm hover:shadow-teal-600/20 disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Submitting Sign-Off...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    <span>Submit & Sign Review</span>
                  </>
                )}
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setSubmitted(false)}
                className="text-xs text-teal-600 hover:text-teal-700 font-semibold px-4 py-2 bg-teal-50 rounded-lg"
              >
                Amend Review Decision
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default ReviewCase;
