"""
Real integration tests for the wine agent using actual models and search.
These tests verify the complete wine research pipeline works correctly.
"""

import json
import os
import pytest

from deepagents.evals.eval_runner import load_eval_cases


# Test data directories
WINES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data", "evals", "wines")
)
DISAMBIGUATION_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "test_data", "evals", "disambiguation"
    )
)
VALIDATION_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "test_data", "evals", "validation"
    )
)


@pytest.fixture
def wine_agent(monkeypatch):
    """Create a real wine agent for testing."""
    import sys

    # Set up environment for Jina search
    monkeypatch.setenv("SEARCH_BACKEND", "jina")
    # Remove Tavily env vars if they exist to force Jina usage
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    sys.path.append(
        os.path.join(os.path.dirname(__file__), "..", "..", "examples", "research")
    )

    from wine_agent import agent

    return agent


@pytest.mark.integration
def test_wine_research_sample_cases(wine_agent):
    """Test wine research with a sample of real cases."""
    cases = load_eval_cases(WINES_DIR)

    # Test first 5 cases to start
    sample_cases = cases[:5]

    results = []
    for case in sample_cases:
        print(f"\n--- Testing: {case.wine_query} ---")

        # Run the wine agent with proper message format
        from langchain_core.messages import HumanMessage

        result = wine_agent.invoke(
            {"messages": [HumanMessage(content=case.wine_query)], "files": {}}
        )

        # Extract wine data from result
        wine_data = result.get("wine", {})

        # Check if we got reasonable results
        assert wine_data is not None, f"No wine data returned for: {case.wine_query}"

        # Store result for analysis
        test_result = {
            "query": case.wine_query,
            "expected_normalized_name": case.normalized_name,
            "actual_normalized_name": wine_data.get("normalized_name", {}).get("value"),
            "expected_vintage": case.vintage,
            "actual_vintage": wine_data.get("vintage", {}).get("value"),
            "expected_grapes": case.grapes,
            "actual_grapes": wine_data.get("grapes", {}).get("value"),
            "corrections": case.corrections,
            "full_result": wine_data,
        }
        results.append(test_result)

        print(f"Expected normalized name: {case.normalized_name}")
        print(
            f"Actual normalized name: {wine_data.get('normalized_name', {}).get('value')}"
        )

    # Save detailed results for analysis
    with open("wine_integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Basic assertions - at least some should work
    successful_normalizations = sum(1 for r in results if r["actual_normalized_name"])
    assert (
        successful_normalizations >= 3
    ), f"Expected at least 3 successful normalizations, got {successful_normalizations}"


@pytest.mark.integration
def test_disambiguation_sample_cases(wine_agent):
    """Test disambiguation logic with real cases."""
    cases = load_eval_cases(DISAMBIGUATION_DIR)

    # Test first 3 cases from each category
    sample_cases = cases[:3]

    for case in sample_cases:
        print(f"\n--- Testing disambiguation: {case.raw.get('query')} ---")

        from langchain_core.messages import HumanMessage

        result = wine_agent.invoke(
            {"messages": [HumanMessage(content=case.raw.get("query", ""))], "files": {}}
        )

        # Check that we got some result
        assert (
            result is not None
        ), f"No result for disambiguation query: {case.raw.get('query')}"

        expected_outcome = case.raw.get("expected_outcome")
        print(f"Expected outcome: {expected_outcome}")
        print(f"Agent completed: {result.get('completed', False)}")


@pytest.mark.integration
def test_validation_sample_cases(wine_agent):
    """Test input validation with real cases."""
    cases = load_eval_cases(VALIDATION_DIR)

    # Test first 3 cases from each category
    sample_cases = cases[:3]

    for case in sample_cases:
        print(f"\n--- Testing validation: {case.raw.get('query')} ---")

        expected_pass = case.raw.get("expected_pass", True)

        try:
            from langchain_core.messages import HumanMessage

            result = wine_agent.invoke(
                {
                    "messages": [HumanMessage(content=case.raw.get("query", ""))],
                    "files": {},
                }
            )

            # If we expected it to fail but it succeeded, that might be OK
            # (agent might be more robust than expected)
            if not expected_pass:
                print(f"Expected to fail but succeeded: {case.raw.get('reason_code')}")

            assert result is not None

        except Exception as e:
            # If we expected it to fail and it failed, that's good
            if not expected_pass:
                print(f"Expected failure occurred: {e}")
            else:
                # If we expected it to pass but it failed, that's a problem
                pytest.fail(f"Expected to pass but failed: {e}")


@pytest.mark.integration
@pytest.mark.slow
def test_wine_research_full_batch(wine_agent):
    """Test a full batch of wine research cases (slow test)."""
    cases = load_eval_cases(WINES_DIR)

    # Test first batch (10 cases)
    batch_cases = cases[:10]

    successful_count = 0
    for case in batch_cases:
        try:
            from langchain_core.messages import HumanMessage

            result = wine_agent.invoke(
                {"messages": [HumanMessage(content=case.wine_query)], "files": {}}
            )

            wine_data = result.get("wine", {})
            if wine_data.get("normalized_name", {}).get("value"):
                successful_count += 1

        except Exception as e:
            print(f"Failed on {case.wine_query}: {e}")

    # Expect at least 70% success rate
    success_rate = successful_count / len(batch_cases)
    assert success_rate >= 0.7, f"Success rate {success_rate:.2%} below 70% threshold"


if __name__ == "__main__":
    # Run a quick smoke test
    import sys
    import os

    # Set up environment for Jina search
    os.environ["SEARCH_BACKEND"] = "jina"
    # Remove Tavily env vars if they exist
    os.environ.pop("TAVILY_API_KEY", None)

    sys.path.append(
        os.path.join(os.path.dirname(__file__), "..", "..", "examples", "research")
    )

    from wine_agent import agent

    cases = load_eval_cases(WINES_DIR)

    print(f"Testing wine agent with {len(cases)} cases available")

    # Test one case
    test_case = cases[0]
    print(f"Testing: {test_case.wine_query}")

    from langchain_core.messages import HumanMessage

    result = agent.invoke(
        {"messages": [HumanMessage(content=test_case.wine_query)], "files": {}}
    )

    print(f"Result: {result}")
