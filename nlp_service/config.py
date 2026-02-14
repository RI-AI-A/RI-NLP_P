"""NLP Service Configuration"""
from typing import List
from pydantic_settings import BaseSettings


class NLPConfig(BaseSettings):
    """NLP Service Configuration"""

    # Model Configuration
    intent_model_name: str = "distilbert-base-uncased"
    intent_model_path: str = "./models/intent_classifier"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    spacy_model: str = "en_core_web_sm"

    # FAISS Configuration
    faiss_index_path: str = "./data/faiss_index"
    faiss_dimension: int = 384
    faiss_top_k: int = 5

    # Voice Configuration
    whisper_model_name: str = "base"
    tts_voice: str = "en-US-AndrewNeural"
    audio_output_dir: str = "./data/audio"

    # Confidence Thresholds
    intent_confidence_threshold: float = 0.3
    slot_confidence_threshold: float = 0.3
    guardrail_confidence_threshold: float = 0.3

    # Intent Classes
    intent_classes: List[str] = [
        "kpi_query",
        "branch_status",
        "performance_analysis",
        "task_management",
        "event_query",
        "promotion_query",
        "chitchat",
        "unknown"
    ]

    # Slot Entity Types
    slot_entities: List[str] = [
        "branch_id",
        "time_range",
        "kpi_type",
        "employee_name",
        "event_type",
        "product_name"
    ]

    # KPI Types
    kpi_types: List[str] = [
        "traffic",
        "sales",
        "conversion",
        "revenue",
        "footfall",
        "dwell_time",
        "basket_size"
    ]

    # LLM Configuration
    use_llm: bool = True
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2:3b"
    llm_base_url: str = "http://localhost:11434"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 500
    llm_timeout: int = 30

    # Optional API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # LLM Features
    enable_llm_caching: bool = True
    enable_hybrid_mode: bool = False
    llm_fallback_to_rules: bool = True

    # ✅ Core Backend (Source of truth)
    core_api_base_url: str = "http://127.0.0.1:8000"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Singleton instance
nlp_config = NLPConfig()
