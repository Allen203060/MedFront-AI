"""
MedFront Knowledge Base Document Chunker.
Splits markdown documents into semantic sections and parses structured JSON clinical records.
"""

import hashlib
import os
import re
from typing import Any

from src.rag.models import DocumentChunk, DocumentMetadata


class DocumentChunker:
    """Chunks structured and unstructured healthcare documents into indexed snippets."""

    def __init__(self, max_chunk_size: int = 1200, chunk_overlap: int = 100):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def generate_chunk_id(source: str, index: int, text: str) -> str:
        """Generate a deterministic unique ID based on source and content hash."""
        digest = hashlib.sha256(f"{source}:{index}:{text}".encode()).hexdigest()[:12]
        clean_source = re.sub(r'[^a-zA-Z0-9_-]', '_', os.path.basename(source))
        return f"{clean_source}_{index}_{digest}"

    def chunk_markdown(self, content: str, source: str, category: str) -> list[DocumentChunk]:
        """
        Split a Markdown document by headers (##) while preserving context.
        Ensures each chunk retains the main document title and current section header.
        """
        chunks: list[DocumentChunk] = []
        lines = content.splitlines()

        doc_title = "Clinic Document"
        for line in lines:
            if line.startswith("# "):
                doc_title = line.strip("# ").strip()
                break

        # Split into sections based on ## or ###
        sections = re.split(r'\n(?=##+\s)', content)
        chunk_idx = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Skip solitary title lines with no body text
            if section.startswith("# ") and len(section.splitlines()) == 1:
                continue

            # Extract section heading if present
            section_match = re.match(r'^(##+\s*[^\n]+)', section)
            section_header = section_match.group(1).strip() if section_match else ""
            header_prefix = f"[{doc_title} > {section_header}]\n" if section_header else ""

            # If section fits within max_chunk_size, keep whole
            if len(section) <= self.max_chunk_size:
                text_content = f"{header_prefix}{section}" if header_prefix else section
                chunk_id = self.generate_chunk_id(source, chunk_idx, text_content)
                metadata = DocumentMetadata(
                    source=os.path.basename(source),
                    category=category,
                    access_level="administrative",
                    author="clinic_admin"
                )
                chunks.append(DocumentChunk(id=chunk_id, text=text_content, metadata=metadata))
                chunk_idx += 1
            else:
                # Split large section into sub-elements (paragraphs or bullet lines)
                units = section.split("\n\n")
                if len(units) == 1:
                    # Single big paragraph or bullet list: split by line
                    units = [u for u in section.splitlines() if u.strip()]

                current_body = ""
                for unit in units:
                    unit_clean = unit.strip()
                    if not unit_clean:
                        continue
                    if len(current_body) + len(unit_clean) > self.max_chunk_size and current_body:
                        full_text = f"{header_prefix}{current_body.strip()}"
                        chunk_id = self.generate_chunk_id(source, chunk_idx, full_text)
                        metadata = DocumentMetadata(
                            source=os.path.basename(source),
                            category=category,
                            access_level="administrative",
                            author="clinic_admin"
                        )
                        chunks.append(DocumentChunk(id=chunk_id, text=full_text, metadata=metadata))
                        chunk_idx += 1
                        current_body = unit_clean + "\n\n"
                    else:
                        current_body += unit_clean + "\n\n"

                if current_body.strip():
                    full_text = f"{header_prefix}{current_body.strip()}"
                    chunk_id = self.generate_chunk_id(source, chunk_idx, full_text)
                    metadata = DocumentMetadata(
                        source=os.path.basename(source),
                        category=category,
                        access_level="administrative",
                        author="clinic_admin"
                    )
                    chunks.append(DocumentChunk(id=chunk_id, text=full_text, metadata=metadata))
                    chunk_idx += 1

        return chunks

    def chunk_patient_records(self, records: list[dict[str, Any]], source: str) -> list[DocumentChunk]:
        """
        Process structured patient clinical and administrative encounters into chunks.
        Strictly embeds the patient_id and access_level into metadata.
        """
        chunks: list[DocumentChunk] = []

        for idx, rec in enumerate(records):
            patient_id = rec.get("patient_id")
            patient_name = rec.get("patient_name")
            record_type = rec.get("record_type", "clinical_note")
            timestamp = rec.get("timestamp")
            access_level = rec.get("access_level", "clinical")
            author = rec.get("author", "physician")
            content = rec.get("content", "")

            # Formulate text with clear identity header
            text = f"[Patient ID: {patient_id} | Name: {patient_name} | Type: {record_type} | Date: {timestamp}]\n{content}"
            chunk_id = self.generate_chunk_id(source, idx, text)

            metadata = DocumentMetadata(
                source=os.path.basename(source),
                category="patient_record",
                patient_id=patient_id,
                patient_name=patient_name,
                record_type=record_type,
                author=author,
                access_level=access_level,
                timestamp=timestamp
            )

            chunks.append(DocumentChunk(id=chunk_id, text=text, metadata=metadata))

        return chunks
