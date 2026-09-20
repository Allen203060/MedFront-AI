import { useState } from 'react';
import { Users, FileText, Activity, AlertCircle, Shield, X } from 'lucide-react';
import type { PatientRecord, SoapNote } from '../types';
import { api } from '../services/api';

interface PatientDirectoryProps {
  patients: PatientRecord[];
}

export const PatientDirectory: React.FC<PatientDirectoryProps> = ({ patients }) => {
  const [selectedPatient, setSelectedPatient] = useState<PatientRecord | null>(null);
  const [clinicalNotes, setClinicalNotes] = useState<SoapNote[]>([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [showChartModal, setShowChartModal] = useState(false);

  const handleOpenChart = async (patient: PatientRecord) => {
    setSelectedPatient(patient);
    setShowChartModal(true);
    setLoadingRecords(true);
    try {
      const data = await api.getPatientRecords(patient.patient_id);
      setClinicalNotes(data.clinical_notes || []);
    } catch (err) {
      console.error('Failed to load patient records:', err);
    } finally {
      setLoadingRecords(false);
    }
  };

  return (
    <div className="med-card">
      <div className="med-card-header">
        <div className="med-card-title">
          <Users size={20} color="#0d9488" />
          <span>Patient Health Records Directory (Layer A + Scoped RAG)</span>
        </div>
        <span className="badge badge-confirmed">{patients.length} Active Records</span>
      </div>

      <div className="custom-table-container">
        <table className="med-table">
          <thead>
            <tr>
              <th>MRN (ID)</th>
              <th>Full Name</th>
              <th>Date of Birth</th>
              <th>Phone</th>
              <th>Insurance Provider</th>
              <th>Active Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.patient_id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--teal-600)' }}>
                  {p.patient_id}
                </td>
                <td style={{ fontWeight: 600 }}>
                  {p.first_name} {p.last_name}
                </td>
                <td>{p.date_of_birth}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{p.phone_number || '--'}</td>
                <td>{p.insurance_provider || 'Self-Pay'}</td>
                <td>
                  <span className="badge badge-confirmed">🟢 Active Patient</span>
                </td>
                <td>
                  <button
                    className="btn-secondary"
                    style={{ fontSize: '0.76rem', padding: '0.3rem 0.65rem' }}
                    onClick={() => handleOpenChart(p)}
                  >
                    <FileText size={13} style={{ marginRight: '4px' }} /> Longitudinal Chart
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Longitudinal Patient Chart Modal */}
      {showChartModal && selectedPatient && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '750px' }}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Shield size={20} color="#0d9488" />
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>
                  Patient Chart: {selectedPatient.first_name} {selectedPatient.last_name}
                </h3>
              </div>
              <button className="modal-close-btn" onClick={() => setShowChartModal(false)}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div style={{ background: 'var(--bg-card-subtle)', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>MRN:</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{selectedPatient.patient_id}</div>
              </div>
              <div style={{ background: 'var(--bg-card-subtle)', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>DOB:</div>
                <div style={{ fontWeight: 600 }}>{selectedPatient.date_of_birth}</div>
              </div>
              <div style={{ background: 'var(--bg-card-subtle)', padding: '0.75rem', borderRadius: '8px' }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Phone:</div>
                <div style={{ fontFamily: 'var(--font-mono)' }}>{selectedPatient.phone_number}</div>
              </div>
            </div>

            {/* Conditions & Allergies */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '1rem' }}>
                <div style={{ fontSize: '0.84rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Activity size={15} color="#0d9488" /> Active Diagnoses
                </div>
                {selectedPatient.active_conditions && selectedPatient.active_conditions.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {selectedPatient.active_conditions.map((c, i) => (
                      <span key={i} className="badge badge-pending" style={{ fontSize: '0.72rem' }}>
                        {c}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No chronic conditions recorded.</div>
                )}
              </div>

              <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '1rem' }}>
                <div style={{ fontSize: '0.84rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <AlertCircle size={15} color="#e11d48" /> Allergies
                </div>
                {selectedPatient.allergies && selectedPatient.allergies.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {selectedPatient.allergies.map((a, i) => (
                      <span key={i} className="badge badge-cancelled" style={{ fontSize: '0.72rem' }}>
                        {a}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No known allergies (NKDA).</div>
                )}
              </div>
            </div>

            {/* Historical Encounters & Scoped Notes */}
            <h4 style={{ fontSize: '0.98rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <FileText size={16} color="#0d9488" />
              Longitudinal Clinical Encounters & SOAP Notes
            </h4>

            {loadingRecords ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
                Querying Scoped Azure AI Search & Cosmos DB records...
              </div>
            ) : clinicalNotes.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', background: 'var(--bg-card-subtle)', borderRadius: '8px' }}>
                No past clinical notes recorded for this patient.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {clinicalNotes.map((n) => (
                  <div
                    key={n.id}
                    style={{
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '10px',
                      padding: '1rem',
                      background: 'var(--bg-card-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.88rem' }}>{n.doctor_name}</span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        📅 {n.date}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.82rem', marginBottom: '0.25rem' }}>
                      <strong>S:</strong> {n.subjective}
                    </div>
                    <div style={{ fontSize: '0.82rem', marginBottom: '0.25rem' }}>
                      <strong>O:</strong> {n.objective}
                    </div>
                    <div style={{ fontSize: '0.82rem', marginBottom: '0.25rem' }}>
                      <strong>A:</strong> {n.assessment}
                    </div>
                    <div style={{ fontSize: '0.82rem' }}>
                      <strong>P:</strong> {n.plan}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
