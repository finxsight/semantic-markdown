#!/usr/bin/env python3
"""Convenience runner for Semantic Markdown CLI.

Usage:
    ./run_smd.py examples/transcript.smd
    ./run_smd.py examples/notebook.smd --json
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from semantic_markdown.__main__ import main

main()
