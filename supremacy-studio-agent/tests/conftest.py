"""Shared fixtures for the test suite."""
import sys
import os

# Ensure the package root is on sys.path so tests can import modules directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
