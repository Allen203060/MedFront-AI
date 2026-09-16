"""
MedFront RAG CLI entrypoint.
Allows querying the clinic knowledge base or scoped patient records directly.
"""

from src.rag.engine import main

if __name__ == "__main__":
    main()
