import { useEffect, useState } from 'react';
import { Stethoscope, Calendar, CheckCircle2, RefreshCw, Wand2, Shield } from 'lucide-react';
import type { Appointment, Doctor, PatientRecord, SoapNote } from '../types';
import { api } from '../services/api';

interface DoctorPortalProps {
  doctors: Doctor[];
  patients: PatientRecord[];
  onRefreshData?: () => void;
}

export const DoctorPortal: React.FC<DoctorPortalProps> = ({ doctors, patients, onRefreshData }) => {
  const [selectedDoctorName, setSelectedDoctorName] = useState<string>('');
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loadingAppts, setLoadingAppts] = useState(false);

  // Scribe State
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [transcript, setTranscript] = useState<string>('');
  const [isGeneratingSoap, setIsGeneratingSoap] = useState(false);
  const [isConfirmingSoap, setIsConfirmingSoap] = useState(false);
  const [soapNote, setSoapNote] = useState<SoapNote | null>(null);
  const [confirmStatus, setConfirmStatus] = useState<string | null>(null);

  useEffect(() => {
    if (doctors.length > 0 && !selectedDoctorName) {
      setSelectedDoctorName(doctors[0].name);
    }
    if (patients.length > 0 && !selectedPatientId) {
      setSelectedPatientId(patients[0].patient_id);
    }
  }, [doctors, patients, selectedDoctorName, selectedPatientId]);

  useEffect(() => {
    if (selectedDoctorName) {
      loadDoctorAppointments(selectedDoctorName);
    }
  }, [selectedDoctorName]);

  const loadDoctorAppointments = async (docName: string) => {
    setLoadingAppts(true);
    try {
      const data = await api.getDoctorAppointments(docName);
      setAppointments(data);
    } catch (err) {
      console.error('Failed to load appointments:', err);
    } finally {
      setLoadingAppts(false);
    }
  };

  const handleLoadSampleTranscript = () => {
    setTranscript(
      'Doctor: Good morning Aarav, how have you been feeling since your last visit?\n' +
      'Patient: Good morning Doctor. I have had recurrent chest tightness and mild shortness of breath when climbing stairs.\n' +
      'Doctor: Blood pressure is 142/88 mmHg. Heart rate is 78 bpm. Lungs clear. ECG shows sinus rhythm with no acute ischemia. We will start Metoprolol 25mg daily and schedule a 2D echocardiogram.'
    );
  };

  const handleGenerateSoap = async () => {
    if (!transcript.trim()) return;
    setIsGeneratingSoap(true);
    setConfirmStatus(null);

    const pat = patients.find((p) => p.patient_id === selectedPatientId);
    const doc = doctors.find((d) => d.name === selectedDoctorName);

    try {
      const note = await api.generateSoapNote({
        transcript,
        patient_id: selectedPatientId,
        patient_name: pat ? `${pat.first_name} ${pat.last_name}` : 'Aarav Sharma',
        doctor_name: selectedDoctorName,
        doctor_id: doc?.id || 'DOC-01',
      });
      setSoapNote(note);
    } catch (err) {
      console.error('Failed to generate SOAP note:', err);
      alert('Error generating SOAP note: ' + (err as Error).message);
    } finally {
      setIsGeneratingSoap(false);
    }
  };

  const handleConfirmSoap = async () => {
    if (!soapNote) return;
    setIsConfirmingSoap(true);
    try {
      const res = await api.confirmSoapNote(soapNote);
      if (res.success) {
        setConfirmStatus('✅ Note verified & indexed to Azure AI Search & Cosmos DB.');
        if (onRefreshData) onRefreshData();
      }
    } catch (err) {
      console.error('Failed to confirm note:', err);
      alert('Failed to sign & index note: ' + (err as Error).message);
    } finally {
      setIsConfirmingSoap(false);
    }
  };

  return (
    <div>
      {/* Clinician Selector Card */}
      <div className="med-card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Stethoscope size={24} color="#0d9488" />
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Clinician Workspace</h2>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                Authenticated Role: Clinical Attending Doctor (Full Longitudinal Access)
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <label style={{ fontSize: '0.86rem', fontWeight: 600 }}>Active Doctor:</label>
            <select
              className="form-select"
              style={{ width: 'auto', minWidth: '240px' }}
              value={selectedDoctorName}
              onChange={(e) => setSelectedDoctorName(e.target.value)}
            >
              {doctors.map((d) => (
                <option key={d.id} value={d.name}>
                  {d.name} ({d.specialty})
                </option>
              ))}
            </select>
            <button className="btn-secondary" onClick={() => loadDoctorAppointments(selectedDoctorName)} title="Refresh">
              <RefreshCw size={15} />
            </button>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
        {/* Ambient AI Scribe Panel */}
        <div className="med-card">
          <div className="med-card-header">
            <div className="med-card-title">
              <Wand2 size={20} color="#0d9488" />
              <span>Ambient AI Clinical Scribe</span>
            </div>
            <button className="btn-secondary" onClick={handleLoadSampleTranscript} style={{ fontSize: '0.76rem', padding: '0.3rem 0.6rem' }}>
              Load Sample Encounter
            </button>
          </div>

          <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <label style={{ fontSize: '0.84rem', fontWeight: 600 }}>Patient Encounter:</label>
            <select
              className="form-select"
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
            >
              {patients.map((p) => (
                <option key={p.patient_id} value={p.patient_id}>
                  {p.first_name} {p.last_name} ({p.patient_id} - DOB: {p.date_of_birth})
                </option>
              ))}
            </select>
          </div>

          <label style={{ fontSize: '0.84rem', fontWeight: 600, display: 'block', marginBottom: '0.4rem' }}>
            Doctor-Patient Encounter Audio Transcript:
          </label>
          <textarea
            className="form-textarea"
            rows={5}
            placeholder="Type or paste conversation between doctor and patient here..."
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
          />

          <div style={{ marginTop: '1rem' }}>
            <button
              className="btn-primary"
              onClick={handleGenerateSoap}
              disabled={isGeneratingSoap || !transcript.trim()}
              style={{ width: '100%' }}
            >
              <Wand2 size={16} />
              {isGeneratingSoap ? 'Generating SOAP Note via GPT-4o...' : 'Generate Structured SOAP Note'}
            </button>
          </div>

          {/* Generated SOAP Note & Approval Gate */}
          {soapNote && (
            <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h4 style={{ fontWeight: 700, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Shield size={16} color="#0d9488" />
                  Doctor Approval Gate (Review & Sign)
                </h4>
                <span className="badge badge-confirmed">Draft Ready</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--teal-600)' }}>SUBJECTIVE:</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    value={soapNote.subjective}
                    onChange={(e) => setSoapNote({ ...soapNote, subjective: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--teal-600)' }}>OBJECTIVE:</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    value={soapNote.objective}
                    onChange={(e) => setSoapNote({ ...soapNote, objective: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--teal-600)' }}>ASSESSMENT:</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    value={soapNote.assessment}
                    onChange={(e) => setSoapNote({ ...soapNote, assessment: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--teal-600)' }}>PLAN:</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    value={soapNote.plan}
                    onChange={(e) => setSoapNote({ ...soapNote, plan: e.target.value })}
                  />
                </div>
              </div>

              {confirmStatus && (
                <div style={{ marginTop: '0.85rem', color: '#059669', fontSize: '0.88rem', fontWeight: 600 }}>
                  {confirmStatus}
                </div>
              )}

              <button
                className="btn-primary"
                onClick={handleConfirmSoap}
                disabled={isConfirmingSoap}
                style={{ marginTop: '1rem', width: '100%', background: 'linear-gradient(135deg, #059669, #047857)' }}
              >
                <CheckCircle2 size={16} />
                {isConfirmingSoap ? 'Indexing to Azure...' : 'Sign & Commit to Patient Health Record'}
              </button>
            </div>
          )}
        </div>

        {/* Doctor Schedule Agenda */}
        <div className="med-card">
          <div className="med-card-header">
            <div className="med-card-title">
              <Calendar size={18} color="#0d9488" />
              <span>Assigned Appointments</span>
            </div>
            <span className="badge badge-confirmed">
              {appointments.length} Total
            </span>
          </div>

          {loadingAppts ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              Loading clinician schedule...
            </div>
          ) : appointments.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              No appointments scheduled for {selectedDoctorName}.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {appointments.map((a) => (
                <div
                  key={a.id}
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: '10px',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-card-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.92rem' }}>{a.patient_name || a.patient_id}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--teal-600)', fontWeight: 600 }}>
                      {a.appointment_time}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                    📅 {a.appointment_date} | {a.specialty}
                  </div>
                  <div style={{ fontSize: '0.82rem' }}>
                    Reason: {a.reason_for_visit}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
