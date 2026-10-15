import { useState } from 'react';
import {
  Stethoscope,
  Search,
  Filter,
  CheckCircle,
  Clock,
  Award,
  PhoneCall,
  UserCheck,
  ShieldCheck,
  Plus,
} from 'lucide-react';

const initialDoctors = [
  {
    id: 'DOC-1',
    name: 'Dr. Sarah Wilson, MD',
    specialty: 'Cardiology',
    license: 'MED-NY-849201',
    hospital: 'Metropolitan Health Center',
    casesReviewed: 142,
    activeQueue: 2,
    status: 'Verified',
    onDuty: true,
  },
  {
    id: 'DOC-2',
    name: 'Dr. Marcus Vance, DO',
    specialty: 'General Practice',
    license: 'MED-CA-920412',
    hospital: 'Pacific Wellness Clinic',
    casesReviewed: 98,
    activeQueue: 1,
    status: 'Verified',
    onDuty: true,
  },
  {
    id: 'DOC-3',
    name: 'Dr. Elena Rostova, MD',
    specialty: 'Hematology',
    license: 'MED-IL-339102',
    hospital: 'Midwest Specialty Institute',
    casesReviewed: 65,
    activeQueue: 0,
    status: 'Verified',
    onDuty: false,
  },
  {
    id: 'DOC-4',
    name: 'Dr. James Thorne, MD',
    specialty: 'Pulmonology',
    license: 'MED-TX-774019',
    hospital: 'Memorial Respiratory Care',
    casesReviewed: 41,
    activeQueue: 1,
    status: 'Pending Verification',
    onDuty: false,
  },
];

