"""
Integration Tests for Hospital Clinical & Receptionist Dashboard.
Validates:
1. Dashboard HTML page serving.
2. High-level system statistics and Azure service states.
3. Patient directory retrieval (Layer A: Cosmos DB).
4. Patient longitudinal health records (Layer B: Scoped RAG).
5. Receptionist verification simulator and HIPAA RBAC audit.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_dashboard_health_endpoint():
    """Verify health check returns dashboard enabled status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["hospital_dashboard"] == "enabled"


def test_dashboard_html_page_served():
    """Verify GET /dashboard returns rich HTML frontend."""
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "AuraCare Health Portal" in res.text
    assert "Hospital Dashboard" in res.text
    assert "Receptionist Inspector" in res.text


def test_dashboard_stats_endpoint():
    """Verify statistics API returns registered patients count and Azure status."""
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["registered_patients"] >= 3
    assert data["clinical_records_indexed"] >= 3
    assert "cloud_services" in data


def test_dashboard_patients_list():
    """Verify patient directory lists Indian cohort from Layer A."""
    res = client.get("/api/dashboard/patients")
    assert res.status_code == 200
    patients = res.json()
    assert len(patients) >= 3
    mrns = [p["id"] for p in patients]
    assert "P-10023" in mrns
    assert "P-10024" in mrns
    assert "P-10025" in mrns


def test_dashboard_patient_longitudinal_records():
    """Verify patient clinical records retrieve SOAP notes and labs."""
    res = client.get("/api/dashboard/patients/P-10023/records")
    assert res.status_code == 200
    data = res.json()
    assert data["patient"]["first_name"] == "Aarav"
    assert len(data["records"]) > 0
    record_types = [r["record_type"] for r in data["records"]]
    assert "soap_note" in record_types


def test_dashboard_verify_receptionist_success():
    """Verify receptionist inspector successfully validates identity."""
    payload = {
        "first_name": "Aarav",
        "last_name": "Sharma",
        "date_of_birth": "1985-04-12"
    }
    res = client.post("/api/dashboard/verify-receptionist", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["action_result"]["success"] is True
    assert data["action_result"]["data"]["patient_id"] == "P-10023"
    assert data["action_result"]["data"]["insurance_provider"] == "Star Health Comprehensive"
    assert data["hipaa_rbac_audit"]["administrative_scope_granted"] is True
    assert data["hipaa_rbac_audit"]["clinical_soap_notes_exposed"] is False


def test_dashboard_verify_receptionist_mismatch():
    """Verify receptionist inspector correctly flags unknown patient."""
    payload = {
        "first_name": "Unknown",
        "last_name": "Person",
        "date_of_birth": "1999-01-01"
    }
    res = client.post("/api/dashboard/verify-receptionist", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["action_result"]["success"] is False
    assert data["hipaa_rbac_audit"]["administrative_scope_granted"] is False


def test_dashboard_doctors_directory():
    """Verify GET /api/dashboard/doctors returns clinicians list."""
    res = client.get("/api/dashboard/doctors")
    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 3
    doc_names = [d["name"] for d in docs]
    assert "Dr. Ananya Rao" in doc_names
    assert "Dr. Rajesh Iyer" in doc_names
    assert "Dr. Sunita Kapoor" in doc_names


def test_dashboard_doctor_appointments():
    """Verify filtering appointments by doctor."""
    res = client.get("/api/dashboard/doctor/Dr.%20Ananya%20Rao/appointments")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_dashboard_patient_chart():
    """Verify comprehensive longitudinal EHR chart endpoint."""
    res = client.get("/api/dashboard/patients/P-10023/chart")
    assert res.status_code == 200
    data = res.json()
    assert data["patient"]["id"] == "P-10023"
    assert "appointments" in data
    assert "clinical_notes" in data


def test_dashboard_new_patient_registration():
    """Verify receptionist new patient onboarding assigns permanent MRN."""
    payload = {
        "first_name": "Sunil",
        "last_name": "Kumar",
        "date_of_birth": "1992-06-15",
        "phone_number": "+91-98765-99887",
        "insurance_provider": "Star Health Comprehensive",
        "insurance_policy_number": "SH-771122"
    }
    res = client.post("/api/dashboard/patients/register", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["patient"]["id"].startswith("P-")
    assert data["patient"]["first_name"] == "Sunil"


def test_dashboard_ambient_scribe_generation_and_confirmation():
    """Verify ambient AI clinical scribe note drafting and doctor confirmation gate."""
    gen_payload = {
        "transcript": "Patient Aarav Sharma complains of exertional chest pain when climbing stairs. BP 132/84, HR 76. Advised Lisinopril 20mg, ordered ECG and stress test.",
        "patient_id": "P-10023",
        "patient_name": "Aarav Sharma",
        "doctor_name": "Dr. Ananya Rao",
        "doctor_id": "DOC-01",
        "encounter_date": "2026-09-19"
    }
    res_gen = client.post("/api/dashboard/scribe/generate", json=gen_payload)
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["success"] is True
    assert "draft_note" in gen_data
    draft = gen_data["draft_note"]
    assert "subjective" in draft
    assert "objective" in draft
    assert "assessment" in draft
    assert "plan" in draft

    # Test confirmation gate
    confirm_payload = {
        "id": draft["id"],
        "patient_id": draft["patient_id"],
        "patient_name": draft["patient_name"],
        "doctor_id": draft["doctor_id"],
        "doctor_name": draft["doctor_name"],
        "date": draft["date"],
        "subjective": draft["subjective"],
        "objective": draft["objective"],
        "assessment": draft["assessment"],
        "plan": draft["plan"],
        "raw_transcript": draft["raw_transcript"],
        "status": "CONFIRMED_BY_DOCTOR"
    }
    res_conf = client.post("/api/dashboard/scribe/confirm", json=confirm_payload)
    assert res_conf.status_code == 200
    conf_data = res_conf.json()
    assert conf_data["success"] is True
    assert conf_data["note"]["status"] == "CONFIRMED_BY_DOCTOR"


def test_dashboard_notifications_endpoint():
    """Verify that /api/dashboard/notifications returns list of dispatched confirmation tickets."""
    res = client.get("/api/dashboard/notifications")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "notifications" in data
    assert isinstance(data["notifications"], list)

