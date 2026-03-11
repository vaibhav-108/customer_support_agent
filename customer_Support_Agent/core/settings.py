from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()


OPENROUTER_API_KEY=os.getenv("OPENROUTER_API_KEY")

class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    app_name: str = "Customer Support Agent"
    OPENAI_API_KEY: str =OPENROUTER_API_KEY
    google_api_key: str = ""
    OPENAI_API_BASE: str = "https://openrouter.ai/api/v1"
    OPENAI_MODEL: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    google_embedding_model: str = "gemini-embedding-001"
    OPENAI_TEMPERATURE: float = 0.1
    huggingface_embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    enable_local_embeddings: bool = True
    
    workspace_dir: Path = Path(__file__).resolve().parent[2]
    data_dir: Path = Path("data")
    db_path: Path = Path("data/customer_support_agent.db")
    chroma_db_dir: Path = Path("data/chroma_db")
    chroma_memo0_dir = Path("data/chroma_memo0")
    knowledge_base_dir: Path = Path("data/knowledge_base")
    
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_top_k: int = 3
    mem0_top_k: int = 5
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    dashboard_api_url: str = "http://localhost:8000"
    
    def resolve(self,path: Path) -> Path:
        """Resolve a path relative to the workspace directory."""
        return path if path.is_absolute() else self.workspace_dir / path
    
    @property
    def db_file(self)-> Path:
        return self.resolve(self.db_path)
    
    @property
    def chroma_db_dir(self)-> Path:
        return self.resolve(self.chroma_db_dir)
    
    @property
    def chroma_memo0_dir(self)-> Path:
        return self.resolve(self.chroma_memo0_dir)
    
    @property
    def knowledge_base_dir(self)-> Path:
        return self.resolve(self.knowledge_base_dir)
    
    @property
    def effective_embedding_model(self)-> str:
        """Determine which embedding model to use based on configuration."""
        model= (self.huggingface_embedding_model or "").strip()
        if not model:
            raise ValueError("No embedding model configured.")
        return model
        
    #***************for gemini embedding model normalization and auto-upgrade, if needed in the future****************
    # @property
    # def effective_google_embedding_model(self) -> str:
    #     """
    #     Normalize and auto-upgrade legacy embedding model IDs to a supported Gemini model.
    #     """
    #     model = (self.google_embedding_model or "").strip()
    #     if not model:
    #         return "gemini-embedding-001"

    #     if model.startswith("models/"):
    #         model = model[len("models/") :]

    #     deprecated_aliases = {
    #         "text-embedding-004",
    #         "embedding-001",
    #         "embedding-gecko-001",
    #         "gemini-embedding-exp",
    #         "gemini-embedding-exp-03-07",
    #     }
    #     if model in deprecated_aliases:
    #         return "gemini-embedding-001"

    #     return model
    
@lru_cache()
def get_settings()-> Settings:
    return Settings()
    
def ensure_directories(settings: Settings | None = None) -> None:
    """Create the local directories required by SQLite and ChromaDB."""
    config = settings or get_settings()

    for path in (
        config.resolve(config.data_dir),
        config.chroma_db_dir,
        config.chroma_memo0_dir,
        config.knowledge_base_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)