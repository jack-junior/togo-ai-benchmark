import os
import json
import uuid
import time
import re
from datetime import datetime, UTC
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from utils...` works when running file directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
from utils.common import get_logger, retry

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# =========================================================
# OPENAI CLIENT
# =========================================================

client = OpenAI(api_key=OPENAI_API_KEY)

logger = get_logger(__name__)

# =========================================================
# CONFIGURATION
# =========================================================

EVALUATOR_PROVIDER = "openai"
# Allow override via env var; if not set we'll fallback to the model that generated the response when appropriate
EVALUATOR_MODEL = os.getenv("OPENAI_MODEL")

INPUT_FILE = "outputs/raw/gemini_results.jsonl"

OUTPUT_FILE = "outputs/evaluations/openai_evaluations.jsonl"

PROMPT_FILE = "evaluators/prompts/openai_evaluator_prompt.txt"

SCORING_FILE = "config/scoring_criteria.json"

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def load_json(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(file_path):

    data = []

    with open(file_path, "r", encoding="utf-8") as f:

        for line in f:
            data.append(json.loads(line))

    return data


def append_jsonl(file_path, data):

    dirpath = os.path.dirname(file_path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def load_text(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_evaluation_id():

    return str(uuid.uuid4())


def calculate_weighted_score(scores):

    coefficients = {
        "C1_exactitude_source_verite": 3,
        "C2_realisme_terrain_togolais": 2,
        "C3_actionnabilite_clarte": 1,
        "C4_lucidite_limites": 1,
        "C5_severite_hallucinations": 3
    }

    weighted_sum = 0
    total_weight = 0

    for criterion, coefficient in coefficients.items():

        score = scores[criterion]["score"]

        weighted_sum += score * coefficient

        total_weight += coefficient

    weighted_score = round(weighted_sum / total_weight, 2)

    normalized_score = round((weighted_score / 5) * 100)

    return weighted_score, normalized_score


# =========================================================
# LOAD CONFIG FILES
# =========================================================

scoring_criteria = load_json(SCORING_FILE)

scoring_criteria_text = json.dumps(
    scoring_criteria,
    ensure_ascii=False,
    indent=2
)

prompt_template = load_text(PROMPT_FILE)

# =========================================================
# MAIN EVALUATION FUNCTION
# =========================================================

def evaluate_response(item):

    question = item["input"]["question"]

    response_text = item["output"]["response"]

    generated_provider = item["benchmark_metadata"]["provider"]

    generated_model = item["benchmark_metadata"]["api_returned_model"]

    question_id = item["question_metadata"]["id"]

    category = item["question_metadata"]["category"]

    language = item["question_metadata"]["language"]

    response_id = item.get(
        "response_id",
        str(uuid.uuid4())
    )

    final_prompt = (
        prompt_template
        .replace(
            "{{SCORING_CRITERIA}}",
            scoring_criteria_text
        )
        .replace(
            "{{QUESTION}}",
            question
        )
        .replace(
            "{{RESPONSE}}",
            response_text
        )
    )

    start_time = time.time()

    # Determine evaluator model: prefer explicit OPENAI_MODEL; else reuse generator model when it was OpenAI and looks like a GPT model; else default
    DEFAULT_OPENAI = "gpt-5.5"

    if EVALUATOR_MODEL:
        model_to_use = EVALUATOR_MODEL
    else:
        if generated_provider and str(generated_provider).lower() == "openai" and generated_model and (
            str(generated_model).lower().startswith("gpt") or "gpt-" in str(generated_model).lower()
        ):
            model_to_use = generated_model
        else:
            model_to_use = DEFAULT_OPENAI

    logger.info("Using OpenAI model for evaluation: %s", model_to_use)

    @retry(tries=3, delay=1, backoff=2)
    def call_api():
        return client.chat.completions.create(
            model=model_to_use,
            messages=[{"role": "user", "content": final_prompt}],
            response_format={"type": "json_object"},
        )

    completion = call_api()

    latency = round(time.time() - start_time, 3)

    raw_content = completion.choices[0].message.content

    try:
        parsed_evaluation = json.loads(raw_content)
    except json.JSONDecodeError:
        # Try to extract a JSON object inside the model output
        m = re.search(r"\{.*\}", raw_content, re.DOTALL)
        if m:
            try:
                parsed_evaluation = json.loads(m.group(0))
            except json.JSONDecodeError:
                raise ValueError(
                    "Evaluator returned malformed JSON. Raw start: " + raw_content[:1000]
                )
        else:
            raise ValueError(
                "Evaluator returned non-JSON response. Raw start: " + raw_content[:1000]
            )

    evaluation_scores = parsed_evaluation.get("evaluation_scores")

    if evaluation_scores is None:
        raise ValueError("Parsed evaluation missing 'evaluation_scores' field")

    weighted_score, normalized_score = calculate_weighted_score(evaluation_scores)

    final_evaluation = {

        "evaluation_metadata": {

            "evaluation_id": generate_evaluation_id(),

            "response_id": response_id,

            "evaluation_timestamp": (
                datetime.now(UTC).isoformat()
            ),

            "evaluation_type": (
                "ai_cross_evaluation"
            ),

            "generated_by": {
                "provider": generated_provider,
                "model": generated_model
            },

            "evaluated_by": {
                "provider": EVALUATOR_PROVIDER,
                "model": model_to_use,
                "evaluator_role": "llm_judge"
            }
        },

        "question_metadata": {

            "question_id": question_id,

            "category": category,

            "language": language
        },

        "evaluation_scores": evaluation_scores,

        "aggregate_scores": {

            "weighted_total_score": (
                weighted_score
            ),

            "normalized_score_100": (
                normalized_score
            )
        },

        "evaluation_summary": (
            parsed_evaluation[
                "evaluation_summary"
            ]
        ),

        "evaluation_metrics": {

            "latency_seconds": latency,

            "prompt_tokens": getattr(getattr(completion, "usage", None), "prompt_tokens", None),

            "completion_tokens": getattr(getattr(completion, "usage", None), "completion_tokens", None),

            "total_tokens": getattr(getattr(completion, "usage", None), "total_tokens", None)
        }
    }

    return final_evaluation


# =========================================================
# MAIN EXECUTION
# =========================================================

def run_evaluator():

    dataset = load_jsonl(INPUT_FILE)

    print(
        f"\nLoaded {len(dataset)} responses"
    )

    print(
        f"Evaluator model: {EVALUATOR_MODEL if EVALUATOR_MODEL else 'dynamic (per-response; will reuse generator model when appropriate or fallback to gpt-5.5)'}"
    )

    print(
        f"Input file: {INPUT_FILE}"
    )

    print(
        f"Output file: {OUTPUT_FILE}\n"
    )

    for item in tqdm(dataset):

        try:

            evaluation = (
                evaluate_response(item)
            )

            append_jsonl(
                OUTPUT_FILE,
                evaluation
            )

            question_id = (
                item["question_metadata"]["id"]
            )

            print(
                f"Evaluated: {question_id}"
            )

        except Exception as e:

            print("\nERROR:")
            print(str(e))

    print("\nEvaluation completed.")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_evaluator()