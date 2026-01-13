"""
Vector Memory - Semantic search for AI memory and recall
Requires: pip install sentence-transformers faiss-cpu numpy
"""

import os
import pickle
import logging
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    VECTOR_LIBS_AVAILABLE = True
except ImportError:
    VECTOR_LIBS_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorMemory:
    """Semantic vector memory for intelligent recall"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: str = "./data/vector_cache"):
        if not VECTOR_LIBS_AVAILABLE:
            logger.error("Vector libraries (faiss, sentence-transformers) NOT available.")
            self.model = None
            return

        try:
            self.model = SentenceTransformer(model_name)
            self.dimension = 384  # all-MiniLM-L6-v2 dimension
            self.index = faiss.IndexFlatL2(self.dimension)
            self.memories = []
            self.cache_dir = cache_dir
            
            os.makedirs(cache_dir, exist_ok=True)
            self._load_from_disk()
            logger.info(f"Vector Memory initialized ({len(self.memories)} memories loaded)")
        except Exception as e:
            logger.error(f"Error initializing VectorMemory: {e}")
            self.model = None

    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        """Add a new memory with automatic deduplication"""
        if not self.model or not text or len(text.strip()) < 5:
            return
        
        try:
            # Deduplication: skip if similar memory exists
            if self.memories:
                existing = self.search(text, top_k=1, min_score=0.85)
                if existing:
                    logger.debug(f"Skipping duplicate memory (score {existing[0]['score']:.2f})")
                    return
            
            embedding = self.model.encode([text])[0]
            self.index.add(np.array([embedding]).astype('float32'))
            
            entry = {
                "text": text,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
                "id": len(self.memories)
            }
            self.memories.append(entry)
            
            if len(self.memories) % 5 == 0:
                self._save_to_disk()
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")

    def search(self, query: str, top_k: int = 3, min_score: float = 0.4) -> List[Dict[str, Any]]:
        """Search memories by semantic similarity"""
        if not self.model or not self.memories or self.index.ntotal == 0:
            return []
        
        try:
            query_embedding = self.model.encode([query])[0]
            distances, indices = self.index.search(np.array([query_embedding]).astype('float32'), top_k)
            
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx < 0 or idx >= len(self.memories):
                    continue
                
                # Convert L2 distance to similarity score
                similarity = 1 / (1 + dist)
                if similarity < min_score:
                    continue
                    
                mem = self.memories[idx].copy()
                mem["score"] = float(similarity)
                results.append(mem)
            
            return results
        except Exception as e:
            logger.error(f"Memory search error: {e}")
            return []

    def search_by_type(self, query: str, type_filter: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search memories filtered by metadata type"""
        results = self.search(query, top_k=top_k * 2)
        return [r for r in results if r.get("metadata", {}).get("type") == type_filter][:top_k]

    def _save_to_disk(self):
        """Persist index and memories to disk"""
        try:
            faiss.write_index(self.index, os.path.join(self.cache_dir, "faiss.index"))
            with open(os.path.join(self.cache_dir, "memories.pkl"), 'wb') as f:
                pickle.dump(self.memories, f)
        except Exception as e:
            logger.error(f"Save error: {e}")

    def _load_from_disk(self):
        """Load index and memories from disk"""
        idx_path = os.path.join(self.cache_dir, "faiss.index")
        mem_path = os.path.join(self.cache_dir, "memories.pkl")
        if os.path.exists(idx_path) and os.path.exists(mem_path):
            try:
                self.index = faiss.read_index(idx_path)
                with open(mem_path, 'rb') as f:
                    self.memories = pickle.load(f)
            except Exception as e:
                logger.warning(f"Load failed: {e}")
