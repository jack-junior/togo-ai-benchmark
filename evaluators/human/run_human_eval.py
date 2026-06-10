from flask import Flask, render_template, request, redirect, url_for, flash, Response
import json
import uuid
import os
from pathlib import Path
from datetime import datetime
import csv
import io
import functools

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('HUMAN_EVAL_SECRET', 'dev-secret')

DEFAULT_SOURCE = os.environ.get('HUMAN_EVAL_SOURCE', 'datasets/health/test_questions.jsonl')
AUTH_TOKEN = os.environ.get('HUMAN_EVAL_TOKEN')
OUTPUT_DIR = Path('outputs/human_annotations')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_items(source_path):
    path = Path(source_path)
    items = []
    if not path.exists():
        return items
    with path.open('r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                # try to recover if it's nested
                continue
            # normalize keys (support both question or prompt formats)
            qid = obj.get('question_id') or obj.get('id') or obj.get('metadata', {}).get('question_id')
            text = obj.get('question') or obj.get('prompt') or obj.get('question_text') or obj.get('text')
            response = obj.get('response') or obj.get('generated_text') or obj.get('model_response') or obj.get('answer')
            response_id = obj.get('response_id') or obj.get('id')
            items.append({
                'question_id': qid,
                'question': text,
                'response': response,
                'response_id': response_id,
                'raw': obj,
            })
    return items


def require_token(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        if not AUTH_TOKEN:
            return view_func(*args, **kwargs)
        # token can be provided as query param or header
        token = request.args.get('token') or request.headers.get('X-Eval-Token') or request.form.get('token')
        if token != AUTH_TOKEN:
            return "Access denied: invalid or missing token", 403
        return view_func(*args, **kwargs)
    return wrapper


@app.route('/', methods=['GET', 'POST'])
def index():
    source = request.args.get('source', DEFAULT_SOURCE)
    idx = int(request.args.get('idx', 0))
    items = load_items(source)
    total = len(items)

    if request.method == 'POST':
        annotator_id = request.form.get('annotator_id', '').strip()
        if not annotator_id:
            flash('Veuillez renseigner un identifiant annotateur', 'error')
            return redirect(url_for('index', idx=idx, source=source))

        # collect scores
        scores = {}
        justifications = {}
        for c in ['C1_exactitude_source_verite', 'C2_realisme_terrain_togolais', 'C3_actionnabilite_clarte', 'C4_lucidite_limites', 'C5_severite_hallucinations']:
            score = request.form.get(c)
            justification = request.form.get(f'just_{c}', '')
            try:
                score = int(score)
            except Exception:
                score = None
            scores[c] = score
            justifications[c] = justification

        overall_comments = request.form.get('overall_comments', '').strip()

        # build annotation record
        annotation = {
            'annotation_id': str(uuid.uuid4()),
            'annotator_id': annotator_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': source,
            'question_idx': idx,
            'question': items[idx]['question'] if 0 <= idx < total else None,
            'question_id': items[idx].get('question_id') if 0 <= idx < total else None,
            'response': items[idx]['response'] if 0 <= idx < total else None,
            'response_id': items[idx].get('response_id') if 0 <= idx < total else None,
            'scores': scores,
            'justifications': justifications,
            'overall_comments': overall_comments,
        }

        out_file = OUTPUT_DIR / f"{annotator_id}.jsonl"
        with out_file.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(annotation, ensure_ascii=False) + '\n')

        flash('Annotation enregistrée', 'success')
        # go to next
        next_idx = idx + 1
        if next_idx >= total:
            return render_template('done.html', annotator_id=annotator_id, total=total)
        return redirect(url_for('index', idx=next_idx, source=source))

    # GET
    if total == 0:
        return "Aucun item trouvé dans la source indiquée: %s" % source, 404

    item = items[idx % total]
    return render_template('form.html', item=item, idx=idx, total=total, source=source)


@app.route('/instructions')
def instructions():
    return render_template('instructions.html')


@app.route('/export')
@require_token
def export_annotations():
    # aggregate all jsonl files into CSV
    files = list(OUTPUT_DIR.glob('*.jsonl'))
    if not files:
        return "No annotations found", 404

    output = io.StringIO()
    writer = None
    for f in files:
        with f.open('r', encoding='utf-8') as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                # flatten some fields
                row = {
                    'annotation_id': obj.get('annotation_id'),
                    'annotator_id': obj.get('annotator_id'),
                    'timestamp': obj.get('timestamp'),
                    'question_id': obj.get('question_id'),
                    'response_id': obj.get('response_id'),
                    'question': obj.get('question'),
                    'response': obj.get('response'),
                    'overall_comments': obj.get('overall_comments'),
                }
                # include scores and justifications as columns
                for k, v in (obj.get('scores') or {}).items():
                    row[k] = v
                for k, v in (obj.get('justifications') or {}).items():
                    row[f"just_{k}"] = v

                if writer is None:
                    writer = csv.DictWriter(output, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)

    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename=human_annotations.csv'
    })


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=5000)
    p.add_argument('--source', default=DEFAULT_SOURCE)
    args = p.parse_args()
    # run with the provided source
    DEFAULT_SOURCE = args.source
    app.run(host=args.host, port=args.port)
