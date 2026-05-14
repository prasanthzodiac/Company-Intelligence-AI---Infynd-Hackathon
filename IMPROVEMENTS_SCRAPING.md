# Web Scraping and LLM Extraction Improvements

## Improvements Made

### 1. Text Cleaning and Normalization
- Added `_clean_text()` function to normalize extracted text
- Removes excessive whitespace, HTML entities, and invisible characters
- Ensures consistent text formatting for LLM processing

### 2. Enhanced HTML Parsing
- Improved error handling in `_extract_page_sections()`
- Better handling of missing or malformed HTML files
- Added support for Open Graph meta descriptions
- Minimum text length validation (20 characters) to filter noise

### 3. Improved JSON Extraction from LLM
- Enhanced `_ensure_valid_json()` function with better error recovery
- Handles markdown code fences (```json, ```)
- Removes trailing commas before closing braces
- Attempts multiple parsing strategies before failing
- Better error messages for debugging

### 4. Better LLM Prompting
- Clearer instructions in user prompt
- Explicit reminder to return flat JSON structure
- Emphasis on no markdown fences or comments

### 5. Structured Data Extraction
- Improved email extraction with better validation
- Enhanced phone number pattern matching (UK and international)
- Better filtering of invalid phone numbers
- Improved social media link detection
- Better people/leadership extraction from team sections

## Key Features

### Text Cleaning
- Normalizes whitespace (multiple spaces → single space)
- Removes HTML entities (&nbsp;, &amp;, etc.)
- Strips invisible Unicode characters
- Validates minimum text length

### Error Handling
- Graceful handling of malformed HTML
- Fallback strategies for JSON parsing
- Better logging for debugging
- Continues processing even if individual files fail

### Data Quality
- Filters out invalid emails (example.com, test.com, noreply)
- Validates phone numbers (minimum length, digit diversity)
- Removes duplicate entries
- Prioritizes structured data over regex extraction

## Usage

The improvements are automatically applied when running:
```bash
python main.py --input domains.csv
```

Or when using the backend API:
```bash
python run_backend.py
```

## Testing

To verify improvements:
1. Check `output/<domain>/chunks.json` for clean, well-structured text
2. Check `output/<domain>/profile.json` for complete, valid JSON
3. Review logs for any extraction errors

## Next Steps

Potential further improvements:
- Add caching for repeated extractions
- Implement incremental updates
- Add support for more languages
- Enhance technology stack detection
- Improve location extraction accuracy

