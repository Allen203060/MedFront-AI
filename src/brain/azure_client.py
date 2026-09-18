"""
Azure OpenAI Client Factory for MedFront-AI Brain.
Supports standard API keys and zero-trust Azure Managed Identity (DefaultAzureCredential).
"""

import logging
from typing import Optional
import httpx
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider


from src.core.config import settings

logger = logging.getLogger("medfront.brain.azure_client")


def get_azure_openai_client() -> Optional[AzureOpenAI]:
    """
    Instantiates an authenticated AzureOpenAI client.
    Returns None if Azure OpenAI is not configured in settings.
    """
    if not settings.azure_openai_endpoint:
        logger.warning("AZURE_OPENAI_ENDPOINT is not configured.")
        return None

    # Option A: Zero-trust Managed Identity Authentication (Enterprise AI-102 Standard)
    if settings.use_managed_identity:
        logger.info("Authenticating Azure OpenAI via DefaultAzureCredential...")
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), 
            "https://cognitiveservices.azure.com/.default"
        )
        return AzureOpenAI(
             azure_endpoint=settings.azure_openai_endpoint,
             azure_ad_token_provider=token_provider,
             api_version=settings.azure_openai_api_version,
            http_client=httpx.Client(),
        )
 
     # Option B: Standard API Key Authentication
    if not settings.azure_openai_api_key or settings.azure_openai_api_key.startswith("<"):
        logger.warning("AZURE_OPENAI_API_KEY is not configured in .env.")
        return None
 
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        http_client=httpx.Client(),
    )