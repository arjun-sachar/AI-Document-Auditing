#!/usr/bin/env python3
"""Simple CLI runner for AI Document Auditing System."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the CLI
from src.cli.main import main

if __name__ == "__main__":
    main()
