"""Intent Classification Module"""
import os
from typing import Dict, Tuple
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)
from .config import nlp_config
import structlog

logger = structlog.get_logger()


class IntentClassifier:
    """Intent classification using BERT-based models with zero-shot fallback"""
    
    def __init__(self):
        self.config = nlp_config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.zero_shot_classifier = None
        self._load_models()
    
    def _load_models(self):
        """Load intent classification models"""
        try:
            # Try to load fine-tuned model if exists
            if os.path.exists(self.config.intent_model_path):
                logger.info("Loading fine-tuned intent classifier", 
                           path=self.config.intent_model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.config.intent_model_path
                )
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.config.intent_model_path
                ).to(self.device)
            else:
                logger.warning("Fine-tuned model not found, using base model",
                             path=self.config.intent_model_path)
                # Fallback to base model (will use zero-shot)
                pass
            
            # Load zero-shot classifier as fallback
            logger.info("Loading zero-shot classifier")
            self.zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("Intent classifier loaded successfully")
            
        except Exception as e:
            logger.error("Failed to load intent classifier", error=str(e))
            raise
    
    async def predict(self, query: str) -> Tuple[str, float]:
        """
        Predict intent for a query
        
        Args:
            query: User query text
            
        Returns:
            Tuple of (intent, confidence)
        """
        try:
            # Use fine-tuned model if available
            if self.model is not None and self.tokenizer is not None:
                return await self._predict_finetuned(query)
            else:
                return await self._predict_zero_shot(query)
                
        except Exception as e:
            logger.error("Intent prediction failed", error=str(e), query=query)
            return "unknown", 0.0
    
    async def _predict_finetuned(self, query: str) -> Tuple[str, float]:
        """Predict using fine-tuned model"""
        inputs = self.tokenizer(
            query,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            confidence, predicted_idx = torch.max(probs, dim=-1)
        
        intent = self.config.intent_classes[predicted_idx.item()]
        confidence_score = confidence.item()
        
        # Apply confidence threshold
        if confidence_score < self.config.intent_confidence_threshold:
            intent = "unknown"
        
        logger.info("Intent predicted (fine-tuned)", 
                   intent=intent, 
                   confidence=confidence_score)
        
        return intent, confidence_score
    
    async def _predict_zero_shot(self, query: str) -> Tuple[str, float]:
        """Predict using zero-shot classifier"""
        result = self.zero_shot_classifier(
            query,
            candidate_labels=self.config.intent_classes,
            multi_label=False
        )
        
        intent = result['labels'][0]
        confidence = result['scores'][0]
        
        # Apply confidence threshold
        if confidence < self.config.intent_confidence_threshold:
            intent = "unknown"
        
        logger.info("Intent predicted (zero-shot)", 
                   intent=intent, 
                   confidence=confidence)
        
        return intent, confidence
    
    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            "kpi_query": "Query about Key Performance Indicators",
            "branch_status": "Query about branch status or information",
            "task_management": "Task creation, assignment, or retrieval",
            "event_query": "Query about events or incidents",
            "promotion_query": "Query about promotions or offers",
            "chitchat": "Casual conversation",
            "unknown": "Intent could not be determined"
        }
        return descriptions.get(intent, "Unknown intent")


# Singleton instance
_intent_classifier = None


def get_intent_classifier() -> IntentClassifier:
    """Get or create intent classifier singleton"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
