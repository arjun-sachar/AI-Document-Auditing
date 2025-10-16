#!/usr/bin/env python3
"""Main entry point for the AI Document Auditing System."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import and run the CLI
from src.cli.main import main

if __name__ == "__main__":
    main()
