import json
import logging
import re
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup

from .csv_loader import Company


logger = logging.getLogger(__name__)


def _is_visible_text_element(el) -> bool:
    # Handle strings (from stripped_strings) - they're always visible
    if isinstance(el, str):
        return True
    # Exclude script/style/meta/noscript etc.
    if hasattr(el, 'parent') and el.parent and hasattr(el.parent, 'name'):
        if el.parent.name in ["script", "style", "noscript"]:
            return False
    return True


def _extract_structured_data(soup: BeautifulSoup) -> Dict:
    """Extract structured data like emails, phones, addresses, social links, company details"""
    structured = {
        "emails": [],
        "phones": [],
        "addresses": [],
        "social_links": {},
        "contact_sections": [],
        "company_details": {},
        "people": []
    }
    
    text = soup.get_text()
    
    # Extract emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    structured["emails"] = [e for e in emails if not any(x in e.lower() for x in ["example.com", "test.com", "domain.com", "noreply", "no-reply"])]
    
    # Extract phone numbers (UK and international formats) - improved filtering
    phone_patterns = [
        r'\+44\s?\d{2,4}\s?\d{3,4}\s?\d{3,4}',  # UK international format
        r'\+44\s?\d{10,11}',  # UK international compact
        r'0\d{2,4}\s?\d{3,4}\s?\d{3,4}',  # UK landline
        r'\(0\d{2,4}\)\s?\d{3,4}\s?\d{3,4}',  # UK with parentheses
        r'\d{5}\s?\d{6}',  # UK mobile format
        r'\+1\s?\(?\d{3}\)?\s?\d{3}[-.\s]?\d{4}',  # US format
        r'\+?\d{1,4}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',  # General international
    ]
    all_phones = []
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        all_phones.extend(phones)
    
    # Filter out invalid phone numbers (too short, all same digits, etc.)
    valid_phones = []
    for phone in all_phones:
        phone_clean = re.sub(r'[\s\-\(\)]', '', phone)  # Remove formatting
        # Must be at least 10 digits (minimum valid phone number)
        if len(re.sub(r'\D', '', phone_clean)) >= 10:
            # Exclude if all digits are the same
            digits_only = re.sub(r'\D', '', phone_clean)
            if len(set(digits_only)) > 1:  # At least 2 different digits
                # Exclude common non-phone patterns (years, codes, etc.)
                if not re.match(r'^(19|20)\d{2}$', digits_only):  # Not a year
                    if phone not in valid_phones:
                        valid_phones.append(phone)
    
    structured["phones"] = valid_phones
    
    # Extract addresses (UK postcode pattern, full addresses)
    # UK postcode pattern: 1-2 letters, 1-2 digits, optional letter, space (optional), 1 digit, 2 letters
    uk_postcode_pattern = r'([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})'
    uk_postcode_pattern_no_space = r'([A-Z]{1,2}\d{1,2}[A-Z]?\d[A-Z]{2})'  # Without space
    
    # Look for addresses in footer, contact sections, and text with postcodes
    address_sections = []
    
    # First, check for explicit address patterns in full text (most reliable)
    address_label_patterns = [
        r'Trading\s+address[:\s]+(?:at\s+)?([^\.]{20,200}?)(?:\.|and|$)',
        r'Registered\s+office[:\s]+(?:address\s+)?([^\.]{20,200}?)(?:\.|and|$)',
        r'Address[:\s]+([^\.]{20,200}?)(?:\.|and|$)',
        r'Headquarters[:\s]+([^\.]{20,200}?)(?:\.|and|$)',
        r'Location[:\s]+([^\.]{20,200}?)(?:\.|and|$)',
    ]
    for pattern in address_label_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches[:3]:  # Limit to 3 matches
            match = match.strip()
            # Clean up
            match = re.sub(r'\s+', ' ', match)
            if len(match) > 20 and len(match) < 300:
                address_sections.append(match)
    
    # Check footer first (most reliable for general addresses)
    footer = soup.find("footer")
    if footer:
        footer_text = footer.get_text()
        # Try with space
        postcode_matches = list(re.finditer(uk_postcode_pattern, footer_text, re.IGNORECASE))
        # Try without space
        if not postcode_matches:
            postcode_matches = list(re.finditer(uk_postcode_pattern_no_space, footer_text, re.IGNORECASE))
        
        for match in postcode_matches:
            # Extract text before and after postcode (address context)
            start = max(0, match.start() - 150)
            end = min(len(footer_text), match.end() + 50)
            address_text = footer_text[start:end].strip()
            # Clean up the address
            address_text = re.sub(r'\s+', ' ', address_text)
            # Try to extract a complete address (look for company name, street, city, postcode)
            if len(address_text) > 20 and len(address_text) < 300:
                # Check if it contains address-like keywords
                if any(kw in address_text.lower() for kw in ["street", "road", "avenue", "park", "court", "house", "building", "ltd", "limited", "uk", "united kingdom", "hub", "gadbrook"]):
                    address_sections.append(address_text)
    
    # Check contact sections
    contact_sections = soup.find_all(["section", "div", "p"], class_=re.compile("contact|address|location|office|footer", re.I))
    for section in contact_sections[:5]:  # Limit to avoid duplicates
        section_text = section.get_text()
        postcode_matches = list(re.finditer(uk_postcode_pattern, section_text, re.IGNORECASE))
        if not postcode_matches:
            postcode_matches = list(re.finditer(uk_postcode_pattern_no_space, section_text, re.IGNORECASE))
        
        for match in postcode_matches:
            start = max(0, match.start() - 150)
            end = min(len(section_text), match.end() + 50)
            address_text = section_text[start:end].strip()
            address_text = re.sub(r'\s+', ' ', address_text)
            if len(address_text) > 20 and len(address_text) < 300:
                # Check if it contains address-like keywords
                if any(kw in address_text.lower() for kw in ["street", "road", "avenue", "park", "court", "house", "building", "ltd", "limited", "uk", "united kingdom"]):
                    address_sections.append(address_text)
    
    # Also search full text for addresses with postcodes (fallback)
    if not address_sections:
        # Look for postcodes in full text
        postcode_matches = list(re.finditer(uk_postcode_pattern, text, re.IGNORECASE))
        if not postcode_matches:
            postcode_matches = list(re.finditer(uk_postcode_pattern_no_space, text, re.IGNORECASE))
        
        for match in postcode_matches[:3]:  # Limit to 3
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 30)
            addr_text = text[start:end].strip()
            addr_text = re.sub(r'\s+', ' ', addr_text)
            if len(addr_text) > 20 and len(addr_text) < 250:
                if any(kw in addr_text.lower() for kw in ["park", "court", "house", "road", "street", "avenue", "ltd", "limited", "uk"]):
                    address_sections.append(addr_text)
    
    # Deduplicate and clean addresses
    seen_addresses = set()
    for addr in address_sections:
        # Normalize for comparison (remove extra spaces, lowercase)
        addr_normalized = re.sub(r'\s+', ' ', addr.lower().strip())
        if addr_normalized not in seen_addresses and len(addr_normalized) > 15:
            seen_addresses.add(addr_normalized)
            # Clean up address (remove extra text before/after)
            addr_clean = addr.strip()
            # Try to extract just the address part (remove leading company name, etc.)
            if len(addr_clean) > 50:
                # Look for common address start patterns
                addr_match = re.search(r'((?:The\s+)?(?:Hub|Park|Court|House|Building|Street|Road|Avenue)[^\.]{10,150})', addr_clean, re.IGNORECASE)
                if addr_match:
                    addr_clean = addr_match.group(1).strip()
            structured["addresses"].append(addr_clean)
    
    # Extract company registration numbers (UK Companies House format, VAT, etc.)
    # UK Company Number: 8 digits or 2 letters + 6 digits
    company_reg_patterns = [
        r'registered.*?company\s+number\s+(\d{8})',  # "registered in England and Wales under company number 09617420" (most common)
        r'Company\s+(?:No|Number|Registration|Reg\.?)[:\s]+([A-Z]{0,2}\d{6,8})',
        r'company\s+number\s+(\d{8})',  # Simple format: "company number 09617420"
        r'Registration\s+(?:No|Number)[:\s]+([A-Z]{0,2}\d{6,8})',
        r'Reg\.?\s+(?:No|Number)[:\s]+([A-Z]{0,2}\d{6,8})',
        r'CRN[:\s]+([A-Z]{0,2}\d{6,8})',
        r'Companies\s+House[:\s]+([A-Z]{0,2}\d{6,8})',
        r'Company\s+Number[:\s]+([A-Z]{0,2}\d{6,8})',
        r'Reg\s+No[:\s]+([A-Z]{0,2}\d{6,8})',
        r'([A-Z]{2}\d{6})\s+(?:Company|Ltd|Limited|PLC)',
        r'Company\s+([A-Z]{2}\d{6})',
    ]
    for pattern in company_reg_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            reg_num = matches[0].strip().upper()
            if reg_num and len(reg_num) >= 6:
                structured["company_details"]["company_registration"] = reg_num
                break
    
    # Extract VAT numbers (UK format: GB + 9 digits, or just numbers)
    vat_patterns = [
        r'VAT\s+(?:No|Number|Registration|Reg\.?)[:\s]+(GB\d{9}|\d{9,12})',
        r'VAT[:\s]+(GB\d{9}|\d{9,12})',
        r'VAT\s+Reg[:\s]+(GB\d{9}|\d{9,12})',
        r'VAT\s+Registration[:\s]+(GB\d{9}|\d{9,12})',
        r'VAT\s+Number[:\s]+(GB\d{9}|\d{9,12})',
    ]
    for pattern in vat_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            vat_num = matches[0].strip().upper()
            if vat_num:
                structured["company_details"]["vat_number"] = vat_num
                break
    
    # Extract hours of operation
    hours_patterns = [
        r'(?:Hours?|Opening|Business)\s+(?:of\s+)?(?:Operation|Hours?)[:\s]+([^\n]{10,100})',
        r'Monday[^\n]{0,50}(?:to|–|-)\s*(?:Friday|Sunday)[^\n]{0,50}',
    ]
    for pattern in hours_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            structured["company_details"]["hours_of_operation"] = matches[0].strip()[:200]
            break
    
    # Extract people/team members (names with titles) - improved extraction
    # Look for patterns like "Name - Title" or "Name Title" in team/about sections
    people_sections = soup.find_all(["section", "div", "article"], class_=re.compile("team|about|leadership|people|staff|founder|executive|management|board|director", re.I))
    
    # Also check for common team/people page structures
    for tag in soup.find_all(["h1", "h2", "h3"]):
        tag_text = tag.get_text().lower()
        if any(kw in tag_text for kw in ["team", "leadership", "about us", "our people", "management", "executive"]):
            # Include parent section
            parent = tag.find_parent(["section", "div", "article"])
            if parent and parent not in people_sections:
                people_sections.append(parent)
    
    for section in people_sections[:10]:  # Limit to first 10 sections to avoid duplicates
        section_text = section.get_text()
        # Pattern 1: Name - Title or Name — Title
        people_pattern1 = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s*[-–—]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        people_matches1 = re.findall(people_pattern1, section_text)
        for name, title in people_matches1[:30]:
            name_parts = name.split()
            if 2 <= len(name_parts) <= 4 and 1 <= len(title.split()) <= 5:
                # Validate name (should have proper capitalization)
                if all(part[0].isupper() for part in name_parts if part):
                    if not any(p.get("name", "").lower() == name.lower() for p in structured["people"]):
                        structured["people"].append({
                            "name": name.strip(),
                            "title": title.strip()
                        })
        
        # Pattern 2: Name Title (e.g., "Michael Bell Co-Founder")
        people_pattern2 = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(CEO|CTO|CFO|Founder|Co-Founder|Co Founder|Director|President|VP|Vice President|Chief|Head of|Managing Director|MD|Executive|Manager)'
        people_matches2 = re.findall(people_pattern2, section_text, re.IGNORECASE)
        for name, title in people_matches2[:30]:
            name_parts = name.split()
            if 2 <= len(name_parts) <= 4:
                # Validate name
                if all(part[0].isupper() for part in name_parts if part):
                    if not any(p.get("name", "").lower() == name.lower() for p in structured["people"]):
                        structured["people"].append({
                            "name": name.strip(),
                            "title": title.strip()
                        })
        
        # Pattern 3: Extract from structured HTML (common in team pages)
        for person_div in section.find_all(["div", "article", "li"], class_=re.compile("person|member|team-member|executive|leader", re.I)):
            person_text = person_div.get_text()
            # Look for name in heading
            name_tag = person_div.find(["h1", "h2", "h3", "h4", "strong", "b"])
            if name_tag:
                name = name_tag.get_text().strip()
                # Find title nearby
                title_tag = person_div.find(["p", "span", "div"], class_=re.compile("title|role|position", re.I))
                if title_tag:
                    title = title_tag.get_text().strip()
                else:
                    # Try to extract from text after name
                    remaining = person_text.replace(name, "", 1).strip()
                    title_match = re.search(r'(CEO|CTO|CFO|Founder|Director|President|VP|Chief|Head of|Managing Director)', remaining, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1)
                    else:
                        continue
                
                if 2 <= len(name.split()) <= 4 and len(title) > 2:
                    if not any(p.get("name", "").lower() == name.lower() for p in structured["people"]):
                        structured["people"].append({
                            "name": name.strip(),
                            "title": title.strip()
                        })
    
    # Extract social media links
    for link in soup.find_all("a", href=True):
        href = link.get("href", "").lower()
        if "linkedin.com" in href:
            structured["social_links"]["linkedin"] = link["href"]
        elif "facebook.com" in href:
            structured["social_links"]["facebook"] = link["href"]
        elif "twitter.com" in href or "x.com" in href:
            structured["social_links"]["x"] = link["href"]
        elif "instagram.com" in href:
            structured["social_links"]["instagram"] = link["href"]
        elif "youtube.com" in href:
            structured["social_links"]["youtube"] = link["href"]
    
    # Extract contact sections (footer, contact page sections)
    contact_keywords = ["contact", "address", "phone", "email", "location", "office"]
    for section in soup.find_all(["section", "div"], class_=re.compile("|".join(contact_keywords), re.I)):
        section_text = section.get_text(strip=True)
        if any(kw in section_text.lower() for kw in contact_keywords):
            structured["contact_sections"].append(section_text[:500])  # Limit length
    
    return structured


