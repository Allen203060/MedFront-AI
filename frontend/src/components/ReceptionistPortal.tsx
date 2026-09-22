import { useState } from 'react';
import { CalendarPlus, Search, UserCheck, Trash2 } from 'lucide-react';
import type { Appointment, Doctor, PatientRecord } from '../types';
import { api } from '../services/api';

interface ReceptionistPortalProps {
  appointments: Appointment[];
  doctors: Doctor[];
  patients: PatientRecord[];
  onRefreshData: () => void;
}

export const ReceptionistPortal: React.FC<ReceptionistPortalProps> = ({
  appointments,
  doctors,
  patients,
  onRefreshData,
}) => {
  // Identity Simulator State
  const [verifyFirst, setVerifyFirst] = useState('Aarav');
  const [verifyLast, setVerifyLast] = useState('Sharma');
  const [verifyDob, setVerifyDob] = useState('1985-05-15');
  const [verifyPhone, setVerifyPhone] = useState('9876543210');
  const [verifyResult, setVerifyResult] = useState<{ success: boolean; message: string; patient?: PatientRecord } | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);

  // Booking Form State
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [bookPatId, setBookPatId] = useState(patients[0]?.patient_id || 'P-10023');
  const [bookDocName, setBookDocName] = useState(doctors[0]?.name || 'Dr. Ananya Rao');
  const [bookDate, setBookDate] = useState(new Date().toISOString().split('T')[0]);
  const [bookTime, setBookTime] = useState('10:00 AM');
  const [bookReason, setBookReason] = useState('General Consultation');
  const [isBooking, setIsBooking] = useState(false);

  // Table Search Filter
  const [searchQuery, setSearchQuery] = useState('');

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsVerifying(true);
    setVerifyResult(null);
    try {
      const res = await api.verifyPatient({
        first_name: verifyFirst,
        last_name: verifyLast,
        date_of_birth: verifyDob,
        phone_number: verifyPhone,
      });
      setVerifyResult(res);
    } catch (err) {
      setVerifyResult({
        success: false,
        message: (err as Error).message,
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsBooking(true);
    try {
      const res = await api.bookAppointment({
        patient_id: bookPatId,
        doctor_name: bookDocName,
        appointment_date: bookDate,
        appointment_time: bookTime,
        reason_for_visit: bookReason,
      });
      if (res.success) {
        alert(`✅ Appointment Confirmed! Ticket ID: ${res.appointment?.id}`);
        setShowBookingModal(false);
        onRefreshData();
      }
    } catch (err) {
      alert('Booking failed: ' + (err as Error).message);
    } finally {
      setIsBooking(false);
    }
  };

  const handleCancel = async (appointmentId: string) => {
    if (!window.confirm(`Are you sure you want to cancel appointment ${appointmentId}?`)) return;
    try {
      await api.cancelAppointment(appointmentId);
      onRefreshData();
    } catch (err) {
      alert('Failed to cancel appointment: ' + (err as Error).message);
    }
  };

  const filteredAppointments = appointments.filter((a) => {
    if (a.status === 'CANCELLED') return false;
    const q = searchQuery.toLowerCase();
    return (
      (a.patient_name || '').toLowerCase().includes(q) ||
      (a.patient_id || '').toLowerCase().includes(q) ||
      (a.doctor_name || '').toLowerCase().includes(q) ||
      (a.reason_for_visit || '').toLowerCase().includes(q)
    );
  });

  return (
    <div>
      {/* Top Receptionist Panels: Verification & Quick Booking */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Verification Simulator */}
        <div className="med-card" style={{ margin: 0 }}>
          <div className="med-card-header">
            <div className="med-card-title">
              <UserCheck size={20} color="#0d9488" />
              <span>Identity Verification Simulator (HIPAA)</span>
            </div>
            <span className="badge badge-confirmed">Strict Two-Factor</span>
          </div>

          <form onSubmit={handleVerify} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 600 }}>First Name:</label>
              <input
                type="text"
                className="form-input"
                value={verifyFirst}
                onChange={(e) => setVerifyFirst(e.target.value)}
                required
              />
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 600 }}>Last Name:</label>
              <input
                type="text"
                className="form-input"
                value={verifyLast}
                onChange={(e) => setVerifyLast(e.target.value)}
                required
              />
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 600 }}>Date of Birth (YYYY-MM-DD):</label>
              <input
                type="date"
                className="form-input"
                value={verifyDob}
                onChange={(e) => setVerifyDob(e.target.value)}
                required
              />
            </div>
            <div>
              <label style={{ fontSize: '0.78rem', fontWeight: 600 }}>Phone Number:</label>
              <input
                type="tel"
                className="form-input"
                value={verifyPhone}
                onChange={(e) => setVerifyPhone(e.target.value)}
              />
            </div>

            <div style={{ gridColumn: 'span 2', marginTop: '0.25rem' }}>
              <button type="submit" className="btn-primary" style={{ width: '100%' }} disabled={isVerifying}>
                {isVerifying ? 'Searching Cosmos DB...' : 'Verify Identity in Layer A'}
              </button>
            </div>
          </form>

          {verifyResult && (
            <div
              style={{
                marginTop: '1rem',
                padding: '0.85rem',
                borderRadius: '8px',
                background: verifyResult.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
                border: `1px solid ${verifyResult.success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
              }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: verifyResult.success ? '#059669' : '#e11d48' }}>
                {verifyResult.success ? '🟢 Identity Verified Successfully' : '🔴 Identity Not Found'}
              </div>
              <div style={{ fontSize: '0.82rem', marginTop: '0.25rem' }}>{verifyResult.message}</div>
              {verifyResult.patient && (
                <div style={{ fontSize: '0.8rem', marginTop: '0.4rem', fontFamily: 'var(--font-mono)' }}>
                  MRN: {verifyResult.patient.patient_id} | Insurance: {verifyResult.patient.insurance_provider || 'Self-Pay'}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Quick Action Card */}
        <div className="med-card" style={{ margin: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
          <div style={{ width: '60px', height: '60px', borderRadius: '50%', background: 'rgba(13, 148, 136, 0.12)', color: '#0d9488', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
            <CalendarPlus size={32} />
          </div>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.5rem' }}>Direct In-Person Appointment Booking</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem', maxWidth: '360px' }}>
            Book clinical slots across the 9:00 AM to 9:00 PM operating spectrum directly into Azure Cosmos DB.
          </p>
          <button className="btn-primary" onClick={() => setShowBookingModal(true)}>
            <CalendarPlus size={16} /> Open Booking Modal
          </button>
        </div>
      </div>

      {/* Master Appointments Table */}
      <div className="med-card">
        <div className="med-card-header">
          <div className="med-card-title">
            <span>Master Appointments Registry</span>
            <span className="badge badge-confirmed">{filteredAppointments.length} Active</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: '320px' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search size={15} style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }} />
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '32px' }}
                placeholder="Search MRN, patient, doctor, reason..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="custom-table-container">
          <table className="med-table">
            <thead>
              <tr>
                <th>Ticket / ID</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Specialty</th>
                <th>Date & Time</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredAppointments.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No appointments matching search criteria.
                  </td>
                </tr>
              ) : (
                filteredAppointments.map((a) => (
                  <tr key={a.id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--teal-600)' }}>
                      {a.id}
                    </td>
                    <td style={{ fontWeight: 600 }}>{a.patient_name || a.patient_id}</td>
                    <td>{a.doctor_name}</td>
                    <td>{a.specialty}</td>
                    <td>
                      {a.appointment_date}{' '}
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--teal-600)' }}>
                        {a.appointment_time}
                      </span>
                    </td>
                    <td>{a.reason_for_visit}</td>
                    <td>
                      <span className={`badge ${a.status === 'CONFIRMED' ? 'badge-confirmed' : 'badge-cancelled'}`}>
                        {a.status}
                      </span>
                    </td>
                    <td>
                      {a.status === 'CONFIRMED' && (
                        <button
                          className="btn-danger"
                          onClick={() => handleCancel(a.id)}
                          title="Cancel appointment"
                        >
                          <Trash2 size={13} style={{ marginRight: '4px' }} /> Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Booking Modal */}
      {showBookingModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Direct Clinical Appointment Booking</h3>
              <button className="modal-close-btn" onClick={() => setShowBookingModal(false)}>
                ✕
              </button>
            </div>

            <form onSubmit={handleBook} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>Patient MRN:</label>
                <select
                  className="form-select"
                  value={bookPatId}
                  onChange={(e) => setBookPatId(e.target.value)}
                >
                  {patients.map((p) => (
                    <option key={p.patient_id} value={p.patient_id}>
                      {p.first_name} {p.last_name} ({p.patient_id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>Attending Clinician:</label>
                <select
                  className="form-select"
                  value={bookDocName}
                  onChange={(e) => setBookDocName(e.target.value)}
                >
                  {doctors.map((d) => (
                    <option key={d.id} value={d.name}>
                      {d.name} ({d.specialty})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>Date:</label>
                  <input
                    type="date"
                    className="form-input"
                    value={bookDate}
                    onChange={(e) => setBookDate(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>Time Slot (9 AM - 9 PM):</label>
                  <select
                    className="form-select"
                    value={bookTime}
                    onChange={(e) => setBookTime(e.target.value)}
                  >
                    <option value="09:00 AM">09:00 AM</option>
                    <option value="10:00 AM">10:00 AM</option>
                    <option value="11:30 AM">11:30 AM</option>
                    <option value="01:00 PM">01:00 PM</option>
                    <option value="02:30 PM">02:30 PM</option>
                    <option value="04:00 PM">04:00 PM</option>
                    <option value="05:30 PM">05:30 PM</option>
                    <option value="07:00 PM">07:00 PM</option>
                    <option value="08:30 PM">08:30 PM</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', fontWeight: 600 }}>Reason for Consultation:</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Right knee pain, Hypertension checkup"
                  value={bookReason}
                  onChange={(e) => setBookReason(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowBookingModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isBooking}>
                  {isBooking ? 'Securing Slot in Cosmos DB...' : 'Confirm Booking'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
