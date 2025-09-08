#!/usr/bin/env python3
"""Test script for Qdrant integration with wine agent."""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


def test_imports():
    """Test that Qdrant tools can be imported."""
    print("Testing Qdrant imports...")

    try:
        from deepagents.qdrant import QdrantTools, CachedDoc

        print("✓ Core Qdrant classes imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import core Qdrant classes: {e}")
        return False

    try:
        from deepagents.qdrant import qdrant_sync_cache, qdrant_retrieve, qdrant_inspect

        print("✓ Qdrant tools imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Qdrant tools: {e}")
        return False

    return True


def test_wine_agent_integration():
    """Test that wine agent can load with Qdrant integration."""
    print("\nTesting wine agent integration...")

    try:
        # Import wine agent (should work with or without Qdrant)
        from wine_agent import agent, QDRANT_AVAILABLE

        print(
            f"✓ Wine agent imported successfully (Qdrant available: {QDRANT_AVAILABLE})"
        )

        # Check agent structure (LangGraph agents don't have direct tools attribute)
        print(f"✓ Agent type: {type(agent).__name__}")

        if QDRANT_AVAILABLE:
            print("✓ Qdrant tools should be available to the agent")
        else:
            print(
                "ℹ Qdrant not available - agent will work without vector database features"
            )

        return True

    except Exception as e:
        print(f"✗ Failed to load wine agent: {e}")
        return False


def test_qdrant_tools_without_config():
    """Test Qdrant tools behavior without configuration."""
    print("\nTesting Qdrant tools without configuration...")

    try:
        from deepagents.qdrant import QdrantTools

        tools = QdrantTools()
        print(
            f"✓ QdrantTools created (URL: {bool(tools.qdrant_url)}, API Key: {bool(tools.qdrant_api_key)})"
        )

        # Test derive_wine_context with empty files
        wine_query, wine_slug = tools.derive_wine_context({})
        print(f"✓ derive_wine_context works: query={wine_query}, slug={wine_slug}")

        # Test collect_docs_from_state with empty files
        docs = tools.collect_docs_from_state({})
        print(f"✓ collect_docs_from_state works: found {len(docs)} docs")

        return True

    except Exception as e:
        print(f"✗ Qdrant tools test failed: {e}")
        return False


def test_qdrant_configuration():
    """Test Qdrant configuration detection."""
    print("\nTesting Qdrant configuration...")

    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    print(f"QDRANT_URL: {'✓ Set' if qdrant_url else '✗ Not set'}")
    print(f"QDRANT_API_KEY: {'✓ Set' if qdrant_api_key else '✗ Not set'}")
    print(f"OPENAI_API_KEY: {'✓ Set' if openai_api_key else '✗ Not set'}")

    if qdrant_url and qdrant_api_key and openai_api_key:
        print("✓ Full Qdrant configuration available")
        return True
    else:
        print(
            "ℹ Partial/no Qdrant configuration - tools will return helpful error messages"
        )
        return False


def main():
    """Run all tests."""
    print("=== Qdrant Integration Test ===\n")

    results = []

    # Test imports
    results.append(test_imports())

    # Test wine agent integration
    results.append(test_wine_agent_integration())

    # Test tools without config
    results.append(test_qdrant_tools_without_config())

    # Test configuration
    config_available = test_qdrant_configuration()

    print("\n=== Test Results ===")
    print(f"Passed: {sum(results)}/{len(results)} tests")

    if all(results):
        print("✓ All integration tests passed!")
        if config_available:
            print("✓ Full Qdrant configuration detected - ready for vector operations")
        else:
            print(
                "ℹ Tools integrated successfully - configure Qdrant environment for full functionality"
            )
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
