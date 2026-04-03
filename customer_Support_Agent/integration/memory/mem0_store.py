from __future__ import annotations
from typing import Any
from customer_Support_Agent.core.settings import Settings

try:
    from mem0 import Memory
except ImportError as e:
    raise ImportError("Memory is not installed")

class CustomeMemoryStore:
    
    def __init__(self, settings: Settings, llm:Any) -> None:
        if Memory is None:
            raise RuntimeError("mem0ai is not installed. please run pip install mem0ai")
        _ = llm
    
        config: dict[str, Any] = {
            
            "llm": {
                "provider": "openai",
                "config": {
                    "model": settings.OPENAI_MODEL,
                    "api_key": settings.OPENAI_API_KEY,
                    "openai_base_url": settings.OPENAI_API_BASE,
                    "temperature": settings.OPENAI_TEMPERATURE,
                    },
                },
            "embedder": {
                    "provider": "nvidia",
                    "config": {
                        "model": settings.effective_embedding_model,},
                },
           "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "mem0_store",
                    "path": str(settings.chroma_mem0_path),  # local storage
                    "embedding_model_dims": 384,              # ✅ must match embedder dims
                },
            }
        }
        
        if settings.google_api_key:
            config["embedder"] = {
                "provider": "gemini",
                "config": {
                    "api_key": settings.google_api_key,
                    "model": settings.effective_embedding_model,
                },
            }
        elif settings.enable_local_embeddings:
            config["embedder"] = {
                "provider": "nvidia",
                "config": {
                    "model": "nvidia/llama-nemotron-embed-vl-1b-v2:free",
                },
            }
        else:
            raise RuntimeError(
                "No embedding provider configured for Mem0. Set GOOGLE_API_KEY (recommended) "
                "or OPENAI_API_KEY. Set ENABLE_LOCAL_EMBEDDINGS=true to use local HuggingFace embeddings."
            )
        self._memory = Memory.from_config(config)
    
    def search(self, query: str, user_id: str, limit: int=5) -> list[dict[str, Any]]:
        try:
            raw = self._memory.search(query=query, user_id=user_id, limit=limit)
        except TypeError:
            raw = self._memory.search(query=query, user_id=user_id)
        return self._normalize_response(raw, limit)
    
    def list_memories(self, user_id: str, limit: int=20) -> list[dict[str, Any]]:
        if hasattr(self._memory, "get_all"):
            raw = self._memory.get_all(user_id=user_id)
            return self._normalize_response(raw, limit)
    
    def add_interaction(self,
                        user_id: str,
                        user_input: str,
                        bot_response: str,
                        metadata: dict[str, Any],
                        ) -> None:
        messages = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": bot_response},
        ]
    
    
    def add_resolution(self,
                        user_id: str,
                        ticket_subject: str,
                        ticket_description: str,
                        accepted_draft: str,
                        entity_links: list[str] | None,
                        ) -> None:
        
        entity_text = ""
        if entity_links:
            entity_text = "\nLinked entities: " + ", ".join(entity_links)
        
        messages = [
            {"role": "user", "content": f"Ticket subject: {ticket_subject}\nProblem: {ticket_description}"},
            {"role": "assistant", "content": f"Resolution accepted by support agent:\n{accepted_draft}{entity_text}"},
        ]
        
        metadata = {"type": "resolution"}
        
        self._add_messages(messages=messages, user_id=user_id, metadata=metadata)   
        
    
    def _add_messages(
        self,
        messages : list[dict[str, Any]],
        user_id: str,
        metadata: dict[str, Any] | None = None
    )-> None:
        try:
            self._memory.add(messages, user_id=user_id, metadata=metadata or {})
        except TypeError:
            self._memory.add(messages, user_id=user_id)
    
    def _normalize_response(
        self,
        raw:Any,
        limit: int
    )-> list[dict[str, Any]]:
        
        items: list[dict[str, Any]] = []
        
        if isinstance(raw, dict) and "results" in raw:
            iterable = raw.get("results") or []
        elif isinstance(raw, list):
            iterable = raw
        else:
            iterable = []
        
        for entry in iterable[:limit]:
            if isinstance(entry, dict):
                memory_text = entry.get("memory") or entry.get("content") or ""
                if memory_text:
                    items.append(
                        {
                            "memory": memory_text,
                            "score": entry.get("score"),
                            "metadata": entry.get("metadata") or {},
                        }
                    )
            elif entry:
                items.append({"memory": str(entry), "score": None, "metadata": {}})
        
        return items