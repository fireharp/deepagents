"""
Atomic tests for individual wine research tools and components.
These tests focus on specific functionality rather than the full agent pipeline.
"""

import json
import os
import pytest
import sys

from deepagents.evals.eval_runner import load_eval_cases

# Add research directory to path
sys.path.append(
    os.path.join(os.path.dirname(__file__), "..", "..", "examples", "research")
)

# Test data directories
WINES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "test_data", "evals", "wines")
)


@pytest.fixture
def setup_search_env(monkeypatch):
    """Set up environment for Jina search."""
    monkeypatch.setenv("SEARCH_BACKEND", "jina")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)


@pytest.mark.integration
def test_internet_search_tool(setup_search_env):
    """Test the internet search tool directly with wine queries."""
    from wine_agent import internet_search

    # Load a few test cases
    cases = load_eval_cases(WINES_DIR)
    test_cases = cases[:3]  # Test first 3 cases

    state = {
        "messages": [],
        "files": {},
        "is_last_step": False,
        "remaining_steps": 100,
    }

    results = []
    for case in test_cases:
        print(f"\n--- Testing search for: {case.wine_query} ---")

        # Create a proper state object
        state = {
            "messages": [],
            "files": {},
            "is_last_step": False,
            "remaining_steps": 100,
        }

        # Call the search tool directly
        search_result = internet_search.invoke(
            {
                "query": case.wine_query,
                "max_results": 2,
                "include_raw_content": True,
                "unrestricted": True,
                "state": state,
                "tool_call_id": "test",
            }
        )

        # Extract result from Command object
        messages = search_result.update.get("messages", [])
        result_content = ""
        if messages:
            result_content = messages[0].content

        print(f"Search result: {result_content[:200]}...")

        # Parse the JSON result
        import json

        try:
            parsed_result = json.loads(result_content)
            num_results = parsed_result.get("num_results", 0)
            urls = parsed_result.get("urls", [])
        except:
            num_results = 0
            urls = []

        print(f"Search found {num_results} results")

        results.append(
            {
                "query": case.wine_query,
                "num_results": num_results,
                "urls": urls,
                "has_results": num_results > 0,
            }
        )

    # Save results for analysis
    with open("atomic_search_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Assert at least some searches returned results
    successful_searches = sum(1 for r in results if r["has_results"])
    assert (
        successful_searches >= 1 or any(k.startswith(".cache/wine_sources/") for k in state["files"].keys())
    ), "Expected >=1 successful search or cached sources"


@pytest.mark.integration
def test_wine_validator_subagent():
    """Test the wine validator subagent directly."""
    from wine_agent import wine_validator_sub_agent
    from langchain_core.messages import HumanMessage

    # Load validation test cases
    validation_dir = os.path.join(os.path.dirname(WINES_DIR), "validation")
    cases = load_eval_cases(validation_dir)

    # Test a few cases
    test_cases = cases[:5]

    state = {
        "messages": [],
        "files": {},
        "is_last_step": False,
        "remaining_steps": 100,
    }

    results = []
    for case in test_cases:
        query = case.raw.get("query", "")
        expected_pass = case.raw.get("expected_pass", True)

        print(f"\n--- Testing validator for: {query} ---")
        print(f"Expected to pass: {expected_pass}")

        # Create state with the query
        state = {
            "messages": [HumanMessage(content=query)],
            "files": {},
            "is_last_step": False,
            "remaining_steps": 100,
        }

        try:
            # Call validator subagent directly
            result = wine_validator_sub_agent.invoke(state)

            # Check if validation passed/failed as expected
            validation_passed = not any(
                "invalid" in str(msg).lower() or "error" in str(msg).lower()
                for msg in result.get("messages", [])
            )

            results.append(
                {
                    "query": query,
                    "expected_pass": expected_pass,
                    "actual_pass": validation_passed,
                    "correct_prediction": expected_pass == validation_passed,
                }
            )

            print(f"Validation passed: {validation_passed}")

        except Exception as e:
            print(f"Validation failed with error: {e}")
            results.append(
                {
                    "query": query,
                    "expected_pass": expected_pass,
                    "actual_pass": False,
                    "correct_prediction": not expected_pass,
                    "error": str(e),
                }
            )

    # Save results
    with open("atomic_validator_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Check accuracy
    correct_predictions = sum(1 for r in results if r["correct_prediction"])
    accuracy = correct_predictions / len(results)

    print(
        f"\nValidator accuracy: {accuracy:.2%} ({correct_predictions}/{len(results)})"
    )
    assert accuracy >= 0.6, f"Validator accuracy {accuracy:.2%} below 60% threshold"


@pytest.mark.integration
def test_wine_disambiguator_subagent():
    """Test the wine disambiguator subagent directly."""
    from wine_agent import wine_disambiguator_sub_agent
    from langchain_core.messages import HumanMessage

    # Load disambiguation test cases
    disambiguation_dir = os.path.join(os.path.dirname(WINES_DIR), "disambiguation")
    cases = load_eval_cases(disambiguation_dir)

    # Test cases from different categories
    test_cases = cases[:6]  # Mix of different expected outcomes

    state = {
        "messages": [],
        "files": {},
        "is_last_step": False,
        "remaining_steps": 100,
    }

    results = []
    for case in test_cases:
        query = case.raw.get("query", "")
        expected_outcome = case.raw.get("expected_outcome", "")

        print(f"\n--- Testing disambiguator for: {query} ---")
        print(f"Expected outcome: {expected_outcome}")

        # Create state with the query
        state = {
            "messages": [HumanMessage(content=query)],
            "files": {},
            "is_last_step": False,
            "remaining_steps": 100,
        }

        try:
            # Call disambiguator subagent directly
            result = wine_disambiguator_sub_agent.invoke(state)

            # Analyze the result
            messages = result.get("messages", [])
            result_text = " ".join(str(msg) for msg in messages).lower()

            # Simple heuristics to determine outcome
            if "need clarification" in result_text or "ambiguous" in result_text:
                actual_outcome = "needs_clarification"
            elif "multiple" in result_text or "several" in result_text:
                actual_outcome = "overcommit"
            else:
                actual_outcome = "one_exact"

            results.append(
                {
                    "query": query,
                    "expected_outcome": expected_outcome,
                    "actual_outcome": actual_outcome,
                    "correct": expected_outcome == actual_outcome,
                }
            )

            print(f"Actual outcome: {actual_outcome}")

        except Exception as e:
            print(f"Disambiguator failed with error: {e}")
            results.append(
                {
                    "query": query,
                    "expected_outcome": expected_outcome,
                    "actual_outcome": "error",
                    "correct": False,
                    "error": str(e),
                }
            )

    # Save results
    with open("atomic_disambiguator_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Check accuracy
    correct_predictions = sum(1 for r in results if r["correct"])
    accuracy = correct_predictions / len(results)

    print(
        f"\nDisambiguator accuracy: {accuracy:.2%} ({correct_predictions}/{len(results)})"
    )
    # Lower threshold since this is harder
    assert accuracy >= 0.3, f"Disambiguator accuracy {accuracy:.2%} below 30% threshold"


@pytest.mark.integration
def test_wine_field_extraction():
    """Test wine field extraction from search results."""
    from wine_agent import wine_field_sub_agent
    from langchain_core.messages import HumanMessage

    # Load wine research cases
    cases = load_eval_cases(WINES_DIR)
    test_cases = cases[:3]  # Test first 3 cases

    state = {
        "messages": [],
        "files": {},
        "is_last_step": False,
        "remaining_steps": 100,
    }

    results = []
    for case in test_cases:
        print(f"\n--- Testing field extraction for: {case.wine_query} ---")

        # Create state with query and mock some search results
        state = {
            "messages": [HumanMessage(content=case.wine_query)],
            "files": {
                "question.txt": case.wine_query,
                # Mock some search content
                "search_cache.json": json.dumps(
                    {
                        "results": [
                            {
                                "title": f"Wine info for {case.wine_query}",
                                "content": f"This wine {case.wine_query} is produced by a winery. It has specific characteristics.",
                            }
                        ]
                    }
                ),
            },
            "is_last_step": False,
            "remaining_steps": 100,
        }

        try:
            # Call wine field subagent directly
            result = wine_field_sub_agent.invoke(state)

            # Check if wine.json was created
            wine_json = result.get("files", {}).get("wine.json")
            wine_data = {}
            if wine_json:
                try:
                    wine_data = json.loads(wine_json)
                except:
                    pass

            results.append(
                {
                    "query": case.wine_query,
                    "expected_normalized_name": case.normalized_name,
                    "extracted_normalized_name": wine_data.get(
                        "normalized_name", {}
                    ).get("value"),
                    "wine_data_created": bool(wine_json),
                    "has_normalized_name": bool(
                        wine_data.get("normalized_name", {}).get("value")
                    ),
                }
            )

            print(f"Wine data created: {bool(wine_json)}")
            print(
                f"Normalized name extracted: {wine_data.get('normalized_name', {}).get('value')}"
            )

        except Exception as e:
            print(f"Field extraction failed with error: {e}")
            results.append(
                {
                    "query": case.wine_query,
                    "expected_normalized_name": case.normalized_name,
                    "extracted_normalized_name": None,
                    "wine_data_created": False,
                    "has_normalized_name": False,
                    "error": str(e),
                }
            )

    # Save results
    with open("atomic_field_extraction_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Check success rate
    successful_extractions = sum(1 for r in results if r["wine_data_created"])
    success_rate = successful_extractions / len(results)

    print(
        f"\nField extraction success rate: {success_rate:.2%} ({successful_extractions}/{len(results)})"
    )
    assert (
        success_rate >= 0.5
    ), f"Field extraction success rate {success_rate:.2%} below 50% threshold"


if __name__ == "__main__":
    # Run a quick test
    import os

    os.environ["SEARCH_BACKEND"] = "jina"

    # Test search tool
    from wine_agent import internet_search

    cases = load_eval_cases(WINES_DIR)
    test_case = cases[0]

    print(f"Testing search for: {test_case.wine_query}")

    state = {"messages": [], "files": {}, "is_last_step": False, "remaining_steps": 100}
    result = internet_search.invoke(
        {
            "query": test_case.wine_query,
            "max_results": 1,
            "state": state,
            "tool_call_id": "test",
        }
    )

    print(f"Search result: {result}")
