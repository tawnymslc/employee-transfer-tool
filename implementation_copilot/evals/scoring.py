from implementation_copilot.schemas import ImplementationUpdate
import re

STOP_WORDS = {
    "a", "an", "the", "and", "or", "to", "for",
    "of", "in", "on", "when", "is", "are", "be",
    "been", "with", "that", "their"
}

def score_blocker(
    result: ImplementationUpdate,
    expected: dict
) -> dict:
    expected_blocker = expected["blocker"]
    actual_blocker = len(result.blockers) > 0

    passed = expected_blocker == actual_blocker

    return {
        "passed": passed,
        "expected": expected_blocker,
        "actual": actual_blocker,
    }

def normalize_text(text: str) -> set[str]:
    words = re.findall(r"\b\w+\b", text.lower())

    return {
        word
        for word in words
        if word not in STOP_WORDS
    }


def action_matches(expected_action: str, actual_action: str) -> bool:
    expected_words = normalize_text(expected_action)
    actual_words = normalize_text(actual_action)

    if not expected_words:
        return False

    overlap = expected_words.intersection(actual_words)

    return len(overlap) / len(expected_words) >= 0.5


def score_action_group(
    expected_actions: list[str],
    actual_actions: list
) -> dict:
    matched = []
    missed = []

    for expected_action in expected_actions:
        found_match = any(
            action_matches(
                expected_action,
                actual if isinstance(actual, str) else actual.task
            )
            for actual in actual_actions
        )

        if found_match:
            matched.append(expected_action)
        else:
            missed.append(expected_action)

    total = len(expected_actions)

    return {
        "passed": len(missed) == 0,
        "matched": matched,
        "missed": missed,
        "score": len(matched) / total if total else 1.0,
    }

def score_action_ownership(
    result: ImplementationUpdate,
    expected: dict
) -> dict:
    expected_client = expected.get("client_actions", [])
    expected_internal = expected.get("internal_actions", [])

    client_score = score_action_group(
        expected_client,
        result.client_action_items,
    )

    internal_score = score_action_group(
        expected_internal,
        result.internal_action_items,
    )

    return {
        "client": client_score,
        "internal": internal_score,
    }

def score_dependencies(
    result: ImplementationUpdate,
    expected: dict
) -> dict:
    expected_dependencies = expected.get("dependencies", [])

    return score_action_group(
        expected_dependencies,
        result.dependencies,
    )

def score_constraints(
    result: ImplementationUpdate,
    expected: dict
) -> dict:
    expected_constraints = expected.get("constraints", [])

    return score_action_group(
        expected_constraints,
        result.constraints,
    )