import { useState, useEffect } from 'react';
import { apiFetch } from '../../context/AuthContext';
import {
  Users as UsersIcon,
  Search,
  Filter,
  UserPlus,
  Shield,
  Stethoscope,
  User,
  CheckCircle2,
  XCircle,
  MoreVertical,
  Plus,
} from 'lucide-react';
import { mockUsers } from '../../data/mockData';

const initialUsersList = [
  ...mockUsers,
  { id: '4', name: 'Maria Gonzalez', role: 'patient', email: 'maria@example.com', status: 'Active', joined: '2026-09-12' },
  { id: '5', name: 'Dr. Marcus Vance', role: 'doctor', email: 'marcus.vance@clinic.org', status: 'Active', joined: '2026-08-01' },
  { id: '6', name: 'David Kim', role: 'patient', email: 'david.kim@example.com', status: 'Suspended', joined: '2026-07-15' },
  { id: '7', name: 'Dr. Elena Rostova', role: 'doctor', email: 'elena.r@hospital.org', status: 'Active', joined: '2026-06-20' },
];

const Users = () => {
  const [users, setUsers] = useState(initialUsersList);
  const [roleFilter, setRoleFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newUser, setNewUser] = useState({ name: '', email: '', role: 'patient' });

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const res = await apiFetch('/api/admin/users');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setUsers(data);
          }
        }
      } catch (err) {
        console.warn('Could not load users from backend API:', err);
      }
    };
    loadUsers();
  }, []);

  const filteredUsers = users.filter((u) => {
    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      u.name.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query) ||
      u.role.toLowerCase().includes(query);

    return matchesRole && matchesSearch;
  });

  const toggleStatus = async (id) => {
    const targetUser = users.find((u) => u.id === id);
    if (!targetUser) return;
    const newStatus = targetUser.status === 'Suspended' ? 'Active' : 'Suspended';

    // Optimistic update
    setUsers((prev) =>
      prev.map((u) => (u.id === id ? { ...u, status: newStatus } : u))
    );

    try {
      await apiFetch(`/api/admin/users/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
    } catch (err) {
      console.warn('Status toggle persistence error:', err);
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    if (!newUser.name || !newUser.email) return;

    try {
      const res = await apiFetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newUser.name,
          email: newUser.email,
          role: newUser.role,
          password: 'password123',
        }),
      });

      if (res.ok) {
        const created = await res.json();
        setUsers([created, ...users]);
      } else {
        const fallback = {
          id: String(Date.now()),
          name: newUser.name,
          email: newUser.email,
          role: newUser.role,
          status: 'Active',
          joined: new Date().toISOString().split('T')[0],
        };
        setUsers([fallback, ...users]);
      }
    } catch {
      const fallback = {
        id: String(Date.now()),
        name: newUser.name,
        email: newUser.email,
        role: newUser.role,
        status: 'Active',
        joined: new Date().toISOString().split('T')[0],
      };
      setUsers([fallback, ...users]);
    }

    setNewUser({ name: '', email: '', role: 'patient' });
    setShowAddModal(false);
  };

  const totalPatients = users.filter((u) => u.role === 'patient').length;
  const totalDoctors = users.filter((u) => u.role === 'doctor').length;
  const totalAdmins = users.filter((u) => u.role === 'admin').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">User Administration</h1>
          <p className="text-slate-500 text-sm mt-1">
            Manage user accounts, roles, access permissions, and account statuses
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white font-medium px-4 py-2.5 rounded-xl text-sm transition-all shadow-sm hover:shadow-teal-600/20 self-start"
        >
          <UserPlus className="w-4 h-4" />
          <span>Add New User</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-slate-100 text-slate-600 rounded-xl">
            <UsersIcon className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">Total Accounts</p>
            <p className="text-2xl font-bold text-slate-800">{users.length}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
            <User className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">Patients</p>
            <p className="text-2xl font-bold text-blue-600">{totalPatients}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-teal-50 text-teal-600 rounded-xl">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">Clinicians</p>
            <p className="text-2xl font-bold text-teal-600">{totalDoctors}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-sm flex items-center space-x-4">
          <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-slate-400 font-semibold tracking-wider">Administrators</p>
            <p className="text-2xl font-bold text-indigo-600">{totalAdmins}</p>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by name, email, or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {['ALL', 'patient', 'doctor', 'admin'].map((role) => (
            <button
              key={role}
              onClick={() => setRoleFilter(role)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-colors ${
                roleFilter === role
                  ? 'bg-teal-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {role === 'ALL' ? 'All Roles' : `${role}s`}
            </button>
          ))}
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-100 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <th className="p-4 pl-6">User</th>
                <th className="p-4">Email</th>
                <th className="p-4">Role</th>
                <th className="p-4">Status</th>
                <th className="p-4">Joined</th>
                <th className="p-4 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {filteredUsers.map((u) => {
                const isSuspended = u.status === 'Suspended';
                const initials = u.name
                  .split(' ')
                  .map((n) => n[0])
                  .join('')
                  .substring(0, 2)
                  .toUpperCase();

                return (
                  <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="p-4 pl-6 flex items-center space-x-3">
                      <div className="w-9 h-9 rounded-full bg-teal-100 text-teal-800 font-bold text-xs flex items-center justify-center shrink-0">
                        {initials}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-800">{u.name}</p>
                        <p className="text-xs text-slate-400">ID: USR-{u.id}</p>
                      </div>
                    </td>
                    <td className="p-4 text-slate-600 font-mono text-xs">{u.email}</td>
                    <td className="p-4">
                      <span
                        className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold capitalize ${
                          u.role === 'doctor'
                            ? 'bg-teal-50 text-teal-700 border border-teal-100'
                            : u.role === 'admin'
                            ? 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                            : 'bg-blue-50 text-blue-700 border border-blue-100'
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="p-4">
                      <span
                        className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          isSuspended
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {isSuspended ? (
                          <XCircle className="w-3 h-3 mr-1" />
                        ) : (
                          <CheckCircle2 className="w-3 h-3 mr-1" />
                        )}
                        <span>{u.status || 'Active'}</span>
                      </span>
                    </td>
                    <td className="p-4 text-slate-400 text-xs">{u.joined || '2026-09-01'}</td>
                    <td className="p-4 pr-6 text-right">
                      <button
                        onClick={() => toggleStatus(u.id)}
                        className={`text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors ${
                          isSuspended
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                            : 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200'
                        }`}
                      >
                        {isSuspended ? 'Activate' : 'Suspend'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex justify-between items-center border-b pb-3">
              <h3 className="font-bold text-slate-800 text-lg">Create New User</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddUser} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Robert Chen"
                  value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. robert.chen@hospital.org"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-1">
                  Role Permission
                </label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                >
                  <option value="patient">Patient</option>
                  <option value="doctor">Doctor / Clinician</option>
                  <option value="admin">System Administrator</option>
                </select>
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
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;
