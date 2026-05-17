import os
import json
import time
from datetime import datetime, UTC

from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

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

# =========================================================
# CONFIGURATION
# =========================================================

RUN_NAME = "health_pilot_v1"

MODEL = "gpt-5.5"

MAX_TOKENS = 1500

INPUT_FILE = "datasets/health/test_questions.jsonl"
OUTPUT_FILE = "outputs/raw/openai_results.jsonl"

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
    """
    Approximate cost estimation.
    Update pricing according to current OpenAI pricing.
    """

    # Placeholder pricing
    input_cost_per_1k = 0.005
    output_cost_per_1k = 0.015

    cost = (
        (input_tokens / 1000) * input_cost_per_1k
        + (output_tokens / 1000) * output_cost_per_1k
    )

    return round(cost, 6)


def load_jsonl(file_path: str):
    """
    Load JSONL dataset.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def append_jsonl(file_path: str, data: dict):
    """
    Append one JSON object to JSONL output file.
    """

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

            response = client.chat.completions.create(
                model=MODEL,
                max_completion_tokens=MAX_TOKENS,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            )

            latency = round(time.time() - start_time, 3)

            output_text = response.choices[0].message.content

            usage = response.usage

            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

            reasoning_tokens = (
                usage.completion_tokens_details.reasoning_tokens
            )

            estimated_cost = estimate_cost(
                prompt_tokens,
                completion_tokens
            )

            result = {
                "timestamp": datetime.now(UTC).isoformat(),

                "benchmark_metadata": {
                    "run_name": RUN_NAME,
                    "provider": "openai",
                    "requested_model": MODEL,
                    "api_returned_model": response.model,
                    "max_completion_tokens": MAX_TOKENS,
                    "finish_reason": response.choices[0].finish_reason
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
                    "reasoning_tokens": reasoning_tokens,
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
                    "provider": "openai",
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