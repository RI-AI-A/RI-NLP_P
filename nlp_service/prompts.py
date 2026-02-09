"""Prompt templates and management for LLM components"""
from typing import Dict, List, Any


# System prompts for different components
SYSTEM_PROMPTS = {
    "intent_classifier": """You are an intent classifier for a retail intelligence system.
Your job is to classify user queries into one of these categories:
- kpi_query: Questions about metrics like sales, traffic, conversion, revenue
- branch_status: Questions about branch information, status, or operations
- performance_analysis: Requests for performance comparisons or analysis
- task_management: Creating, viewing, or managing tasks
- event_query: Questions about events, incidents, or alerts
- promotion_query: Questions about promotions, offers, or campaigns
- chitchat: Casual conversation, greetings, or off-topic questions
- unknown: Queries that don't fit any category

Respond with JSON containing:
- intent: The classified intent
- confidence: A score from 0.0 to 1.0
- reasoning: Brief explanation of your classification""",

    "slot_filler": """You are an entity extractor for retail analytics queries.
Extract these entities when present:
- branch_id: Branch identifier (e.g., "A", "B", "branch-001")
- time_range: Time period (e.g., "yesterday", "last week", "Q1 2024")
- kpi_type: Metric type (traffic, sales, conversion, revenue, footfall, dwell_time, basket_size)
- employee_name: Employee or staff name
- event_type: Type of event or incident
- product_name: Product or item name

Respond with JSON containing only the entities found. Use null for missing entities.""",

    "response_generator": """You are a helpful retail analytics assistant.
Generate natural, professional responses based on the user's query and the information provided.

Your responses should:
1. Acknowledge what data will be retrieved
2. Explain what the system will do
3. Set clear expectations
4. Use natural, conversational language
5. Be concise but informative

Do NOT make up data or numbers. Only explain what will be retrieved."""
}


# Few-shot examples for slot filling
SLOT_FILLING_EXAMPLES = [
    {
        "query": "How was branch A yesterday?",
        "output": {
            "branch_id": "A",
            "time_range": "yesterday",
            "kpi_type": None,
            "employee_name": None,
            "event_type": None,
            "product_name": None
        }
    },
    {
        "query": "Show me sales for branch B last week",
        "output": {
            "branch_id": "B",
            "time_range": "last week",
            "kpi_type": "sales",
            "employee_name": None,
            "event_type": None,
            "product_name": None
        }
    },
    {
        "query": "What's the conversion rate for all branches this month?",
        "output": {
            "branch_id": None,
            "time_range": "this month",
            "kpi_type": "conversion",
            "employee_name": None,
            "event_type": None,
            "product_name": None
        }
    },
    {
        "query": "Create a task for John to check inventory",
        "output": {
            "branch_id": None,
            "time_range": None,
            "kpi_type": None,
            "employee_name": "John",
            "event_type": None,
            "product_name": None
        }
    }
]


# Intent classification examples
INTENT_EXAMPLES = [
    {
        "query": "What were the sales yesterday?",
        "intent": "kpi_query",
        "confidence": 0.95,
        "reasoning": "User is asking about a specific KPI (sales) for a time period"
    },
    {
        "query": "Is branch A open today?",
        "intent": "branch_status",
        "confidence": 0.92,
        "reasoning": "User is asking about the operational status of a branch"
    },
    {
        "query": "Compare performance of branch A and B",
        "intent": "performance_analysis",
        "confidence": 0.90,
        "reasoning": "User wants to analyze and compare branch performance"
    },
    {
        "query": "Create a task for inventory check",
        "intent": "task_management",
        "confidence": 0.93,
        "reasoning": "User wants to create a new task"
    },
    {
        "query": "Hello, how are you?",
        "intent": "chitchat",
        "confidence": 0.98,
        "reasoning": "Casual greeting, not related to retail analytics"
    }
]


# JSON schemas for structured outputs
INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "kpi_query",
                "branch_status",
                "performance_analysis",
                "task_management",
                "event_query",
                "promotion_query",
                "chitchat",
                "unknown"
            ]
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        },
        "reasoning": {
            "type": "string"
        }
    },
    "required": ["intent", "confidence", "reasoning"]
}


SLOT_SCHEMA = {
    "type": "object",
    "properties": {
        "branch_id": {"type": ["string", "null"]},
        "time_range": {"type": ["string", "null"]},
        "kpi_type": {"type": ["string", "null"]},
        "employee_name": {"type": ["string", "null"]},
        "event_type": {"type": ["string", "null"]},
        "product_name": {"type": ["string", "null"]}
    },
    "required": ["branch_id", "time_range", "kpi_type", "employee_name", "event_type", "product_name"]
}


def format_slot_filling_prompt(query: str) -> str:
    """Format few-shot prompt for slot filling"""
    examples_text = "\n\n".join([
        f"Query: {ex['query']}\nOutput: {ex['output']}"
        for ex in SLOT_FILLING_EXAMPLES
    ])
    
    return f"""{SYSTEM_PROMPTS['slot_filler']}

Examples:
{examples_text}

Now extract entities from this query:
Query: {query}
Output:"""


def format_intent_prompt(query: str) -> str:
    """Format few-shot prompt for intent classification"""
    examples_text = "\n\n".join([
        f"Query: {ex['query']}\nIntent: {ex['intent']}\nConfidence: {ex['confidence']}\nReasoning: {ex['reasoning']}"
        for ex in INTENT_EXAMPLES[:3]  # Use first 3 examples
    ])
    
    return f"""{SYSTEM_PROMPTS['intent_classifier']}

Examples:
{examples_text}

Now classify this query:
Query: {query}"""


def format_response_prompt(
    query: str,
    intent: str,
    slots: Dict[str, Any],
    routed_endpoint: str,
    context_docs: List[str] = None
) -> str:
    """Format prompt for response generation"""
    context_text = ""
    if context_docs:
        context_text = "\n\nRelevant context from knowledge base:\n" + "\n".join(
            f"- {doc}" for doc in context_docs[:3]
        )
    
    slots_text = ", ".join([f"{k}={v}" for k, v in slots.items() if v is not None])
    
    return f"""{SYSTEM_PROMPTS['response_generator']}
{context_text}

User query: {query}
Detected intent: {intent}
Extracted information: {slots_text}
API endpoint to call: {routed_endpoint}

Generate a helpful response:"""
