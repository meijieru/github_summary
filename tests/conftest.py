"""Shared test configuration for pytest

This file provides:
- Test markers configuration
- Shared fixtures used across multiple test files
"""


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
