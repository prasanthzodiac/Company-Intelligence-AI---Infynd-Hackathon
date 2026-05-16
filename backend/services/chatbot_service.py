"""
Chatbot service — uses configurable LLM (Ollama or OpenAI-compatible).
"""
import json
import logging
from pathlib import Path
from typing import Dict

from services.llm_client import chat_completion
from services.settings_loader import get_llm_config, load_settings

logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self, repo_base: Path, output_dir: Path | None = None):
        self.repo_base = repo_base
        self.output_dir = output_dir if output_dir is not None else repo_base / "output"
        settings = load_settings(repo_base)
        self.llm_config = get_llm_config(settings)

    def get_response(self, domain: str, question: str) -> str:
        try:
            chunks_path = self.output_dir / domain / "chunks.json"

            if not chunks_path.exists():
                return (
                    f"Sorry, I don't have scraped data for {domain}. "
                    "Please ensure the company has been downloaded and scraped."
                )

            with chunks_path.open("r", encoding="utf-8") as f:
                chunks = json.load(f)

            if not chunks:
                return f"Sorry, no scraped content available for {domain}."

            profile = {}
            profile_path = self.base_dir / "output" / domain / "profile.json"
            if profile_path.exists():
                with profile_path.open("r", encoding="utf-8") as f:
                    profile = json.load(f)

            question_lower = question.lower()
            question_keywords = question_lower.split()

            scored_chunks = []
            for chunk in chunks:
                score = 0
                text_lower = chunk.get("text", "").lower()
                section_lower = chunk.get("section", "").lower()

                for keyword in question_keywords:
                    if len(keyword) > 3:
                        if keyword in text_lower:
                            score += 2
                        if keyword in section_lower:
                            score += 3

                if any(
                    kw in section_lower
                    for kw in ["contact", "service", "team", "about", "leadership"]
                ):
                    score += 1

                scored_chunks.append((score, chunk))

            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            relevant_chunks = [
                chunk for _, chunk in scored_chunks[:20] if _ > 0
            ] or [chunk for _, chunk in scored_chunks[:15]]

            context = self._build_context(profile, relevant_chunks)

            company_name = profile.get(
                "company_name", domain.replace(".com", "").replace(".", "").title()
            )
            domain_base = domain.replace(".com", "").replace(".co.uk", "").replace(".", "")

            system_prompt = (
                "You are a company intelligence analyst. "
                "Answer questions using ONLY the scraped website content provided below. "
                "The domain and company name refer to the SAME company. "
                "Be concise, factual, and direct. "
                "If information is not in the provided content, say "
                "'Information not available in the scraped content.'"
            )

            user_prompt = (
                f"Company Information:\n"
                f"- Domain: {domain}\n"
                f"- Company Name: {company_name}\n\n"
                f"SCRAPED WEBSITE CONTENT:\n{context}\n\n"
                f"Question: {question}\n\n"
                f"Answer based ONLY on the scraped content above."
            )

            return chat_completion(
                self.llm_config,
                system_prompt,
                user_prompt,
                timeout=60,
                max_tokens=300,
            )

        except Exception as e:
            logger.error("Error getting chatbot response: %s", e)
            provider = self.llm_config.provider
            hint = (
                "Set LLM_API_URL / LLM_PROVIDER (Ollama) or LLM_API_KEY + LLM_API_URL (OpenAI-compatible) "
                "on your server — see .env.example."
            )
            return f"Sorry, I couldn't reach the AI service ({provider}). {hint} Details: {e}"

    def _build_context(self, profile: Dict, chunks: list) -> str:
        context_parts = []

        if profile.get("company_name"):
            context_parts.append(f"Company: {profile['company_name']}")
        if profile.get("industry"):
            context_parts.append(f"Industry: {profile['industry']}")

        if chunks:
            relevant_chunks = []
            for chunk in chunks:
                section = chunk.get("section", "").lower()
                if any(
                    kw in section
                    for kw in ["contact", "about", "service", "team", "leadership", "product"]
                ):
                    relevant_chunks.append(chunk)

            chunks_to_use = relevant_chunks[:15] if relevant_chunks else chunks[:15]

            chunk_texts = []
            for chunk in chunks_to_use:
                section = chunk.get("section", "")
                page = chunk.get("page", "")
                text = chunk.get("text", "")
                structured = chunk.get("structured_data", {})
                chunk_info = f"[Page: {page}] [Section: {section}]"
                if structured:
                    if structured.get("emails"):
                        chunk_info += f" [Emails: {', '.join(structured['emails'])}]"
                    if structured.get("phones"):
                        chunk_info += f" [Phones: {', '.join(structured['phones'])}]"
                chunk_texts.append(f"{chunk_info}\n{text[:500]}")

            context_parts.append(
                "\n\n=== SCRAPED WEBSITE CONTENT ===\n" + "\n\n---\n\n".join(chunk_texts)
            )
        elif profile.get("description_long"):
            context_parts.append(f"Description: {profile['description_long']}")

        return "\n".join(context_parts)