def _clean_text(text: str) -> str:
    """Clean extracted text by removing excessive whitespace and normalizing"""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Remove common HTML artifacts
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    return text


def _extract_page_sections(html_path: Path) -> List[Dict]:
    try:
        with html_path.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            soup = BeautifulSoup(content, "html.parser")
    except Exception as e:
        logger.warning(f"Error reading HTML file {html_path}: {e}")
        return []

    title_tag = soup.find("title")
    title = _clean_text(title_tag.get_text()) if title_tag else ""

    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = _clean_text(meta_tag["content"])
    
    # Also check Open Graph description
    if not meta_desc:
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc and og_desc.get("content"):
            meta_desc = _clean_text(og_desc["content"])
    
    # Extract structured data BEFORE removing elements
    structured_data = _extract_structured_data(soup)

    # Remove common layout noise (but keep footer for contact info)
    # Also remove script, style, and other non-content elements
    for selector in [
        "nav",
        "header",
        "form",
        "aside",
        "script",
        "style",
        "noscript",
        "iframe",
        "svg",  # Remove SVG icons but keep content
    ]:
        for tag in soup.find_all(selector):
            tag.decompose()
    
    # Remove common ad/analytics containers
    for tag in soup.find_all(class_=re.compile("ad|advertisement|analytics|tracking|cookie|banner", re.I)):
        tag.decompose()
    
    # Keep footer but mark it for special handling
    footer = soup.find("footer")
    footer_text = ""
    if footer:
        footer_text = footer.get_text(strip=True)

    sections: List[Dict] = []

    # Add a special "Contact Information" section with structured data
    if structured_data["emails"] or structured_data["phones"] or structured_data["contact_sections"]:
        contact_text = ""
        if structured_data["emails"]:
            contact_text += f"Email addresses: {', '.join(structured_data['emails'])}\n"
        if structured_data["phones"]:
            contact_text += f"Phone numbers: {', '.join(structured_data['phones'])}\n"
        if structured_data["contact_sections"]:
            contact_text += "\n".join(structured_data["contact_sections"][:3])  # First 3 contact sections
        if footer_text:
            contact_text += f"\nFooter information: {footer_text[:500]}"
        
        if contact_text.strip():
            sections.append({
                "section": "Contact Information",
                "title": title,
                "meta_description": meta_desc,
                "text": contact_text.strip(),
                "structured_data": {
                    "emails": structured_data["emails"],
                    "phones": structured_data["phones"],
                    "social_links": structured_data["social_links"]
                }
            })

    # Enhanced section detection: look for specific section keywords
    section_keywords = {
        "About": ["about", "about us", "who we are", "our story", "company", "overview"],
        "Services": ["services", "what we do", "solutions", "offerings", "products", "what we offer"],
        "Products": ["products", "product", "platform", "software", "tools"],
        "Team": ["team", "our team", "people", "staff", "employees", "workforce"],
        "Leadership": ["leadership", "executive", "management", "directors", "board", "ceo", "founders"],
        "Contact": ["contact", "get in touch", "reach us", "contact us", "get in contact"],
        "Locations": ["locations", "offices", "headquarters", "hq", "where we are", "addresses"],
        "Certifications": ["certifications", "certified", "accreditations", "compliance", "iso", "standards"],
        "Technology": ["technology", "tech stack", "tools", "platforms", "infrastructure", "cloud"],
        "Careers": ["careers", "jobs", "join us", "we're hiring", "open positions"],
        "Partners": ["partners", "partnerships", "alliances", "resellers"],
        "Case Studies": ["case studies", "success stories", "testimonials", "clients", "customers"],
    }
    
    # Group by headings (h1-h6): each heading + following siblings until next heading becomes a section
    body = soup.body or soup
    headings = body.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    if not headings:
        # Fallback: entire body as a single section
        texts = [
            _clean_text(t)
            for t in body.stripped_strings
            if _is_visible_text_element(t) and len(t.strip()) > 2
        ]
        combined = " ".join(texts)
        combined = _clean_text(combined)
        if combined and len(combined) >= 20:
            sections.append(
                {
                    "section": "General",
                    "title": title,
                    "meta_description": meta_desc,
                    "text": combined,
                }
            )
        return sections

    for idx, heading in enumerate(headings):
        heading_text = heading.get_text(strip=True).lower()
        section_name = heading.get_text(strip=True) or "Section"
        
        # Try to match heading to known section types
        matched_section = None
        for section_type, keywords in section_keywords.items():
            if any(kw in heading_text for kw in keywords):
                matched_section = section_type
                break
        
        # Use matched section or original heading
        final_section_name = matched_section if matched_section else _clean_text(section_name)
        
        texts: List[str] = []

        # Collect siblings until next heading
        for sibling in heading.next_siblings:
            if getattr(sibling, "name", None) in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                break
            for t in getattr(sibling, "stripped_strings", []):
                txt = _clean_text(t)
                if txt and len(txt) > 2:  # Filter out very short fragments
                    texts.append(txt)

        combined = " ".join(texts)
        combined = _clean_text(combined)
        if not combined or len(combined) < 20:  # Minimum meaningful text length
            continue

        # Add structured data if this is a contact or team section
        chunk_structured = {}
        if matched_section in ["Contact", "Team", "Leadership"]:
            chunk_structured = structured_data.copy()

        sections.append(
            {
                "section": final_section_name,
                "title": title,
                "meta_description": meta_desc,
                "text": combined,
                "structured_data": chunk_structured if chunk_structured else None
            }
        )
        
        # Remove None structured_data
        if sections[-1]["structured_data"] is None:
            del sections[-1]["structured_data"]
    
    # Add People Information section if found
    if structured_data["people"]:
        people_text = "People Information:\n"
        for person in structured_data["people"][:20]:  # Limit to first 20
            name = person.get("name", "")
            title = person.get("title", "")
            if name:
                people_text += f"{name}"
                if title:
                    people_text += f" - {title}"
                people_text += "\n"
        sections.append({
            "section": "People Information",
            "title": title,
            "meta_description": meta_desc,
            "text": people_text.strip(),
            "structured_data": {"people": structured_data["people"][:20]}
        })
    
    # Add social media section if found
    if structured_data["social_links"]:
        social_text = "Social Media Links:\n"
        for platform, url in structured_data["social_links"].items():
            social_text += f"{platform.capitalize()}: {url}\n"
        sections.append({
            "section": "Social Media",
            "title": title,
            "meta_description": meta_desc,
            "text": social_text.strip(),
            "structured_data": {"social_links": structured_data["social_links"]}
        })

    return sections


