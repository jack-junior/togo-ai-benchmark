# Togo AI Benchmark — Pipeline et mode d'emploi complet

Ce document décrit l'architecture, les formats, le flux de données, et les procédures opérationnelles pour exécuter et maintenir le pipeline de benchmarking (runners → évaluateurs LLM → annotations humaines → dashboard → analyses reproductibles). Destiné à l'équipe pour prise en main et poursuite du projet.

---

## 1. Vue d'ensemble

- Objectif: comparer automatiquement et humainement les réponses de modèles LLM dans le contexte togolais, produire des scores et rapports réutilisables pour publication.
- Flux principal: Runner (génère réponses) → Raw outputs (`outputs/raw/*.jsonl`) → Evaluator LLM (évalue automatiquement) → `outputs/evaluations/*.jsonl` → Human annotations via UI → `outputs/human_annotations/*.jsonl` → Dashboard & Notebook (agrégation, visualisations, exports).

## 2. Composants et responsabilités

- Runners (`runners/`): scripts qui lisent un dataset JSONL d'items/questions et appellent un LLM pour générer une réponse. Exemple: `runners/openai_runner.py`, `runners/gemini_runner.py`.
- Evaluators automatiques (`evaluators/*.py`): prennent `outputs/raw/*.jsonl`, appellent un modèle évaluateur (OpenAI ou Gemini) pour produire des scores structurés (C1..C5). Exemple: `evaluators/openai_evaluator.py`, `evaluators/gemini_evaluator.py`.
- Collecte humaine (`evaluators/human/run_human_eval.py`): petite webapp Flask qui présente question+réponse, enregistre annotations (scores + justifications) en JSONL par annotateur.
- Dashboard (`dashboard/app.py`): agrège évaluations automatiques et humaines, offre visualisations par modèle et par question, export CSV et API JSON.
- Notebook reproductible (`notebooks/analysis_reproducible.ipynb`): charge outputs, calcule agrégations, génère figures et exports pour rapports.
- Utilitaires: `utils/common.py` (logger & retry), `scripts/smoke_test.py`.

## 3. Formats de fichiers et conventions

- Format: JSONL (une ligne JSON par enregistrement).
- Raw runner line attendue: {
  - `response_id`: identifiant unique de la réponse,
  - `question_id` ou `metadata.question_id`,
  - `response`: texte produit,
  - `benchmark_metadata` ou `metadata`: {`model`, `provider`, `usage`...}
}
- Evaluator output (par ligne): {
  - `evaluation_metadata`: {`evaluation_id`, `response_id`, `evaluation_timestamp`, `generated_by`, `evaluated_by`}
  - `question_metadata`: {`question_id`, `category`, `language`}
  - `evaluation_scores`: {`C1_*`: {`score`, `justification`}, ...}
  - `aggregate_scores`, `evaluation_summary`, `evaluation_metrics` (latency, tokens)
}
- Human annotation entry: {
  - `annotation_id`, `annotator_id`, `timestamp`, `question_id`, `response_id`,
  - `scores`: {C1...: int}, `justifications`: {C1...: str}, `overall_comments`
}

Conserver `response_id` comme clé de jointure entre raw, auto eval et human annotations.

## 4. Pré-requis

- Python 3.8+ (préférer 3.10+)
- Variables d'environnement:
  - `OPENAI_API_KEY` (si OpenAI),
  - `GEMINI_API_KEY` (si Gemini),
  - optionnels: `GEMINI_MODEL`, `OPENAI_MODEL`, `HUMAN_EVAL_TOKEN` (protéger UI/API).
- Installer dépendances principales:
```bash
python -m venv .venv
.venv/Scripts/activate    # Windows
pip install -r requirements.txt
pip install -r requirements-human.txt
pip install Flask pandas matplotlib seaborn
```

## 5. Quickstart — exécution du pipeline (pas-à-pas)

1. Smoke test (offline, sans API externes):
```bash
python scripts/smoke_test.py
```
Vérifier `outputs/raw/smoke_raw.jsonl` et `outputs/evaluations/smoke_evaluations.jsonl`.

2. Lancer runners (générer réponses):
- OpenAI (exemple):
```bash
python runners/openai_runner.py --source datasets/health/test_questions.jsonl --output outputs/raw/openai_results.jsonl
```
- Gemini (exemple):
```bash
python runners/gemini_runner.py --source datasets/health/test_questions.jsonl --output outputs/raw/gemini_results.jsonl
```

