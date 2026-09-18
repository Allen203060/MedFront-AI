"""
MedFront Core Configuration Module.
Loads environment variables safely using Pydantic Settings with support
for local development (.env) and enterprise Managed Identity (DefaultAzureCredential).
"""


from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General
    environment: str = Field(default="development", description="Runtime environment")
    log_level: str = Field(default="INFO", description="Logging verbosity")
    app_host: str = Field(default="0.0.0.0", description="FastAPI host")
    app_port: int = Field(default=8000, description="FastAPI port")

    # Module 1: Telephony (Azure Communication Services)
    acs_connection_string: str | None = Field(default=None)
    acs_phone_number: str | None = Field(default=None)
    acs_callback_base_url: str | None = Field(default=None)

    # Module 2: Azure AI Speech
    azure_speech_key: Optional[str] = Field(default=None)
    azure_speech_region: str = Field(default="uaenorth")
    azure_speech_voice_name: str = Field(default="en-IN-NeerjaNeural")
    azure_speech_language: str = Field(default="en-IN", description="STT recognition language locale")

    # Module 3: Azure OpenAI
    azure_openai_endpoint: str | None = Field(default=None)
    azure_openai_api_key: str | None = Field(default=None)
    azure_openai_api_version: str = Field(default="2024-08-01-preview")
    azure_openai_deployment_name: str = Field(default="gpt-4o")
    azure_openai_embedding_deployment: str = Field(default="text-embedding-3-large")

    # Module 4: Azure AI Search & RAG
    azure_search_endpoint: str | None = Field(default=None)
    azure_search_api_key: str | None = Field(default=None)
    azure_search_patient_index: str = Field(default="patient-records-index")
    azure_search_clinic_index: str = Field(default="clinic-knowledge-index")
    use_local_rag: bool = Field(
        default=False,
        description="Force local vector engine regardless of Azure credentials"
    )

    # Module 5: Azure Cosmos DB
    cosmos_db_endpoint: str | None = Field(default=None)
    cosmos_db_key: str | None = Field(default=None)
    cosmos_db_database_name: str = Field(default="MedFront_db")
    cosmos_db_patients_container: str = Field(default="patients")
    cosmos_db_appointments_container: str = Field(default="appointments")

    # Security & Feature Flags
    use_managed_identity: bool = Field(
        default=False, 
        description="If True, authenticate via DefaultAzureCredential instead of API keys"
    )
    enable_barge_in: bool = Field(
        default=True, 
        description="Enable real-time STT interrupt during TTS output"
    )

    @property
    def is_azure_search_configured(self) -> bool:
        """Check if Azure AI Search credentials and endpoint are available."""
        return bool(self.azure_search_endpoint and (self.azure_search_api_key or self.use_managed_identity))

    @property
    def is_azure_openai_configured(self) -> bool:
        """Check if Azure OpenAI credentials and endpoint are available."""
        return bool(self.azure_openai_endpoint and (self.azure_openai_api_key or self.use_managed_identity))

    @property
    def effective_rag_mode(self) -> str:
        """Return 'azure' if configured and not explicitly forced local, else 'local'."""
        if self.use_local_rag:
            return "local"
        if self.is_azure_search_configured and self.is_azure_openai_configured:
            return "azure"
        return "local"


# Singleton instance exported across the application
settings = Settings()
