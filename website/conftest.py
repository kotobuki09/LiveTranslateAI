"""
conftest.py — Add src/ to sys.path so pytest can import project modules.
"""
import sys
import os

# Insert the src/ directory at the front of the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
