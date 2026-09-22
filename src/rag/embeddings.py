"""
MedFront Embedding Providers.
Supports both Azure OpenAI text embeddings and a fast, deterministic local vectorizer.
"""

import hashlib
import logging
import math
import re
from abc import ABC, abstractmethod
from typing import Any

from src.core.config import settings

logger = logging.getLogger("medfront.rag.embeddings")

try:
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AzureOpenAI
except ImportError:
    DefaultAzureCredential = None  # type: ignore[assignment]
    get_bearer_token_provider = None  # type: ignore[assignment]
    AzureOpenAI = None  # type: ignore[assignment]

STOP_WORDS: frozenset[str] = frozenset({
    "a", "about", "an", "are", "as", "at", "be", "by", "for", "from",
    "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
    "this", "to", "was", "what", "when", "where", "who", "will", "with",
    "do", "does", "can", "could", "should", "would", "you", "your"
})


class BaseEmbeddingProvider(ABC):
    """Abstract interface for generating vector embeddings."""

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single string."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of strings."""


class LocalDeterministicEmbeddings(BaseEmbeddingProvider):
    """
    Lightweight, deterministic hashed bag-of-words + bigram vectorizer.
    Runs locally with zero external dependencies and supports exact cosine similarity.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _tokenize(self, text: str) -> list[str]:
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        tokens = [t for t in cleaned.split() if len(t) > 1 and t not in STOP_WORDS]
        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def embed_text(self, text: str) -> list[float]:
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.dimension

        vector = [0.0] * self.dimension
        for token in tokens:
            # Deterministic hash to bucket
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 16) & 1) else -1.0
            vector[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


class AzureOpenAIEmbeddings(BaseEmbeddingProvider):
    """Production vectorizer calling Azure OpenAI text-embedding models."""

    client: Any = None
    deployment: str = ""

    def __init__(self):
        if AzureOpenAI is None or DefaultAzureCredential is None or get_bearer_token_provider is None:
            raise RuntimeError(
                "The 'openai' and 'azure-identity' packages are required for AzureOpenAIEmbeddings. "
                "Please run `pip install -r requirements.txt`."
            )

        endpoint = settings.azure_openai_endpoint
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is not configured.")

        try:
            import httpx

            if settings.use_managed_identity:
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(), 
                    "https://cognitiveservices.azure.com/.default"
                )
                self.client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    azure_ad_token_provider=token_provider,
                    api_version=settings.azure_openai_api_version,
                    http_client=httpx.Client(),
                )
            else:
                api_key = settings.azure_openai_api_key
                if not api_key:
                    raise ValueError("AZURE_OPENAI_API_KEY is not configured.")
                self.client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=settings.azure_openai_api_version,
                    http_client=httpx.Client(),
                )
            self.deployment = settings.azure_openai_embedding_deployment
            self._local_fallback = LocalDeterministicEmbeddings(dimension=384)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AzureOpenAI client: {e}") from e

    @staticmethod
    def _truncate_and_normalize(vector: list[float], target_dim: int = 1536) -> list[float]:
        """
        Matryoshka Representation Learning (MRL) shortening safeguard.
        If an embedding vector exceeds target_dim (e.g. 3072 from text-embedding-3-large),
        slices the first target_dim floats and re-normalizes using L2 norm.
        """
        if len(vector) > target_dim:
            truncated = vector[:target_dim]
            norm = math.sqrt(sum(x * x for x in truncated))
            return [x / norm for x in truncated] if norm > 0 else truncated
        return vector

    def embed_text(self, text: str) -> list[float]:
        if not self.client:
            return self._local_fallback.embed_text(text)
        try:
            try:
                response = self.client.embeddings.create(
                    input=[text],
                    model=self.deployment,
                    dimensions=1536,
                )
            except Exception as inner_err:
                logger.debug(f"Direct dimensions=1536 parameter not supported by endpoint ({inner_err}), falling back to MRL truncation.")
                response = self.client.embeddings.create(
                    input=[text],
                    model=self.deployment,
                )
            raw_vector = response.data[0].embedding
            return self._truncate_and_normalize(raw_vector, 1536)
        except Exception as e:
            logger.warning(f"Azure OpenAI Embeddings failed ({e}). Falling back to LocalDeterministicEmbeddings.")
            return self._local_fallback.embed_text(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.client:
            return self._local_fallback.embed_batch(texts)
        try:
            try:
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.deployment,
                    dimensions=1536,
                )
            except Exception as inner_err:
                logger.debug(f"Direct dimensions=1536 parameter not supported by endpoint ({inner_err}), falling back to MRL truncation.")
                response = self.client.embeddings.create(
                    input=texts,
                    model=self.deployment,
                )
            raw_vectors = [item.embedding for item in response.data]
            return [self._truncate_and_normalize(v, 1536) for v in raw_vectors]
        except Exception as e:
            logger.warning(f"Azure OpenAI Embeddings batch failed ({e}). Falling back to LocalDeterministicEmbeddings.")
            return self._local_fallback.embed_batch(texts)


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory function returning the configured or fallback embedding provider."""
    mode = settings.effective_rag_mode
    if mode == "azure":
        try:
            return AzureOpenAIEmbeddings()
        except Exception as err:  # noqa: BLE001
            logger.warning(f"Azure OpenAI Embeddings unavailable ({err}). Falling back to LocalDeterministicEmbeddings.")
            return LocalDeterministicEmbeddings()
    return LocalDeterministicEmbeddings()