const Doctors = () => {
  const [doctors, setDoctors] = useState(initialDoctors);
  const [specialtyFilter, setSpecialtyFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newDoctor, setNewDoctor] = useState({
    name: '',
    specialty: 'Cardiology',
    license: '',
    hospital: '',
  });

  const filteredDoctors = doctors.filter((doc) => {
    const matchesSpec = specialtyFilter === 'ALL' || doc.specialty === specialtyFilter;
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      doc.name.toLowerCase().includes(query) ||
      doc.license.toLowerCase().includes(query) ||
      doc.specialty.toLowerCase().includes(query) ||
      doc.hospital.toLowerCase().includes(query);

    return matchesSpec && matchesSearch;
  });

  const toggleOnDuty = (id) => {
    setDoctors((prev) =>
      prev.map((d) => (d.id === id ? { ...d, onDuty: !d.onDuty } : d))
    );
  };

  const handleAddDoctor = (e) => {
    e.preventDefault();
    if (!newDoctor.name || !newDoctor.license) return;

    const created = {
      id: `DOC-${Date.now()}`,
      name: newDoctor.name,
      specialty: newDoctor.specialty,
      license: newDoctor.license,
      hospital: newDoctor.hospital || 'MediGuide Affiliate Network',
      casesReviewed: 0,
      activeQueue: 0,
      status: 'Verified',
      onDuty: true,
    };

    setDoctors([created, ...doctors]);
    setNewDoctor({ name: '', specialty: 'Cardiology', license: '', hospital: '' });
    setShowAddModal(false);
  };

  const onDutyCount = doctors.filter((d) => d.onDuty).length;
  const verifiedCount = doctors.filter((d) => d.status === 'Verified').length;
  const totalReviews = doctors.reduce((acc, d) => acc + d.casesReviewed, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Clinician Registry & Credentialing</h1>
          <p className="text-slate-500 text-sm mt-1">
            Registered medical specialists, active on-call coverage, and clinical review distribution
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-medium px-4 py-2.5 rounded-xl text-sm transition-all shadow-sm hover:shadow-teal-600/20 self-start"
        >
          <Plus className="w-4 h-4" />
          <span>Credential New Clinician</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-teal-50 text-teal-600 rounded-xl">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">Total Clinicians</p>
            <p className="text-2xl font-bold text-slate-800">{doctors.length}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <CheckCircle className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">On-Duty / Active</p>
            <p className="text-2xl font-bold text-emerald-600">{onDutyCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">License Verified</p>
            <p className="text-2xl font-bold text-blue-600">{verifiedCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">Reviews Completed</p>
            <p className="text-2xl font-bold text-indigo-600">{totalReviews}</p>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search clinician name, specialty, license, or clinic..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {['ALL', 'Cardiology', 'General Practice', 'Hematology', 'Pulmonology'].map((spec) => (
            <button
              key={spec}
              onClick={() => setSpecialtyFilter(spec)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                specialtyFilter === spec
                  ? 'bg-teal-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {spec === 'ALL' ? 'All Specialties' : spec}
            </button>
          ))}
        </div>
      </div>

      {/* Clinicians Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filteredDoctors.map((doc) => {
          const initials = doc.name
            .replace('Dr. ', '')
            .split(' ')
            .map((n) => n[0])
            .join('')
            .substring(0, 2);

          return (
            <div
              key={doc.id}
              className="bg-white rounded-2xl p-6 border border-slate-100 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3.5">
                  <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-700 font-bold text-sm flex items-center justify-center border border-teal-100 shrink-0">
                    {initials}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-base">{doc.name}</h3>
                    <p className="text-teal-600 text-xs font-semibold">{doc.specialty}</p>
                    <p className="text-slate-400 text-xs mt-0.5">{doc.hospital}</p>
                  </div>
                </div>

                <span
                  className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                    doc.status === 'Verified'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  {doc.status}
                </span>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100 grid grid-cols-3 gap-2 text-center text-xs">
                <div>
                  <p className="text-slate-400 uppercase font-medium">License</p>
                  <p className="font-mono font-bold text-slate-700 mt-0.5 text-[11px] truncate">
                    {doc.license}
                  </p>
                </div>
                <div>
                  <p className="text-slate-400 uppercase font-medium">Reviewed</p>
                  <p className="font-bold text-slate-800 mt-0.5">{doc.casesReviewed}</p>
                </div>
                <div>
                  <p className="text-slate-400 uppercase font-medium">Active Queue</p>
                  <p className="font-bold text-teal-600 mt-0.5">{doc.activeQueue} cases</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-50">
                <div className="flex items-center space-x-2">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${
                      doc.onDuty ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'
                    }`}
                  ></span>
                  <span className="text-xs text-slate-600 font-medium">
                    {doc.onDuty ? 'On-Call & Active' : 'Off-Duty'}
                  </span>
                </div>

                <button
                  onClick={() => toggleOnDuty(doc.id)}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors ${
                    doc.onDuty
                      ? 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
                      : 'bg-teal-50 border-teal-200 text-teal-700 hover:bg-teal-100'
                  }`}
                >
                  {doc.onDuty ? 'Set Off-Duty' : 'Set On-Call'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b pb-3">
              <h3 className="font-bold text-slate-800 text-lg">Credential New Clinician</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddDoctor} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  Physician Full Name & Credentials
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Jennifer Wu, MD"
                  value={newDoctor.name}
                  onChange={(e) => setNewDoctor({ ...newDoctor, name: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  Primary Medical Specialty
                </label>
                <select
                  value={newDoctor.specialty}
                  onChange={(e) => setNewDoctor({ ...newDoctor, specialty: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                >
                  <option value="Cardiology">Cardiology</option>
                  <option value="General Practice">General Practice</option>
                  <option value="Hematology">Hematology</option>
                  <option value="Pulmonology">Pulmonology</option>
                  <option value="Neurology">Neurology</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  State Medical License / NPI Number
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. MED-MA-104928"
                  value={newDoctor.license}
                  onChange={(e) => setNewDoctor({ ...newDoctor, license: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  Affiliated Hospital or Clinic
                </label>
                <input
                  type="text"
                  placeholder="e.g. Boston General Hospital"
                  value={newDoctor.hospital}
                  onChange={(e) => setNewDoctor({ ...newDoctor, hospital: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 text-sm bg-teal-600 hover:bg-teal-700 text-white font-medium rounded-xl shadow-sm"
                >
                  Save Clinician
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Doctors;
