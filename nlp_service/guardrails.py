"""Guardrails for safety and quality control"""
import re
from typing import Dict, Any, List, Tuple
from better_profanity import profanity
from .config import nlp_config
import structlog

logger = structlog.get_logger()


class GuardrailResult:
    """Result of guardrail check"""
    def __init__(self, passed: bool, reason: str = ""):
        self.passed = passed
        self.reason = reason
    
    def __bool__(self):
        return self.passed


class Guardrails:
    """Comprehensive guardrails for NLP service"""
    
    def __init__(self):
        self.config = nlp_config
        # Initialize profanity filter
        profanity.load_censor_words()
        
        # PII patterns
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        }
        
        # Retail domain keywords (for scope validation)
        self.retail_keywords = [
            "branch", "store", "kpi", "sales", "revenue", "traffic", "footfall",
            "conversion", "customer", "task", "event", "promotion", "product",
            "inventory", "staff", "employee", "manager", "analytics", "performance",
            "busy", "occupancy", "dwell", "basket", "transaction"
        ]
        
        # Out-of-scope indicators
        self.out_of_scope_keywords = [
            "weather", "news", "sports", "entertainment", "politics",
            "recipe", "travel", "medical", "legal", "financial advice"
        ]
    
    async def check_all(
        self,
        query: str,
        intent: str,
        confidence: float,
        response: str
    ) -> GuardrailResult:
        """
        Run all guardrail checks
        
        Args:
            query: User query
            intent: Predicted intent
            confidence: Intent confidence score
            response: Generated response
            
        Returns:
            GuardrailResult indicating if all checks passed
        """
        # Check profanity
        profanity_check = self.check_profanity(query)
        if not profanity_check:
            return profanity_check
        
        # Check PII
        pii_check = self.check_pii(query)
        if not pii_check:
            return pii_check
        
        # Check confidence threshold
        confidence_check = self.check_confidence(confidence)
        if not confidence_check:
            return confidence_check
        
        # Check scope
        scope_check = self.check_scope(query, intent)
        if not scope_check:
            return scope_check
        
        # Check hallucination (basic)
        hallucination_check = self.check_hallucination(response, query)
        if not hallucination_check:
            return hallucination_check
        
        return GuardrailResult(True, "All checks passed")
    
    def check_profanity(self, text: str) -> GuardrailResult:
        """Check for profanity"""
        if profanity.contains_profanity(text):
            logger.warning("Profanity detected", text=text[:50])
            return GuardrailResult(
                False,
                "Your query contains inappropriate language. Please rephrase."
            )
        return GuardrailResult(True)
    
    def check_pii(self, text: str) -> GuardrailResult:
        """Check for Personally Identifiable Information"""
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, text):
                logger.warning("PII detected", pii_type=pii_type)
                return GuardrailResult(
                    False,
                    f"Your query contains sensitive information ({pii_type}). "
                    "Please remove personal data and try again."
                )
        return GuardrailResult(True)
    
    def check_confidence(self, confidence: float, threshold: float = None) -> GuardrailResult:
        """Check if confidence meets threshold"""
        if threshold is None:
            threshold = self.config.guardrail_confidence_threshold
            
        if confidence < threshold:
            logger.warning("Low confidence", confidence=confidence, threshold=threshold)
            return GuardrailResult(
                False,
                f"I'm not confident enough in understanding your request "
                f"(confidence: {confidence:.2f}). Could you please rephrase?"
            )
        return GuardrailResult(True)
    
    def check_scope(self, query: str, intent: str) -> GuardrailResult:
        """Check if query is within retail domain scope"""
        query_lower = query.lower()
        
        # Check for explicit out-of-scope keywords
        for keyword in self.out_of_scope_keywords:
            if keyword in query_lower:
                logger.warning("Out of scope query", keyword=keyword)
                return GuardrailResult(
                    False,
                    "I'm specialized in retail analytics queries. "
                    "Your question appears to be outside my area of expertise."
                )
        
        # If intent is unknown and no retail keywords found, reject
        if intent == "unknown":
            has_retail_keyword = any(
                keyword in query_lower for keyword in self.retail_keywords
            )
            if not has_retail_keyword and len(query.split()) > 3:
                logger.warning("Unknown intent with no retail keywords")
                return GuardrailResult(
                    False,
                    "I couldn't understand your request. I specialize in retail analytics. "
                    "Try asking about KPIs, branch status, tasks, events, or promotions."
                )
        
        return GuardrailResult(True)
    
    def check_hallucination(self, response: str, query: str) -> GuardrailResult:
        """
        Basic hallucination check
        
        This is a simplified check. In production, you'd use more sophisticated methods.
        """
        response_lower = response.lower()
        
        # Check for unsupported claims (basic patterns)
        unsupported_patterns = [
            r'\b\d+%\s+(?:increase|decrease|growth|decline)\b',  # Specific percentages
            r'\b\$\d+(?:,\d{3})*(?:\.\d{2})?\b',  # Specific dollar amounts
            r'\b\d+\s+(?:customers|visitors|transactions)\b'  # Specific counts
        ]
        
        # If response contains specific numbers without "I'll retrieve" or "Access"
        if not any(phrase in response_lower for phrase in ["i'll retrieve", "access", "check"]):
            for pattern in unsupported_patterns:
                if re.search(pattern, response_lower):
                    logger.warning("Potential hallucination detected", pattern=pattern)
                    # Don't reject, but log for monitoring
                    # In production, you might want to add a disclaimer
        
        return GuardrailResult(True)
    
    def redact_pii(self, text: str) -> str:
        """Redact PII from text"""
        redacted = text
        for pii_type, pattern in self.pii_patterns.items():
            redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted)
        return redacted
    
    def get_rejection_response(self, result: GuardrailResult) -> str:
        """Get user-friendly rejection message"""
        return result.reason


# Singleton instance
_guardrails = None


def get_guardrails() -> Guardrails:
    """Get or create guardrails singleton"""
    global _guardrails
    if _guardrails is None:
        _guardrails = Guardrails()
    return _guardrails
