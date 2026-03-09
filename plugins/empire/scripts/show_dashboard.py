#!/usr/bin/env python3
"""Entry point for /empire command — prints the status dashboard."""

import os
import sys

plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, plugin_root)

from core.dashboard import render_dashboard

if __name__ == "__main__":
    print(render_dashboard())
