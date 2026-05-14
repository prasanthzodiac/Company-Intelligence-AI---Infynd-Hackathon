#!/usr/bin/env python3
"""
Run the full pipeline with parallel processing for all domains
This script will:
1. Download websites in parallel
2. Scrape in parallel
3. Extract with LLM in parallel (if enabled)
"""
import sys
from pathlib import Path

# Add project root to path
base_dir = Path(__file__).parent
sys.path.insert(0, str(base_dir))

from main import main

if __name__ == "__main__":
    # Run with default arguments
    sys.argv = ["main.py", "--input", "domains.csv"]
    main()

