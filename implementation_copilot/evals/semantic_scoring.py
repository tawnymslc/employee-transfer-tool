import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from implementation_copilot.schemas import ImplementationUpdate


if not os.getenv("OPENAI_API_KEY"):
    load_dotenv(".env.development")


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


class SemanticMatch(BaseModel):
    match: bool
    reason: str

class SemanticGroupResult(BaseModel):
    matched: list[str]
    missed: list[str]
    reason: str

def semantic_match(
    expected: str,
    actual: str,
    evaluation_type: str = "general",
) -> SemanticMatch:

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "You are evaluating the output of an AI implementation assistant. "
                    "Determine whether the actual statement captures the implementation "
                    "meaning or requirement represented by the expected statement. "
                    "The actual statement may be more specific, more detailed, or worded "
                    "differently than the expected statement. "
                    "A match does not require identical wording or identical level of detail. "
                    "Mark it as a match when the expected implementation concept is clearly "
                    "represented by the actual statement without contradicting it. "
                    "Do not mark statements as matching merely because they discuss the same "
                    "general topic. The actual statement must substantively capture the "
                    "expected responsibility, dependency, constraint, or requirement. "
                    f"The evaluation type is: {evaluation_type}. "
                    "When evaluating an action, one actual task may combine multiple expected "
                    "actions. Mark the expected action as matched if its required action is "
                    "clearly contained within the larger actual task."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"EXPECTED:\n{expected}\n\n"
                    f"ACTUAL:\n{actual}"
                ),
            },
        ],
        text_format=SemanticMatch,
    )

    return response.output_parsed

def semantic_match_group(
    expected_items: list[str],
    actual_items: list[str],
) -> SemanticGroupResult:

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "You are evaluating action items extracted by an AI "
                    "implementation assistant. "
                    "Compare the complete list of expected actions against "
                    "the complete list of actual actions. "
                    "Determine which expected actions are substantively "
                    "represented in the actual actions. "
                    "One actual action may satisfy multiple expected actions. "
                    "Actions may be combined, more detailed, or worded differently. "
                    "Do not require identical wording. "
                    "Do not mark an expected action as matched unless the "
                    "actual actions clearly represent the required work. "
                    "Return each expected action exactly once in either "
                    "matched or missed, using its original wording. "
                    "Do not invent additional expected actions."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"EXPECTED ACTIONS:\n{expected_items}\n\n"
                    f"ACTUAL ACTIONS:\n{actual_items}"
                ),
            },
        ],
        text_format=SemanticGroupResult,
    )

    return response.output_parsed

def score_semantic_group(
    expected_items: list[str],
    actual_items: list[str],
    evaluation_type: str = "general",
) -> dict:

    matched = []
    missed = []

    for expected_item in expected_items:
        found_match = False

        for actual_item in actual_items:
            result = semantic_match(
                expected=expected_item,
                actual=actual_item,
                evaluation_type=evaluation_type,
            )

            if result.match:
                found_match = True
                break

        if found_match:
            matched.append(expected_item)
        else:
            missed.append(expected_item)

    total = len(expected_items)

    return {
        "passed": len(missed) == 0,
        "matched": matched,
        "missed": missed,
        "score": len(matched) / total if total else 1.0,
    }

def score_semantic_constraints(
    result: ImplementationUpdate,
    expected: dict,
) -> dict:

    expected_constraints = expected.get("constraints", [])

    return score_semantic_group(
        expected_items=expected_constraints,
        actual_items=result.constraints,
    )

def score_semantic_dependencies(
    result: ImplementationUpdate,
    expected: dict,
) -> dict:

    expected_dependencies = expected.get("dependencies", [])

    return score_semantic_group(
        expected_items=expected_dependencies,
        actual_items=result.dependencies,
    )

def score_semantic_action_ownership(
    result: ImplementationUpdate,
    expected: dict,
) -> dict:

    expected_client = expected.get("client_actions", [])
    expected_internal = expected.get("internal_actions", [])

    actual_client = [
        f"{action.task} (Owner: {action.owner or 'Client'})"
        for action in result.client_action_items
    ]

    actual_internal = [
        f"{action.task} (Owner: {action.owner or 'Internal team'})"
        for action in result.internal_action_items
    ]

    client_result = semantic_match_group(
        expected_items=expected_client,
        actual_items=actual_client,
    )

    internal_result = semantic_match_group(
        expected_items=expected_internal,
        actual_items=actual_internal,
    )

    client_score = {
        "passed": len(client_result.missed) == 0,
        "matched": client_result.matched,
        "missed": client_result.missed,
        "score": (
            len(client_result.matched) / len(expected_client)
            if expected_client else 1.0
        ),
    }

    internal_score = {
        "passed": len(internal_result.missed) == 0,
        "matched": internal_result.matched,
        "missed": internal_result.missed,
        "score": (
            len(internal_result.matched) / len(expected_internal)
            if expected_internal else 1.0
        ),
    }

    return {
        "client": client_score,
        "internal": internal_score,
    }