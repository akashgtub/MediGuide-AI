import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Landing from './pages/Landing';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import DashboardLayout from './layouts/DashboardLayout';
import ProtectedRoute from './components/ProtectedRoute';

// Patient
import PatientDashboard from './pages/patient/PatientDashboard';
import UploadReport from './pages/patient/UploadReport';
import MyReports from './pages/patient/MyReports';
import ReportAnalysis from './pages/patient/ReportAnalysis';
import PatientAssistant from './pages/patient/PatientAssistant';
import AppointmentPrep from './pages/patient/AppointmentPrep';

// Doctor
import DoctorDashboard from './pages/doctor/DoctorDashboard';
import ReviewRequests from './pages/doctor/ReviewRequests';
import ReviewCase from './pages/doctor/ReviewCase';
import CompletedReviews from './pages/doctor/CompletedReviews';

// Admin
import AdminDashboard from './pages/admin/AdminDashboard';
import Users from './pages/admin/Users';
import Doctors from './pages/admin/Doctors';
import SystemMonitoring from './pages/admin/SystemMonitoring';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        
        {/* Patient Routes */}
        <Route path="/patient" element={<ProtectedRoute allowedRoles={['patient']}><DashboardLayout /></ProtectedRoute>}>
          <Route index element={<PatientDashboard />} />
          <Route path="upload" element={<UploadReport />} />
          <Route path="reports" element={<MyReports />} />
          <Route path="reports/:id" element={<ReportAnalysis />} />
          <Route path="assistant" element={<PatientAssistant />} />
          <Route path="appointment" element={<AppointmentPrep />} />
        </Route>

        {/* Doctor Routes */}
        <Route path="/doctor" element={<ProtectedRoute allowedRoles={['doctor']}><DashboardLayout /></ProtectedRoute>}>
          <Route index element={<DoctorDashboard />} />
          <Route path="reviews" element={<ReviewRequests />} />
          <Route path="reviews/:id" element={<ReviewCase />} />
          <Route path="completed" element={<CompletedReviews />} />
        </Route>

        {/* Admin Routes */}
        <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><DashboardLayout /></ProtectedRoute>}>
          <Route index element={<AdminDashboard />} />
          <Route path="users" element={<Users />} />
          <Route path="doctors" element={<Doctors />} />
          <Route path="monitoring" element={<SystemMonitoring />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

export default App;
