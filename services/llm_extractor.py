import json
import logging
import re
from pathlib import Path
from typing import Dict, List

import requests

from .csv_loader import Company


logger = logging.getLogger(__name__)


def _load_chunks(chunks_path: Path) -> List[Dict]:
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {chunks_path}")
    with chunks_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _build_prompt_text(domain: str, chunks: List[Dict]) -> str:
    # Aggregate text while keeping source context lightweight
    # Prioritize contact and social media chunks
    # Limit to first 150 chunks and truncate very long chunks to prevent token overflow
    lines: List[str] = []
    max_chunks = 150
    max_chunk_length = 2000  # Limit each chunk to 2000 chars
    
    # Separate chunks by priority
    priority_chunks = []  # Contact, Social Media, Team, Leadership sections
    other_chunks = []
    
    for ch in chunks:
        section = ch.get("section", "").lower()
        if any(keyword in section for keyword in ["contact", "social", "team", "leadership", "about", "location", "office"]):
            priority_chunks.append(ch)
        else:
            other_chunks.append(ch)
    
    # Process priority chunks first, then others
    processed_chunks = priority_chunks[:max_chunks] + other_chunks[:max_chunks - len(priority_chunks)]
    
    for ch in processed_chunks[:max_chunks]:
        section = ch.get("section", "")
        page = ch.get("page", "")
        txt = ch.get("text", "")
        if not txt:
            continue
        
        # Include structured data if available - this is CRITICAL for accurate extraction
        structured = ch.get("structured_data", {})
        if structured:
            structured_parts = []
            if structured.get("emails"):
                structured_parts.append(f"EMAILS: {', '.join(structured['emails'])}")
            if structured.get("phones"):
                structured_parts.append(f"PHONES: {', '.join(structured['phones'])}")
            if structured.get("addresses"):
                structured_parts.append(f"ADDRESSES: {', '.join(structured['addresses'])}")
            if structured.get("social_links"):
                social_text = "SOCIAL LINKS: " + ", ".join([f"{k}: {v}" for k, v in structured["social_links"].items() if v])
                structured_parts.append(social_text)
            if structured.get("company_details"):
                company_details = structured["company_details"]
                if company_details.get("company_registration"):
                    structured_parts.append(f"COMPANY REGISTRATION: {company_details['company_registration']}")
                if company_details.get("vat_number"):
                    structured_parts.append(f"VAT NUMBER: {company_details['vat_number']}")
                if company_details.get("hours_of_operation"):
                    structured_parts.append(f"HOURS OF OPERATION: {company_details['hours_of_operation']}")
            if structured.get("people"):
                people_text = "PEOPLE: " + ", ".join([f"{p.get('name', '')} - {p.get('title', '')}" for p in structured["people"] if p.get("name")])
                if people_text != "PEOPLE: ":
                    structured_parts.append(people_text)
            if structured_parts:
                txt = "\n".join(structured_parts) + "\n\n" + txt
        
        # Truncate very long chunks
        if len(txt) > max_chunk_length:
            txt = txt[:max_chunk_length] + "..."
        lines.append(f"[PAGE: {page}] [SECTION: {section}]\n{txt}")
    
    result = "\n\n".join(lines)
    # Add summary if we truncated
    if len(chunks) > max_chunks:
        result += f"\n\n[NOTE: Showing first {max_chunks} of {len(chunks)} total chunks]"
    return result


def _call_ollama(model: str, system_prompt: str, user_prompt: str, api_url: str, temperature: float = 0.0) -> str:
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = requests.post(api_url, json=payload, timeout=600)
        response.raise_for_status()
        data = response.json()

        # Ollama's /chat returns {"message": {"content": "..."}}
        content = ""
        if isinstance(data, dict):
            msg = data.get("message") or {}
            content = msg.get("content") or ""
        if not content:
            raise ValueError("Empty response from Ollama")
        return content.strip()
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out after 600 seconds")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error("Could not connect to Ollama at %s: %s", api_url, e)
        raise ValueError(f"Could not connect to Ollama: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error("Ollama HTTP error: %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error calling Ollama: %s", e)
        raise


def _ensure_valid_json(raw: str) -> Dict:
    """Extract and validate JSON from LLM response, handling common formatting issues"""
    # Strip accidental fences or leading/trailing junk
    text = raw.strip()
    
    # Remove markdown code fences
    if text.startswith("```json"):
        text = text[7:].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    
    # Remove leading/trailing whitespace and newlines
    text = text.strip()
    
    # Try plain json first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to isolate JSON object - find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Try to fix common issues
                # Remove trailing commas before closing braces/brackets
                candidate = re.sub(r',(\s*[}\]])', r'\1', candidate)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
        
        # Last resort: try to extract any valid JSON structure
        logger.warning(f"Failed to parse JSON, attempting recovery. Raw text length: {len(text)}")
        # Look for JSON-like structures
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        raise ValueError(f"Could not extract valid JSON from LLM response. First 500 chars: {text[:500]}")


def _calculate_extraction_confidence(profile_data: Dict) -> float:
    """
    Calculate extraction confidence based on how many important fields are filled.
    Returns a float between 0.0 and 1.0.
    """
    # Define important fields and their weights
    field_weights = {
        # Critical fields (high weight)
        "company_name": 10,
        "domain": 5,  # Always present, so low weight
        "description_short": 8,
        "description_long": 8,
        "industry": 7,
        "headquarters": 6,
        "contact_email": 6,  # contact.email
        "contact_phone": 6,  # contact.phone
        
        # Important fields (medium weight)
        "sub_industry": 5,
        "business_type": 5,
        "company_size": 5,
        "locations": 5,  # Array - count if has items
        "services": 6,  # Array - count if has items
        "products": 5,  # Array - count if has items
        "technology_signals": 4,  # Array - count if has items
        "sectors": 4,  # Array - count if has items
        
        # Contact details
        "contact_full_address": 4,
        "contact_sales_phone": 3,
        "contact_other_numbers": 2,
        "contact_hours": 2,
        
        # People/Leadership
        "leadership": 5,  # Array - count if has items
        "people": 4,  # Array - count if has items
        
        # Certifications
        "certifications": 4,  # Array - count if has items
        
        # Social media
        "social_linkedin": 3,
        "social_facebook": 2,
        "social_x": 2,
        "social_instagram": 2,
        "social_youtube": 2,
        
        # Registration details
        "company_registration": 4,
        "vat_number": 3,
        "domain_status": 2,
        "acronym": 2,
        "ssc_code": 2,
        "logo_url": 2,
    }
    
    # Helper to check if a value is "filled" (not empty, not None, not empty string/array)
    def is_filled(value):
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list):
            return len(value) > 0
        if isinstance(value, dict):
            return len(value) > 0 and any(is_filled(v) for v in value.values())
        return True
    
    total_weight = 0
    filled_weight = 0
    
    # Check each field
    for field_key, weight in field_weights.items():
        total_weight += weight
        
        # Handle nested fields (contact.*, social.*)
        if field_key.startswith("contact_"):
            nested_key = field_key.replace("contact_", "")
            value = profile_data.get("contact", {}).get(nested_key, "")
        elif field_key.startswith("social_"):
            nested_key = field_key.replace("social_", "")
            value = profile_data.get("social", {}).get(nested_key, "")
        else:
            value = profile_data.get(field_key, "")
        
        if is_filled(value):
            filled_weight += weight
    
    # Calculate confidence (0.0 to 1.0)
    if total_weight == 0:
        return 0.0
    
    confidence = filled_weight / total_weight
    
    # Round to 2 decimal places and ensure it's between 0.0 and 1.0
    return max(0.0, min(1.0, round(confidence, 2)))


