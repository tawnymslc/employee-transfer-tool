from implementation_copilot.schemas import MeetingAnalysisRequest
from implementation_copilot.services import analyze_meeting
from implementation_copilot.evals.scenarios import SCENARIOS
from implementation_copilot.evals.scoring import (
    score_blocker,
    score_action_ownership,
    score_dependencies,
    score_constraints,
)


def run_evals():
    blocker_results = []
    ownership_results = []
    dependency_results = []
    constraint_results = []

    for scenario in SCENARIOS:
        print("\n" + "=" * 60)
        print(f"SCENARIO: {scenario['id']}")
        print("=" * 60)

        request = MeetingAnalysisRequest(
            customer=scenario["customer"],
            meeting_notes=scenario["meeting_notes"],
            consultant_notes=scenario["consultant_notes"],
        )

        result = analyze_meeting(request)

        blocker_score = score_blocker(
            result=result,
            expected=scenario["expected"],
        )

        blocker_results.append({
            "scenario": scenario["id"],
            **blocker_score,
        })

        ownership_score = score_action_ownership(
            result=result,
            expected=scenario["expected"],
        )

        ownership_results.append({
            "scenario": scenario["id"],
            **ownership_score,
        })

        dependency_score = score_dependencies(
            result=result,
            expected=scenario["expected"],
        )

        dependency_results.append({
            "scenario": scenario["id"],
            **dependency_score,
        })

        constraint_score = score_constraints(
            result=result,
            expected=scenario["expected"],
        )

        constraint_results.append({
            "scenario": scenario["id"],
            **constraint_score,
        })

        print("\nAI RESULT:")
        print(result.model_dump_json(indent=2))

        print("\nEXPECTED:")
        print(scenario["expected"])

    print("\n" + "=" * 60)
    print("BLOCKER EVALUATION")
    print("=" * 60)

    passed_count = 0

    for evaluation in blocker_results:
        status = "PASS" if evaluation["passed"] else "FAIL"

        if evaluation["passed"]:
            passed_count += 1

        print(
            f"{evaluation['scenario']:<30} "
            f"{status} "
            f"(expected={evaluation['expected']}, "
            f"actual={evaluation['actual']})"
        )

    total = len(blocker_results)
    accuracy = (passed_count / total) * 100 if total else 0

    print("\nRESULTS")
    print(f"Passed: {passed_count}/{total}")
    print(f"Accuracy: {accuracy:.1f}%")

    print("\n" + "=" * 60)
    print("ACTION OWNERSHIP EVALUATION")
    print("=" * 60)

    total_expected_actions = 0
    total_matched_actions = 0

    for evaluation in ownership_results:
        client = evaluation["client"]
        internal = evaluation["internal"]

        print(f"\n{evaluation['scenario']}")

        if client["matched"] or client["missed"]:
            print(
                f"  Client:   "
                f"{len(client['matched'])}/"
                f"{len(client['matched']) + len(client['missed'])}"
            )

            for missed in client["missed"]:
                print(f"    MISSED: {missed}")

        if internal["matched"] or internal["missed"]:
            print(
                f"  Internal: "
                f"{len(internal['matched'])}/"
                f"{len(internal['matched']) + len(internal['missed'])}"
            )

            for missed in internal["missed"]:
                print(f"    MISSED: {missed}")

        total_expected_actions += (
            len(client["matched"])
            + len(client["missed"])
            + len(internal["matched"])
            + len(internal["missed"])
        )

        total_matched_actions += (
            len(client["matched"])
            + len(internal["matched"])
        )

    ownership_accuracy = (
        total_matched_actions / total_expected_actions * 100
        if total_expected_actions
        else 0
    )

    print("\nRESULTS")
    print(
        f"Matched actions: "
        f"{total_matched_actions}/{total_expected_actions}"
    )
    print(f"Action ownership accuracy: {ownership_accuracy:.1f}%")

    print("\n" + "=" * 60)
    print("DEPENDENCY EVALUATION")
    print("=" * 60)

    total_expected_dependencies = 0
    total_matched_dependencies = 0

    for evaluation in dependency_results:
        matched = evaluation["matched"]
        missed = evaluation["missed"]

        if matched or missed:
            print(f"\n{evaluation['scenario']}")
            print(
                f"  Dependencies: "
                f"{len(matched)}/"
                f"{len(matched) + len(missed)}"
            )

            for dependency in missed:
                print(f"    MISSED: {dependency}")

        total_expected_dependencies += (
            len(matched) + len(missed)
        )

        total_matched_dependencies += len(matched)

    dependency_accuracy = (
        total_matched_dependencies
        / total_expected_dependencies
        * 100
        if total_expected_dependencies
        else 0
    )

    print("\nRESULTS")
    print(
        f"Matched dependencies: "
        f"{total_matched_dependencies}/"
        f"{total_expected_dependencies}"
    )
    print(
        f"Dependency accuracy: "
        f"{dependency_accuracy:.1f}%"
    )

    print("\n" + "=" * 60)
    print("CONSTRAINT EVALUATION")
    print("=" * 60)

    total_expected_constraints = 0
    total_matched_constraints = 0

    for evaluation in constraint_results:
        matched = evaluation["matched"]
        missed = evaluation["missed"]

        if matched or missed:
            print(f"\n{evaluation['scenario']}")
            print(
                f"  Constraints: "
                f"{len(matched)}/"
                f"{len(matched) + len(missed)}"
            )

            for constraint in missed:
                print(f"    MISSED: {constraint}")

        total_expected_constraints += (
            len(matched) + len(missed)
        )

        total_matched_constraints += len(matched)

    constraint_accuracy = (
        total_matched_constraints
        / total_expected_constraints
        * 100
        if total_expected_constraints
        else 0
    )

    print("\nRESULTS")
    print(
        f"Matched constraints: "
        f"{total_matched_constraints}/"
        f"{total_expected_constraints}"
    )
    print(
        f"Constraint accuracy: "
        f"{constraint_accuracy:.1f}%"
    )


if __name__ == "__main__":
    run_evals()