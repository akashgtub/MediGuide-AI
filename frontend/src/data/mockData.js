export const mockUsers = [
  { id: '1', name: 'Alex Morgan', role: 'patient', email: 'alex@example.com' },
  { id: '2', name: 'Dr. Sarah Wilson', role: 'doctor', email: 'sarah@example.com' },
  { id: '3', name: 'System Administrator', role: 'admin', email: 'admin@example.com' }
];

export const mockReports = [
  { id: '101', type: 'Complete Blood Count', date: '2023-10-12', status: 'Analyzed', risk: 'Low' },
  { id: '102', type: 'General Health Report', date: '2023-11-05', status: 'Review Required', risk: 'High' }
];

export const mockStats = {
  patient: { uploaded: 5, analyzed: 5, pending: 1, prep: 2 },
  doctor: { pending: 3, highPriority: 1, reviewedToday: 2, completed: 45 },
  admin: { users: 1204, doctors: 45, reports: 3400, pending: 12 }
};
