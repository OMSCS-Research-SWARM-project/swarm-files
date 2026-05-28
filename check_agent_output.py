"""
Student diagnostic script to check agent output against labeled datasets.

Usage:
    uv run python datasets/student_release/check_agent_output.py \
      --expected datasets/student_release/realistic_sample/expected_classifications.json \
      --agent-output tmp/_sample_agent_output.json
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_CLASSIFICATION_KEYS = {
    "event_id",
    "classification",
    "scenario_id",
    "cve",
}


def normalize_classification(classification: dict[str, Any]) -> dict[str, Any]:
    """Normalize a possibly-rich agent classification to spec fields."""
    return {
        "event_id": classification["event_id"],
        "classification": classification["classification"],
        "scenario_id": classification.get("scenario_id"),
        "cve": classification.get("cve"),
    }


def load_json(path: Path) -> Any:
    if not path.exists():
        print(f"Error: File not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def index_classifications(
    data: dict[str, Any],
    *,
    label: str,
    strict: bool = False,
) -> tuple[dict[int, dict[str, Any]], list[int]]:
    """Index classifications by event_id and report duplicates."""
    indexed: dict[int, dict[str, Any]] = {}
    duplicates: list[int] = []

    for classification in data.get("classifications", []):
        if strict:
            extra = set(classification) - ALLOWED_CLASSIFICATION_KEYS
            if extra:
                print(
                    f"Error: Expected classification for event {classification.get('event_id')} "
                    f"contains non-spec fields: {sorted(extra)}"
                )
                sys.exit(1)

        normalized = normalize_classification(classification)
        event_id = normalized.get("event_id")
        if event_id in indexed:
            duplicates.append(event_id)
            continue
        indexed[event_id] = normalized

    if duplicates:
        print(f"Duplicate event IDs in {label}: {sorted(duplicates)}")

    return indexed, duplicates


def main():
    parser = argparse.ArgumentParser(
        description="Check agent output against expected classifications."
    )
    parser.add_argument(
        "--expected",
        type=Path,
        required=True,
        help="Path to expected_classifications.json",
    )
    parser.add_argument(
        "--agent-output", type=Path, required=True, help="Path to agent output JSON"
    )
    parser.add_argument(
        "--events", type=Path, help="Optional path to events.json for more context"
    )
    parser.add_argument(
        "--details-csv", type=Path, help="Optional path to write a CSV with details"
    )
    parser.add_argument(
        "--fail-on-mismatch", action="store_true", help="Exit nonzero on any mismatch"
    )

    args = parser.parse_args()

    expected_data = load_json(args.expected)
    agent_data = load_json(args.agent_output)

    expected_classifications, expected_duplicates = index_classifications(
        expected_data,
        label="expected classifications",
        strict=True,
    )
    predicted_classifications, predicted_duplicates = index_classifications(
        agent_data,
        label="agent output",
        strict=False,
    )

    events_context = {}
    if args.events:
        events_data = load_json(args.events)
        events_context = {e["id"]: e for e in events_data.get("events", [])}

    expected_ids = set(expected_classifications.keys())
    predicted_ids = set(predicted_classifications.keys())

    missing_ids = sorted(list(expected_ids - predicted_ids))
    extra_ids = sorted(list(predicted_ids - expected_ids))

    common_ids = expected_ids.intersection(predicted_ids)
    wrong_labels = []
    correct_count = 0

    for eid in sorted(list(common_ids)):
        expected_label = expected_classifications[eid]["classification"]
        predicted_label = predicted_classifications[eid]["classification"]
        if expected_label == predicted_label:
            correct_count += 1
        else:
            wrong_labels.append(eid)

    print("Agent Output Check")
    print("==================")
    print(f"Expected events: {len(expected_ids)}")
    print(f"Predicted events: {len(predicted_ids)}")

    accuracy = (correct_count / len(expected_ids)) * 100 if expected_ids else 0
    print(
        f"Correct labels over expected IDs: {correct_count} / {len(expected_ids)} = {accuracy:.2f}%"
    )

    print(f"Missing IDs: {missing_ids}")
    print(f"Extra IDs: {extra_ids}")
    print(f"Wrong labels: {len(wrong_labels)}")

    if wrong_labels:
        print("\nWrong classifications:")
        for eid in wrong_labels:
            expected = expected_classifications[eid]["classification"]
            predicted = predicted_classifications[eid]["classification"]
            event = events_context.get(eid, {})
            protocol = event.get("protocol", "unknown")
            scenario_id = event.get("scenario_id")
            print(
                f"  event_id={eid} expected={expected} predicted={predicted} protocol={protocol} scenario_id={scenario_id}"
            )

    # Confusion matrix
    if common_ids:
        print("\nError confusion matrix:")
        matrix = {}
        for eid in common_ids:
            expected = expected_classifications[eid]["classification"]
            predicted = predicted_classifications[eid]["classification"]
            if expected != predicted:
                key = (expected, predicted)
                matrix[key] = matrix.get(key, 0) + 1

        for (expected, predicted), count in sorted(matrix.items()):
            print(f"  expected={expected} predicted={predicted} count={count}")

    if args.details_csv:
        args.details_csv.parent.mkdir(parents=True, exist_ok=True)
        with open(args.details_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "event_id",
                    "expected_label",
                    "predicted_label",
                    "status",
                    "protocol",
                    "scenario_id",
                    "expected_cve",
                    "predicted_cve",
                ]
            )
            all_ids = sorted(list(expected_ids.union(predicted_ids)))
            for eid in all_ids:
                expected = expected_classifications.get(eid, {})
                predicted = predicted_classifications.get(eid, {})
                event = events_context.get(eid, {})

                status = "correct"
                if eid in missing_ids:
                    status = "missing"
                elif eid in extra_ids:
                    status = "extra"
                elif eid in wrong_labels:
                    status = "wrong"

                writer.writerow(
                    [
                        eid,
                        expected.get("classification", ""),
                        predicted.get("classification", ""),
                        status,
                        event.get("protocol", ""),
                        event.get("scenario_id", ""),
                        expected.get("cve", ""),
                        predicted.get("cve", ""),
                    ]
                )
        print(f"\nDetails written to {args.details_csv}")

    if args.fail_on_mismatch:
        if (
            expected_duplicates
            or predicted_duplicates
            or missing_ids
            or extra_ids
            or wrong_labels
        ):
            sys.exit(1)


if __name__ == "__main__":
    main()
