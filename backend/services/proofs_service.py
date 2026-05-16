"""
Proofs service - tracks evidence sources for chatbot responses
"""
import json
import logging
from pathlib import Path
from typing import List, Dict

from services.domain_paths import resolve_domain_dir

logger = logging.getLogger(__name__)


class ProofsService:
    def __init__(self, repo_base: Path, output_dir: Path | None = None):
        self.repo_base = repo_base
        self.output_dir = output_dir if output_dir is not None else repo_base / "output"
    
    def get_proofs(self, domain: str, query: str, response: str) -> List[Dict]:
        """
        Get proof sources for a query/response
        
        Args:
            domain: Company domain
            query: User query
            response: Chatbot response
            
        Returns:
            List of proof objects with source information
        """
        try:
            domain_dir = resolve_domain_dir(self.output_dir, domain)
            chunks_path = domain_dir / "chunks.json"
            if not chunks_path.exists():
                return []
            
            with chunks_path.open('r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            # Find relevant chunks based on query keywords
            query_lower = query.lower()
            keywords = [w.strip() for w in query_lower.split() if len(w) > 3]
            
            proofs = []
            for chunk in chunks:
                chunk_text = chunk.get('text', '').lower()
                page = chunk.get('page', 'unknown')
                section = chunk.get('section', 'unknown')
                
                # Check if chunk is relevant
                relevance_score = sum(1 for kw in keywords if kw in chunk_text)
                
                if relevance_score > 0:
                    proofs.append({
                        "page": page,
                        "section": section,
                        "text": chunk.get('text', '')[:300],  # Truncate for display
                        "source_path": chunk.get('source_path', ''),
                        "relevance_score": relevance_score
                    })
            
            # Sort by relevance and return top 5
            proofs.sort(key=lambda x: x['relevance_score'], reverse=True)
            return proofs[:5]
            
        except Exception as e:
            logger.error(f"Error getting proofs: {e}")
            return []

