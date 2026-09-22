export interface Doctor {
  id: string;
  name: string;
  specialty: string;
  room?: string;
  experience?: string;
  qualification?: string;
  languages?: string[];
  available_days?: string[];
}

export interface Appointment {
  id: string;
  patient_id: string;
  patient_name?: string;
  doctor_id: string;
  doctor_name: string;
  specialty: string;
  appointment_date: string;
  appointment_time: string;
  reason_for_visit: string;
  status: 'CONFIRMED' | 'CANCELLED' | 'COMPLETED' | 'PENDING';
  phone_number?: string;
  created_at?: string;
}

export interface PatientRecord {
  patient_id: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone_number: string;
  email?: string;
  blood_group?: string;
  emergency_contact?: string;
  allergies?: string[];
  active_conditions?: string[];
  medications?: string[];
  insurance_provider?: string;
  policy_number?: string;
  address?: string;
}

export interface TestReport {
  id: string;
  patient_id: string;
  patient_name: string;
  test_name: string;
  test_date: string;
  result_summary: string;
  doctor_id: string;
  doctor_name: string;
  status: string;
  created_at?: string;
}

export interface VisitSummary {
  id: string;
  patient_id: string;
  doctor_name: string;
  visit_date: string;
  reason_for_visit: string;
  diagnosis: string;
  prescriptions: string[];
  follow_up_instructions: string;
  created_at?: string;
}

export interface SoapNote {
  id: string;
  patient_id: string;
  patient_name: string;
  doctor_id: string;
  doctor_name: string;
  appointment_id?: string;
  date: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  raw_transcript?: string;
  status?: string;
}

export interface CloudServices {
  cosmos_db: string;
  azure_ai_search: string;
  azure_openai: string;
  rag_mode: string;
}

export interface DashboardStats {
  registered_patients: number;
  total_patients: number;
  total_appointments: number;
  confirmed_appointments: number;
  doctors_count: number;
  active_doctors: number;
  clinical_records_indexed: number;
  cloud_services: CloudServices;
  clinic_name: string;
}

export interface VoiceMessage {
  id: string;
  sender: 'caller' | 'aura' | 'system';
  text: string;
  timestamp: string;
  intent?: string;
  tool?: string;
}

export interface RecognizedPatient {
  patient_id: string;
  name: string;
  phone: string;
  upcoming_doctor?: string | null;
  appointment_date?: string | null;
  appointment_time?: string | null;
}
