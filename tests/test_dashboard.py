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
