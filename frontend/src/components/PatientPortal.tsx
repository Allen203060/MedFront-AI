import React, { useState, useEffect } from 'react';
import { CalendarCheck, FileText, FlaskConical, PhoneCall } from 'lucide-react';
import { VoiceConsole } from './VoiceConsole';
import type { Appointment, TestReport, VisitSummary, PatientRecord } from '../types';
import { api } from '../services/api';

interface PatientPortalProps {
  patientId: string;
  onLogout: () => void;
}

export const PatientPortal: React.FC<PatientPortalProps> = ({ patientId, onLogout }) => {
  const [patientData, setPatientData] = useState<PatientRecord | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [testReports, setTestReports] = useState<TestReport[]>([]);
  const [visitSummaries, setVisitSummaries] = useState<VisitSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showVoiceConsole, setShowVoiceConsole] = useState(false);

  const loadPatientData = async (id: string) => {
    try {
      const appts = await api.getAppointments();
      setAppointments(appts.filter(a => a.patient_id === id));
      
      try {
        const [reports, summaries] = await Promise.all([
          (api as any).getTestReports ? (api as any).getTestReports(id) : Promise.resolve([]),
          (api as any).getVisitSummaries ? (api as any).getVisitSummaries(id) : Promise.resolve([])
        ]);
        setTestReports(reports);
        setVisitSummaries(summaries);
      } catch (e) {
        console.warn('Could not load reports or summaries', e);
      }
      
    } catch (err) {
      console.error('Failed to load patient data:', err);
    }
  };

  useEffect(() => {
    const fetchPatientData = async () => {
      setLoading(true);
      try {
        const patients = await api.getPatients();
        const patient = patients.find(p => (p as any).id === patientId || (p as any).id === `P-${patientId}` || p.patient_id === patientId || p.patient_id === `P-${patientId}`);
        if (patient) {
          setPatientData(patient);
          await loadPatientData((patient as any).id || patient.patient_id);
        }
      } catch (err) {
        console.error('Failed to load patient data:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPatientData();
  }, [patientId]);

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading your portal...</div>;
  }

  return (
    <div className="patient-portal" style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ color: 'var(--text-color)' }}>Welcome, {patientData?.first_name} {patientData?.last_name}</h1>
          <p style={{ color: 'var(--text-secondary)' }}>MRN: {(patientData as any)?.id || patientData?.patient_id}</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button 
            onClick={() => setShowVoiceConsole(!showVoiceConsole)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', background: 'var(--brand-primary)', border: 'none', borderRadius: '6px', cursor: 'pointer', color: 'white', fontWeight: 600 }}
          >
            <PhoneCall size={16} />
            {showVoiceConsole ? 'Back to Portal' : 'Call Receptionist'}
          </button>
          <button 
            onClick={onLogout}
            style={{ padding: '0.5rem 1rem', background: 'var(--surface-color)', border: '1px solid var(--border-color)', borderRadius: '6px', cursor: 'pointer', color: 'var(--text-color)' }}
          >
            Sign Out
          </button>
        </div>
      </div>

      {showVoiceConsole ? (
        <div style={{ marginTop: '2rem' }}>
          <VoiceConsole onAppointmentBooked={() => patientData && loadPatientData((patientData as any).id || patientData.patient_id)} />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
        {/* Appointments Section */}
        <div className="portal-card" style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-color)', marginBottom: '1rem' }}>
            <CalendarCheck size={20} color="var(--brand-primary)" />
            Upcoming Appointments
          </h3>
          {appointments.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {appointments.filter(a => a.status === 'CONFIRMED').map(appt => (
                <li key={appt.id} style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontWeight: 500, color: 'var(--text-color)' }}>{appt.doctor_name}</div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{appt.specialty}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 500, color: 'var(--brand-primary)' }}>{appt.appointment_date}</div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{appt.appointment_time}</div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No upcoming appointments scheduled.</p>
          )}
        </div>

        {/* Test Reports Section */}
        <div className="portal-card" style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-color)', marginBottom: '1rem' }}>
            <FlaskConical size={20} color="var(--purple-500)" />
            Lab & Test Reports
          </h3>
          {testReports.length > 0 ? (
             <ul style={{ listStyle: 'none', padding: 0 }}>
             {testReports.map(report => (
               <li key={report.id} style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)' }}>
                 <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                   <span style={{ fontWeight: 500, color: 'var(--text-color)' }}>{report.test_name}</span>
                   <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{report.test_date}</span>
                 </div>
                 <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}>{report.result_summary}</p>
                 <div style={{ fontSize: '0.8rem', color: 'var(--brand-primary)', marginTop: '0.5rem' }}>Ordered by: {report.doctor_name} ({report.status})</div>
               </li>
             ))}
           </ul>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No recent test reports available.</p>
          )}
        </div>

        {/* Visit Summaries Section */}
        <div className="portal-card" style={{ background: 'var(--surface-color)', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-color)', marginBottom: '1rem' }}>
            <FileText size={20} color="var(--emerald-500)" />
            Visit Summaries
          </h3>
          {visitSummaries.length > 0 ? (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {visitSummaries.map(summary => (
                <li key={summary.id} style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 500, color: 'var(--text-color)' }}>Visit with {summary.doctor_name}</span>
                    <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{summary.visit_date}</span>
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-color)', margin: '0 0 0.5rem 0' }}><strong>Diagnosis:</strong> {summary.diagnosis}</p>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0 }}><strong>Plan:</strong> {summary.follow_up_instructions}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No visit summaries available.</p>
          )}
        </div>
      </div>
      )}
    </div>
  );
};
