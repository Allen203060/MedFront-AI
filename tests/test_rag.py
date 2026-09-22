"""
Comprehensive Verification Tests for MedFront Module 4: Knowledge Base & RAG.
Tests chunking, dual-mode vector search, HIPAA patient isolation, and Brain tool execution.
"""

import pytest
from src.rag.chunker import DocumentChunker
from src.rag.embeddings import LocalDeterministicEmbeddings
from src.rag.store import LocalVectorStore, cosine_similarity
from src.rag.engine import RAGEngine
from src.rag.ingest import run_ingestion
from src.rag.tools import execute_rag_tool


@pytest.fixture(scope="session", autouse=True)
def setup_ingested_knowledge():
    """Ensure sample knowledge is ingested before tests run."""
    run_ingestion(target="local")


class TestRAGPipeline:

    def test_chunking_markdown_preserves_context(self):
        sample_md = """# General Clinic Rules
## Hours
We are open Monday to Friday 9am to 5pm.
## Parking
Parking is validated on the 2nd floor.
"""
        chunker = DocumentChunker()
        chunks = chunker.chunk_markdown(sample_md, source="test.md", category="clinic_policy")
        
        assert len(chunks) == 2
        assert "General Clinic Rules" in chunks[0].text
        assert "Hours" in chunks[0].text
        assert chunks[0].metadata.category == "clinic_policy"

    def test_chunking_patient_records_metadata(self):
        sample_records = [
            {
                "patient_id": "P-9999",
                "patient_name": "Test Subject",
                "record_type": "soap_note",
                "timestamp": "2025-01-01T00:00:00Z",
                "content": "Patient reports no issues."
            }
        ]
        chunker = DocumentChunker()
        chunks = chunker.chunk_patient_records(sample_records, source="test.json")
        
        assert len(chunks) == 1
        assert chunks[0].metadata.patient_id == "P-9999"
        assert chunks[0].metadata.category == "patient_record"
        assert "P-9999" in chunks[0].text

    def test_deterministic_embeddings_similarity(self):
        embedder = LocalDeterministicEmbeddings(dimension=384)
        v1 = embedder.embed_text("blood pressure hypertension lisinopril")
        v2 = embedder.embed_text("patient blood pressure high hypertension medication")
        v3 = embedder.embed_text("parking garage elevator building public transit")

        sim_related = cosine_similarity(v1, v2)
        sim_unrelated = cosine_similarity(v1, v3)

        assert sim_related > sim_unrelated
        assert sim_related > 0.3

    def test_clinic_knowledge_search_hours(self):
        engine = RAGEngine()
        results = engine.search_clinic("What are your hours on Saturday?", top_k=2)
        
        assert len(results) > 0
        combined_text = " ".join([r.text for r in results])
        assert "Saturday" in combined_text
        assert "2:00 PM" in combined_text or "9:00 AM" in combined_text

    def test_clinic_knowledge_search_insurance(self):
        engine = RAGEngine()
        results = engine.search_clinic("Do you accept Aetna insurance?", top_k=2)
        
        assert len(results) > 0
        combined_text = " ".join([r.text for r in results])
        assert "Aetna" in combined_text

    def test_clinic_knowledge_search_fasting_prep(self):
        engine = RAGEngine()
        results = engine.search_clinic("Do I need to fast before a lipid panel blood test?", top_k=2)
        
        assert len(results) > 0
        combined_text = " ".join([r.text for r in results])
        assert "Lipid Panel" in combined_text or "fasting" in combined_text.lower()
        assert "12 hours" in combined_text

    def test_hipaa_patient_isolation_security(self):
        """
        Critical security test:
        - Querying P-10023 must return Aarav Sharma's records (hypertension/Lisinopril)
        - Querying P-10023 must NEVER return Priya Patel's records (P-10024)
        - Querying clinic knowledge must NEVER return patient records
        """
        engine = RAGEngine()
        
        # 1. Search for Aarav Sharma
        results_aarav = engine.search_patient(patient_id="P-10023", query="medication hypertension")
        assert len(results_aarav) > 0
        for r in results_aarav:
            assert r.metadata.patient_id == "P-10023"
            assert r.metadata.patient_id != "P-10024"
            assert "Priya Patel" not in r.text

        # 2. Search for Priya Patel
        results_priya = engine.search_patient(patient_id="P-10024", query="allergies")
        assert len(results_priya) > 0
        for r in results_priya:
            assert r.metadata.patient_id == "P-10024"
            assert r.metadata.patient_id != "P-10023"
            assert "Aarav Sharma" not in r.text

        # 3. Public clinic search must NOT contain any patient_id
        results_clinic = engine.search_clinic(query="hypertension lisinopril")
        for r in results_clinic:
            assert r.metadata.patient_id is None

    def test_brain_tool_query_clinic(self):
        context = execute_rag_tool("query_clinic_knowledge", {"question": "parking instructions"})
        assert "Parking" in context or "garage" in context.lower()

    def test_brain_tool_query_patient_records(self):
        context = execute_rag_tool(
            "query_patient_records",
            {"patient_id": "P-10023", "query": "blood pressure"}
        )
        assert "Aarav Sharma" in context
        assert "Lisinopril" in context

    def test_brain_tool_blocks_missing_patient_id(self):
        error_resp = execute_rag_tool("query_patient_records", {"query": "blood pressure"})
        assert "Error" in error_resp
        assert "patient_id is required" in error_resp
