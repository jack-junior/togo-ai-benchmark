Togo AI Benchmark — README minimal


Installation

- Créez et activez un environnement Python 

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

- Installez les dépendances :

```bash
pip install -r requirements.txt
```

Variables d'environnement

- Créez un fichier `.env` à la racine et définissez :
  - `OPENAI_API_KEY` (clé OpenAI si vous utilisez `runners/openai_runner.py` ou `evaluators/openai_evaluator.py`)
  - `GEMINI_API_KEY` (clé Google Gemini si vous utilisez `runners/gemini_runner.py` ou `evaluators/gemini_evaluator.py`)
  - `GEMINI_MODEL` (optionnel) : modèle Gemini à utiliser par défaut. Exemple : `gemini-3.1-flash-lite`. Si non spécifié, le projet utilisera `gemini-3.1-flash-lite`.

Exemples :

```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=ya29...
```

Exécution rapide (smoke test)

- Générer réponses (runners) — utilise `datasets/health/test_questions.jsonl` :

```bash
python runners/openai_runner.py
python runners/gemini_runner.py
```

- Lancer les évaluateurs (prend en entrée les fichiers dans `outputs/raw/`) :

```bash
python evaluators/openai_evaluator.py
python evaluators/gemini_evaluator.py
```

Fichiers d'entrée/sortie importants

- `datasets/health/test_questions.jsonl` : dataset d'exemple
- `outputs/raw/openai_results.jsonl` et `outputs/raw/gemini_results.jsonl` : sorties brutes existantes
- `outputs/evaluations/` : dossier de sortie pour évaluations (créé automatiquement)



Conventions JSONL et format des questions

- Format d'une ligne (question) dans les fichiers JSONL (`datasets/*.jsonl`):

```json
{
  "id": "HLT_001",
  "language": "fr",
  "category": "health",
  "question": "Texte de la question en français"
}
```

- Format attendu d'une sortie de runner (extrait):

```json
{
  "timestamp": "ISO8601",
  "benchmark_metadata": {"run_name": "...", "provider": "openai|google|local", ...},
  "question_metadata": {"id": "HLT_001", "category": "health", "language": "fr"},
  "input": {"question": "..."},
  "output": {"response": "Texte du modèle"},
  "metrics": {...},
  "status": "success"
}
```

Contribution et bonnes pratiques

- Ouvrez une issue pour tout bug ou proposition d'amélioration.
- Respectez la structure JSONL et testez localement avec `scripts/smoke_test.py` avant d'ouvrir une PR.
- N'ajoutez pas de clés secrètes au dépôt; utilisez le fichier `.env` pour les clés d'API.

Logger et retry

- Un utilitaire `utils/common.py` fournit un logger simple (`get_logger`) et un décorateur `retry`.
- Les runners et évaluateurs utilisent `retry` autour des appels API pour réduire les échecs transitoires.

Script de smoke-test

- `scripts/smoke_test.py` génère `outputs/raw/smoke_raw.jsonl` puis `outputs/evaluations/smoke_evaluations.jsonl` sans appeler d'API externe : utile pour valider le pipeline et les formats.

