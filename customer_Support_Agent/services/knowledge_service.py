from __future__ import annotations

from customer_Support_Agent.core.settings import Settings
from customer_Support_Agent.integration.rag.chroma_kb import knowledgeBaseService

class KnowledgeService:
    def __init__(self, settings: Settings):
        self._settings = settings
        
    def ingest(self, clear_existing: bool = False) -> dict[str, int]:
        rag_service = knowledgeBaseService(self._settings)
        return rag_service.ingest_directory(
            directory = self._settings.knowledge_base_dir,
            clear_existing = clear_existing
        )