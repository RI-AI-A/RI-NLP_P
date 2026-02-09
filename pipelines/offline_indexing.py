"""Offline FAISS Index Building"""
import asyncio
import json
from typing import List, Dict, Any
from pathlib import Path
from nlp_service.retrieval import RetrievalSystem, Document
from nlp_service.embedding_service import get_embedding_service
import structlog

logger = structlog.get_logger()


async def build_index_from_json(documents_path: str, index_output_path: str = None):
    """
    Build FAISS index from JSON documents file
    
    JSON format:
    [
        {
            "text": "Document text...",
            "metadata": {
                "source": "kpi_docs",
                "type": "explanation",
                ...
            }
        },
        ...
    ]
    
    Args:
        documents_path: Path to JSON file with documents
        index_output_path: Path to save FAISS index (optional)
    """
    logger.info("Building FAISS index from documents", path=documents_path)
    
    # Load documents
    with open(documents_path, 'r') as f:
        docs_data = json.load(f)
    
    documents = [Document.from_dict(d) for d in docs_data]
    logger.info("Loaded documents", count=len(documents))
    
    # Create retrieval system
    retrieval_system = RetrievalSystem()
    retrieval_system.documents = documents
    
    # Build index
    await retrieval_system.build_index()
    logger.info("FAISS index built successfully")
    
    # Save index
    if index_output_path:
        retrieval_system.config.faiss_index_path = index_output_path
        retrieval_system.save_index()
        logger.info("Index saved", path=index_output_path)
    else:
        retrieval_system.save_index()
        logger.info("Index saved to default location")
    
    return retrieval_system


async def add_documents_to_index(
    new_documents_path: str,
    existing_index_path: str = None
):
    """
    Add new documents to existing FAISS index
    
    Args:
        new_documents_path: Path to JSON file with new documents
        existing_index_path: Path to existing index (optional, uses default if not provided)
    """
    logger.info("Adding documents to existing index")
    
    # Load existing index
    retrieval_system = RetrievalSystem()
    if existing_index_path:
        retrieval_system.config.faiss_index_path = existing_index_path
    retrieval_system.load_index()
    
    logger.info("Loaded existing index", doc_count=len(retrieval_system.documents))
    
    # Load new documents
    with open(new_documents_path, 'r') as f:
        docs_data = json.load(f)
    
    new_documents = [Document.from_dict(d) for d in docs_data]
    logger.info("Loaded new documents", count=len(new_documents))
    
    # Add documents
    retrieval_system.add_documents(new_documents)
    
    # Rebuild index
    await retrieval_system.build_index()
    logger.info("Index rebuilt with new documents", 
               total_docs=len(retrieval_system.documents))
    
    # Save updated index
    retrieval_system.save_index()
    logger.info("Updated index saved")
    
    return retrieval_system


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Build new index: python offline_indexing.py build <documents.json> [output_path]")
        print("  Add to index: python offline_indexing.py add <new_documents.json> [existing_index_path]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "build":
        docs_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else None
        asyncio.run(build_index_from_json(docs_path, output_path))
    
    elif command == "add":
        new_docs_path = sys.argv[2]
        existing_path = sys.argv[3] if len(sys.argv) > 3 else None
        asyncio.run(add_documents_to_index(new_docs_path, existing_path))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
