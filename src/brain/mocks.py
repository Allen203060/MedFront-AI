"""
Mock implementations of RAG and Tool interfaces for standalone Brain testing.
"""

from src.brain.interfaces import RAGProviderInterface, ToolRegistryInterface
from src.brain.models import RAGRequest, RAGResponse, ToolCallRequest, ToolCallResult
from src.brain.taxonomy import ToolName


class MockRAGProvider(RAGProviderInterface):
    """
    Mock RAG Provider simulating clinic policy FAQs and patient record retrieval.
    """
    def query(self, request: RAGRequest) -> RAGResponse:
        query_lower = request.query_text.lower()

        # 1. Simulated Clinic FAQ Search
        if request.index_target == "clinic_faq":
            if "hour" in query_lower or "open" in query_lower:
                return RAGResponse(
                    success=True,
                    retrieved_chunks=["MedFront Clinic is open Monday to Friday, 8:00 AM to 6:00 PM, and Saturday 9:00 AM to 1:00 PM."],
                    sources=["clinic_policy_faq.pdf#page=1"]
                )
            if "insurance" in query_lower or "medicare" in query_lower:
                return RAGResponse(
                    success=True,
                    retrieved_chunks=["We accept Aetna, Blue Cross Blue Shield, Medicare, and UnitedHealthcare."],
                    sources=["clinic_policy_faq.pdf#page=3"]
                )
            return RAGResponse(
                success=True,
                retrieved_chunks=["MedFront offers primary care, cardiology checkups, and outpatient services."],
                sources=["clinic_policy_faq.pdf#page=1"]
            )

        # 2. Simulated Scoped Patient Record Search
        if request.index_target == "patient_records":
            if not request.patient_id:
                return RAGResponse(
                    success=False,
                    error_message="Access Denied: Unverified patient_id required for patient record lookup."
                )
            return RAGResponse(
                success=True,
                retrieved_chunks=[f"Patient {request.patient_id} past visit note: Patient completed routine annual physical on 2025-11-10. All vitals normal."],
                sources=[f"patient_{request.patient_id}_records.json"]
            )

        return RAGResponse(success=False, error_message=f"Unknown index target: {request.index_target}")


class MockToolRegistry(ToolRegistryInterface):
    """
    Mock Tool Registry simulating appointment booking, availability checks, and cancellation.
    """
    def execute_tool(self, request: ToolCallRequest) -> ToolCallResult:
        params = request.parameters

        if request.tool_name == ToolName.CHECK_AVAILABILITY:
            doctor = params.get("doctor", "any available doctor")
            date = params.get("date", "tomorrow")
            return ToolCallResult(
                success=True,
                output_data={"available_slots": ["09:00 AM", "02:00 PM", "04:30 PM"]},
                user_message=f"Open slots for {doctor} on {date}: 9:00 AM, 2:00 PM, and 4:30 PM."
            )

        if request.tool_name == ToolName.BOOK_APPOINTMENT:
            doctor = params.get("doctor", "Dr. Smith")
            date = params.get("date", "tomorrow")
            time = params.get("time", "02:00 PM")
            return ToolCallResult(
                success=True,
                output_data={"appointment_id": "APPT-99823", "status": "CONFIRMED"},
                user_message=f"Successfully booked appointment with {doctor} for {date} at {time}. Confirmation ID: APPT-99823."
            )

        if request.tool_name == ToolName.CANCEL_APPOINTMENT:
            return ToolCallResult(
                success=True,
                output_data={"status": "CANCELLED"},
                user_message="Your appointment has been successfully cancelled."
            )

        if request.tool_name == ToolName.VERIFY_PATIENT_IDENTITY:
            name = params.get("full_name", "Unknown")
            return ToolCallResult(
                success=True,
                output_data={"patient_id": "P-88214", "verified": True},
                user_message=f"Patient {name} identity verified. Assigned patient_id: P-88214."
            )

        return ToolCallResult(success=False, error_message=f"Unsupported tool: {request.tool_name}")
