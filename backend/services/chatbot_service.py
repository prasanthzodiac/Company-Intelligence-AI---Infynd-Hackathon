"""
Chatbot service that connects to Ollama for company intelligence queries
"""
import json
import logging
import requests
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.api_url = "http://localhost:11434/api/chat"
        self.model = "llama3"
        
        # Load settings if available
        settings_path = base_dir / "config" / "settings.yaml"
        if settings_path.exists():
            try:
                import yaml
                with settings_path.open('r', encoding='utf-8') as f:
                    settings = yaml.safe_load(f)
                    llm_cfg = settings.get("llm", {})
                    self.api_url = llm_cfg.get("api_url", self.api_url)
                    self.model = llm_cfg.get("model", self.model)
            except Exception as e:
                logger.warning(f"Could not load settings: {e}")
    
    def get_response(self, domain: str, question: str) -> str:
        """
        Get chatbot response for a question about a company - optimized for speed using raw chunks
        
        Args:
            domain: Company domain
            question: User question
            
        Returns:
            Response string from LLM
        """
        try:
            # Load chunks FIRST (raw scraped data) - this is faster
            chunks_path = self.base_dir / "output" / domain / "chunks.json"
            
            if not chunks_path.exists():
                return f"Sorry, I don't have scraped data for {domain}. Please ensure the company has been downloaded and scraped."
            
            with chunks_path.open('r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            if not chunks:
                return f"Sorry, no scraped content available for {domain}."
            
            # Load profile for basic info only
            profile = {}
            profile_path = self.base_dir / "output" / domain / "profile.json"
            if profile_path.exists():
                with profile_path.open('r', encoding='utf-8') as f:
                    profile = json.load(f)
            
            # Find most relevant chunks based on question keywords
            question_lower = question.lower()
            question_keywords = question_lower.split()
            
            # Score chunks by relevance
            scored_chunks = []
            for chunk in chunks:
                score = 0
                text_lower = chunk.get("text", "").lower()
                section_lower = chunk.get("section", "").lower()
                
                # Higher score for keyword matches
                for keyword in question_keywords:
                    if len(keyword) > 3:  # Ignore short words
                        if keyword in text_lower:
                            score += 2
                        if keyword in section_lower:
                            score += 3
                
                # Boost score for contact/service/team sections
                if any(kw in section_lower for kw in ["contact", "service", "team", "about", "leadership"]):
                    score += 1
                
                scored_chunks.append((score, chunk))
            
            # Sort by score and take top 20 most relevant chunks
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            relevant_chunks = [chunk for _, chunk in scored_chunks[:20] if _ > 0] or [chunk for _, chunk in scored_chunks[:15]]
            
            # Build context from relevant chunks (raw scraped data)
            context = self._build_context(profile, relevant_chunks)
            
            # Get company name and normalize domain references
            company_name = profile.get('company_name', domain.replace('.com', '').replace('.', '').title())
            # Normalize domain variations (e.g., "afreespace" -> "Freespace" if company_name is "Freespace")
            domain_base = domain.replace('.com', '').replace('.co.uk', '').replace('.', '')
            
            # Create optimized prompt for fast responses
            system_prompt = (
                "You are an offline company intelligence analyst. "
                "Answer questions using ONLY the scraped website content provided below. "
                "IMPORTANT: The domain and company name refer to the SAME company. "
                "For example, if the domain is 'afreespace.com' and the company name is 'Freespace', "
                "they are the same entity. Handle name variations (with/without 'a' prefix, case differences) as referring to the same company. "
                "When asked about company quality or comparisons, highlight positive aspects, certifications, services, and capabilities found in the content. "
                "Be concise, factual, and direct. Cite specific information when possible. "
                "If information is not in the provided content, say 'Information not available in the scraped content.' "
                "Do not make up or infer information that is not explicitly stated."
            )
            
            user_prompt = (
                f"Company Information:\n"
                f"- Domain: {domain}\n"
                f"- Company Name: {company_name}\n"
                f"- Note: The domain '{domain}' and company name '{company_name}' refer to the SAME company. "
                f"Also, '{domain_base}' and variations like '{company_name}' all refer to this same company.\n\n"
                f"SCRAPED WEBSITE CONTENT:\n{context}\n\n"
                f"Question: {question}\n\n"
                f"Answer based ONLY on the scraped content above. When the question mentions the domain, domain base, or company name, "
                f"understand they all refer to the same company. Be concise and factual."
            )
            
            # Call Ollama API with shorter timeout for faster responses
            response = self._call_ollama(system_prompt, user_prompt, timeout=30)
            return response
            
        except Exception as e:
            logger.error(f"Error getting chatbot response: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _build_context(self, profile: Dict, chunks: list) -> str:
        """Build context string from profile and chunks - optimized for fast responses using raw chunks"""
        # For fast responses, prioritize raw chunks over profile summary
        # This allows the LLM to answer directly from source material
        
        context_parts = []
        
        # Quick profile summary (minimal)
        if profile.get('company_name'):
            context_parts.append(f"Company: {profile['company_name']}")
        if profile.get('industry'):
            context_parts.append(f"Industry: {profile['industry']}")
        
        # Use raw chunks directly - this is faster and more accurate
        if chunks:
            # Find relevant chunks based on question keywords (will be done in get_response)
            # For now, include most relevant chunks (contact, about, services sections)
            relevant_chunks = []
            for chunk in chunks:
                section = chunk.get("section", "").lower()
                # Prioritize contact, about, services, team sections
                if any(kw in section for kw in ["contact", "about", "service", "team", "leadership", "product"]):
                    relevant_chunks.append(chunk)
            
            # If we have relevant chunks, use those; otherwise use first 10 chunks
            chunks_to_use = relevant_chunks[:15] if relevant_chunks else chunks[:15]
            
            # Build context from chunks (raw scraped data)
            chunk_texts = []
            for chunk in chunks_to_use:
                section = chunk.get("section", "")
                page = chunk.get("page", "")
                text = chunk.get("text", "")
                # Include structured data if available
                structured = chunk.get("structured_data", {})
                chunk_info = f"[Page: {page}] [Section: {section}]"
                if structured:
                    if structured.get("emails"):
                        chunk_info += f" [Emails: {', '.join(structured['emails'])}]"
                    if structured.get("phones"):
                        chunk_info += f" [Phones: {', '.join(structured['phones'])}]"
                chunk_texts.append(f"{chunk_info}\n{text[:500]}")  # Limit to 500 chars per chunk
            
            context_parts.append("\n\n=== SCRAPED WEBSITE CONTENT ===\n" + "\n\n---\n\n".join(chunk_texts))
        else:
            # Fallback to profile if no chunks
            if profile.get('description_long'):
                context_parts.append(f"Description: {profile['description_long']}")
            if profile.get('services'):
                services = [s.get('name', str(s)) for s in profile['services']]
                context_parts.append(f"Services: {', '.join(services)}")
        
        return "\n".join(context_parts)
    
    def _call_ollama(self, system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
        """Call Ollama API - optimized for fast responses"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Lower temperature for faster, more deterministic responses
                    "num_predict": 200,  # Limit response length for speed
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', 'No response generated')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            return f"Sorry, I couldn't connect to the AI model. Please ensure Ollama is running on {self.api_url}"
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

