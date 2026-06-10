from flask import Flask, render_template, request, jsonify, Response
import json
from pathlib import Path
import os
import statistics
import functools

app = Flask(__name__, template_folder='templates')

DATA_EVAL_DIR = Path('outputs/evaluations')
DATA_RAW_DIR = Path('outputs/raw')
DATA_HUMAN_DIR = Path('outputs/human_annotations')

AUTH_TOKEN = os.environ.get('HUMAN_EVAL_TOKEN')


def require_token(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        if not AUTH_TOKEN:
            return view_func(*args, **kwargs)
        token = request.args.get('token') or request.headers.get('X-Eval-Token')
        if token != AUTH_TOKEN:
            return "Access denied", 403
        return view_func(*args, **kwargs)
    return wrapper


def load_jsonl(path):
    items = []
    p = Path(path)
    if not p.exists():
        return items
    with p.open('r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def build_raw_map():
    # map response_id -> generated model
    mapping = {}
    for f in DATA_RAW_DIR.glob('*.jsonl'):
        for obj in load_jsonl(f):
            rid = obj.get('response_id') or obj.get('id') or obj.get('response', {}).get('id')
            gen = None
            meta = obj.get('benchmark_metadata') or obj.get('metadata') or {}
            gen = meta.get('model') or (obj.get('generated_by') or {}).get('model') or (obj.get('generated_by') or {}).get('provider')
            if rid and gen:
                mapping[str(rid)] = gen
    return mapping


def aggregate_auto_evals():
    per_model = {}
    for f in DATA_EVAL_DIR.glob('*.jsonl'):
        for rec in load_jsonl(f):
            gen = (rec.get('evaluation_metadata', {}).get('generated_by') or {}).get('model') or (rec.get('evaluation_metadata', {}).get('generated_by') or {}).get('provider')
            if not gen:
                gen = 'unknown'
            scores = rec.get('evaluation_scores') or {}
            if gen not in per_model:
                per_model[gen] = {'counts': 0, 'metrics': {}}
            per_model[gen]['counts'] += 1
            for k, v in scores.items():
                # expect v to be object with score
                s = v.get('score') if isinstance(v, dict) else v
                try:
                    s = float(s)
                except Exception:
                    continue
                per_model[gen]['metrics'].setdefault(k, []).append(s)
    # compute averages
    summary = {}
    for m, data in per_model.items():
        summary[m] = {'count': data['counts'], 'metrics': {}}
        for k, vals in data['metrics'].items():
            summary[m]['metrics'][k] = round(statistics.mean(vals), 3)
    return summary


def aggregate_auto_per_question():
    # question_id -> model -> metric -> [scores]
    data = {}
    for f in DATA_EVAL_DIR.glob('*.jsonl'):
        for rec in load_jsonl(f):
            qid = (rec.get('question_metadata') or {}).get('question_id') or (rec.get('question_id'))
            gen = (rec.get('evaluation_metadata', {}).get('generated_by') or {}).get('model') or (rec.get('evaluation_metadata', {}).get('generated_by') or {}).get('provider') or 'unknown'
            scores = rec.get('evaluation_scores') or {}
            if not qid:
                continue
            data.setdefault(qid, {})
            data[qid].setdefault(gen, {})
            for k, v in scores.items():
                s = v.get('score') if isinstance(v, dict) else v
                try:
                    s = float(s)
                except Exception:
                    continue
                data[qid][gen].setdefault(k, []).append(s)
    # compute means
    out = {}
    for q, models in data.items():
        out[q] = {}
        for m, metrics in models.items():
            out[q][m] = {k: round(statistics.mean(v), 3) for k, v in metrics.items()}
    return out


def aggregate_human_per_question(raw_map):
    data = {}
    for f in DATA_HUMAN_DIR.glob('*.jsonl'):
        for rec in load_jsonl(f):
            qid = rec.get('question_id')
            rid = rec.get('response_id')
            model = raw_map.get(str(rid), 'unknown')
            scores = rec.get('scores') or {}
            if not qid:
                continue
            data.setdefault(qid, {})
            data[qid].setdefault(model, {})
            for k, v in scores.items():
                try:
                    s = float(v)
                except Exception:
                    continue
                data[qid][model].setdefault(k, []).append(s)
    out = {}
    for q, models in data.items():
        out[q] = {}
        for m, metrics in models.items():
            out[q][m] = {k: round(statistics.mean(v), 3) for k, v in metrics.items()}
    return out


@app.route('/api/question_data')
@require_token
def api_question_data():
    raw_map = build_raw_map()
    auto = aggregate_auto_per_question()
    human = aggregate_human_per_question(raw_map)
    return jsonify({'auto': auto, 'human': human})


@app.route('/export_details')
@require_token
def export_details():
    # Export CSV per question, per model, with metric columns
    raw_map = build_raw_map()
    auto = aggregate_auto_per_question()
    human = aggregate_human_per_question(raw_map)

    # collect metric names
    metric_names = set()
    for d in (auto, human):
        for q in d.values():
            for m in q.values():
                metric_names.update(m.keys())
    metric_names = sorted(metric_names)

    import io, csv
    output = io.StringIO()
    fieldnames = ['question_id', 'model', 'source'] + metric_names
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for qid, models in auto.items():
        for m, metrics in models.items():
            row = {'question_id': qid, 'model': m, 'source': 'auto'}
            for k in metric_names:
                row[k] = metrics.get(k)
            writer.writerow(row)

    for qid, models in human.items():
        for m, metrics in models.items():
            row = {'question_id': qid, 'model': m, 'source': 'human'}
            for k in metric_names:
                row[k] = metrics.get(k)
            writer.writerow(row)

    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=per_question_metrics.csv'
    })


def aggregate_human_evals(raw_map):
    per_model = {}
    for f in DATA_HUMAN_DIR.glob('*.jsonl'):
        for rec in load_jsonl(f):
            rid = rec.get('response_id') or rec.get('response_id')
            model = raw_map.get(str(rid), 'unknown')
            scores = rec.get('scores') or {}
            if model not in per_model:
                per_model[model] = {'counts': 0, 'metrics': {}}
            per_model[model]['counts'] += 1
            for k, v in scores.items():
                try:
                    s = float(v)
                except Exception:
                    continue
                per_model[model]['metrics'].setdefault(k, []).append(s)
    summary = {}
    for m, data in per_model.items():
        summary[m] = {'count': data['counts'], 'metrics': {}}
        for k, vals in data['metrics'].items():
            summary[m]['metrics'][k] = round(statistics.mean(vals), 3)
    return summary


@app.route('/')
@require_token
def index():
    raw_map = build_raw_map()
    auto = aggregate_auto_evals()
    human = aggregate_human_evals(raw_map)
    return render_template('dashboard.html', auto=auto, human=human)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8050)
    args = p.parse_args()
    app.run(host=args.host, port=args.port)