def _default_profile_schema(domain: str) -> Dict:
    return {
        "company_name": "",
        "domain": domain,
        "description_short": "",
        "description_long": "",
        "industry": "",
        "sub_industry": "",
        "sectors": [],
        "ssc_code": "",
        "products": [],
        # Extended company information
        "domain_status": "",
        "company_registration": "",
        "vat_number": "",
        "acronym": "",
        "logo_url": "",
        "headquarters": "",
        "locations": [],
        # People / leadership
        "leadership": [],
        "people": [],
        # Contact information
        "contact": {
            "domain": "",
            "company_name": "",
            "full_address": "",
            "phone": "",
            "sales_phone": "",
            "fax": "",
            "mobile": "",
            "other_numbers": [],
            "email": "",
            "hours_of_operation": "",
            "hq_indicator": "",
        },
        # Social media
        "social": {
            "linkedin": "",
            "facebook": "",
            "x": "",
            "instagram": "",
            "youtube": "",
            "blog": "",
            "articles": "",
        },
        # Certifications and services
        "certifications": [],
        "services": [],
        "business_type": "",
        "company_size": "",
        "technology_signals": [],
        "extraction_confidence": 0.0,
    }


def extract_profile_for_company(
    company: Company,
    output_dir: Path,
    settings: Dict,
    base_dir: Path,
) -> str:
    """
    Run LLaMA-3 via Ollama over chunks.json and produce profile.json.

    Returns: 'profile_generated' or 'failed_llm'.
    """
    domain_output_dir = output_dir / company.domain
    chunks_path = domain_output_dir / "chunks.json"
    profile_path = domain_output_dir / "profile.json"

    try:
        chunks = _load_chunks(chunks_path)
    except Exception as e:
        logger.error("Failed to load chunks for %s: %s", company.domain, e)
        return "failed_llm"

    if not chunks:
        logger.error("No chunks available for %s", company.domain)
        return "failed_llm"

    llm_cfg = settings.get("llm", {})
    model = llm_cfg.get("model", "llama3")
    temperature = float(llm_cfg.get("temperature", 0.0))
    api_url = llm_cfg.get("api_url", "http://localhost:11434/api/chat")

    prompt_path = base_dir / "prompts" / "profile_extraction.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with prompt_path.open("r", encoding="utf-8") as f:
        system_prompt = f.read()

    text_corpus = _build_prompt_text(company.domain, chunks)

    user_prompt = (
        "You are an information extraction engine. "
        "Using ONLY the content below, extract a company profile according to the required JSON schema. "
        "Output strictly valid JSON with no markdown, comments, or extra text.\n\n"
        f"DOMAIN: {company.domain}\n\n"
        "CONTENT:\n"
        f"{text_corpus}\n\n"
        "IMPORTANT: Return ONLY valid JSON. No markdown fences, no explanations, no comments. "
        "Start with { and end with }. All fields should be at the root level, not nested."
    )

    profile_data: Dict
    last_error: Exception | None = None

    for attempt in range(2):  # one retry allowed
        try:
            raw = _call_ollama(model=model, system_prompt=system_prompt, user_prompt=user_prompt, api_url=api_url, temperature=temperature)
            parsed = _ensure_valid_json(raw)
            profile_data = _default_profile_schema(company.domain)
            
            # Handle nested structures if LLM returns them
            if isinstance(parsed, dict):
                # Extract from nested "Company Profile" structure if present
                if "Company Profile" in parsed and isinstance(parsed["Company Profile"], dict):
                    nested = parsed["Company Profile"]
                    # Map nested fields to flat structure
                    if "Name" in nested and not parsed.get("company_name"):
                        parsed["company_name"] = nested["Name"]
                    if "Description" in nested:
                        if not parsed.get("description_long"):
                            parsed["description_long"] = nested["Description"]
                        if not parsed.get("description_short"):
                            desc = nested["Description"]
                            words = desc.split()[:50]
                            parsed["description_short"] = " ".join(words)
                    if "Industry" in nested and not parsed.get("industry"):
                        parsed["industry"] = nested["Industry"]
                    if "Services" in nested and not parsed.get("services"):
                        parsed["services"] = nested["Services"]
                    if "Certifications" in nested and not parsed.get("certifications"):
                        parsed["certifications"] = nested["Certifications"]
                    if "Leadership" in nested and not parsed.get("leadership"):
                        parsed["leadership"] = nested["Leadership"]
                    # Remove nested structure after extraction
                    del parsed["Company Profile"]
                
                # Handle "Products/Services" nested object - convert to services array
                if "Products/Services" in parsed and isinstance(parsed["Products/Services"], dict):
                    services_dict = parsed["Products/Services"]
                    services_list = []
                    for service_name, service_desc in services_dict.items():
                        if service_name and service_name.strip():
                            service_obj = {
                                "name": service_name.strip(),
                                "type": "service"
                            }
                            if service_desc and isinstance(service_desc, str) and service_desc.strip():
                                service_obj["description"] = service_desc.strip()[:200]
                            services_list.append(service_obj)
                    if services_list:
                        # Merge with existing services or replace if empty
                        existing_services = parsed.get("services", [])
                        if not existing_services or len(existing_services) == 0:
                            parsed["services"] = services_list
                        else:
                            # Merge, avoiding duplicates
                            existing_names = {s.get("name", "") for s in existing_services if isinstance(s, dict)}
                            for new_service in services_list:
                                if new_service.get("name", "") not in existing_names:
                                    existing_services.append(new_service)
                            parsed["services"] = existing_services
                
                # Handle "Add-on Services" nested object
                if "Add-on Services" in parsed and isinstance(parsed["Add-on Services"], dict):
                    addon_dict = parsed["Add-on Services"]
                    addon_list = []
                    for service_name, service_desc in addon_dict.items():
                        if service_name and service_name.strip():
                            addon_list.append({
                                "name": service_name.strip(),
                                "type": "add-on"
                            })
                    if addon_list:
                        existing_services = parsed.get("services", [])
                        if not isinstance(existing_services, list):
                            existing_services = []
                        # Merge add-on services
                        existing_names = {s.get("name", "") for s in existing_services if isinstance(s, dict)}
                        for addon in addon_list:
                            if addon.get("name", "") not in existing_names:
                                existing_services.append(addon)
                        parsed["services"] = existing_services
                
                # Extract business_type from description if empty
                if not parsed.get("business_type") or not parsed.get("business_type").strip():
                    desc = (parsed.get("description_long") or parsed.get("description_short") or "").lower()
                    if "saas" in desc or "software as a service" in desc:
                        parsed["business_type"] = "SaaS"
                    elif "b2b" in desc or "business to business" in desc:
                        parsed["business_type"] = "B2B"
                    elif "b2c" in desc or "business to consumer" in desc:
                        parsed["business_type"] = "B2C"
                    elif "platform" in desc:
                        parsed["business_type"] = "Platform"
                    elif "consulting" in desc or "advisory" in desc:
                        parsed["business_type"] = "Consulting"
                
                # Extract sectors from industry if empty
                if (not parsed.get("sectors") or len(parsed.get("sectors", [])) == 0) and parsed.get("industry"):
                    industry = parsed["industry"].lower()
                    sectors = []
                    if "health" in industry or "medical" in industry:
                        sectors.append("Healthcare")
                    if "tech" in industry or "technology" in industry:
                        sectors.append("Technology")
                    if "finance" in industry or "fintech" in industry:
                        sectors.append("Finance")
                    if "compliance" in industry or "security" in industry:
                        sectors.append("Compliance")
                    if sectors:
                        parsed["sectors"] = sectors
            
            # Update profile with parsed data
            profile_data.update(parsed or {})
            
            # Handle extraction_confidence from parsed data (might be in root or meta object)
            if isinstance(parsed, dict):
                # Check if LLM returned it in meta object
                if "meta" in parsed and isinstance(parsed["meta"], dict):
                    if "extraction_confidence" in parsed["meta"]:
                        profile_data["extraction_confidence"] = float(parsed["meta"]["extraction_confidence"])
                    # Remove meta object after extraction
                    del parsed["meta"]
                # Also check root level (if LLM returned it directly)
                elif "extraction_confidence" in parsed and parsed["extraction_confidence"] is not None:
                    try:
                        profile_data["extraction_confidence"] = float(parsed["extraction_confidence"])
                    except (ValueError, TypeError):
                        pass  # Will calculate below
            
            # Post-process: Extract basic info from chunks if fields are still empty
            if not profile_data.get("company_name") or profile_data.get("company_name") == "Unknown":
                # Try to extract from page titles
                for chunk in chunks[:10]:  # Check first 10 chunks
                    page_title = chunk.get("page_title", "")
                    if page_title and "|" in page_title:
                        # Extract company name from title (usually before |)
                        potential_name = page_title.split("|")[0].strip()
                        if potential_name and len(potential_name) < 100:
                            profile_data["company_name"] = potential_name
                            break
                    # Also check meta description
                    meta_desc = chunk.get("meta_description", "")
                    if meta_desc and not profile_data.get("description_long"):
                        profile_data["description_long"] = meta_desc
                        words = meta_desc.split()[:50]
                        profile_data["description_short"] = " ".join(words)
            
            # Post-process: Normalize services - convert strings to objects if needed
            services = profile_data.get("services", [])
            if services:
                normalized_services = []
                for svc in services:
                    if isinstance(svc, str) and svc.strip():
                        normalized_services.append({
                            "name": svc.strip(),
                            "type": "service"
                        })
                    elif isinstance(svc, dict):
                        normalized_services.append({
                            "name": svc.get("name", svc.get("title", "")).strip() if svc.get("name") or svc.get("title") else "",
                            "type": svc.get("type", svc.get("category", "service")).strip() if svc.get("type") or svc.get("category") else "service"
                        })
                if normalized_services:
                    profile_data["services"] = normalized_services
            
            # Post-process: Extract services from chunks and description if services array is empty
            if not profile_data.get("services") or len(profile_data.get("services", [])) == 0 or all(not s.get("name", "").strip() for s in profile_data.get("services", [])):
                found_services = []
                # First check chunks for service sections
                for chunk in chunks[:100]:
                    section = chunk.get("section", "").lower()
                    text = chunk.get("text", "")
                    if any(kw in section for kw in ["service", "product", "solution", "offering", "what we do"]):
                        # Extract service names from section text
                        lines = text.split('\n')
                        for line in lines:
                            line = line.strip()
                            # Skip very short lines or common prefixes
                            if len(line) > 5 and not line.lower().startswith(('the ', 'our ', 'we ', 'a ', 'an ')):
                                # Check if it looks like a service name (not a full sentence)
                                if len(line) < 80 and not line.endswith('.'):
                                    # Clean up common prefixes
                                    service_name = re.sub(r'^(Services?|Products?|Solutions?|Offerings?)[:\s]+', '', line, flags=re.IGNORECASE).strip()
                                    if service_name and len(service_name) > 3:
                                        found_services.append(service_name[:100])
                
                # Also check description
                desc = profile_data.get("description_long", "") or profile_data.get("description_short", "")
                if desc and len(found_services) < 5:
                    # Look for service keywords in description
                    service_keywords = ["software", "platform", "solution", "service", "tool", "compliance", "certification", "framework", "consulting", "audit", "security", "payment"]
                    desc_lower = desc.lower()
                    for keyword in service_keywords:
                        if keyword in desc_lower:
                            # Try to extract service name from context
                            idx = desc_lower.find(keyword)
                            start = max(0, idx - 30)
                            end = min(len(desc), idx + 50)
                            context = desc[start:end]
                            # Extract potential service name
                            words = context.split()
                            for i, word in enumerate(words):
                                if keyword in word.lower():
                                    # Get surrounding words as service name
                                    service_name = " ".join(words[max(0, i-2):min(len(words), i+3)])
                                    service_name = service_name.strip('.,;:')
                                    if len(service_name) > 5 and service_name not in found_services:
                                        found_services.append(service_name[:100])  # Limit length
                
                if found_services:
                    # Remove duplicates and empty strings
                    unique_services = []
                    seen = set()
                    for svc in found_services:
                        svc_lower = svc.lower().strip()
                        if svc_lower and svc_lower not in seen and len(svc_lower) > 3:
                            seen.add(svc_lower)
                            unique_services.append(svc)
                    if unique_services:
                        profile_data["services"] = [{"name": s, "type": "service"} for s in unique_services[:10]]
            
            # Post-process: Extract industry from description if empty
            if not profile_data.get("industry"):
                desc = profile_data.get("description_long", "") or profile_data.get("description_short", "")
                if desc:
                    desc_lower = desc.lower()
                    industry_keywords = {
                        "technology": ["software", "tech", "platform", "saas", "cloud"],
                        "compliance": ["compliance", "certification", "audit", "security"],
                        "consulting": ["consulting", "advisory", "services"],
                        "healthcare": ["health", "medical", "healthcare"],
                        "finance": ["financial", "fintech", "banking", "finance"]
                    }
                    for industry, keywords in industry_keywords.items():
                        if any(kw in desc_lower for kw in keywords):
                            profile_data["industry"] = industry.capitalize()
                            break
            
            # Post-process: Normalize certifications - convert strings to array if needed
            certs = profile_data.get("certifications", [])
            if certs:
                normalized_certs = []
                for cert in certs:
                    if isinstance(cert, str) and cert.strip():
                        normalized_certs.append(cert.strip())
                    elif isinstance(cert, dict):
                        cert_name = cert.get("name", cert.get("Name", "")).strip()
                        if cert_name:
                            normalized_certs.append(cert_name)
                if normalized_certs:
                    profile_data["certifications"] = list(set(normalized_certs))  # Remove duplicates
            
            # Post-process: Extract certifications from description or chunks if still empty
            if not profile_data.get("certifications") or len(profile_data.get("certifications", [])) == 0:
                cert_keywords = ["ISO 27001", "SOC 2", "GDPR", "NIST", "DORA", "CAF", "NIS", "ISO", "certified", "certification", "DTAC", "MDR"]
                found_certs = []
                # Check description
                desc = (profile_data.get("description_long", "") + " " + profile_data.get("description_short", "")).lower()
                for cert in cert_keywords:
                    if cert.lower() in desc:
                        found_certs.append(cert)
                # Check chunks
                if not found_certs:
                    for chunk in chunks[:30]:
                        text = chunk.get("text", "").lower()
                        for cert in cert_keywords:
                            if cert.lower() in text and cert not in found_certs:
                                found_certs.append(cert)
                if found_certs:
                    profile_data["certifications"] = list(set(found_certs))  # Remove duplicates
            
            # Post-process: Normalize contact.email - ensure it's a string, not an array
            # Handle both cases: if LLM returns email as array, or if it's already set from parsed data
            if profile_data.get("contact", {}).get("email"):
                email_val = profile_data["contact"]["email"]
                if isinstance(email_val, list):
                    # If LLM returned email as array, use first valid email
                    valid_emails = [e for e in email_val if isinstance(e, str) and e.strip() and "@" in e]
                    profile_data["contact"]["email"] = valid_emails[0] if valid_emails else ""
                elif isinstance(email_val, str) and email_val.strip():
                    # Already a string, ensure it's clean (remove trailing characters that might be from parsing errors)
                    email_val = email_val.strip()
                    # Extract just the email part if there's trailing text (e.g., "sales@aculab.comHead" -> "sales@aculab.com")
                    email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', email_val)
                    if email_match:
                        profile_data["contact"]["email"] = email_match.group(1)
                    else:
                        profile_data["contact"]["email"] = email_val
                elif not isinstance(email_val, str):
                    profile_data["contact"]["email"] = str(email_val) if email_val else ""
            
            # Post-process: Extract contact information from structured_data in chunks FIRST
            # This is more reliable than regex extraction
            for chunk in chunks:
                structured = chunk.get("structured_data", {})
                if structured:
                    # Extract emails from structured_data
                    if not profile_data.get("contact", {}).get("email") and structured.get("emails"):
                        valid_emails = [e for e in structured["emails"] if not any(x in e.lower() for x in ["example.com", "test.com", "domain.com", "noreply", "no-reply"])]
                        if valid_emails:
                            # Clean email - extract just the email part using regex (handles cases where email has extra text)
                            email = valid_emails[0]
                            # Extract clean email - handle cases like "info@acorncompliance.comDon"
                            # Find email pattern and extract only up to valid TLD
                            email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:com|co\.uk|org|net|io|ai|uk|us|eu|de|fr|it|es|nl|be|ch|at|se|no|dk|fi|pl|cz|ie|pt|gr|ro|hu|bg|hr|sk|si|lt|lv|ee|lu|mt|cy)[A-Z]?)', email, re.IGNORECASE)
                            if email_match:
                                matched = email_match.group(1)
                                # If match ends with capital letter, it's likely trailing text
                                if matched and matched[-1].isupper() and len(matched) > 1:
                                    # Remove last character if it's capital and not part of TLD
                                    profile_data["contact"]["email"] = matched[:-1] if matched[-2].islower() else matched
                                else:
                                    profile_data["contact"]["email"] = matched
                            else:
                                # Fallback: simple extraction and manual cleanup
                                email_match2 = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', email)
                                if email_match2:
                                    matched = email_match2.group(1)
                                    # Remove trailing capital letters that aren't part of email
                                    while matched and matched[-1].isupper() and len(matched) > 5:
                                        # Check if last 3 chars form a valid TLD pattern
                                        if not re.search(r'\.[a-z]{2,3}$', matched, re.IGNORECASE):
                                            matched = matched[:-1]
                                        else:
                                            break
                                    profile_data["contact"]["email"] = matched
                                else:
                                    profile_data["contact"]["email"] = email.split()[0] if email else ""
                    
                    # Extract phones from structured_data - prioritize longer/more complete numbers
                    if structured.get("phones"):
                        phones = structured["phones"]
                        # Sort by length (longer = more complete) and prefer +44 format
                        phones_sorted = sorted(phones, key=lambda p: (p.startswith("+44"), len(p)), reverse=True)
                        contact = profile_data.get("contact", {})
                        if not contact.get("phone") and phones_sorted:
                            contact["phone"] = phones_sorted[0].strip()
                        # Extract additional phone numbers
                        if len(phones_sorted) > 1 and not contact.get("sales_phone"):
                            # Try to identify sales phone
                            for phone in phones_sorted[1:]:
                                phone_lower = phone.lower()
                                if "sales" in phone_lower or "support" in phone_lower:
                                    contact["sales_phone"] = phone.strip()
                                    break
                            if not contact.get("sales_phone") and len(phones_sorted) > 1:
                                contact["sales_phone"] = phones_sorted[1].strip()
                        if len(phones_sorted) > 2 and not contact.get("mobile"):
                            # Mobile often has different format or keyword
                            for phone in phones_sorted:
                                phone_lower = phone.lower()
                                if "mobile" in phone_lower or "cell" in phone_lower or len(phone.replace(" ", "").replace("-", "")) == 11:
                                    contact["mobile"] = phone.strip()
                                    break
                        if len(phones_sorted) > 3:
                            # Store remaining as other_numbers
                            used_phones = {contact.get("phone", ""), contact.get("sales_phone", ""), contact.get("mobile", "")}
                            other_nums = [p.strip() for p in phones_sorted if p.strip() not in used_phones]
                            if other_nums:
                                contact["other_numbers"] = other_nums[:5]  # Limit to 5
                    
                    # Extract addresses from structured_data
                    if structured.get("addresses") and not profile_data.get("headquarters"):
                        addresses = structured["addresses"]
                        if addresses:
                            profile_data["headquarters"] = addresses[0]
                            if not profile_data.get("contact", {}).get("full_address"):
                                profile_data["contact"]["full_address"] = addresses[0]
                    
                    # Extract company details from structured_data
                    company_details = structured.get("company_details", {})
                    if company_details:
                        if company_details.get("company_registration") and not profile_data.get("company_registration"):
                            profile_data["company_registration"] = company_details["company_registration"]
                        if company_details.get("vat_number") and not profile_data.get("vat_number"):
                            profile_data["vat_number"] = company_details["vat_number"]
                        if company_details.get("hours_of_operation") and not profile_data.get("contact", {}).get("hours_of_operation"):
                            profile_data["contact"]["hours_of_operation"] = company_details["hours_of_operation"]
            
            # Fallback: Extract company registration from text chunks if not found in structured_data
            if not profile_data.get("company_registration"):
                for chunk in chunks[:50]:
                    text = chunk.get("text", "")
                    # Look for "company number 09617420" pattern
                    reg_match = re.search(r'registered.*?company\s+number\s+(\d{8})', text, re.IGNORECASE)
                    if reg_match:
                        profile_data["company_registration"] = reg_match.group(1)
                        break
                    # Also try other patterns
                    reg_match2 = re.search(r'company\s+number[:\s]+(\d{8})', text, re.IGNORECASE)
                    if reg_match2:
                        profile_data["company_registration"] = reg_match2.group(1)
                        break
            
            # Fallback: Extract addresses from text chunks if not found in structured_data
            if not profile_data.get("headquarters") or not profile_data.get("contact", {}).get("full_address"):
                for chunk in chunks[:50]:
                    text = chunk.get("text", "")
                    # Look for "Trading address at" pattern - capture until postcode (handle "UK. CW9 7UT" format)
                    addr_match = re.search(r'Trading\s+address\s+at\s+([^\.]{20,250}?)(?:\.\s+)?([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})', text, re.IGNORECASE)
                    if addr_match:
                        addr_part1 = addr_match.group(1).strip()
                        postcode = addr_match.group(2).strip()
                        # Remove trailing "UK" if present
                        addr_part1 = re.sub(r'\s+UK\.?\s*$', '', addr_part1).strip()
                        addr = (addr_part1 + " " + postcode).strip()
                        if len(addr) > 20:
                            profile_data["headquarters"] = addr
                            if not profile_data.get("contact", {}).get("full_address"):
                                profile_data["contact"]["full_address"] = addr
                            break
                    # Look for "Registered office address" pattern with postcode
                    if not profile_data.get("headquarters"):
                        addr_match2 = re.search(r'Registered\s+office\s+address\s+([^\.]{20,200}?)(?:\.\s+)?([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})', text, re.IGNORECASE)
                        if addr_match2:
                            addr_part1 = addr_match2.group(1).strip()
                            postcode = addr_match2.group(2).strip()
                            addr = (addr_part1 + " " + postcode).strip()
                            if len(addr) > 20:
                                profile_data["headquarters"] = addr
                                if not profile_data.get("contact", {}).get("full_address"):
                                    profile_data["contact"]["full_address"] = addr
                                break
                    
                    # Extract people from structured_data
                    if structured.get("people") and (not profile_data.get("people") or len(profile_data.get("people", [])) == 0):
                        people_list = []
                        for person in structured["people"][:50]:  # Limit to 50
                            people_list.append({
                                "people_name": person.get("name", ""),
                                "people_title": person.get("title", ""),
                                "people_email": "",
                                "url": ""
                            })
                        if people_list:
                            profile_data["people"] = people_list
                    
                    # Extract social links from structured_data
                    social = profile_data.get("social", {})
                    if structured.get("social_links"):
                        for platform, url in structured["social_links"].items():
                            if platform == "linkedin" and not social.get("linkedin"):
                                social["linkedin"] = url
                            elif platform == "facebook" and not social.get("facebook"):
                                social["facebook"] = url
                            elif platform == "x" and not social.get("x"):
                                social["x"] = url
                            elif platform == "instagram" and not social.get("instagram"):
                                social["instagram"] = url
                            elif platform == "youtube" and not social.get("youtube"):
                                social["youtube"] = url
            
            # Fallback: Extract contact information from chunk text if not found in structured_data
            if not profile_data.get("contact", {}).get("email"):
                for chunk in chunks[:100]:
                    text = chunk.get("text", "")
                    # Look for email patterns
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, text)
                    if emails:
                        # Filter out common non-company emails
                        valid_emails = [e for e in emails if not any(x in e.lower() for x in ["example.com", "test.com", "domain.com", "noreply", "no-reply"])]
                        if valid_emails:
                            profile_data["contact"]["email"] = valid_emails[0]
                            break
            
            if not profile_data.get("contact", {}).get("phone"):
                for chunk in chunks[:100]:
                    text = chunk.get("text", "")
                    # Look for phone patterns (UK format)
                    phone_patterns = [
                        r'\+44\s?\d{2,4}\s?\d{3,4}\s?\d{3,4}',  # +44 format
                        r'0\d{2,4}\s?\d{3,4}\s?\d{3,4}',  # UK landline
                        r'\d{5}\s?\d{6}',  # UK mobile
                    ]
                    for pattern in phone_patterns:
                        phones = re.findall(pattern, text)
                        if phones:
                            profile_data["contact"]["phone"] = phones[0].strip()
                            break
                    if profile_data.get("contact", {}).get("phone"):
                        break
            
            # Fallback: Extract social media links from chunk text if not found in structured_data
            social = profile_data.get("social", {})
            if not social.get("linkedin"):
                for chunk in chunks[:100]:
                    text = chunk.get("text", "")
                    linkedin_pattern = r'(?:linkedin\.com/company/|linkedin\.com/in/)([a-zA-Z0-9-]+)'
                    match = re.search(linkedin_pattern, text, re.IGNORECASE)
                    if match:
                        social["linkedin"] = f"https://linkedin.com/company/{match.group(1)}"
                        break
            
            # Post-process: Extract leadership/people from chunks
            if not profile_data.get("leadership") or len(profile_data.get("leadership", [])) == 0:
                leadership_keywords = ["CEO", "CTO", "CFO", "Founder", "Director", "President", "VP", "Vice President", "Chief", "Head of", "Managing Director", "Co-Founder", "Co Founder"]
                found_leadership = []
                for chunk in chunks[:300]:
                    text = chunk.get("text", "")
                    section = chunk.get("section", "").lower()
                    # Look in Team, Leadership, About sections, or any chunk with leadership keywords
                    if any(kw in section for kw in ["team", "leadership", "about", "management", "executive", "founder"]) or any(kw.lower() in text.lower() for kw in leadership_keywords):
                        # Try multiple patterns
                        # Pattern 1: "Name Title" or "Name Title Description" - improved regex
                        for title_kw in leadership_keywords:
                            # Look for patterns like "Michael Bell Co-Founder" or "Name Co-Founder LinkedIn"
                            # Match: 1-3 capitalized words (name) followed by title
                            pattern1 = rf'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){{0,2}})\s+{re.escape(title_kw)}\b'
                            matches1 = re.finditer(pattern1, text, re.IGNORECASE)
                            for match in matches1:
                                name = match.group(1).strip()
                                # Clean up name - remove common prefixes and validate
                                name = re.sub(r'^(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Our|The)\s*', '', name, flags=re.IGNORECASE)
                                name = re.sub(r'\s+', ' ', name).strip()
                                # Validate name (should be 2-4 words, each starting with capital)
                                name_parts = name.split()
                                if len(name_parts) >= 1 and len(name_parts) <= 4 and all(p[0].isupper() for p in name_parts if p):
                                    if name and len(name) > 2 and len(name) < 50:
                                        if not any(l.get("name", "").lower() == name.lower() for l in found_leadership):
                                            found_leadership.append({
                                                "name": name,
                                                "title": title_kw,
                                                "role_type": "executive" if any(t in title_kw.lower() for t in ["ceo", "cto", "cfo", "president", "founder", "director"]) else "other"
                                            })
                        
                        # Pattern 2: Split by lines and look for name-title patterns
                        lines = text.split("\n")
                        for line in lines:
                            line_stripped = line.strip()
                            if not line_stripped or len(line_stripped) < 5:
                                continue
                            line_lower = line_lower = line_stripped.lower()
                            for title_kw in leadership_keywords:
                                if title_kw.lower() in line_lower:
                                    # Try to extract name before title
                                    parts = line_stripped.split(title_kw)
                                    if len(parts) > 0:
                                        name = parts[0].strip()
                                        # Clean up name - remove common prefixes
                                        name = re.sub(r'^(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Our|The|Senior|Junior)\s*', '', name, flags=re.IGNORECASE)
                                        name = re.sub(r'\s+', ' ', name).strip()
                                        # Validate name (should be 1-4 words, each starting with capital)
                                        name_parts = name.split()
                                        if not (len(name_parts) >= 1 and len(name_parts) <= 4 and all(p[0].isupper() for p in name_parts if p)):
                                            continue
                                        
                                        # Extract title
                                        title = title_kw
                                        if len(parts) > 1:
                                            title_suffix = parts[1].strip()[:50]
                                            # Clean title suffix - remove "LinkedIn", "and", etc.
                                            title_suffix = re.sub(r'\b(LinkedIn|and|the|a|an)\b', '', title_suffix, flags=re.IGNORECASE).strip()
                                            if title_suffix and len(title_suffix) > 2:
                                                title = f"{title_kw} {title_suffix}"
                                        
                                        if name and len(name) > 2 and len(name) < 50:
                                            # Check if we already have this person (case-insensitive)
                                            existing = [l for l in found_leadership if l.get("name", "").lower() == name.lower()]
                                            if not existing:
                                                found_leadership.append({
                                                    "name": name,
                                                    "title": title,
                                                    "role_type": "executive" if any(t in title_kw.lower() for t in ["ceo", "cto", "cfo", "president", "founder", "director"]) else "other"
                                                })
                                            elif existing and title_kw.lower() not in existing[0].get("title", "").lower():
                                                # Update title if we found a better one
                                                existing[0]["title"] = title
                                    break
                if found_leadership:
                    profile_data["leadership"] = found_leadership[:20]  # Limit to 20
            
            # Post-process: Extract locations/addresses from structured_data FIRST
            for chunk in chunks:
                structured = chunk.get("structured_data", {})
                if structured and structured.get("addresses"):
                    addresses = structured["addresses"]
                    if addresses and not profile_data.get("headquarters"):
                        # Use first address as headquarters
                        profile_data["headquarters"] = addresses[0]
                    if addresses and (not profile_data.get("locations") or len(profile_data.get("locations", [])) == 0):
                        # Extract city/location from addresses
                        locations = []
                        for addr in addresses:
                            # Extract city name (usually before postcode or after comma)
                            # UK postcode pattern
                            postcode_match = re.search(r'([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})', addr, re.IGNORECASE)
                            if postcode_match:
                                # Get text before postcode
                                before_postcode = addr[:postcode_match.start()].strip()
                                # Extract last significant word (likely city)
                                parts = [p.strip() for p in before_postcode.split(',') if p.strip()]
                                if parts:
                                    # Last part before postcode is usually city
                                    city = parts[-1] if parts else ""
                                    if city and city not in locations:
                                        locations.append(city)
                            else:
                                # No postcode, try to extract city from address
                                parts = [p.strip() for p in addr.split(',') if p.strip()]
                                if len(parts) >= 2:
                                    city = parts[-2]  # Second to last is often city
                                    if city and city not in locations:
                                        locations.append(city)
                        if locations:
                            profile_data["locations"] = locations[:10]
                        # Also set full address in contact
                        if addresses and not profile_data.get("contact", {}).get("full_address"):
                            profile_data["contact"]["full_address"] = addresses[0]
            
            # Fallback: Extract locations/addresses from chunks if not found in structured_data
            if not profile_data.get("headquarters") and (not profile_data.get("locations") or len(profile_data.get("locations", [])) == 0):
                found_locations = []
                for chunk in chunks[:150]:
                    text = chunk.get("text", "")
                    section = chunk.get("section", "").lower()
                    if any(kw in section for kw in ["location", "office", "address", "contact", "headquarters", "footer"]):
                        # Look for UK addresses (postcodes, cities)
                        uk_cities = ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Edinburgh", "Bristol", "Liverpool", "Newcastle", "Sheffield", "Northwich", "Cheshire", "Bracknell", "Reading", "Oxford", "Cambridge"]
                        for city in uk_cities:
                            if city in text and city not in found_locations:
                                found_locations.append(city)
                        # Also look for postcodes
                        postcode_pattern = r'([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})'
                        postcodes = re.findall(postcode_pattern, text, re.IGNORECASE)
                        if postcodes and not profile_data.get("headquarters"):
                            # Try to get context around postcode
                            for postcode in postcodes[:1]:
                                idx = text.find(postcode)
                                if idx > 0:
                                    context = text[max(0, idx-150):idx+20]
                                    # Clean context - remove common footer text
                                    context = re.sub(r'(Copyright|©|Terms|Privacy|All rights|Cookie)', '', context, flags=re.IGNORECASE)
                                    context = context.strip()
                                    if len(context) > 10:
                                        profile_data["headquarters"] = context[:200]
                                        # Also set in contact
                                        if not profile_data.get("contact", {}).get("full_address"):
                                            profile_data["contact"]["full_address"] = context[:200]
                                    break
                if found_locations:
                    profile_data["locations"] = found_locations[:10]
            
            # Post-process: Extract technology signals from chunks
            if not profile_data.get("technology_signals") or len(profile_data.get("technology_signals", [])) == 0:
                tech_keywords = ["AI", "Machine Learning", "Cloud", "AWS", "Azure", "GCP", "Python", "JavaScript", "React", "Node.js", "API", "REST", "GraphQL", "Docker", "Kubernetes", "Microservices"]
                found_tech = []
                for chunk in chunks[:50]:
                    text = chunk.get("text", "").lower()
                    for tech in tech_keywords:
                        if tech.lower() in text and tech not in found_tech:
                            found_tech.append(tech)
                if found_tech:
                    profile_data["technology_signals"] = found_tech[:10]  # Limit to 10
            
            # Post-process: Extract domain status
            if not profile_data.get("domain_status"):
                # Check if domain is active (basic check - if we got content, it's likely active)
                if chunks and len(chunks) > 0:
                    profile_data["domain_status"] = "Active"
                else:
                    profile_data["domain_status"] = "Unknown"
            
            # Post-process: Extract company size from description or keywords
            if not profile_data.get("company_size"):
                desc = (profile_data.get("description_long", "") + " " + profile_data.get("description_short", "")).lower()
                # Look for size indicators
                size_keywords = {
                    "1-10": ["startup", "small team", "few employees", "1-10", "1 to 10"],
                    "11-50": ["small business", "11-50", "11 to 50", "small company"],
                    "51-200": ["medium", "51-200", "51 to 200", "growing company"],
                    "201-500": ["large", "201-500", "201 to 500", "established"],
                    "501-1000": ["enterprise", "501-1000", "501 to 1000", "large enterprise"],
                    "1000+": ["multinational", "1000+", "over 1000", "global", "fortune"]
                }
                for size, keywords in size_keywords.items():
                    if any(kw in desc for kw in keywords):
                        profile_data["company_size"] = size
                        break
                # If still empty, try to infer from description
                if not profile_data.get("company_size"):
                    if "startup" in desc or "small" in desc:
                        profile_data["company_size"] = "1-10"
                    elif "medium" in desc:
                        profile_data["company_size"] = "51-200"
                    elif "large" in desc or "enterprise" in desc:
                        profile_data["company_size"] = "201-500"
            
            # Post-process: Improve business_type extraction
            if not profile_data.get("business_type") or not profile_data.get("business_type").strip():
                desc = (profile_data.get("description_long", "") + " " + profile_data.get("description_short", "")).lower()
                if "saas" in desc or "software as a service" in desc:
                    profile_data["business_type"] = "SaaS"
                elif "b2b" in desc or "business to business" in desc or "b2b" in desc:
                    profile_data["business_type"] = "B2B"
                elif "b2c" in desc or "business to consumer" in desc:
                    profile_data["business_type"] = "B2C"
                elif "b2b2c" in desc:
                    profile_data["business_type"] = "B2B2C"
                elif "platform" in desc:
                    profile_data["business_type"] = "Platform"
                elif "consulting" in desc or "advisory" in desc:
                    profile_data["business_type"] = "Consulting"
                elif "marketplace" in desc:
                    profile_data["business_type"] = "Marketplace"
                elif "enterprise" in desc:
                    profile_data["business_type"] = "Enterprise SaaS"
            
            # Ensure domain field is correct
            profile_data["domain"] = company.domain
            
            # Post-process: Extract contact domain and company_name if missing
            if not profile_data.get("contact", {}).get("domain"):
                profile_data["contact"]["domain"] = company.domain
            if not profile_data.get("contact", {}).get("company_name"):
                profile_data["contact"]["company_name"] = profile_data.get("company_name", "")
            
            # Validate and clean up
            if not profile_data.get("company_name"):
                # Fallback: derive from domain
                domain_parts = company.domain.split(".")
                profile_data["company_name"] = domain_parts[0].capitalize() + " Inc."
            
            # Final normalization: Ensure email is a string (not array) before saving
            if profile_data.get("contact", {}).get("email"):
                email_val = profile_data["contact"]["email"]
                if isinstance(email_val, list) and len(email_val) > 0:
                    # Get first valid email from array
                    valid_emails = [e for e in email_val if isinstance(e, str) and e.strip() and "@" in e]
                    if valid_emails:
                        # Clean email - extract just email part
                        email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', valid_emails[0])
                        profile_data["contact"]["email"] = email_match.group(1) if email_match else valid_emails[0]
                    else:
                        profile_data["contact"]["email"] = ""
            
            # Remove any "meta" object if it exists (cleanup) - extract confidence if present
            if "meta" in profile_data:
                # If meta has extraction_confidence, use it if reasonable
                if isinstance(profile_data.get("meta"), dict) and "extraction_confidence" in profile_data["meta"]:
                    meta_confidence = profile_data["meta"]["extraction_confidence"]
                    try:
                        conf_val = float(meta_confidence)
                        # Only use meta confidence if it's reasonable (> 0.1)
                        if conf_val > 0.1:
                            profile_data["extraction_confidence"] = conf_val
                    except (ValueError, TypeError):
                        pass
                del profile_data["meta"]
            
            # Calculate extraction_confidence based on filled fields (if not already set by LLM or meta)
            if not profile_data.get("extraction_confidence") or profile_data.get("extraction_confidence") == 0.0:
                profile_data["extraction_confidence"] = _calculate_extraction_confidence(profile_data)
            
            with profile_path.open("w", encoding="utf-8") as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            logger.info("Wrote profile.json for %s to %s", company.domain, profile_path)
            return "profile_generated"
        except Exception as e:
            last_error = e
            logger.warning("Attempt %d to extract profile for %s failed: %s", attempt + 1, company.domain, e)

    logger.error("LLM extraction failed for %s after retries: %s", company.domain, last_error)
    # Write a minimal failed profile for traceability
    failed_profile = _default_profile_schema(company.domain)
    failed_profile["extraction_confidence"] = 0.0
    failed_profile["error"] = str(last_error) if last_error else "Unknown error"
    with profile_path.open("w", encoding="utf-8") as f:
        json.dump(failed_profile, f, ensure_ascii=False, indent=2)
    return "failed_llm"


