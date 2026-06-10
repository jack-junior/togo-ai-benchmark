# Dashboard

Lightweight Flask dashboard that aggregates automatic evaluator scores (`outputs/evaluations/*.jsonl`) and human annotations (`outputs/human_annotations/*.jsonl`).

Run:

```bash
pip install Flask
python dashboard/app.py --host 0.0.0.0 --port 8050
```

If `HUMAN_EVAL_TOKEN` is set, provide `?token=...` to access the dashboard.
