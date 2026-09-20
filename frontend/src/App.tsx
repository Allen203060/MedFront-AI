import { useEffect, useState } from 'react';
import {
  Users,
  CalendarCheck,
  Stethoscope,
  PhoneCall,
  UserCheck,
  FileCheck2,
} from 'lucide-react';
import type { Appointment, DashboardStats, Doctor, PatientRecord } from './types';
import { api } from './services/api';
import { Header } from './components/Header';
import { DoctorPortal } from './components/DoctorPortal';
import { ReceptionistPortal } from './components/ReceptionistPortal';
import { PatientDirectory } from './components/PatientDirectory';
import { VoiceConsole } from './components/VoiceConsole';

export function App() {
  const [activeTab, setActiveTab] = useState<'doctor' | 'receptionist' | 'patients' | 'voice'>('doctor');
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return localStorage.getItem('medfront_dark_mode') === 'true';
  });

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  // Apply dark mode class to document.body
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
    localStorage.setItem('medfront_dark_mode', String(darkMode));
  }, [darkMode]);

  const loadData = async () => {
    try {
      const [s, d, p, a] = await Promise.all([
        api.getStats().catch(() => null),
        api.getDoctors().catch(() => []),
        api.getPatients().catch(() => []),
        api.getAppointments().catch(() => []),
      ]);
      if (s) setStats(s);
      setDoctors(d);
      setPatients(p);
      setAppointments(a);
    } catch (err) {
      console.warn('Failed to load initial hospital data:', err);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* Header with Cloud Health Pills & Theme Toggle */}
      <Header stats={stats} darkMode={darkMode} onToggleTheme={() => setDarkMode(!darkMode)} />

      {/* Top Clinical Stat Cards */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <Users size={22} />
          </div>
          <div>
            <div className="stat-value">{stats?.total_patients ?? patients.length}</div>
            <div className="stat-label">Registered Patients (MRNs)</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--emerald-600)' }}>
            <CalendarCheck size={22} />
          </div>
          <div>
            <div className="stat-value">{stats?.confirmed_appointments ?? appointments.length}</div>
            <div className="stat-label">Confirmed Appointments</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.12)', color: 'var(--blue-500)' }}>
            <Stethoscope size={22} />
          </div>
          <div>
            <div className="stat-value">{stats?.active_doctors ?? doctors.length}</div>
            <div className="stat-label">On-Duty Clinicians</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.12)', color: 'var(--amber-500)' }}>
            <FileCheck2 size={22} />
          </div>
          <div>
            <div className="stat-value">{stats?.clinical_records_indexed ?? 17}</div>
            <div className="stat-label">Indexed Knowledge & Notes</div>
          </div>
        </div>
      </div>

      {/* Role & Feature Navigation Tabs */}
      <nav className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === 'doctor' ? 'active' : ''}`}
          onClick={() => setActiveTab('doctor')}
        >
          <Stethoscope size={18} />
          <span>Doctor Portal & Scribe</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'receptionist' ? 'active' : ''}`}
          onClick={() => setActiveTab('receptionist')}
        >
          <UserCheck size={18} />
          <span>Receptionist & Schedule</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'patients' ? 'active' : ''}`}
          onClick={() => setActiveTab('patients')}
        >
          <Users size={18} />
          <span>Patient Directory</span>
        </button>

        <button
          className={`tab-btn ${activeTab === 'voice' ? 'active' : ''}`}
          onClick={() => setActiveTab('voice')}
        >
          <PhoneCall size={18} />
          <span>Aura Voice Console</span>
        </button>
      </nav>

      {/* Active Tab Views */}
      <main>
        {activeTab === 'doctor' && (
          <DoctorPortal doctors={doctors} patients={patients} onRefreshData={loadData} />
        )}

        {activeTab === 'receptionist' && (
          <ReceptionistPortal
            appointments={appointments}
            doctors={doctors}
            patients={patients}
            onRefreshData={loadData}
          />
        )}

        {activeTab === 'patients' && (
          <PatientDirectory patients={patients} />
        )}

        {activeTab === 'voice' && (
          <VoiceConsole onAppointmentBooked={loadData} />
        )}
      </main>
    </div>
  );
}

export default App;