3. Lancer évaluateurs automatiques:
- OpenAI evaluator (évalue raw):
```bash
python evaluators/openai_evaluator.py --input outputs/raw/gemini_results.jsonl --output outputs/evaluations/openai_evaluations.jsonl
```
- Gemini evaluator:
```bash
python evaluators/gemini_evaluator.py --input outputs/raw/openai_results.jsonl --output outputs/evaluations/gemini_evaluations.jsonl
```

4. Collecte humaine (UI):
```bash
export HUMAN_EVAL_TOKEN=mon-token   # facultatif mais recommandé
python evaluators/human/run_human_eval.py --host 0.0.0.0 --port 5000 --source outputs/raw/gemini_results.jsonl
```
Ouvrir `http://127.0.0.1:5000`, annoter avec `annotator_id`. Les annotations sont stockées dans `outputs/human_annotations/<annotator_id>.jsonl`.

5. Dashboard & visualisations:
```bash
python dashboard/app.py --host 0.0.0.0 --port 8050
```
Ouvrir `http://127.0.0.1:8050`. Utiliser la sélection par question, télécharger CSV détaillé via `Télécharger CSV détaillé` ou `/export_details`.

6. Analyse reproductible (notebook):
```bash
jupyter nbconvert --to notebook --execute notebooks/analysis_reproducible.ipynb --ExecutePreprocessor.timeout=600
```
Ce notebook charge `outputs/evaluations` et `outputs/human_annotations`, produit agrégations et exports en `outputs/reports`.

## 6. Détails d'intégration entre étapes

- Le runner écrit `benchmark_metadata` contenant model/provider. Les evaluators lisent ce champ pour décider du modèle évaluateur (logique: env override -> reuse generated model when appropriate -> fallback).
- Les annotations humaines utilisent `response_id` pour se lier au raw; le dashboard construit un `raw_map` (response_id -> generated_model) pour agréger annotations humaines par modèle.
- Les prompts d'évaluateur demandent une sortie JSON stricte pour faciliter le parsing; le code inclut un fallback d'extraction du premier bloc JSON si le modèle renvoie du texte additionnel.

## 7. Pilotage & évaluation qualité

- Recommandation pilote: 100 items × 3 annotateurs.
- Mesures IAA: Cohen's kappa (applications binaires/catégorielles) ou Krippendorff's alpha (continues). Calculer IAA par critère (C1..C5) et corriger consignes si IAA faible.
- Adjudication: définir règles (majority vote, discussion d'experts pour désaccords majeurs).

## 8. Bonnes pratiques pour publication

- Documenter le dataset: taille, stratification, langue, date de collecte.
- Conserver les seeds, versions de packages (`pip freeze > outputs/reports/requirements-<date>.txt`).
- Fournir la méthodologie: prompt templates, barème, processus d'adjudication, protection éthique et consentement annotateurs.
- Préparer un dossier `outputs/reports/<run-timestamp>/` contenant: raw JSONL, eval JSONL, human JSONL, CSVs, figures, notebook exécuté.

## 9. Dépannage rapide

- Pas de fichiers dans `outputs/raw`: vérifier `--source` et la présence des clés API.
- Evaluator renvoie texte non JSON: vérifier logs, relancer pour petit batch, utiliser le fallback ou améliorer prompt.
- Dashboard affiche aucune donnée: vérifier que `outputs/evaluations` et `outputs/human_annotations` existent et contiennent des lignes JSON valides.

## 10. Checklist de publication

- [ ] Dataset décrit et versionné
- [ ] Protocoles d'annotation finalisés
- [ ] Pilot effectué et IAA acceptable
- [ ] Scripts reproductibles (notebook) validés
- [ ] Exports et figures prêtes
- [ ] Documentation technique (`docs/PIPELINE.md`, README) prête

---

Pour toute modification (nouvelle métrique, changement de format, ajout d’un modèle), suivez ces règles:
1. Versionnez les changements (ajoutez `run-id`/`timestamp` dans le nom des outputs).
2. Mettez à jour `config/scoring_criteria.json` et le notebook.
3. Relancez smoke-test avant un run complet.

Contact technique: l’équipe responsable (indiquer personnes) — partager ce document et le notebook pour revue.
