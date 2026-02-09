"""Orchestration Service - Coordinates all NLP components"""
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from nlp_service.intent_classifier import get_intent_classifier
from nlp_service.slot_filling import get_slot_filler
from nlp_service.query_router import get_query_router
from nlp_service.response_generator import get_response_generator
from nlp_service.guardrails import get_guardrails
from db.models import NLPQueryLog
from schemas.nlp_response import NLPResponse, NLPErrorResponse
import structlog

logger = structlog.get_logger()


class OrchestrationService:
    """Orchestrates the NLP pipeline"""
    
    def __init__(self):
        self.intent_classifier = get_intent_classifier()
        self.slot_filler = get_slot_filler()
        self.query_router = get_query_router()
        self.response_generator = get_response_generator()
        self.guardrails = get_guardrails()
    
    async def process_query(
        self,
        query: str,
        conversation_id: UUID,
        user_role: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process a user query through the NLP pipeline
        
        Args:
            query: User query text
            conversation_id: Conversation identifier
            user_role: User role (manager, analyst, staff)
            db: Database session
            
        Returns:
            Dictionary with response or error
        """
        try:
            logger.info("Processing query", 
                       query=query[:100], 
                       conversation_id=str(conversation_id),
                       user_role=user_role)
            
            # Step 1: Intent Classification
            intent, confidence = await self.intent_classifier.predict(query)
            logger.info("Intent classified", intent=intent, confidence=confidence)
            
            # Step 2: Slot Filling
            slots = await self.slot_filler.extract_slots(query, intent)
            logger.info("Slots extracted", slots=slots)
            
            # Step 3: Query Routing
            routed_endpoint = await self.query_router.route(intent, slots)
            logger.info("Query routed", endpoint=routed_endpoint)
            
            # Step 4: Response Generation
            response_text, sources = await self.response_generator.generate(
                query, intent, slots, routed_endpoint
            )
            logger.info("Response generated", sources=sources)
            
            # Step 5: Guardrails Check
            guardrail_result = await self.guardrails.check_all(
                query, intent, confidence, response_text
            )
            
            if not guardrail_result.passed:
                logger.warning("Guardrail check failed", reason=guardrail_result.reason)
                
                # Log the rejected query
                await self._log_query(
                    db, conversation_id, user_role, query,
                    "rejected", confidence, None
                )
                
                return {
                    "success": False,
                    "error": guardrail_result.reason
                }
            
            # Step 6: Log Query
            query_log = await self._log_query(
                db, conversation_id, user_role, query,
                intent, confidence, routed_endpoint
            )
            
            # Step 7: Build Response
            response = NLPResponse(
                intent=intent,
                slots=slots,
                routed_endpoint=routed_endpoint,
                response_text=response_text,
                confidence=confidence,
                sources=sources
            )
            
            logger.info("Query processed successfully", 
                       query_id=str(query_log.id),
                       intent=intent)
            
            return {
                "success": True,
                "data": response.model_dump(),
                "query_id": str(query_log.id)
            }
            
        except Exception as e:
            logger.error("Query processing failed", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": "An error occurred while processing your query. Please try again."
            }
    
    async def _log_query(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        user_role: str,
        query_text: str,
        intent: str,
        confidence: float,
        routed_endpoint: str
    ) -> NLPQueryLog:
        """Log query to database"""
        try:
            query_log = NLPQueryLog(
                conversation_id=conversation_id,
                user_role=user_role,
                query_text=query_text,
                intent=intent,
                confidence=confidence,
                routed_endpoint=routed_endpoint
            )
            
            db.add(query_log)
            await db.commit()
            await db.refresh(query_log)
            
            logger.debug("Query logged", query_id=str(query_log.id))
            
            return query_log
            
        except Exception as e:
            logger.error("Failed to log query", error=str(e))
            await db.rollback()
            raise


# Singleton instance
_orchestration_service = None


def get_orchestration_service() -> OrchestrationService:
    """Get or create orchestration service singleton"""
    global _orchestration_service
    if _orchestration_service is None:
        _orchestration_service = OrchestrationService()
    return _orchestration_service
