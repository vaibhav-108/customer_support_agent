from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any
import os

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from chromadb import Documents, Embeddings, EmbeddingFunction
from customer_Support_Agent.core import Settings

class OpenRouterEmbeddingFunction(EmbeddingFunction):
    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            response = self._client.embeddings.create(
                model=self._model,
                input=[{"content": [{"type": "text", "text": text}]}],
                encoding_format="float"
            )
            embeddings.append(response.data[0].embedding)
        return embeddings

class knowledgeBaseService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = chromadb.PersistentClient(path=str(settings.chroma_rag_dir))
        self._collection_name = "support_kb"
        self._collection = self._client.get_or_create_collection(name=self._collection_name)
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap)
        self._embedding_function = OpenRouterEmbeddingFunction(
            api_key=self._settings.OPENAI_API_KEY,
            base_url=self._settings.OPENAI_API_BASE,
            model=self._settings.nvidia_embedding_model
        )
            
       
    def ingest_directory(self, directory: Path, clear_existing: bool = False)-> dict[str, Any]:
        if clear_existing:
            self._client.delete_collection(name=self._collection_name)
            self._collection = self._client.get_or_create_collection(name=self._collection_name,
                                                                    embedding_function=self._embedding_function,)
        
        Source_files = sorted(
            [
                *directory.glob("**/*.md"),
                *directory.glob("**/*.txt"),
                # *directory.glob("**/*.docx"),
                # *directory.glob("**/*.doc"),
            ]
        )
        docs: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, Any]] = []
        
        for file_path in Source_files:
            text = file_path.read_text(encoding="utf-8")
            chunks = self._splitter.split_text(text)
        
            for index, chunk in enumerate(chunks):
                chunk_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
                doc_id = f"{file_path.stem}-{index}-{chunk_hash}"
                docs.append(chunk)
                ids.append(doc_id)
                metadatas.append(
                    {
                        "source": file_path.name,
                        "chunk_index": index,
                    }
                    )
        
        if docs:
            self._collection.upsert(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
        return {
            "files_indexed": len(Source_files),
            "chunks_indexed": len(docs),
            "collection_count": self._collection.count(),
        }
        
    def search(self, query: str, top_k:int | None = None,) -> list[dict[str, Any]]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k or self._settings.rag_top_k,
            include= ["metadatas", "documents", "distances"]
        )
        
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        
        combined: list[dict[str, Any]] = []
        for i, document in enumerate(documents):
            metadata = metadatas[i] if metadatas else {}
            distance = distances[i] if distances else None
            combined.append(
                {
                    "content": document,
                    "source": metadata.get("source","unknown"),
                    "distance": distance,
                }
            )
        
        return combined
    

