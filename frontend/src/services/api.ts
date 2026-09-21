import type {
  Appointment,
  DashboardStats,
  Doctor,
  PatientRecord,
  SoapNote,
} from '../types';

const API_BASE = '/api/dashboard';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || errData.message || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  async getStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE}/stats`);
    return handleResponse<DashboardStats>(res);
  },

  async getDoctors(): Promise<Doctor[]> {
    const res = await fetch(`${API_BASE}/doctors`);
    return handleResponse<Doctor[]>(res);
  },

  async getDoctorAppointments(doctorName: string, targetDate?: string): Promise<Appointment[]> {
    const params = new URLSearchParams();
    if (targetDate) params.append('target_date', targetDate);
    const url = `${API_BASE}/doctor/${encodeURIComponent(doctorName)}/appointments?${params.toString()}`;
    const res = await fetch(url);
    return handleResponse<Appointment[]>(res);
  },

  async getPatients(): Promise<PatientRecord[]> {
    const res = await fetch(`${API_BASE}/patients`);
    return handleResponse<PatientRecord[]>(res);
  },

  async getPatientRecords(patientId: string): Promise<{ patient: PatientRecord; clinical_notes: SoapNote[] }> {
    const res = await fetch(`${API_BASE}/patient/${encodeURIComponent(patientId)}/records`);
    return handleResponse<{ patient: PatientRecord; clinical_notes: SoapNote[] }>(res);
  },

  async registerPatient(payload: {
    first_name: string;
    last_name: string;
    date_of_birth: string;
    phone_number: string;
  }): Promise<{ success: boolean; message: string; patient?: PatientRecord }> {
    const res = await fetch(`${API_BASE}/patients/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async getAppointments(targetDate?: string): Promise<Appointment[]> {
    const params = new URLSearchParams();
    if (targetDate) params.append('target_date', targetDate);
    const res = await fetch(`${API_BASE}/appointments?${params.toString()}`);
    return handleResponse<Appointment[]>(res);
  },

  async verifyPatient(payload: {
    first_name: string;
    last_name: string;
    date_of_birth: string;
    phone_number?: string;
  }): Promise<{ success: boolean; message: string; patient?: PatientRecord }> {
    const res = await fetch(`${API_BASE}/verify-patient`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async bookAppointment(payload: {
    patient_id: string;
    doctor_name: string;
    appointment_date: string;
    appointment_time: string;
    reason_for_visit?: string;
  }): Promise<{ success: boolean; message: string; appointment?: Appointment }> {
    const res = await fetch(`${API_BASE}/book-appointment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async cancelAppointment(appointmentId: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/cancel-appointment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appointment_id: appointmentId }),
    });
    return handleResponse(res);
  },

  async generateSoapNote(payload: {
    transcript: string;
    patient_id: string;
    patient_name: string;
    doctor_name: string;
    doctor_id?: string;
    appointment_id?: string;
    encounter_date?: string;
  }): Promise<SoapNote> {
    const res = await fetch(`${API_BASE}/scribe/generate-soap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<SoapNote>(res);
  },

  async confirmSoapNote(note: SoapNote): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/scribe/confirm-note`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(note),
    });
    return handleResponse(res);
  },
};
