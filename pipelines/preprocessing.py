"""Text Preprocessing Utilities"""
import re
from typing import List


def normalize_text(text: str) -> str:
    """
    Normalize text for NLP processing
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove extra spaces
    text = text.strip()
    
    return text


def remove_special_characters(text: str, keep_punctuation: bool = True) -> str:
    """
    Remove special characters from text
    
    Args:
        text: Input text
        keep_punctuation: Whether to keep basic punctuation
        
    Returns:
        Cleaned text
    """
    if keep_punctuation:
        # Keep letters, numbers, and basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s.,!?-]', '', text)
    else:
        # Keep only letters, numbers, and spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    return text


def tokenize_simple(text: str) -> List[str]:
    """
    Simple tokenization by splitting on whitespace
    
    Args:
        text: Input text
        
    Returns:
        List of tokens
    """
    return text.split()


def preprocess_query(query: str) -> str:
    """
    Full preprocessing pipeline for queries
    
    Args:
        query: User query
        
    Returns:
        Preprocessed query
    """
    # Normalize
    query = normalize_text(query)
    
    # Keep punctuation for better NER
    query = remove_special_characters(query, keep_punctuation=True)
    
    return query
