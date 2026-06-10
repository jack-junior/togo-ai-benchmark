# Human evaluation web runner

Run a lightweight Flask app to collect human annotations for model responses.

Usage:

1. Install dependencies (add `Flask` to your env):

```bash
pip install Flask
```

2. Launch the app (default source: `datasets/health/test_questions.jsonl`):

```bash
python evaluators/human/run_human_eval.py --host 0.0.0.0 --port 5000 --source outputs/raw/gemini_results.jsonl
```

3. Open http://127.0.0.1:5000 in a browser, provide an `annotator_id`, and annotate.

Annotations are appended to `outputs/human_annotations/<annotator_id>.jsonl`.

Optional features
- Protect the app with a token by setting environment variable `HUMAN_EVAL_TOKEN`.
	Provide the token via `?token=...` or the `X-Eval-Token` header to access export endpoints.
- Export all annotations as CSV via the `/export` endpoint (requires token if enabled):

```bash
curl 'http://127.0.0.1:5000/export?token=YOUR_TOKEN' -o annotations.csv
```
