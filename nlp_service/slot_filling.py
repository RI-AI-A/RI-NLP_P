"""Slot Filling Module using spaCy NER and regex patterns"""
import re
from typing import Dict, Any, List, Optional
import spacy
from datetime import datetime, timedelta
from .config import nlp_config
import structlog

logger = structlog.get_logger()


class SlotFiller:
    """Extract entities and slots from user queries"""
    
    def __init__(self):
        self.config = nlp_config
        self.nlp = None
        self._load_models()
        self._compile_patterns()
    
    def _load_models(self):
        """Load spaCy model"""
        try:
            logger.info("Loading spaCy model", model=self.config.spacy_model)
            self.nlp = spacy.load(self.config.spacy_model)
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            logger.error("Failed to load spaCy model", error=str(e))
            raise
    
    def _compile_patterns(self):
        """Compile regex patterns for slot extraction"""
        # Time range patterns
        self.time_patterns = [
            (r'\b(yesterday)\b', 'yesterday'),
            (r'\b(today)\b', 'today'),
            (r'\b(last\s+week)\b', 'last_week'),
            (r'\b(this\s+week)\b', 'this_week'),
            (r'\b(last\s+month)\b', 'last_month'),
            (r'\b(this\s+month)\b', 'this_month'),
            (r'\b(last\s+quarter)\b', 'last_quarter'),
            (r'\b(Q[1-4]\s+\d{4})\b', None),  # Q1 2024
            (r'\b(\d{4}-\d{2}-\d{2})\b', None),  # 2024-01-15
            (r'\b(\d{1,2}/\d{1,2}/\d{4})\b', None),  # 01/15/2024
        ]
        
        # Branch ID patterns
        self.branch_patterns = [
            (r'\bbranch\s+([A-Z0-9]+)\b', 1),
            (r'\bstore\s+([A-Z0-9]+)\b', 1),
            (r'\blocation\s+([A-Z0-9]+)\b', 1),
            (r'\boutlet\s+([A-Z0-9]+)\b', 1),
        ]
        
        # KPI type patterns
        self.kpi_patterns = [
            (r'\b(traffic|footfall|foot\s+traffic)\b', 'traffic'),
            (r'\b(sales|revenue)\b', 'sales'),
            (r'\b(conversion|conversion\s+rate)\b', 'conversion'),
            (r'\b(dwell\s+time|time\s+spent)\b', 'dwell_time'),
            (r'\b(basket\s+size|average\s+basket)\b', 'basket_size'),
            (r'\b(busy|busyness|occupancy)\b', 'traffic'),
        ]
        
        # Event type patterns
        self.event_patterns = [
            (r'\b(incident|accident|emergency)\b', 'incident'),
            (r'\b(maintenance|repair)\b', 'maintenance'),
            (r'\b(delivery|shipment)\b', 'delivery'),
            (r'\b(meeting|conference)\b', 'meeting'),
        ]
    
    async def extract_slots(self, query: str, intent: str) -> Dict[str, Any]:
        """
        Extract slots from query based on intent
        
        Args:
            query: User query text
            intent: Predicted intent
            
        Returns:
            Dictionary of extracted slots
        """
        slots = {}
        
        try:
            # Extract using spaCy NER
            doc = self.nlp(query)
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ == "ORG" and "branch_id" not in slots:
                    slots["branch_id"] = ent.text
                elif ent.label_ == "PERSON" and "employee_name" not in slots:
                    slots["employee_name"] = ent.text
                elif ent.label_ == "PRODUCT" and "product_name" not in slots:
                    slots["product_name"] = ent.text
                elif ent.label_ == "DATE" and "time_range" not in slots:
                    slots["time_range"] = self._normalize_date(ent.text)
            
            # Extract using regex patterns
            slots.update(self._extract_time_range(query))
            slots.update(self._extract_branch_id(query))
            slots.update(self._extract_kpi_type(query))
            slots.update(self._extract_event_type(query))
            
            # Intent-specific slot extraction
            if intent == "kpi_query":
                if "kpi_type" not in slots:
                    slots["kpi_type"] = "general"
            
            logger.info("Slots extracted", slots=slots, intent=intent)
            
        except Exception as e:
            logger.error("Slot extraction failed", error=str(e), query=query)
        
        return slots
    
    def _extract_time_range(self, query: str) -> Dict[str, str]:
        """Extract time range from query"""
        query_lower = query.lower()
        for pattern, normalized in self.time_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                value = normalized if normalized else match.group(1)
                return {"time_range": value}
        return {}
    
    def _extract_branch_id(self, query: str) -> Dict[str, str]:
        """Extract branch ID from query"""
        for pattern, group_idx in self.branch_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return {"branch_id": match.group(group_idx).upper()}
        return {}
    
    def _extract_kpi_type(self, query: str) -> Dict[str, str]:
        """Extract KPI type from query"""
        query_lower = query.lower()
        for pattern, normalized in self.kpi_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return {"kpi_type": normalized}
        return {}
    
    def _extract_event_type(self, query: str) -> Dict[str, str]:
        """Extract event type from query"""
        query_lower = query.lower()
        for pattern, normalized in self.event_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return {"event_type": normalized}
        return {}
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to standard format"""
        date_str_lower = date_str.lower()
        
        # Handle relative dates
        if "yesterday" in date_str_lower:
            date = datetime.now() - timedelta(days=1)
            return date.strftime("%Y-%m-%d")
        elif "today" in date_str_lower:
            return datetime.now().strftime("%Y-%m-%d")
        elif "last week" in date_str_lower:
            return "last_week"
        elif "this week" in date_str_lower:
            return "this_week"
        
        # Return as-is for absolute dates
        return date_str
    
    def validate_slots(self, slots: Dict[str, Any], intent: str) -> bool:
        """
        Validate extracted slots for given intent
        
        Args:
            slots: Extracted slots
            intent: Intent type
            
        Returns:
            True if slots are valid for intent
        """
        required_slots = {
            "kpi_query": ["branch_id"],
            "branch_status": ["branch_id"],
            "task_management": [],
            "event_query": [],
            "promotion_query": [],
            "chitchat": [],
            "unknown": []
        }
        
        required = required_slots.get(intent, [])
        return all(slot in slots for slot in required)


# Singleton instance
_slot_filler = None


def get_slot_filler() -> SlotFiller:
    """Get or create slot filler singleton"""
    global _slot_filler
    if _slot_filler is None:
        _slot_filler = SlotFiller()
    return _slot_filler
