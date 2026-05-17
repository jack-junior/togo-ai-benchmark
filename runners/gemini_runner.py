import os
import json
import time
from datetime import datetime, UTC

from google import genai
from dotenv import load_dotenv
from tqdm import tqdm

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(api_key=GEMINI_API_KEY)

# =========================================================
# CONFIGURATION
# =========================================================

RUN_NAME = "health_pilot_v1"

MODEL = "gemini-3.1-flash-lite"

MAX_TOKENS = 1500

INPUT_FILE = "datasets/health/test_questions.jsonl"
OUTPUT_FILE = "outputs/raw/gemini_results.jsonl"

SYSTEM_PROMPT = """
You are a precise and helpful AI assistant specialized in:
- public health
- informal economy
- socio-economic analysis
- legal systems
- francophone West African contexts, especially Togo.

Provide concise, factual, and well-structured answers.
"""

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def estimate_cost(input_tokens: int, output_tokens: int) -> float:

    input_cost_per_1k = 0.0035
    output_cost_per_1k = 0.0105

    cost = (
        (input_tokens / 1000) * input_cost_per_1k
        + (output_tokens / 1000) * output_cost_per_1k
    )

    return round(cost, 6)


def load_jsonl(file_path: str):

    with open(file_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def append_jsonl(file_path: str, data: dict):

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


# =========================================================
# MAIN EXECUTION
# =========================================================

def run_benchmark():

    dataset = load_jsonl(INPUT_FILE)

    print(f"\nLoaded {len(dataset)} questions")
    print(f"Run name: {RUN_NAME}")
    print(f"Model: {MODEL}")
    print(f"Output file: {OUTPUT_FILE}\n")

    for item in tqdm(dataset):

        question_id = item.get("id")
        question = item.get("question")
        language = item.get("language", "unknown")
        category = item.get("category", "unknown")

        start_time = time.time()

        try:

            full_prompt = f"""
{SYSTEM_PROMPT}

User Question:
{question}
"""

            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt,
                config={
                    "max_output_tokens": MAX_TOKENS
                }
            )

            latency = round(time.time() - start_time, 3)

            output_text = response.text

            usage_metadata = response.usage_metadata

            prompt_tokens = getattr(
                usage_metadata,
                "prompt_token_count",
                None
            )

            completion_tokens = getattr(
                usage_metadata,
                "candidates_token_count",
                None
            )

            total_tokens = getattr(
                usage_metadata,
                "total_token_count",
                None
            )

            estimated_cost = estimate_cost(
                prompt_tokens or 0,
                completion_tokens or 0
            )

            result = {
                "timestamp": datetime.now(UTC).isoformat(),

                "benchmark_metadata": {
                    "run_name": RUN_NAME,
                    "provider": "google",
                    "requested_model": MODEL,
                    "api_returned_model": MODEL,
                    "max_completion_tokens": MAX_TOKENS,
                    "finish_reason": "STOP"
                },

                "question_metadata": {
                    "id": question_id,
                    "category": category,
                    "language": language
                },

                "input": {
                    "question": question
                },

                "output": {
                    "response": output_text
                },

                "metrics": {
                    "latency_seconds": latency,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "reasoning_tokens": None,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": estimated_cost
                },

                "status": "success"
            }

            append_jsonl(OUTPUT_FILE, result)

            print(f"Completed: {question_id}")

        except Exception as e:

            latency = round(time.time() - start_time, 3)

            error_result = {
                "timestamp": datetime.now(UTC).isoformat(),

                "benchmark_metadata": {
                    "run_name": RUN_NAME,
                    "provider": "google",
                    "requested_model": MODEL,
                    "finish_reason": None
                },

                "question_metadata": {
                    "id": question_id,
                    "category": category,
                    "language": language
                },

                "input": {
                    "question": question
                },

                "error": {
                    "message": str(e),
                    "type": type(e).__name__
                },

                "metrics": {
                    "latency_seconds": latency
                },

                "status": "failed"
            }

            append_jsonl(OUTPUT_FILE, error_result)

            print(f"\nERROR on {question_id}")
            print(str(e))

    print("\nBenchmark completed.")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run_benchmark()