"""Embedding Service using Sentence-Transformers"""
from typing import List
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from .config import nlp_config
import structlog

logger = structlog.get_logger()


class EmbeddingService:
    """Generate sentence embeddings for semantic search"""
    
    def __init__(self):
        self.config = nlp_config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load sentence transformer model"""
        try:
            logger.info("Loading embedding model", 
                       model=self.config.embedding_model_name)
            
            self.model = SentenceTransformer(
                self.config.embedding_model_name,
                device=self.device
            )
            
            logger.info("Embedding model loaded successfully",
                       dimension=self.config.faiss_dimension)
            
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            raise
    
    async def encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """
        Encode texts to embeddings
        
        Args:
            texts: List of text strings to encode
            normalize: Whether to normalize embeddings (for cosine similarity)
            
        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            logger.debug("Texts encoded", 
                        count=len(texts), 
                        shape=embeddings.shape)
            
            return embeddings
            
        except Exception as e:
            logger.error("Encoding failed", error=str(e))
            raise
    
    async def encode_single(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Encode a single text to embedding
        
        Args:
            text: Text string to encode
            normalize: Whether to normalize embedding
            
        Returns:
            Numpy array of embedding (embedding_dim,)
        """
        embeddings = await self.encode([text], normalize=normalize)
        return embeddings[0]
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