def crawl_company(company: Company, data_dir: Path, output_dir: Path, settings: Dict) -> str:
    """
    Crawl the already-downloaded HTML for a company and produce chunks.json.

    Returns: 'crawled' or 'failed_crawl'.
    """
    domain_dir = data_dir / company.domain
    if not domain_dir.exists():
        logger.error("Domain directory does not exist for %s: %s", company.domain, domain_dir)
        return "failed_crawl"

    output_domain_dir = output_dir / company.domain
    output_domain_dir.mkdir(parents=True, exist_ok=True)
    chunks_path = output_domain_dir / "chunks.json"

    html_files = list(domain_dir.rglob("*.html")) + list(domain_dir.rglob("*.htm"))
    if not html_files:
        logger.error("No HTML files found to crawl for %s", company.domain)
        return "failed_crawl"

    logger.info("Crawling %d HTML files for %s", len(html_files), company.domain)
    chunks: List[Dict] = []
    processed_files = 0
    failed_files = 0

    for html_file in html_files:
        try:
            rel_page = html_file.relative_to(domain_dir).as_posix()
            sections = _extract_page_sections(html_file)
            processed_files += 1

            for sec in sections:
                # Only add chunks with meaningful text
                text = sec.get("text", "").strip()
                if not text or len(text) < 20:
                    continue
                    
                chunk = {
                    "domain": company.domain,
                    "page": rel_page,
                    "section": sec["section"],
                    "text": text,
                    "source_path": str(html_file),
                    "page_title": sec.get("title", ""),
                    "meta_description": sec.get("meta_description", ""),
                }
                # Include structured data if available
                if "structured_data" in sec:
                    chunk["structured_data"] = sec["structured_data"]
                chunks.append(chunk)
        except Exception as e:
            failed_files += 1
            logger.warning("Error processing %s: %s", html_file, e)
            continue

    logger.info("Processed %d files, %d failed, extracted %d chunks for %s", processed_files, failed_files, len(chunks), company.domain)

    if not chunks:
        # Explicitly mark crawl as failed if no usable text was extracted
        logger.error("Crawl produced 0 chunks for %s; marking as failed_crawl", company.domain)
        # Still write an empty file for debugging/inspection
        with chunks_path.open("w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return "failed_crawl"
    
    # Validate chunks have actual text content
    valid_chunks = [c for c in chunks if c.get("text", "").strip() and len(c.get("text", "").strip()) > 20]
    if not valid_chunks:
        logger.error("Crawl produced chunks but none have valid text content for %s", company.domain)
        with chunks_path.open("w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return "failed_crawl"

    # Sort chunks by page and section for better organization
    valid_chunks.sort(key=lambda x: (x.get("page", ""), x.get("section", "")))

    try:
        with chunks_path.open("w", encoding="utf-8") as f:
            json.dump(valid_chunks, f, ensure_ascii=False, indent=2)
        logger.info("Wrote %d valid chunks for %s to %s (from %d total, %d files processed)", 
                   len(valid_chunks), company.domain, chunks_path, len(chunks), processed_files)
    except Exception as e:
        logger.error("Failed to write chunks.json for %s: %s", company.domain, e)
        return "failed_crawl"

    return "crawled"


