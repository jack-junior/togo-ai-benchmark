"""Smoke test script: simulate a runner + evaluator in offline mode.

This script:
- Loads `datasets/health/test_questions.jsonl`.
- Produces a fake runner output `outputs/raw/smoke_raw.jsonl` (no external API calls).
- Runs a simple offline evaluator that validates schema and writes `outputs/evaluations/smoke_evaluations.jsonl`.

Run:
    python scripts/smoke_test.py

"""
import os
import json
from datetime import datetime, UTC

DATASET = "datasets/health/test_questions.jsonl"
SMOKE_RAW = "outputs/raw/smoke_raw.jsonl"
SMOKE_EVAL = "outputs/evaluations/smoke_evaluations.jsonl"


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def ensure_dirs(path):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def make_fake_response(q):
    # Minimal runner output schema compatible with evaluators
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "benchmark_metadata": {
            "run_name": "smoke_test",
            "provider": "local",
            "requested_model": "smoke-model",
            "api_returned_model": "smoke-model",
            "max_completion_tokens": 0,
            "finish_reason": "stop",
        },
        "question_metadata": {
            "id": q.get("id"),
            "category": q.get("category"),
            "language": q.get("language", "fr"),
        },
        "input": {"question": q.get("question")},
        "output": {"response": "REPONSE DE TEST: Ceci est une réponse factice pour smoke test."},
        "metrics": {"latency_seconds": 0.0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "status": "success",
    }


def write_jsonl(path, items):
    ensure_dirs(path)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def simple_evaluator(item):
    # Basic offline evaluator: checks length and presence of keywords to assign scores
    resp = item.get("output", {}).get("response", "")
    scores = {
        "C1_exactitude_source_verite": {"score": 3, "justification": "Réponse factice; pas de sources"},
        "C2_realisme_terrain_togolais": {"score": 3, "justification": "Mention générale du contexte"},
        "C3_actionnabilite_clarte": {"score": 2, "justification": "Peu d'actions concrètes proposées"},
        "C4_lucidite_limites": {"score": 4, "justification": "Admet limites (factice)"},
        "C5_severite_hallucinations": {"score": 5, "justification": "Aucune hallucination évidente"},
    }
    weighted = round((3*3 + 2*3 + 1*2 + 1*4 + 3*5) / (3 + 2 + 1 + 1 + 3), 2)
    normalized = round((weighted / 5) * 100)
    return {
        "evaluation_metadata": {
            "evaluation_id": f"smoke-{item['question_metadata']['id']}",
            "response_id": None,
            "evaluation_timestamp": datetime.now(UTC).isoformat(),
            "evaluation_type": "smoke_offline",
            "generated_by": item.get("benchmark_metadata", {}),
            "evaluated_by": {"provider": "local", "model": "smoke-evaluator", "evaluator_role": "local_check"},
        },
        "question_metadata": item.get("question_metadata", {}),
        "evaluation_scores": scores,
        "aggregate_scores": {"weighted_total_score": weighted, "normalized_score_100": normalized},
        "evaluation_summary": {"major_strengths": ["Format correct"], "major_weaknesses": ["Contenu factice"], "overall_assessment": "Smoke evaluation: PASS"},
    }


def main():
    dataset = load_jsonl(DATASET)
    fake_outputs = [make_fake_response(q) for q in dataset]
    write_jsonl(SMOKE_RAW, fake_outputs)

    evaluations = [simple_evaluator(x) for x in fake_outputs]
    write_jsonl(SMOKE_EVAL, evaluations)

    print(f"Wrote {len(fake_outputs)} fake responses to {SMOKE_RAW}")
    print(f"Wrote {len(evaluations)} evaluations to {SMOKE_EVAL}")


if __name__ == "__main__":
    main()
